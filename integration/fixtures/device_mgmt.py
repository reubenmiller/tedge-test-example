"""Custom Device Management fixture"""

import logging
from pytest_c8y.core import device_management

log = logging.getLogger()


class CumulocityDeviceManagement(device_management.DeviceManagement):
    """Cumulocity device management"""

    def delete_inventory(self, mo_id: str, cascade: bool = None, **params):
        """Delete an inventory with options

        Args:
            mo_id (str): Managed object id
            cascade (bool): Delete all nested values
            params (*kwargs): Additional query parameters
        """
        if cascade is not None:
            params["cascade"] = cascade
        self.c8y.delete(f"/inventory/managedObjects/{mo_id}", params=params)
