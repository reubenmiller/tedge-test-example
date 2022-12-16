"""Device adapter"""
import logging
from typing import List, Any, Tuple
from datetime import datetime, timezone


class DeviceAdapter:
    """Device Adapter

    Common interface which is the minimum support to write more a test
    which can have multiple device endpoints (e.g. docker, ssh, podman etc.)
    """

    def __init__(self, name: str, device_id: str = None):
        self._name = name
        self._device_id = device_id
        self._start_time = None
        self._test_start_time = datetime.now(timezone.utc)
        self._is_existing_device = False

    @property
    def test_start_time(self) -> datetime:
        """Test start time (in utc)

        Returns:
            datetime: Start time of the test
        """
        return self._test_start_time

    @test_start_time.setter
    def test_start_time(self, now: datetime):
        """Set the test start time

        Args:
            now (datetime): Datetime when the test started
        """
        self._test_start_time = now

    @property
    def start_time(self) -> datetime:
        """Get the start time of the device

        Returns:
            datetime: Device start time. None if the device does not exist
        """
        raise NotImplementedError()

    def get_uptime(self) -> int:
        """Get device uptime in seconds

        A zero is returned if the container does not exist

        Returns:
            int: Uptime in seconds
        """
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    def execute_command(
        self, cmd: str, log_output: bool = True, shell: bool = True, **kwargs
    ) -> Tuple[int, Any]:
        """Execute a command inside the docker container

        Args:
            cmd (str): Command to execute
            log_output (bool, optional): Log the stdout after the command has executed
            shell (bool, optional): Execute the command in a shell
            **kwargs (Any, optional): Additional keyword arguments

        Returns:
            Tuple[int, Any]: Docker command output (exit_code, output)
        """
        raise NotImplementedError()

    def assert_command(
        self, cmd: str, exp_exit_code: int = 0, log_output: bool = True, **kwargs
    ) -> Any:
        """Execute a command inside the docker container

        Args:
            cmd (str): Command to execute
            log_output (bool, optional): Log the stdout after the command has executed
            exp_exit_code (int, optional): Expected exit code, defaults to 0.
            **kwargs (Any, optional): Additional keyword arguments

        Returns:
            Any: Command output
        """
        raise NotImplementedError()

    @property
    def name(self) -> str:
        """Get the name of the device

        Returns:
            str: Device name
        """
        return self._name

    def restart(self):
        """Restart device"""
        logging.info("Restarting %s", self.name)
        self.execute_command("shutdown -r now")

    def disconnect_network(self):
        """Disconnect device from the network"""
        raise NotImplementedError()

    def connect_network(self):
        """Connect the device to the network"""
        raise NotImplementedError()

    def get_logs(self, since: Any = None) -> List[str]:
        """Get a list of log entries from the docker container

        Args:
            timestamps (bool, optional): Included timestamps in the log entries. Defaults to False.
            since (Any, optional): Get logs since the provided data. Defaults to None.

        Returns:
            List[str]: List of log entries
        """
        cmd = "journalctl --lines 100000 --no-pager -u 'tedge*' -u 'c8y*' -u mosquitto"

        output = []
        if since:
            cmd += f' --since "{since}"'
        exit_code, logs = self.execute_command(cmd, log_output=False)

        if exit_code != 0:
            logging.warning(
                "Could not retrieve journalctl logs. cmd=%d, exit_code=%d",
                cmd,
                exit_code,
            )
        output.extend(logs.decode("utf8").splitlines())

        return output

    def get_id(self) -> str:
        """Get the device id

        Returns:
            str: Device id
        """
        return self._device_id

    def cleanup(self):
        """Cleanup the device. This will be called when the define is no longer needed"""

    def copy_to(self, src: str, dst: str):
        """Copy file to the device

        Args:
            src (str): Source file (on host)
            dst (str): Destination (in container)
        """
        raise NotImplementedError()
