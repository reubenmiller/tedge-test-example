"""Restart tests"""

from integration.fixtures.device_mgmt import DeviceManagement

def test_restart(tedge: DeviceManagement):
    """Restart device via Cumulocity operation"""
    operation = tedge.restart()
    operation.assert_success()
