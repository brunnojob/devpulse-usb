import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_agent(self, *args):
        return subprocess.run(
            [sys.executable, "agent.py", *args], text=True, capture_output=True, timeout=10
        )

    def test_real_capture_is_finite_and_never_overwrites_existing_session(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "session.ndjson"
            result = self.run_agent(
                "--record", str(target), "--duration", "0.5", "--interval", "0.25"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            original = target.read_bytes()
            rows = [json.loads(line) for line in original.splitlines()]
            self.assertGreaterEqual(len(rows), 1)
            self.assertTrue(all(0 <= row["cpu"] <= 100 for row in rows))
            self.assertTrue(all(a["t"] < b["t"] for a, b in zip(rows, rows[1:], strict=False)))
            duplicate = self.run_agent(
                "--record", str(target), "--duration", "0.25", "--interval", "0.25"
            )
            self.assertEqual(duplicate.returncode, 1)
            self.assertEqual(target.read_bytes(), original)

    def test_bad_arguments_are_rejected_before_collecting(self):
        for args in [
            ("--stdout", "--interval", "nan"),
            ("--stdout", "--port", "COM5"),
            ("--stdout", "--duration", "0"),
            ("--list", "--record", "bad.ndjson"),
        ]:
            with self.subTest(args=args):
                self.assertEqual(self.run_agent(*args).returncode, 2)

    def test_invalid_volume_has_a_readable_error(self):
        result = self.run_agent("--stdout", "--disk", "/nonexistent/devpulse/missing")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot collect telemetry", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
