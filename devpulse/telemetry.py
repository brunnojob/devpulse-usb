"""Sampling and elapsed-time-based alert state, independent of serial I/O."""

import math
from dataclasses import dataclass
from typing import Any

from .protocol import Snapshot


@dataclass
class SustainedAlert:
    threshold: float = 90.0
    duration: float = 10.0
    max_gap: float = 3.0
    since: float | None = None
    previous_time: float | None = None

    def update(self, value: float, now: float) -> bool:
        if self.previous_time is not None and (
            now < self.previous_time or now - self.previous_time > self.max_gap
        ):
            self.since = None
        self.previous_time = now
        if not math.isfinite(value) or value < self.threshold:
            self.since = None
            return False
        if self.since is None:
            self.since = now
        return now - self.since >= self.duration


def rate(current: int, previous: int, elapsed: float) -> float:
    if elapsed <= 0 or current < previous:
        return 0.0
    return round((current - previous) / elapsed / 1024, 1)


class Sampler:
    def __init__(self, metrics: Any, disk: str, now: float):
        self.metrics = metrics
        self.disk = disk
        self.started = self.previous_time = now
        self.previous_net = metrics.net_io_counters()
        self.cpu_alert = SustainedAlert()
        self.ram_alert = SustainedAlert()
        metrics.disk_usage(disk)
        metrics.cpu_percent(interval=None)

    def sample(self, now: float) -> Snapshot:
        net = self.metrics.net_io_counters()
        cpu = self.metrics.cpu_percent(interval=None)
        ram = self.metrics.virtual_memory().percent
        disk = self.metrics.disk_usage(self.disk).percent
        elapsed = now - self.previous_time
        rx = tx = 0.0
        if net is not None and self.previous_net is not None:
            rx = rate(net.bytes_recv, self.previous_net.bytes_recv, elapsed)
            tx = rate(net.bytes_sent, self.previous_net.bytes_sent, elapsed)
        cpu_hot = self.cpu_alert.update(cpu, now)
        ram_hot = self.ram_alert.update(ram, now)
        alert = (
            "CPU+RAM" if cpu_hot and ram_hot else "CPU" if cpu_hot else "RAM" if ram_hot else "OK"
        )
        snapshot = Snapshot(cpu, ram, disk, rx, tx, alert, now - self.started)
        self.previous_net, self.previous_time = net, now
        return snapshot
