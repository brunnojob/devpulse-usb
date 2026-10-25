"""The shared v1 wire format: one bounded JSON object per line."""

import json
import math
from dataclasses import asdict, dataclass

MAX_FRAME_BYTES = 255
MAX_RATE_KIB = 1_000_000_000_000
ALERTS = frozenset({"OK", "CPU", "RAM", "CPU+RAM"})


def checked_number(name: str, value: float, upper: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be numeric")
    if not 0 <= value <= upper or not math.isfinite(value):
        raise ValueError(f"{name} is outside its valid range")


@dataclass(frozen=True)
class Snapshot:
    cpu: float
    ram: float
    disk: float
    rx: float
    tx: float
    alert: str = "OK"
    t: float = 0.0

    def encode(self) -> bytes:
        for name in ("cpu", "ram", "disk"):
            checked_number(name, getattr(self, name), 100)
        for name in ("rx", "tx"):
            checked_number(name, getattr(self, name), MAX_RATE_KIB)
        checked_number("t", self.t, 1e12)
        if not isinstance(self.alert, str) or self.alert not in ALERTS:
            raise ValueError("Unknown alert state")
        payload = {"v": 1, **asdict(self)}
        for name in ("cpu", "ram", "disk", "rx", "tx"):
            payload[name] = round(payload[name], 1)
        payload["t"] = round(self.t, 3)
        line = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("ascii")
        if len(line) > MAX_FRAME_BYTES:
            raise ValueError("Packet exceeds the firmware frame limit")
        return line + b"\n"
