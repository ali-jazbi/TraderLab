import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "normalize_mt5_log.py"


class NormalizeNativeLogChecks(unittest.TestCase):
    def normalize(self, row):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        capture = root / "capture.jsonl"
        output = root / "normalized.jsonl"
        capture.write_text(json.dumps(row) + "\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(capture), str(output)],
            capture_output=True, text=True, check=False,
        )
        return result, output

    @staticmethod
    def tick_row(utc_time="2026-07-01T09:00:00.123Z"):
        return {
            "seq": 1,
            "kind": "tick",
            "event": "TICK",
            "server_time": "2026-07-01T12:00:00.123",
            "time": utc_time,
            "server_utc_offset_seconds": 10800,
            "tehran_utc_offset_seconds": 12600,
            "strategy_time": "2026-07-01T12:30:00.123+03:30",
            "bid": "4146.4",
            "ask": "4146.6",
        }

    def test_native_tick_normalizes_and_preserves_utc_milliseconds(self):
        result, output = self.normalize(self.tick_row())

        self.assertEqual(result.returncode, 0, result.stderr)
        normalized = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(normalized["time"], "2026-07-01T09:00:00.123Z")
        self.assertEqual(normalized["server_time"], "2026-07-01T12:00:00.123")
        self.assertEqual(normalized["server_offset_diagnostic"], "MATCH")

    def test_native_tick_rejects_genuine_one_millisecond_mismatch(self):
        result, output = self.normalize(self.tick_row("2026-07-01T09:00:00.124Z"))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("recorded UTC does not match", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
