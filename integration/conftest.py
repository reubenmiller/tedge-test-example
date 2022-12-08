"""Pytest fixtures
"""

import os
import logging
import pytest
from docker.errors import APIError
from pytest_c8y.utils import RandomNameGenerator
from pytest_c8y.device_management import DeviceManagement
from integration.fixtures.device_mgmt import CumulocityDeviceManagement
from integration.fixtures.docker.factory import DockerDeviceFactory
from integration.fixtures.device.device import Device


log = logging.getLogger()


@pytest.fixture(name="device_mgmt", scope="session")
def fixture_device_mgmt(device_mgmt: DeviceManagement) -> CumulocityDeviceManagement:
    """Provide a live CumulocityApi instance as defined by the environment.
    This fixture uses the device_mgmt fixture from pytest_c8y and extends via
    class inheritance
    """
    mgmt = CumulocityDeviceManagement(device_mgmt.context)
    mgmt.configure_retries(timeout=30)
    return mgmt


def generate_name(prefix: str = "STC") -> str:
    """Generate a random name"""
    generator = RandomNameGenerator()
    return "-".join([prefix, generator.random_name()])


@pytest.fixture(name="random_name", scope="function")
def fixture_random_name(variables: dict) -> str:
    """Generate a random name

    Returns:
        str: Random name
    """
    return generate_name(prefix=variables.get("PREFIX", "STC"))


@pytest.fixture(name="random_name_factory")
def fixture_random_name_factory(variables: dict) -> str:
    """Generate a random name

    Returns:
        Callable[[], str]: Random name factory
    """

    def generate():
        return generate_name(prefix=variables.get("PREFIX", "STC"))

    return generate


@pytest.fixture(name="dut")
def device_under_test(device_mgmt: DeviceManagement, request, random_name: str):
    """Create a docker device to use for testing"""
    device_factory = DockerDeviceFactory()

    devices = {}
    device_sn = random_name

    device = device_factory.create_device(
        device_sn,
        "debian-systemd",
        env_file=".env",
        test_suite="inttest",
    )
    # Install/Bootstrap tedge here after the container starts due to
    # install problems when systemd is not running (during the build stage)
    # But it also allows us to possibly customize which version is installed
    # for the test
    device.assert_command("/demo/bootstrap.sh", log_output=False, shell=True)
    cert_fingerprint = (
        device.assert_command(
            "tedge cert show | grep '^Thumbprint:' | cut -d' ' -f2 | tr A-Z a-z"
        )
        .decode("utf8")
        .strip()
    )

    devices[device_sn] = device

    managed_object = device_mgmt.identity.assert_exists(device_sn, "c8y_Serial")

    if managed_object:
        mo_id = managed_object.id
        device_mgmt.context.device_id = mo_id

        mgmt_url = "/".join(
            [
                device_mgmt.c8y.base_url,
                "apps/devicemanagement/index.html#/device",
                mo_id,
                "events",
            ]
        )
        logging.info("-" * 60)
        logging.info("DEVICE SERIAL  : %s", device_sn)
        logging.info("DEVICE ID      : %s", mo_id)
        logging.info("DEVICE URL     : %s", mgmt_url)
        logging.info("-" * 60)

    dut = Device(
        adapter=device,
        cloud=device_mgmt,
    )
    yield dut

    try:
        test_result = ""
        # make logs which are failed so they are easier to find
        test_name = str(request.node.name).replace("[", "-").replace("]", "")

        has_meta_data = hasattr(request.node, "rep_call")

        if has_meta_data and request.node.rep_call.failed:
            test_result = ".failed"

        logging.info("Saving device logs")
        output_folder = "test_output"
        # test_id = session_data.get("test_id", "") + "x" + session_data.get("id", "")
        test_id = "dummy"
        output_file = os.path.join(
            output_folder, f"inttest-{test_id}-{test_name}-{device_sn}{test_result}.log"
        )

        os.makedirs(output_folder, exist_ok=True)

        with open(output_file, "w", encoding="utf8") as file:
            # save stacktrace to output file
            if has_meta_data:
                file.write("--------------------- Test case ---------------------\n")
                file.write(request.node.rep_call.longreprtext)
                file.write(
                    "\n--------------------- Test case end ---------------------\n"
                )

                file.write("\n--------------------- Log output ---------------------\n")
                file.write(request.node.rep_call.caplog)
                file.write(
                    "\n--------------------- Log output end ---------------------\n"
                )

            file.write("\n--------------------- Device logs ---------------------\n")

            file.write("\n".join(device.get_logs()))

        log.info("Removing container")
        device.container.remove(force=True)

        if cert_fingerprint:
            try:
                log.info(
                    "Removing device certificate. fingerprint=%s", cert_fingerprint
                )
                dut.cloud.c8y.delete(
                    (
                        f"/tenant/tenants/{dut.cloud.c8y.tenant_id}"
                        f"/trusted-certificates/{cert_fingerprint}"
                    ),
                )
            except KeyError as ex:
                log.error("Could not delete device certificate. ex=%s", ex)

        # Cleanup device
        try:
            log.info(
                "Removing managed object and child devices. id=%s",
                dut.cloud.context.device_id,
            )
            dut.cloud.c8y.delete(
                f"/inventory/managedObjects/{dut.cloud.context.device_id}",
                params={
                    "cascade": True,
                    "withDeviceUser": False,
                },
            )

            device_owner = f"device_{device_sn}"
            log.info("Removing device certificate. user=%s", device_owner)
            dut.cloud.c8y.delete(
                f"/user/{dut.cloud.c8y.tenant_id}/users/{device_owner}"
            )
        except Exception as ex:
            log.error("Could not delete device. %s", ex)

    except APIError as ex:
        log.error("Failed cleaning up the container. %s", ex)
