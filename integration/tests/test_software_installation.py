"""Software installation tests"""

import pytest
from pytest_c8y.models import Software
from integration.fixtures.device.device import Device

SEMVER_PATTERN = r"^\d+\.\d+\.\d+\S*$"


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
    dut: Device,
):
    """Install standard plugins"""
    operation = dut.cloud.software_management.install(
        Software(name=plugin_name),
        timeout=60,
    )
    operation.assert_success()
    dut.cloud.software_management.assert_software_installed(
        Software(name=plugin_name, version=SEMVER_PATTERN),
    )
