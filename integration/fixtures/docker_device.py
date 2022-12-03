"""Docker Device Simulator"""
import os
import logging
from pathlib import Path
from typing import List, Any, Tuple
import time
import tarfile
from datetime import datetime, timezone
from docker.models.containers import Container


def convert_docker_timestamp(value: str) -> datetime:
    """Convert a docker timestamp string to a python datetime object
    The milliseconds/nanoseconds will be stripped from the timestamp

    Args:
        value (str): Timestamp as a string

    Returns:
        datetime: Datetime
    """
    # Note: Strip the fractions of seconds as strptime does not support nanoseconds
    # (resolution of docker timestamp), and the fraction of seconds resolution is not
    # required for testing
    date, _, _ = value.partition(".")

    tz_suffix = "Z"
    if "+" in value:
        _, tz_sep, time_zone = value.partition("+")
        tz_suffix = tz_sep + time_zone

    if not date.endswith(tz_suffix):
        date = date + tz_suffix

    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")


class DockerDeviceAdapter:
    """Docker Device"""

    # pylint: disable=too-many-public-methods

    def __init__(self, name: str):
        self._name = name
        self._container = None
        self.simulator = None
        self._start_time = None
        self._test_start_time = datetime.now(timezone.utc)
        self._is_existing_device = False

    @property
    def container(self) -> Container:
        """Docker container

        Returns:
            Container: Container
        """
        return self._container

    @container.setter
    def container(self, container: Container):
        self._container = container

    @property
    def is_existing_device(self) -> bool:
        """Is existing device

        Returns:
            bool: If this device is an existing device
        """
        return self._is_existing_device

    @is_existing_device.setter
    def is_existing_device(self, is_existing_device: bool):
        """Set the is_existing_device

        Args:
            is_existing_device (bool): If this device is an existing device
        """
        self._is_existing_device = is_existing_device

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
        """Get the start time of the container

        Returns:
            datetime: Device start time. None if the container does not exist
        """
        self.container.reload()
        return convert_docker_timestamp(self.container.attrs["State"]["StartedAt"])

    def get_uptime(self) -> int:
        """Get device uptime in seconds

        A zero is returned if the container does not exist

        Returns:
            int: Uptime in seconds
        """
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    def get_device_stats(self) -> Any:
        """Get container statistics (i.e. cpu, network traffic etc.)

        Returns:
            Optional[Any]: Container stats object as provided by docker
        """
        return self.container.stats(stream=False)

    def execute_command(
        self, cmd: str, log_output: bool = True, **kwargs
    ) -> Tuple[int, Any]:
        """Execute a command inside the docker container

        Args:
            cmd (str): Command to execute
            log_output (bool, optional): Log the stdout after the command has executed
            **kwargs (Any, optional): Additional keyword arguments

        Raises:
            Exception: Docker container not found error

        Returns:
            Tuple[int, Any]: Docker command output (exit_code, output)
        """
        if "shell" in kwargs and kwargs["shell"]:
            cmd = ["/bin/bash", "-c", cmd]

        exit_code, output = self.container.exec_run(cmd)
        if log_output:
            logging.info(
                "cmd: %s, exit code: %d, stdout: %s",
                cmd,
                exit_code,
                output.decode("utf-8"),
            )
        else:
            logging.info("cmd: %s, exit code: %d", cmd, exit_code)
        return exit_code, output

    @property
    def name(self) -> str:
        """Get the name of the device

        Returns:
            str: Device name
        """
        return self._name

    def restart(self):
        """Restart the docker container"""
        logging.info("Restarting %s", self.name)
        startup_delay_sec = 1
        self.container.stop()
        if startup_delay_sec > 0:
            time.sleep(startup_delay_sec)
        logging.info("Starting container %s", self.name)
        self.container.start()

    def disconnect_network(self):
        """Disconnect the docker container from the network"""
        if self.simulator:
            self.simulator.disconnect_network(self.container)

    def connect_network(self):
        """Connect the docker container to the network"""
        if self.simulator:
            self.simulator.connect_network(self.container)

    def get_logs(self, since: Any = None) -> List[str]:
        """Get a list of log entries from the docker container

        Args:
            timestamps (bool, optional): Included timestamps in the log entries. Defaults to False.
            since (Any, optional): Get logs since the provided data. Defaults to None.

        Returns:
            List[str]: List of log entries
        """
        cmd = "journalctl --lines 100000 --no-pager -u 'tedge*' -u 'c8y*'"

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

        Raises:
            Exception: Cube id not found

        Returns:
            str: Device id
        """
        (code, output) = self.container.exec_run(
            'sh -c "tedge config get device.id"', stderr=True, demux=True
        )
        stdout, stderr = output
        if code != 0:
            raise Exception(
                "Failed to get device id. container: "
                f"name={self.container.name}, id={self.container.id}, "
                f"code={code}, stdout={stdout}, stderr={stderr}"
            )
        device_id = stdout.strip().decode("utf-8")

        logging.info("Device id: %s", device_id)
        return device_id

    def copy_to(self, src: str, dst: str):
        """Copy file to the device

        Args:
            src (str): Source file (on host)
            dst (str): Destination (in container)
        """
        abs_src = os.path.abspath(src)
        owd = os.getcwd()
        os.chdir(os.path.dirname(src))
        src_name = os.path.basename(src)

        with tarfile.open(abs_src + ".tar", mode="w") as tar:
            tar.add(src_name)

        data = Path(abs_src + ".tar").read_bytes()
        self.container.put_archive(os.path.dirname(dst), data)

        os.remove(abs_src + ".tar")
        os.chdir(owd)

    def cleanup(self):
        """Cleanup the device. This will be called when the define is no longer needed"""
        # Make sure device is connected again after the test
        if self.simulator:
            self.simulator.connect_network(self.container)
