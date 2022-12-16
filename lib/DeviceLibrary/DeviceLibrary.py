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

    @keyword("Execute Command On Device")
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
            log.info("Removing container")
            dut.device.container.remove(force=True)
        except APIError as ex:
            log.error("Failed cleaning up the container. %s", ex)

    @keyword("Transfer To Device")
    def transfer_to_device(self, src: str, dst: str):
        """Transfer files to a device

        Args:
            src (str): Source file, folder or pattern
            dst (str): Destination path to copy to the files to
        """
        self.current.device.copy_to(src, dst)

    # ----------------------------------------------------
    # Operation system
    # ----------------------------------------------------
    #
    # APT
    #
    @keyword("Update APT Cache")
    def apt_update(self) -> str:
        """Update APT package cache

        Returns:
            str: Command output
        """
        return self.current.device.assert_command("apt-get update").decode("utf8")

    @keyword("Install Package Using APT")
    def apt_install(self, *packages: str):
        """Install a list of packages via APT

        You can specify specify to install the latest available, or use
        a specific version

        Args:
            *packages (str): packages to be installed. Version is optional, but when
            provided it should be in the format of 'mypackage=1.0.0'

        Returns:
            str: Command output
        """
        return self.current.device.assert_command(
            "apt-get -y install " + " ".join(packages)
        ).decode("utf8")

    @keyword("Remove Package Using APT")
    def apt_remove(self, *packages: str) -> str:
        """Remove a package via APT

        Returns:
            str: Command output
        """
        return self.current.device.assert_command(
            "apt-get -y remove " + " ".join(packages)
        ).decode("utf8")

    @keyword("Purge Package Using APT")
    def apt_purge(self, *packages: str) -> str:
        """Purge a package (and its configuration) using APT

        Args:
            *packages (str): packages to be installed

        Returns:
            str: Command output
        """
        return self.current.device.assert_command(
            "apt-get -y remove " + " ".join(packages)
        ).decode("utf8")

    #
    # Files/folders
    #
    @keyword("Directory Should Be Empty On Device")
    def assert_directory_empty(self, path: str):
        """Check if a directory is empty

        Args:
            path (str): Directory path
        """
        self.current.device.assert_command(f"""
            [ -d '{path}' ] && [ -z "$(ls -A '{path}')" ]
        """.strip())

    @keyword("Directory Should Not Be Empty On Device")
    def assert_directory_not_empty(self, path: str):
        """Check if a directory is empty

        Args:
            path (str): Directory path
        """
        self.current.device.assert_command(f"""
            [ -d '{path}' ] && [ -n "$(ls -A '{path}')" ]
        """.strip())

    @keyword("Directory Should Exist on Device")
    def assert_directory(self, path: str):
        """Check if a directory exists

        Args:
            path (str): Directory path
        """
        self.current.device.assert_command(f"test -d '{path}'")

    @keyword("Directory Should Not Exist on Device")
    def assert_not_directory(self, path: str):
        """Check if a directory does not exists

        Args:
            path (str): Directory path
        """
        self.current.device.assert_command(f"! test -d '{path}'")

    @keyword("File Should Exist on Device")
    def assert_file_exists(self, path: str):
        """Check if a file exists

        Args:
            path (str): File path
        """
        self.current.device.assert_command(f"test -f '{path}'")

    @keyword("File Should Not Exist on Device")
    def assert_not_file_exists(self, path: str):
        """Check if a file does not exists

        Args:
            path (str): File path
        """
        self.current.device.assert_command(f"! test -f '{path}'")

    @keyword("Start Service")
    def start_service(self, name: str, init_system: str = "systemd"):
        """Start a service

        Args:
            path (str): File path
        """
        self._control_service("start", name, init_system=init_system)

    @keyword("Stop Service")
    def stop_service(self, name: str, init_system: str = "systemd"):
        """Stop a service

        Args:
            path (str): File path
        """
        self._control_service("stop", name, init_system=init_system)

    @keyword("Restart Service")
    def restart_service(self, name: str, init_system: str = "systemd"):
        """Restart a service

        Args:
            path (str): File path
        """
        self._control_service("restart", name, init_system=init_system)

    @keyword("Reload Services Manager")
    def reload_services_manager(self, init_system: str = "systemd"):
        """Reload the services manager
        For systemd this would be a systemctl daemon-reload
        """
        # self._control_service("reload", "", init_system=init_system)
        raise NotImplementedError()

    def _control_service(self, action: str, name: str, init_system: str = "systemd"):
        """Check if a file does not exists

        Args:
            path (str): File path
        """
        init_system = init_system.lower()
        action = "start"

        if init_system == "systemd":
            command = f"systemctl {action} {name}"
        elif init_system == "sytemv":
            command = f"systemctl {action} {name}"

        self.current.device.assert_command(command)


    #
    # Processes
    #
    def _count_processes(self, pattern: str) -> int:
        _, output = self.current.device.execute_command(
            f"pgrep --count -fa '{pattern}' || true"
        )
        count = output.decode("utf8").strip()
        return int(count)

    @keyword("Process Should Be Running On Device")
    def assert_process_exists(self, pattern: str):
        """Check if at least 1 process is running given a pattern

        Args:
            pattern (str): Process pattern (passed to pgrep -fa '<pattern>')
        """
        self.current.device.assert_command(f"pgrep -fa '{pattern}'")

    @keyword("Process Should Not Be Running On Device")
    def assert_process_not_exists(self, pattern: str):
        """Check that there are no processes matching a given pattern

        Args:
            pattern (str): Process pattern (passed to pgrep -fa '<pattern>')
        """
        count = self._count_processes(pattern)
        assert count == 0, f"No processes should have matched. got {count}"

    @keyword("Should Match Processes on Device")
    def assert_process_count(
        self, pattern: str, minimum: int = 1, maximum: int = None
    ) -> int:
        """Check how many processes are running which match a given pattern

        Args:
            pattern (str): Process pattern (passed to pgrep -fa '<pattern>')
            minimum (int, optional): Minimum number of matches. Defaults to 1.
            maximum (int, optional): Maximum number of matches. Defaults to None.

        Returns:
            int: Count of matching processes
        """
        count = self._count_processes(pattern)
        if minimum is not None:
            assert (
                count >= minimum
            ), f"Expected process count to be greater than or equal to {minimum}, got {count}"

        if maximum is not None:
            assert (
                count <= maximum
            ), f"Expected process count to be less than or equal to {maximum}, got {count}"

        return count


if __name__ == "__main__":
    pass
