"""APAMA plugin tests"""

import pytest
from pytest_c8y.models import Software
from integration.fixtures.device_mgmt import DeviceManagement

APAMA_PLUGIN = "tedge-apama-plugin"


@pytest.fixture(name="tedge")
def tedge_fixture(tedge: DeviceManagement):
    """APAMA device setup"""
    # install software
    operation = tedge.software_management.install(
        Software(
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
    yield tedge

    # remove software
    operation = tedge.software_management.remove(
        Software(APAMA_PLUGIN),
    )
    operation.assert_success()


@pytest.mark.skip("TODO")
def test_apama_installation(
    tedge: DeviceManagement,
):
    """Custom APAMA application"""
    operation = tedge.command.execute("tedge mqtt pub tedge/local_event ''")
    operation.assert_success()
    tedge.alarms.assert_count(type="test_alarm")
