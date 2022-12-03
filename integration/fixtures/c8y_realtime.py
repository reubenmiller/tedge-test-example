"""c8y realtime fixture"""
import json
import subprocess
from typing import Any, Callable, List, Optional


class JsonReader:
    """JSON reader supports parsing stdout and returning a list
    using the preferred class factory, or by default a list of dictionaries
    """

    def __init__(self, proc: subprocess.Popen) -> None:
        self._proc = proc

    def wait(self, timeout: float = None):
        """Wait for the process to finish

        Args:
            timeout (float, optional): Timeout in seconds. Defaults to None.
        """
        code = self._proc.wait(timeout)
        assert code == 0

    def read_all(self, func: Optional[Callable] = None) -> Optional[List[Any]]:
        """Read all data and transform the output using a given function

        Args:
            func (Optional[Callable], optional): Function to be called on each outupt line.
                Defaults to None.

        Returns:
            Optional[List[Any]]: List of objects created from each line of output
        """
        if func:
            return [func(json.loads(line)) for line in self._proc.stdout]
        return [json.loads(line) for line in self._proc.stdout]


class Subscriber:
    """Subscriber factory"""

    # pylint: disable=too-few-public-methods
    @classmethod
    def to_measurements(cls, device_id: str, duration: int) -> JsonReader:
        """Create a subscription to measurements for a device

        Args:
            device_id (str): device id to subscribe to
            duration (int): Duration in seconds to subscribe for

        Returns:
            _type_: _description_
        """
        # pylint: disable=consider-using-with
        proc = subprocess.Popen(
            [
                "c8y",
                "measurements",
                "subscribe",
                "--device",
                device_id,
                "--duration",
                f"{duration}s",
            ],
            universal_newlines=True,
            stdout=subprocess.PIPE,
        )
        return JsonReader(proc)
