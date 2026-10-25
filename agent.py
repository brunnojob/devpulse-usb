"""DevPulse USB: local telemetry, no server or network connections."""
import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass


@dataclass
class SustainedAlert:
    threshold: float = 90.0
    duration: float = 10.0
    since: float | None = None

    def update(self, value, now):
        if value < self.threshold:
            self.since = None
            return False
        if self.since is None:
            self.since = now
        return now - self.since >= self.duration


def rate(current, previous, elapsed):
    if elapsed <= 0 or current < previous:
        return 0.0
    return round((current - previous) / elapsed / 1024, 1)


def encode(cpu, ram, disk, rx, tx, alert):
    values = [cpu, ram, disk, rx, tx]
    if not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError('Invalid metric')
    if any(v > 100 for v in values[:3]):
        raise ValueError('Invalid percentage')
    return (json.dumps(dict(v=1, cpu=round(cpu, 1), ram=round(ram, 1),
                            disk=round(disk, 1), rx=rx, tx=tx, alert=alert),
                       separators=(',', ':'), allow_nan=False) + '\n').encode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', help='COM5 or /dev/ttyACM0; explicit device selection')
    parser.add_argument('--list', action='store_true', help='List serial ports')
    parser.add_argument('--stdout', action='store_true', help='Read real metrics without a board')
    parser.add_argument('--interval', type=float, default=1.0)
    parser.add_argument('--disk', default=os.path.abspath(os.sep))
    args = parser.parse_args()
    if not math.isfinite(args.interval) or not 0.25 <= args.interval <= 2:
        parser.error('--interval must be between 0.25 and 2 seconds')
    try:
        import psutil
        import serial
        from serial.tools import list_ports
    except ImportError:
        parser.exit(1, 'Install dependencies: python -m pip install -r requirements.txt\n')
    if args.list:
        for p in list_ports.comports():
            print(f'{p.device}: {p.description}')
        return
    if not args.stdout and not args.port:
        parser.error('Use --port, --list or --stdout')
    cpu_alert, ram_alert = SustainedAlert(), SustainedAlert()
    previous = psutil.net_io_counters()
    previous_time = time.monotonic()
    psutil.cpu_percent()
    link = None
    try:
        while True:
            time.sleep(args.interval)
            now = time.monotonic()
            net = psutil.net_io_counters()
            cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
            cpu_hot = cpu_alert.update(cpu, now)
            ram_hot = ram_alert.update(ram, now)
            alert = 'CPU+RAM' if cpu_hot and ram_hot else 'CPU' if cpu_hot else 'RAM' if ram_hot else 'OK'
            packet = encode(cpu, ram, psutil.disk_usage(args.disk).percent,
                            rate(net.bytes_recv, previous.bytes_recv, now - previous_time),
                            rate(net.bytes_sent, previous.bytes_sent, now - previous_time), alert)
            previous, previous_time = net, now
            if args.stdout:
                print(packet.decode().strip(), flush=True)
                continue
            try:
                if link is None:
                    link = serial.Serial(args.port, 115200, timeout=0, write_timeout=1)
                if link.write(packet) != len(packet):
                    raise serial.SerialTimeoutException('Incomplete packet')
            except (serial.SerialException, OSError) as exc:
                print(f'USB unavailable; retrying: {exc}', file=sys.stderr)
                if link is not None:
                    link.close()
                    link = None
                time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        if link is not None:
            link.close()


if __name__ == '__main__':
    main()
