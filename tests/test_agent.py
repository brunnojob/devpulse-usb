import json
import unittest
from agent import SustainedAlert, encode, rate


class AgentTests(unittest.TestCase):
    def test_requires_continuous_high_usage(self):
        alarm = SustainedAlert()
        self.assertFalse(alarm.update(95, 0))
        self.assertFalse(alarm.update(95, 9))
        self.assertTrue(alarm.update(95, 10))
        self.assertFalse(alarm.update(50, 11))
        self.assertFalse(alarm.update(95, 12))
        self.assertFalse(alarm.update(95, 21))

    def test_counter_reset_does_not_create_negative_throughput(self):
        self.assertEqual(rate(10, 100, 1), 0)
        self.assertEqual(rate(2048, 0, 2), 1)
        self.assertEqual(rate(100, 0, 0), 0)

    def test_packet_fits_firmware_buffer(self):
        packet = encode(100, 99.5, 100, 123456789.1, 123456789.1, 'CPU+RAM')
        self.assertLess(len(packet), 256)
        self.assertEqual(packet.count(b'\n'), 1)
        self.assertEqual(json.loads(packet)['v'], 1)

    def test_invalid_metrics_are_rejected(self):
        for cpu in [float('nan'), float('inf'), -1, 101]:
            with self.assertRaises(ValueError):
                encode(cpu, 20, 40, 0, 0, 'OK')


if __name__ == '__main__':
    unittest.main()
