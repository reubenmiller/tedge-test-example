"""Event tests"""

import json
import pytest
from integration.fixtures.device import Device

# pylint: disable=too-many-arguments


@pytest.mark.parametrize(
    "topic,payload",
    [
        pytest.param(
            "tedge/events/login_event",
            '{"text": "A user just logged in"}',
            id="event_without_timestamp",
        ),
        pytest.param(
            "tedge/events/login_event",
            '{"text": "A user just logged in", "time": "2099-01-01T00:00:00-05:00"}',
            id="event_with_negative_timestamp",
        ),
    ],
)
def test_tedge_event(dut: Device, topic, payload):
    """Create a tedge event via mqtt"""
    dut.device.assert_command(f"tedge mqtt pub {topic} '{payload}'")
    event = json.loads(payload)

    items = dut.cloud.events.assert_count(
        expected_text=event.get("text"),
        type=topic.split("/")[-1],
        max_matches=1,
        after=dut.device.test_start_time,
    )
    assert items
