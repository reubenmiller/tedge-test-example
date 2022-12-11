#!/usr/local/bin/python3
#
# A simple Robot Framework library example in Python
# Author: Joerg Schultze-Lutter, 2022
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import os
import logging

import pytest
from robot.api.deco import library, keyword
from pytest_c8y.device_management import DeviceManagement
from pytest_c8y.c8y import CustomCumulocityApp
from pytest_c8y.device_management import DeviceManagement, create_context_from_identity
from dotenv import load_dotenv


from docker.errors import APIError
from pytest_c8y.utils import RandomNameGenerator
from pytest_c8y.device_management import DeviceManagement
from integration.fixtures.device_mgmt import CumulocityDeviceManagement
from integration.fixtures.docker.factory import DockerDeviceFactory
from integration.fixtures.device.device import Device


log = logging.getLogger()


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__author__ = "Reuben Miller"


def generate_name(prefix: str = "STC") -> str:
    """Generate a random name"""
    generator = RandomNameGenerator()
    return "-".join([prefix, generator.random_name()])


# Our demo class
# We use Global scope along with Robot's
# "auto_keywords" feature in disabled mode
@library(scope="GLOBAL", auto_keywords=False)
class DeviceLibrary:

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

        self.ROBOT_LIBRARY_LISTENER = self

    def _end_suite(self, data, result):
        print("Suite %s (%s) ending." % (result.name, result.message))
        self.teardown(test_name=result.name)

    # def end_test(self, name, attributes):
    #     logger.info("Listener: detected end of test")
    #     if not result.passed:
    #         print('Test "%s" failed: %s' % (result.name, result.message))
    #         input('Press enter to continue.')
    def end_test(self, data, result):
        logger.info("Listener: detected end of test")
        if not result.passed:
            print('Test "%s" failed: %s' % (result.name, result.message))
            # input('Press enter to continue.')

    # def _end_suite(self, data, result):
    #     logger.info("Suite is ending. data=%s, result=%s", data, result)
    # print('Suite %s (%s) ending.' % (data, result))

    @keyword("Display Banner")
    def display(self):
        logger.info("DeviceLibrary Banner")

    @keyword("Start Device")
    def start(self) -> str:
        """Create a container device to use for testing"""
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
        device.assert_command("/demo/bootstrap.sh", log_output=True, shell=True)

        self.devices[device_sn] = device

        # managed_object = device_mgmt.identity.assert_exists(device_sn, "c8y_Serial")

        # if managed_object:
        #     mo_id = managed_object.id
        #     device_mgmt.context.device_id = mo_id

        #     mgmt_url = "/".join(
        #         [
        #             device_mgmt.c8y.base_url,
        #             "apps/devicemanagement/index.html#/device",
        #             mo_id,
        #             "events",
        #         ]
        #     )
        #     logging.info("-" * 60)
        #     logging.info("DEVICE SERIAL  : %s", device_sn)
        #     logging.info("DEVICE ID      : %s", mo_id)
        #     logging.info("DEVICE URL     : %s", mgmt_url)
        #     logging.info("-" * 60)

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

    @keyword("Simulate Error")
    def simulate_error(self):
        raise Exception("Simulated error")

    @keyword("Stop Device")
    def teardown(self, test_name: str = None):
        for name, device in self.devices.items():
            logger.info("Stopping device: %s", name)
            self.destory_device(device, test_name)

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

    def destory_device(self, dut: Device, test_name: str = "current-test"):
        try:
            device = dut.device
            device_sn = device.get_id()
            cert_fingerprint = (
                device.assert_command(
                    "tedge cert show | grep '^Thumbprint:' | cut -d' ' -f2 | tr A-Z a-z"
                )
                .decode("utf8")
                .strip()
            )
            test_result = ""
            # make logs which are failed so they are easier to find
            # test_name = str(request.node.name).replace("[", "-").replace("]", "")

            # has_meta_data = hasattr(request.node, "rep_call")

            # if has_meta_data and request.node.rep_call.failed:
            #     test_result = ".failed"

            logger.info("Saving device logs")
            output_folder = "test_output"
            # test_id = session_data.get("test_id", "") + "x" + session_data.get("id", "")
            test_id = "dummy"
            output_file = os.path.join(
                output_folder,
                f"inttest-{test_id}-{test_name}-{device_sn}{test_result}.log",
            )

            # os.makedirs(output_folder, exist_ok=True)

            with open(output_file, "w", encoding="utf8") as file:
                # save stacktrace to output file
                # if has_meta_data:
                #     file.write("\n--------------------- Log output ---------------------\n")
                #     file.write(request.node.rep_call.caplog)
                #     file.write(
                #         "\n--------------------- Log output end ---------------------\n"
                #     )

                file.write(
                    "\n--------------------- Device logs ---------------------\n"
                )

                file.write("\n".join(device.get_logs()))

            logger.info("--------------------- Device logs BEGIN ---------------------")
            for line in device.get_logs():
                print(line)
                # logger.info(line)

            logger.info("--------------------- Device logs END ---------------------")

            log.info("Removing container")
            device.container.remove(force=True)

            # Cleanup cloud device
            # if cert_fingerprint:
            #     dut.cloud.trusted_certificates.delete_certificate(cert_fingerprint)
            # dut.cloud.inventory.delete_device_and_user(managed_object)

        except APIError as ex:
            log.error("Failed cleaning up the container. %s", ex)


if __name__ == "__main__":
    pass
