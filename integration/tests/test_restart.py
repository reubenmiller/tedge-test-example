"""Restart tests"""

import time
from integration.fixtures.device_mgmt import DeviceManagement


def test_restart(tedge: DeviceManagement):
    """Restart device via Cumulocity operation"""
    # Wait for devices to startup before restarting
    # NOTE: Check if this is an issue or not, or just something more related to containers
    time.sleep(5)
    operation = tedge.restart()
    operation.assert_success()
