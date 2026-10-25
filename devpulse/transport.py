"""Bounded USB writes and scheduled reconnects without retry sleeps."""

from collections.abc import Callable
from typing import Any


class SerialTransport:
    def __init__(self, port: str, serial_module: Any, report: Callable[[str], None]):
        self.port = port
        self.serial = serial_module
        self.report = report
        self.link = None
        self.retry_at = 0.0
        self.backoff = 1.0
        self.needs_boundary = True
        self.wrote_packet = False

    def send(self, packet: bytes, now: float) -> bool:
        if now < self.retry_at:
            return False
        try:
            if self.link is None:
                self.link = self.serial.Serial(self.port, 115200, timeout=0, write_timeout=0.2)
                self.needs_boundary = True
            if self.needs_boundary:
                if self.link.write(b"\n") != 1:
                    raise self.serial.SerialTimeoutException("Incomplete frame boundary")
                self.needs_boundary = False
            if self.link.write(packet) != len(packet):
                raise self.serial.SerialTimeoutException("Incomplete packet")
            if not self.wrote_packet:
                self.report(f"USB writes resumed on {self.port}; delivery is not acknowledged")
            self.wrote_packet = True
            self.backoff = 1.0
            return True
        except (self.serial.SerialException, OSError) as exc:
            self.close()
            self.wrote_packet = False
            self.retry_at = now + self.backoff
            self.report(f"USB unavailable ({exc}); retry in {self.backoff:g}s")
            self.backoff = min(self.backoff * 2, 8.0)
            return False

    def close(self) -> None:
        link, self.link = self.link, None
        self.needs_boundary = True
        if link is not None:
            try:
                link.close()
            except (self.serial.SerialException, OSError):
                pass
