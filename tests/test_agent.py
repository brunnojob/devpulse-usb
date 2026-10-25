import json
import unittest
from types import SimpleNamespace

from devpulse.protocol import MAX_FRAME_BYTES, Snapshot
from devpulse.telemetry import Sampler, SustainedAlert, rate
from devpulse.transport import SerialTransport


class AlertTests(unittest.TestCase):
    def test_requires_ten_seconds_of_continuous_high_samples(self):
        alarm = SustainedAlert()
        for second in range(10):
            self.assertFalse(alarm.update(90, second))
        self.assertTrue(alarm.update(90, 10))
        self.assertFalse(alarm.update(89.9, 11))
        self.assertFalse(alarm.update(95, 12))

    def test_sampling_gap_resets_continuity(self):
        alarm = SustainedAlert()
        for second in range(9):
            alarm.update(95, second)
        self.assertFalse(alarm.update(95, 25))
        self.assertFalse(alarm.update(95, 26))

    def test_clock_reset_and_invalid_reading_reset_alert(self):
        alarm = SustainedAlert()
        alarm.update(95, 5)
        self.assertFalse(alarm.update(95, 1))
        self.assertFalse(alarm.update(float("nan"), 2))
        self.assertIsNone(alarm.since)


class ProtocolTests(unittest.TestCase):
    def test_packet_fits_buffer_at_maximum_supported_values(self):
        packet = Snapshot(100, 100, 100, 1e12, 1e12, "CPU+RAM", 1e12).encode()
        self.assertLessEqual(len(packet) - 1, MAX_FRAME_BYTES)
        self.assertEqual(packet.count(b"\n"), 1)
        self.assertEqual(json.loads(packet)["v"], 1)

    def test_rejects_nonfinite_negative_boolean_and_out_of_range_values(self):
        for value in [float("nan"), float("inf"), -1, 101, True, "50"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Snapshot(value, 20, 40, 0, 0).encode()
        with self.assertRaises(ValueError):
            Snapshot(20, 20, 20, 1e13, 0).encode()

    def test_rejects_unknown_alert(self):
        with self.assertRaises(ValueError):
            Snapshot(20, 20, 20, 0, 0, "REBOOT").encode()

    def test_rounding_and_recording_timestamp(self):
        payload = json.loads(Snapshot(12.34, 50, 10, 1.25, 2.5, t=1.23456).encode())
        self.assertEqual(payload["cpu"], 12.3)
        self.assertEqual(payload["t"], 1.235)


class SamplingTests(unittest.TestCase):
    def test_counter_reset_and_zero_elapsed(self):
        self.assertEqual(rate(10, 100, 1), 0)
        self.assertEqual(rate(2048, 0, 2), 1)
        self.assertEqual(rate(100, 0, 0), 0)

    def test_real_elapsed_time_and_missing_network_adapter(self):
        metrics = SimpleNamespace(
            net_io_counters=lambda: SimpleNamespace(bytes_recv=0, bytes_sent=0),
            cpu_percent=lambda interval: 40,
            virtual_memory=lambda: SimpleNamespace(percent=60),
            disk_usage=lambda path: SimpleNamespace(percent=20),
        )
        sampler = Sampler(metrics, "/", 10)
        metrics.net_io_counters = lambda: SimpleNamespace(bytes_recv=4096, bytes_sent=2048)
        sample = sampler.sample(12)
        self.assertEqual((sample.rx, sample.tx, sample.t), (2, 1, 2))
        metrics.net_io_counters = lambda: None
        sample = sampler.sample(13)
        self.assertEqual((sample.rx, sample.tx), (0, 0))


class SerialFailure(Exception):
    pass


class FakeLink:
    def __init__(self):
        self.writes = []
        self.partial = False
        self.closed = False

    def write(self, data):
        self.writes.append(data)
        return len(data) - 1 if self.partial else len(data)

    def close(self):
        self.closed = True


class TransportTests(unittest.TestCase):
    def make_serial(self, factory):
        return SimpleNamespace(
            Serial=factory, SerialException=SerialFailure, SerialTimeoutException=SerialFailure
        )

    def test_partial_write_closes_port_and_resynchronizes_next_connection(self):
        first, second = FakeLink(), FakeLink()
        links = iter([first, second])
        transport = SerialTransport(
            "test", self.make_serial(lambda *a, **kw: next(links)), lambda _: None
        )
        self.assertTrue(transport.send(b"one\n", 0))
        first.partial = True
        self.assertFalse(transport.send(b"two\n", 1))
        self.assertTrue(first.closed)
        self.assertFalse(transport.send(b"three\n", 1.5))
        self.assertTrue(transport.send(b"four\n", 2))
        self.assertEqual(second.writes, [b"\n", b"four\n"])
        transport.close()
        self.assertTrue(second.closed)

    def test_backoff_is_bounded_and_does_not_sleep(self):
        attempts = []

        def fail(*args, **kwargs):
            attempts.append(True)
            raise SerialFailure("unplugged")

        transport = SerialTransport("test", self.make_serial(fail), lambda _: None)
        for now in [0, 1, 3, 7, 15]:
            self.assertFalse(transport.send(b"packet\n", now))
        self.assertEqual(len(attempts), 5)
        self.assertEqual(transport.backoff, 8)
        self.assertEqual(transport.retry_at, 23)


if __name__ == "__main__":
    unittest.main()
