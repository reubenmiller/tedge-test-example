"""Cumulocity child device tests"""

import time
from integration.fixtures.device.device import Device


def test_child_device_registration(dut: Device, random_name_factory: str):
    """Register child devices"""
    child_name = random_name_factory()
    # TODO: Sleep is required due to delayed startup
    time.sleep(5)
    code, _ = dut.device.execute_command(
        f"mkdir -p /etc/tedge/operations/c8y/{child_name}",
        shell=True,
    )
    assert code == 0
    dut.cloud.inventory.assert_exists()

    children = dut.cloud.inventory.assert_child_device_names(child_name, timeout=10)
    assert len(children) > 0, "Expected at least 1 child device"


def test_child_supported_operations(dut: Device, random_name_factory: str):
    """Register child devices with supported operations"""
    child_name = random_name_factory()
    time.sleep(5)
    code, _ = dut.device.execute_command(
        f"""
        mkdir -p /etc/tedge/operations/c8y/{child_name};
        touch /etc/tedge/operations/c8y/{child_name}/c8y_Restart
        """,
        shell=True,
    )
    assert code == 0

    dut.cloud.inventory.assert_exists()
    dut.cloud.inventory.assert_contains_fragment_values(
        {
            "c8y_SupportedOperations": [
                # "c8y_DownloadConfigFile",
                # "c8y_LogfileRequest",
                "c8y_Restart",
                "c8y_SoftwareUpdate",
                # "c8y_UploadConfigFile",
            ]
        }
    )

    dut.cloud.inventory.assert_child_device_names(child_name, timeout=10)
    child_managed_object = dut.cloud.identity.assert_exists(child_name)
    dut.cloud.inventory.assert_contains_fragment_values(
        {
            "c8y_SupportedOperations": [
                "c8y_Restart",
            ]
        },
        child_managed_object,
    )
