"""Device"""
from pytest_c8y.core import device_management
from device_test_core.adapter import DeviceAdapter


class Device:
    """Device interfaces"""

    # pylint: disable=too-few-public-methods
    def __init__(
        self, adapter: DeviceAdapter, cloud: device_management.DeviceManagement = None
    ) -> None:
        self.device = adapter
        self.cloud = cloud
