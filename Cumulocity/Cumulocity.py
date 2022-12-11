#!/usr/local/bin/python3

import json
import logging
from typing import List, Union

from dotenv import load_dotenv
from pytest_c8y.assert_operation import AssertOperation
from pytest_c8y.c8y import CustomCumulocityApp
from pytest_c8y.device_management import DeviceManagement, create_context_from_identity
from pytest_c8y.models import Software
from robot.api.deco import keyword, library
from robot.utils.asserts import fail

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

__version__ = "0.0.1"
__author__ = "Reuben Miller"

ASSERTION_MAPPING = {
    "assert_count": "Device Should Have %s/s",
    "assert_exists": "%s Should Exist",
}


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

    #
    # Alarms
    #
    @keyword("Device Should Have Alarm/s")
    def alarm_assert_count(self, minimum: int = 1, expected_text: str = None, **kwargs):
        return self._convert_to_json(
            self.__device_mgmt.alarms.assert_count(
                min_matches=minimum, expected_text=expected_text, **kwargs
            )
        )

    @keyword("Alarm Should Exist")
    def alarm_assert_exist(self, alarm_id: str, **kwargs):
        return self._convert_to_json(
            self.__device_mgmt.alarms.assert_exists(alarm_id, **kwargs)
        )

    #
    # Events
    #
    @keyword("Device Should Have Event/s")
    def event_assert_count(
        self,
        expected_text: str = None,
        with_attachment: bool = None,
        minimum: int = 1,
        maximum: int = None,
        **kwargs,
    ):
        return self._convert_to_json(
            self.__device_mgmt.events.assert_count(
                min_matches=minimum,
                max_matches=maximum,
                expected_text=expected_text,
                with_attachment=with_attachment,
                **kwargs,
            )
        )

    @keyword("Event Should Have An Attachment")
    def event_assert_attachment(
        self,
        event_id: str,
        expected_contents: str = None,
        expected_pattern: str = None,
        expected_size_min: int = None,
        encoding: str = None,
        **kwargs,
    ):
        return self._convert_to_json(
            self.__device_mgmt.events.assert_attachment(
                event_id=event_id,
                encoding=encoding,
                expected_contents=expected_contents,
                expected_pattern=expected_pattern,
                expected_size_min=expected_size_min,
                **kwargs,
            )
        )

    @keyword("Event Should Not Have An Attachment")
    def event_assert_no_attachment(self, event_id: str, **kwargs):
        return self._convert_to_json(
            self.__device_mgmt.events.assert_no_attachment(
                event_id=event_id,
                **kwargs,
            )
        )

    #
    # Software
    #
    def _software_format_list(self, *items: str) -> List[Software]:
        return [Software(*item.split(",", 3)) for item in items if item]

    @keyword("Device Should Have Installed Software")
    def software_assert_installed(
        self, *expected_software_list: str, mo: str = None, **kwargs
    ):
        items = self._software_format_list(*expected_software_list)

        return self._convert_to_json(
            self.__device_mgmt.software_management.assert_software_installed(
                *items,
                mo=mo,
                **kwargs,
            )
        )

    @keyword("Install Software")
    def software_install(self, *software_list: str, **kwargs):
        items = self._software_format_list(*software_list)
        operation = self.__device_mgmt.software_management.install(
            *items,
            **kwargs,
        )
        return operation

    #
    # Operations
    #
    @keyword("Operation Should Be SUCCESSFUL")
    def operation_assert_success(self, operation: AssertOperation, **kwargs):
        return self._convert_to_json(operation.assert_success(**kwargs))

    @keyword("Operation Should Be PENDING")
    def operation_assert_pending(self, operation: AssertOperation, **kwargs):
        return self._convert_to_json(operation.assert_pending(**kwargs))

    @keyword("Operation Should Not Be PENDING")
    def operation_assert_not_pending(self, operation: AssertOperation, **kwargs):
        return self._convert_to_json(operation.assert_not_pending(**kwargs))

    @keyword("Operation Should Be DONE")
    def operation_assert_done(self, operation: AssertOperation, **kwargs):
        return self._convert_to_json(operation.assert_done(**kwargs))

    @keyword("Operation Should Be FAILED")
    def operation_assert(
        self, operation: AssertOperation, failure_reason: str = ".+", **kwargs
    ):
        return self._convert_to_json(
            operation.assert_failed(failure_reason=failure_reason, **kwargs)
        )

    #
    # Trusted Certificates
    #
    @keyword("Delete Device Certificate From Platform")
    def trusted_certificate_delete(self, fingerprint: str, **kwargs):
        """Delete the trusted certificate from the platform

        Args:
            fingerprint (str): Certificate fingerprint
        """
        self.__device_mgmt.trusted_certificates.delete_certificate(
            fingerprint,
            **kwargs,
        )

    def _convert_item(self, item: any) -> str:
        if not item:
            return ""

        data = item
        if item and hasattr(item, "to_json"):
            data = item.to_json()

        return json.dumps(data)

    def _convert_to_json(self, item: any) -> Union[str, List[str]]:
        if isinstance(item, list):
            return [self._convert_item(subitem) for subitem in item]

        return self._convert_item(item)

    #
    # Library settings
    #
    @keyword("Set API Timeout")
    def set_timeout(self, timeout: float = 30):
        self.__device_mgmt.configure_retries(timeout=timeout)

    #
    # Devices / Child devices
    #
    @keyword("Set Device")
    def set_device(self, external_id: str = None, external_type: str = "c8y_Serial"):
        identity = self.__device_mgmt.identity.assert_exists(external_id, external_type)
        self.__device_mgmt.set_device_id(identity.id)

    @keyword("Device Should Have Child Devices")
    def assert_child_device_names(self, *name: str):
        return self.__device_mgmt.inventory.assert_child_device_names(*name)

    @keyword("Device Should Have Measurements")
    def assert_measurement_count(self, minimum: int = 1, maximum: int = None, **kwargs):
        try:
            return self._convert_to_json(
                self.__device_mgmt.measurements.assert_count(
                    min_count=minimum, max_count=maximum, **kwargs
                )
            )
        except AssertionError as ex:
            fail(f"not enough measurements were found. args={ex.args}")

    @keyword("Device Should Have Fragments")
    def assert_contains_fragments(self, *fragments: str):
        return self.__device_mgmt.inventory.assert_contains_fragments(fragments)

    @keyword("Device Should Exist")
    def assert_device_exists(self, external_id: str, external_type: str = "c8y_Serial"):
        identity = self.__device_mgmt.identity.assert_exists(external_id, external_type)
        self.__device_mgmt.set_device_id(identity.id)

        mgmt_url = "/".join(
            [
                self.__device_mgmt.c8y.base_url,
                "apps/devicemanagement/index.html#/device",
                identity.id,
                "control",
            ]
        )
        logger.info("-" * 60)
        logger.info("DEVICE SERIAL  : %s", external_id)
        logger.info("DEVICE ID      : %s", identity.id)
        logger.info("DEVICE URL     : %s", mgmt_url)
        logger.info("-" * 60)

        return self.__device_mgmt.inventory.assert_exists()


if __name__ == "__main__":
    pass
