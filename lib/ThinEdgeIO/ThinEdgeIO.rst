ThinEdgeIO
==========
Scope:    GLOBAL

ThinEdgeIO Library

Importing
---------
Arguments:  [image: str = debian-systemd]

Initialize self.  See help(type(self)) for accurate signature.

Execute Device Command
----------------------
Arguments:  [cmd: str, exp_exit_code: int = 0, log_output: bool = True]

Execute a device command

Args:
    exp_exit_code (int, optional): Expected return code. Defaults to 0.

Returns:
    str: _description_

Get Device Logs
---------------
Arguments:  [name: str | None = None]

Get device logs (override base class method to add additional debug info)

Args:
    name (str, optional): Device name to get logs for. Defaults to None.

Get Random Name
---------------
Arguments:  [prefix: str = STC]

Get random name

Args:
    prefix (str, optional): Name prefix. Defaults to "STC".

Returns:
    str: Random name

Setup Device
------------
Arguments:  []

Create a container device to use for testing

Returns:
    str: Device serial number

Stop Device
-----------
Arguments:  []

Stop and cleanup the device

Wait For Device To Be Ready
---------------------------
Arguments:  []

Wait for the device to be ready

