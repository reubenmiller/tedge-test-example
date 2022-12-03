"""Command plugin tests"""

import pytest
from pytest_c8y.models import Software
from integration.fixtures.device_mgmt import DeviceManagement


@pytest.mark.skip("TODO")
def test_apama_installation(
    tedge: DeviceManagement,
):
    """Execute a custom command"""
    operation = tedge.software_management.install(
        Software(
            name="c8y-command-plugin",
            url="https://svndae.apama.com/apama_installers/Apama/debian-apt/apama-repo-internal_2022_all.deb",
        ),
        timeout=60,
    )
    operation.assert_success()

    alarms = tedge.alarms.assert_count(type="test_alarm")

    operation = tedge.command.execute("ls -la").assert_success().to_json()
    assert operation["c8y_Command"].get("result"), "Result should not be empty"
