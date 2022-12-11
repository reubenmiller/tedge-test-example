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

from robot.api.deco import library, keyword, not_keyword
from datetime import datetime
import logging
from pytest_c8y.device_management import DeviceManagement
from pytest_c8y.c8y import CustomCumulocityApp
from pytest_c8y.device_management import DeviceManagement, create_context_from_identity
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__author__ = "Reuben Miller"

# Our demo class
# We use Global scope along with Robot's
# "auto_keywords" feature in disabled mode
@library(scope="GLOBAL", auto_keywords=False)
class Cumulocity:

    # Default parameter settings
    DEFAULT_TIMEOUT = 30

    # Class-internal parameters
    __device_mgmt: DeviceManagement = None
    __live_c8y: CustomCumulocityApp = None

    # Constructor
    def __init__(
        self,
        timeout: str = DEFAULT_TIMEOUT,
    ):
        self.devices = {}
        load_dotenv()

        self.__live_c8y = CustomCumulocityApp()
        self.__device_mgmt = create_context_from_identity(self.__live_c8y)
        self.__device_mgmt.configure_retries(timeout=timeout)
        # self.__device_mgmt = create_context_from_identity(live_c8y)

        # self.__device_mgmt.alarms.assert_count.robot_name = "Assert Count"
        # self.assert_count = keyword("Assert Count")(self.__device_mgmt.alarms.assert_count)

    @keyword("Set API Timeout")
    def set_timeout(self, timeout: float = 30):
        self.__device_mgmt.configure_retries(timeout=timeout)

    @keyword("Device Should Have Alarm/s")
    def assert_count(self, min_matches: int = 1, expected_text: str = None, **kwargs):
        self.__device_mgmt.alarms.assert_count(
            min_matches=min_matches, expected_text=expected_text, **kwargs
        )

    @keyword("Set Device")
    def set_device(self, external_id: str = None, external_type: str = "c8y_Serial"):
        identity = self.__device_mgmt.identity.assert_exists(external_id, external_type)
        self.__device_mgmt.set_device_id(identity.id)

    @keyword("Device Should Have Child Devices")
    def assert_child_device_names(self, *name: str):
        return self.__device_mgmt.inventory.assert_child_device_names(*name)

    @keyword("Device Should Have Measurements")
    def assert_measurement_count(self, min_count: int = 1, **kwargs):
        return self.__device_mgmt.measurements.assert_count(
            min_count=min_count, **kwargs
        )

    @keyword("Device Should Have Fragments")
    def assert_contains_framgnets(self, *fragments: str):
        return self.__device_mgmt.inventory.assert_contains_fragments(fragments)

    @keyword("Device Should Exist")
    def assert_device_exists(self, external_id: str, external_type: str = "c8y_Serial"):
        identity = self.__device_mgmt.identity.assert_exists(external_id, external_type)
        self.__device_mgmt.set_device_id(identity.id)
        return self.__device_mgmt.inventory.assert_exists()


if __name__ == "__main__":
    pass
