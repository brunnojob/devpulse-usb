"""Command-line entry point. No discovery scans or network services."""

import argparse
import math
import os
import sys
import time
from contextlib import ExitStack
from pathlib import Path

from . import __version__
from .telemetry import Sampler
from .transport import SerialTransport


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local PC telemetry over USB serial")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--port", help="Explicit serial port, e.g. COM5 or /dev/ttyACM0")
    output.add_argument("--stdout", action="store_true", help="Print real NDJSON metrics")
    output.add_argument("--list", action="store_true", help="List ports without opening them")
    parser.add_argument("--record", type=Path, help="Create a new NDJSON session; never overwrite")
    parser.add_argument("--duration", type=float, help="Stop after 0.25–3600 seconds")
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Sampling interval, 0.25–2 seconds"
    )
    parser.add_argument("--disk", default=os.path.abspath(os.sep), help="Volume to measure")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if not math.isfinite(args.interval) or not 0.25 <= args.interval <= 2:
        parser.error("--interval must be between 0.25 and 2 seconds")
    if args.duration is not None and (
        not math.isfinite(args.duration) or not args.interval <= args.duration <= 3600
    ):
        parser.error("--duration must be between --interval and 3600 seconds")
    if args.list and (args.record or args.duration is not None):
        parser.error("--list cannot be combined with recording or duration")
    if not (args.port or args.stdout or args.record or args.list):
        parser.error("Choose --port, --stdout, --record or --list")
    try:
        if args.list:
            from serial.tools import list_ports

            for port in list_ports.comports():
                print(f"{port.device}: {port.description}")
            return 0
        import psutil

        serial_module = None
        if args.port:
            import serial as serial_module
    except ImportError:
        print("Install dependencies: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1

    def report(message: str) -> None:
        print(message, file=sys.stderr, flush=True)

    with ExitStack() as stack:
        transport = None
        try:
            sampler = Sampler(psutil, args.disk, time.monotonic())
            recording = stack.enter_context(args.record.open("xb")) if args.record else None
            if args.port:
                transport = SerialTransport(args.port, serial_module, report)
                stack.callback(transport.close)
            if recording:
                report(f"Recording to {args.record}; Ctrl+C stops cleanly")
            started = time.monotonic()
            next_tick = started + args.interval
            while True:
                time.sleep(max(0.0, next_tick - time.monotonic()))
                now = time.monotonic()
                packet = sampler.sample(now).encode()
                if recording:
                    recording.write(packet)
                    recording.flush()
                if args.stdout:
                    print(packet.decode("ascii").rstrip(), flush=True)
                if transport:
                    transport.send(packet, now)
                if args.duration is not None and now - started >= args.duration:
                    break
                next_tick += args.interval
                if next_tick <= time.monotonic():
                    next_tick = time.monotonic() + args.interval
        except KeyboardInterrupt:
            report("Stopped")
        except BrokenPipeError:
            return 0
        except (OSError, ValueError, psutil.Error) as exc:
            report(f"Cannot collect telemetry: {exc}")
            return 1
    return 0
