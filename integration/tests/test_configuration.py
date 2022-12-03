"""Configuration plugin tests"""

from datetime import datetime
from pytest_c8y.compare import RegexPattern
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
        type=PLUGIN_NAME, after=dut.device.test_start_time
    )
    assert len(events) == 1, "Should be exactly 1 event"
    event = events[0].to_json()
    assert "c8y_IsBinary" in event
    assert event["c8y_IsBinary"]["name"] == RegexPattern(r"^.+$")

    # Download binary and verify contents
    event_binary_url = (
        dut.cloud.context.client.events.build_object_path(events[0].id) + "/binaries"
    )
    downloaded_file = dut.cloud.c8y.get_file(event_binary_url)
    contents = downloaded_file.decode("utf8")
    assert contents == config, "Configuration roundtrip should match"
