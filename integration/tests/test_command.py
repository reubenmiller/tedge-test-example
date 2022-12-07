"""Command plugin tests"""

import pytest
from pytest_c8y.models import Software
from integration.fixtures.device.device import Device


@pytest.mark.skip("Currently failing in versions <= 0.8.1")
def test_execute_shell_command(
    dut: Device,
):
    """Execute a custom command"""
    operation = dut.cloud.software_management.install(
        Software(name="c8y-command-plugin"),
        timeout=60,
    )
    operation.assert_success()
    operation = dut.cloud.command.execute("ls -la").assert_success().to_json()
    assert operation["c8y_Command"].get("result"), "Result should not be empty"
