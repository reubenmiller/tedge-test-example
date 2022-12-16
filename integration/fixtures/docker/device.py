"""Docker Device Simulator"""
import os
import logging
import glob
import tempfile
from typing import List, Any, Tuple, IO
import time
import tarfile
from datetime import datetime, timezone
from docker.models.containers import Container
from integration.fixtures.device.adapter import DeviceAdapter


log = logging.getLogger()


def _parse_base_path_from_pattern(pattern: str) -> str:
    output = []
    parts = pattern.split(os.path.sep)
    for part in parts:
        if "*" in part:
            break
        output.append(part)

    return os.path.sep.join(output)


def make_tarfile(
    fileobj: IO[bytes], patterns: List[str], compress: bool = False
) -> int:
    """Make a tar file given a list of patterns

    If the file already exists the files will be appended to it.

    Args:
        file (str): Tar file where the files will be added to. It does not have to exist.
        patterns (List[str]): List of glob patterns to be added to the tar file
        compress (bool, optional): Use compression when creating tar (e.g. gzip)
    """
    total_files = 0
    mode = "w:gz" if compress else "w"
    with tarfile.open(fileobj=fileobj, mode=mode) as tar:
        for pattern in patterns:
            source_dir = _parse_base_path_from_pattern(pattern)

            for match in glob.glob(pattern):
                archive_path = match[len(source_dir) :].lstrip("/")
                log.debug("Adding file: path=%s, archive_path=%s", match, archive_path)
                tar.add(match, arcname=archive_path)
                total_files += 1
                # tar.add(source_dir, arcname=os.path.basename(source_dir))

    return total_files


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


class DockerDeviceAdapter(DeviceAdapter):
    """Docker Device"""

    # pylint: disable=too-many-public-methods

    def __init__(self, name: str, device_id: str = None):
        self._name = name
        self._container = None
        self.simulator = None
        self._start_time = None
        self._test_start_time = datetime.now(timezone.utc)
        self._is_existing_device = False
        super().__init__(name, device_id)

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
        self, cmd: str, log_output: bool = True, shell: bool = True, **kwargs
    ) -> Tuple[int, Any]:
        """Execute a command inside the docker container

        Args:
            cmd (str): Command to execute
            log_output (bool, optional): Log the stdout after the command has executed
            shell (bool, optional): Execute the command in a shell
            **kwargs (Any, optional): Additional keyword arguments

        Raises:
            Exception: Docker container not found error

        Returns:
            Tuple[int, Any]: Docker command output (exit_code, output)
        """
        if shell:
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

    def assert_command(
        self, cmd: str, exp_exit_code: int = 0, log_output: bool = True, **kwargs
    ) -> Any:
        """Execute a command inside the docker container

        Args:
            cmd (str): Command to execute
            log_output (bool, optional): Log the stdout after the command has executed
            exp_exit_code (int, optional): Expected exit code, defaults to 0.
                Ignored if set to None.
            **kwargs (Any, optional): Additional keyword arguments

        Raises:
            Exception: Docker container not found error

        Returns:
            Any: Command output
        """
        exit_code, output = self.execute_command(cmd, log_output=log_output, **kwargs)

        if exp_exit_code is not None:
            cmd_snippet = cmd
            if len(cmd_snippet) > 30:
                cmd_snippet = cmd_snippet[0:30] + "..."

            assert (
                exit_code == exp_exit_code
            ), f"`{cmd_snippet}` returned an unexpected exit code"

        return output

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

        Raises:
            Exception: Device id not found

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
        try:
            total_files = 0
            archive_path = ""

            # build archive
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".tar", delete=False
            ) as file:
                total_files = make_tarfile(file, [src])
                archive_path = file.name

            # put archive
            with open(archive_path, "rb") as file:
                if total_files > 1 or dst.endswith("/"):
                    parent_dir = dst.rstrip("/") + "/"
                else:
                    parent_dir = os.path.dirname(dst)

                code, _ = self.execute_command(f"mkdir -p {parent_dir}")
                assert code == 0
                self.container.put_archive(parent_dir, file)
        finally:
            if archive_path and os.path.exists(archive_path):
                os.unlink(archive_path)

    def cleanup(self):
        """Cleanup the device. This will be called when the define is no longer needed"""
        # Make sure device is connected again after the test
        if self.simulator:
            self.simulator.connect_network(self.container)
