"""Restart tests"""

import time
from integration.fixtures.device import Device


def test_restart(dut: Device):
    """Restart device via Cumulocity operation"""
    # Wait for devices to startup before restarting
    # NOTE: Check if this is an issue or not, or just something more related to containers
    time.sleep(5)
    operation = dut.cloud.restart()
    operation.assert_success()
