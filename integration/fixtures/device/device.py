from integration.fixtures.device.adapter import DeviceAdapter
from pytest_c8y.device_management import DeviceManagement


class Device:
    def __init__(self, adapter: DeviceAdapter, cloud: DeviceManagement = None) -> None:
        self.device = adapter
        self.cloud = cloud
