"""Pytest fixtures
"""

import os
import logging
import pytest
from docker.errors import APIError
from pytest_c8y.utils import RandomNameGenerator
from pytest_c8y.device_management import DeviceManagement
from integration.fixtures.device_mgmt import CumulocityDeviceManagement
from integration.fixtures.device import DockerDeviceFixture

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


@pytest.fixture(name="random_name")
def fixture_random_name(variables: dict) -> str:
    """Generate a random name

    Returns:
        str: Random name
    """
    generator = RandomNameGenerator()
    prefix = "STC"
    if variables:
        prefix = variables.get("PREFIX", "STC")
    return "-".join([prefix, generator.random_name()])


@pytest.fixture
def tedge(device_mgmt: DeviceManagement, request, random_name: str):
    """Create a docker device to use for testing"""
    device_factory = DockerDeviceFixture()

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
    exit_code, _ = device.execute_command("/demo/bootstrap.sh")
    assert exit_code == 0, "Bootstrap should not have any errors"

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

    yield device_mgmt

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
    except APIError as ex:
        log.error("Failed cleaning up the container. %s", ex)
