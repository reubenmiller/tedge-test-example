"""APAMA plugin tests"""

import pytest
from pytest_c8y.core import models
from integration.fixtures.device import Device

APAMA_PLUGIN = "tedge-apama-plugin"


@pytest.fixture(name="dut")
def tedge_fixture(dut: Device):
    """APAMA device setup"""
    # install software
    operation = dut.cloud.software_management.install(
        models.Software(
            name=APAMA_PLUGIN,
            url=(
                "https://svndae.apama.com/apama_installers/Apama"
                "/debian-apt/apama-repo-internal_2022_all.deb"
            ),
        ),
        timeout=60,
    )
    operation.assert_success()

    # yield to test
    yield dut

    # remove software
    operation = dut.cloud.software_management.remove(
        models.Software(APAMA_PLUGIN),
    )
    operation.assert_success()


@pytest.mark.skip("TODO")
def test_apama_installation(
    dut: Device,
):
    """Custom APAMA application"""
    operation = dut.cloud.command.execute("tedge mqtt pub tedge/local_event ''")
    operation.assert_success()
    dut.cloud.alarms.assert_count(type="test_alarm")
