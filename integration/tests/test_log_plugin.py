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
    dut.cloud.configuration.apply_and_wait(
        Configuration(type=CONFIG_NAME), contents=CONFIG_CONTENTS
    )

    # Update log file configuration (to contain the dummy log type)
    dut.cloud.configuration.apply_and_wait(
        Configuration(type=PLUGIN_NAME), contents=PLUGIN_CONFIG
    )

    # Create dummy log file target with contents
    dut.device.assert_command(
        f"""
        echo "{LOG_CONTENTS}" > /var/log/dummy.log
        """
    )

    # Request log file
    operation = dut.cloud.logs.get_logfile(
        type=log_type,
        date_from=datetime.now() - timedelta(hours=1),
        date_to=datetime.now(),
        maximum_lines=1000,
        search_text="",
    )
    op_data = operation.assert_success().to_json()
    assert "file" in op_data["c8y_LogfileRequest"]
    assert op_data["c8y_LogfileRequest"]["file"] == RegexPattern(
        r"^https://.+/event/events/\d+/binaries$"
    ), "Expected operation to contain a link to the uploaded log file"

    # Event should have been created with an attachment
    events = dut.cloud.events.assert_count(
        type=log_type,
        after=dut.device.test_start_time,
        with_attachment=True,
        max_matches=1,
    )
    dut.cloud.events.assert_attachment_info(events[0], expected_name_pattern=r"^.+$")

    # Check attachment
    expected_contents = f"filename: dummy.log\n{LOG_CONTENTS}\n"
    dut.cloud.events.assert_attachment(
        events[0].id, expected_contents=expected_contents
    )
