"""Installation tests"""

import pytest
from pytest_c8y.models import Software
from integration.fixtures.device_mgmt import DeviceManagement


@pytest.mark.parametrize(
    "plugin_name",
    [
        "c8y-log-plugin",
        "c8y-configuration-plugin",
        "c8y-remoteaccess-plugin",
    ],
)
def test_plugin_install(
    plugin_name: str,
    tedge: DeviceManagement,
):
    """Install standard plugins"""
    operation = tedge.software_management.install(
        Software(name=plugin_name),
        timeout=60,
    )
    operation.assert_success()