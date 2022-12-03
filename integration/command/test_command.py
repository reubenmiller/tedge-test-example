"""Command plugin tests"""

from pytest_c8y.models import Software
from integration.fixtures.device_mgmt import DeviceManagement


def test_execute_command(
    tedge: DeviceManagement,
):
    """Execute a custom command"""
    operation = tedge.software_management.install(
        Software(name="c8y-command-plugin"),
        timeout=60,
    )
    operation.assert_success()
    operation = tedge.command.execute("ls -la").assert_success().to_json()
    assert operation["c8y_Command"].get("result"), "Result should not be empty"
