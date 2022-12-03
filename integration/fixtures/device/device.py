"""Device"""
from pytest_c8y.device_management import DeviceManagement
from integration.fixtures.device.adapter import DeviceAdapter


class Device:
    """Device interfaces
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, adapter: DeviceAdapter, cloud: DeviceManagement = None) -> None:
        self.device = adapter
        self.cloud = cloud
