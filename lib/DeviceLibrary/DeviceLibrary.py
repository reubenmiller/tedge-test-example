#!/usr/local/bin/python3
"""Device Library for Robot Framework

It enables the creation of devices which can be used in tests.
It currently support the creation of Docker devices only
"""

import logging
import time
from typing import Any
from datetime import datetime, timezone

from docker.errors import APIError
from pytest_c8y.utils import RandomNameGenerator
from robot.api.deco import keyword, library
from integration.fixtures.device.device import Device
from integration.fixtures.docker.factory import DockerDeviceFactory

log = logging.getLogger()


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

__version__ = "0.0.1"
__author__ = "Reuben Miller"


def generate_name(prefix: str = "STC") -> str:
    """Generate a random name"""
    generator = RandomNameGenerator()
    return "-".join([prefix, generator.random_name()])


@library(scope="GLOBAL", auto_keywords=False)
class DeviceLibrary:
    """Device Library"""

    ROBOT_LISTENER_API_VERSION = 3

    # Default parameter settings
    DEFAULT_IMAGE = "debian-systemd"

    # Class-internal parameters
    __image = ""
    current = None

    # Constructor
    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
    ):
        self.devices = {}
        self.__image = image
        self.current = None
        self.test_start_time = None

        # pylint: disable=invalid-name
        self.ROBOT_LIBRARY_LISTENER = self

    def start_test(self, _data: Any, _result: Any):
        """Hook which is triggered when the test starts

        Store information about the running of the test
        such as the time the test started.

        Args:
            _data (Any): Test case
            _result (Any): Test case results
        """
        self.test_start_time = datetime.now(tz=timezone.utc)

    def end_suite(self, _data: Any, result: Any):
        """End suite hook which is called by Robot Framework
        when the test suite has finished

        Args:
            _data (Any): Test data
            result (Any): Test details
        """
        logger.info("Suite %s (%s) ending", result.name, result.message)
        self.teardown()

    def end_test(self, _data: Any, result: Any):
        """End test hook which is called by Robot Framework
        when the test has ended

        Args:
            _data (Any): Test data
            result (Any): Test details
        """
        logger.info("Listener: detected end of test")
        if not result.passed:
            logger.info("Test '%s' failed: %s", result.name, result.message)

    @keyword("Wait For Device To Be Ready")
    def wait_for_ready(self):
        """Wait for the device to be ready"""
        logger.info("Waiting for device to be ready")
        time.sleep(2)

    @keyword("Get Random Name")
    def get_random_name(self, prefix: str = "STC") -> str:
        """Get random name

        Args:
            prefix (str, optional): Name prefix. Defaults to "STC".

        Returns:
            str: Random name
        """
        return generate_name(prefix)

    @keyword("Setup Device")
    def start(self, skip_bootstrap: bool = False) -> str:
        """Create a container device to use for testing

        Returns:
            str: Device serial number
        """
        device_factory = DockerDeviceFactory()

        device_sn = generate_name()

        device = device_factory.create_device(
            device_sn,
            self.__image,
            env_file=".env",
        )
        # Install/Bootstrap tedge here after the container starts due to
        # install problems when systemd is not running (during the build stage)
        # But it also allows us to possibly customize which version is installed
        # for the test
        if not skip_bootstrap:
            device.assert_command("/demo/bootstrap.sh", log_output=True, shell=True)

        self.devices[device_sn] = device

        dut = Device(
            adapter=device,
            # cloud=device_mgmt,
        )

        self.devices[device_sn] = dut
        self.current = dut
        return device_sn

    @keyword("Execute Device Command")
    def execute_command(
        self, cmd: str, exp_exit_code: int = 0, log_output: bool = True
    ) -> str:
        """Execute a device command

        Args:
            exp_exit_code (int, optional): Expected return code. Defaults to 0.

        Returns:
            str: _description_
        """
        return self.current.device.assert_command(
            cmd, exp_exit_code=exp_exit_code, log_output=log_output
        )

    @keyword("Stop Device")
    def teardown(self):
        """Stop and cleanup the device"""
        for name, device in self.devices.items():
            logger.info("Stopping device: %s", name)
            self.destory_device(device)

    @keyword("Get Device Logs")
    def get_logs(self, name: str = None):
        """Get device log

        Args:
            name (str, optional): name. Defaults to current device.

        Raises:
            Exception: Unknown device
        """
        dut = self.current
        if name:
            if name not in self.devices:
                raise Exception(f"Could not find device. {name}")

            dut = self.devices.get(name)

        for line in dut.device.get_logs():
            print(line)

    def destory_device(self, dut: Device):
        """Destroy the device by either removing the
        container, or shutting down the ssh connection

        Args:
            dut (Device): Device under test
        """
        try:
            # device = dut.device
            # device_sn = device.get_id()
            # cert_fingerprint = (
            #     device.assert_command(
            #         "tedge cert show | grep '^Thumbprint:' | cut -d' ' -f2 | tr A-Z a-z"
            #     )
            #     .decode("utf8")
            #     .strip()
            # )
            # Cleanup cloud device
            # if cert_fingerprint:
            #     dut.cloud.trusted_certificates.delete_certificate(cert_fingerprint)
            # dut.cloud.inventory.delete_device_and_user(managed_object)

            log.info("Removing container")
            dut.device.container.remove(force=True)
        except APIError as ex:
            log.error("Failed cleaning up the container. %s", ex)


if __name__ == "__main__":
    pass
