"""Measurement tests"""

import pytest
from integration.fixtures.device import Device

# pylint: disable=too-many-arguments


@pytest.mark.parametrize(
    "topic,payload,exp_fragment,exp_series,exp_type,exp_value",
    [
        pytest.param(
            "tedge/measurements",
            '{"temperature": 21.3}',
            "temperature",
            "temperature",
            "ThinEdgeMeasurement",
            21.3,
            id="measurement",
        )
    ],
)
def test_tedge_measurement(
    dut: Device, topic, payload, exp_fragment, exp_series, exp_type, exp_value
):
    """Create a tedge measurement via mqtt"""
    dut.device.assert_command(f"tedge mqtt pub {topic} '{payload}'")
    items = dut.cloud.measurements.assert_count(
        max_count=1,
        after=dut.device.test_start_time,
        type=exp_type,
        value=exp_fragment,
        series=exp_series,
    )
    assert items[0][exp_fragment][exp_series]["value"] == exp_value
