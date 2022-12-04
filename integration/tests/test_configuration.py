"""Configuration plugin tests"""

from datetime import datetime
from pytest_c8y.models import Software, Configuration
from integration.fixtures.device.device import Device

PLUGIN_NAME = "c8y-configuration-plugin"
PLUGIN_CONFIG = """
files = [
    { path = '/etc/tedge/tedge.toml', type = 'tedge.toml' },
    { path = '/etc/tedge/mosquitto-conf/c8y-bridge.conf' },
    { path = '/etc/tedge/mosquitto-conf/tedge-mosquitto.conf' },
    { path = '/etc/mosquitto/mosquitto.conf', type = 'mosquitto', user = 'mosquitto', group = 'mosquitto', mode = 0o644 }
]
"""


def test_set_configuration(
    dut: Device,
):
    """get/set configuration using Cumulocity"""
    dut.cloud.software_management.install(Software(PLUGIN_NAME)).assert_success()

    config = (
        f"# Test configuration generated on {datetime.now().isoformat()}Z\n"
        + PLUGIN_CONFIG
    )

    with dut.cloud.binaries.new_binary("dummyfile", contents=config) as ref:
        operation = dut.cloud.configuration.set_configuration(
            Configuration(type=PLUGIN_NAME, url=ref.url),
        )
        operation.assert_success()

    operation = dut.cloud.configuration.get_configuration(
        Configuration(type=PLUGIN_NAME)
    )
    operation.assert_success()

    # Event should have been created with an attachment
    events = dut.cloud.events.assert_count(
        type=PLUGIN_NAME,
        with_attachment=True,
        after=dut.device.test_start_time,
        max_matches=1,
    )
    dut.cloud.events.assert_attachment_info(events[0], expected_name_pattern=r"^.+$")
    dut.cloud.events.assert_attachment(events[0].id, expected_contents=config)
