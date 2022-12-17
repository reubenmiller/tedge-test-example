"""Alarm tests"""

import json
import pytest
from integration.fixtures.device import Device

# pylint: disable=too-many-arguments


@pytest.mark.parametrize(
    "topic,payload",
    [
        pytest.param(
            "tedge/alarms/critical/temperature_high_high",
            '{"text": "Temperature is very high"}',
            id="critical_alarm_without_timestamp",
        ),
        pytest.param(
            "tedge/alarms/major/temperature_high",
            '{"text": "Temperature is high", "time": "2099-01-01T00:00:00-05:00"}',
            id="major_alarm_with_negative_timestamp",
        ),
        pytest.param(
            "tedge/alarms/minor/temperature_low",
            '{"text": "Temperature is low", "time": "2099-01-01T00:00:00+05:00"}',
            id="minor_alarm",
        ),
        pytest.param(
            "tedge/alarms/warning/temperature_low",
            '{"text": "Temperature is low low", "time": "2099-01-01T00:00:00Z"}',
            id="warning_alarm",
        ),
    ],
)
def test_tedge_alarm(dut: Device, topic, payload):
    """Create a tedge alarm via mqtt"""
    dut.device.assert_command(f"tedge mqtt pub {topic} '{payload}'")
    alarm = json.loads(payload)

    items = dut.cloud.alarms.assert_count(
        expected_text=alarm.get("text"),
        type=topic.split("/")[-1],
        severity=topic.split("/")[-2].upper(),
        max_matches=1,
        after=dut.device.test_start_time,
    )
    assert items


@pytest.mark.parametrize(
    "topic,payload",
    [
        pytest.param(
            "tedge/alarms/critical/temperature_high_high",
            '{"text": "Temperature is very high"}',
            id="critical_alarm_without_timestamp",
        ),
    ],
)
def test_clear_tedge_alarm(dut: Device, topic, payload):
    """Create then clear a tedge measurement via mqtt"""
    dut.device.assert_command(f"tedge mqtt pub {topic} '{payload}'")
    alarm = json.loads(payload)

    items = dut.cloud.alarms.assert_count(
        expected_text=alarm.get("text"),
        type=topic.split("/")[-1],
        severity=topic.split("/")[-2].upper(),
        resolved=False,
        max_matches=1,
        after=dut.device.test_start_time,
    )
    assert items

    dut.device.assert_command(f"tedge mqtt pub {topic} ''")

    dut.cloud.alarms.assert_count(
        expected_text=alarm.get("text"),
        type=topic.split("/")[-1],
        severity=topic.split("/")[-2].upper(),
        resolved=False,
        max_matches=0,
        min_matches=0,
        after=dut.device.test_start_time,
    )

    alarm = dut.cloud.alarms.assert_exists(items[0].id)
    assert alarm.status == alarm.Status.CLEARED, "Alarm should be cleared"
