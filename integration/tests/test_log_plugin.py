"""Cumulocity log plugin tests"""

from datetime import datetime, timedelta
from pytest_c8y.compare import RegexPattern
from pytest_c8y.models import Software, Configuration
from integration.fixtures.device.device import Device

PLUGIN_NAME = "c8y-log-plugin"
PLUGIN_CONFIG = """
files = [
    { type = "mosquitto", path = '/var/log/mosquitto/mosquitto.log' },
    { type = "commands", path = '/var/log/tedge/agent/c8y_Command-*' },
    { type = "software-management", path = '/var/log/tedge/agent/software-*' },
    { type = "c8y_LogRequest", path = '/var/log/tedge/agent/c8y_LogRequest/*' },
    { type = "dummy-log", path = '/var/log/dummy.log' },
]
"""

CONFIG_NAME = "c8y-configuration-plugin"
CONFIG_CONTENTS = """
files = [
    { path = '/etc/tedge/tedge.toml', type = 'tedge.toml' },
    { path = '/etc/tedge/c8y/c8y-log-plugin.toml', type = 'c8y-log-plugin' },
]
"""

LOG_CONTENTS = """
log entry 1
log entry 2
""".strip()


def test_get_log_file(
    dut: Device,
):
    """get a log file using Cumulocity"""
    dut.cloud.software_management.install(
        Software(PLUGIN_NAME),
        Software(CONFIG_NAME),
    ).assert_success()

    log_type = "dummy-log"

    # Update configuration (to enable updating of the log file)
    with dut.cloud.binaries.new_binary("dummyfile", contents=CONFIG_CONTENTS) as ref:
        operation = dut.cloud.configuration.set_configuration(
            Configuration(type=CONFIG_NAME, url=ref.url),
        )
        operation.assert_success()

    # Update log file configuration
    with dut.cloud.binaries.new_binary("dummyfile", contents=PLUGIN_CONFIG) as ref:
        operation = dut.cloud.configuration.set_configuration(
            Configuration(type=PLUGIN_NAME, url=ref.url),
        )
        operation.assert_success()

    # Create dummy file
    code, _ = dut.device.execute_command(
        f"bash -c 'echo \"{LOG_CONTENTS}\"' > /var/log/dummy.log",
        shell=True,
    )
    assert code == 0

    # Request log file
    operation = dut.cloud.create_operation(
        description="Request log file type",
        c8y_LogfileRequest={
            "dateFrom": (datetime.now() - timedelta(hours=1)).isoformat() + "Z",
            "dateTo": datetime.now().isoformat() + "Z",
            "logFile": log_type,
            "maximumLines": 1000,
            "searchText": "",
        },
    )
    op_data = operation.assert_success().to_json()
    assert "file" in op_data["c8y_LogfileRequest"]
    assert op_data["c8y_LogfileRequest"]["file"] == RegexPattern(
        r"^https://.*/event/events/\d+/binaries$"
    )

    # Event should have been created with an attachment
    events = dut.cloud.events.assert_count(
        type=log_type, after=dut.device.test_start_time
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
    expected_contents = f"filename: dummy.log\n{LOG_CONTENTS}\n"
    assert contents == expected_contents, "Configuration roundtrip should match"
