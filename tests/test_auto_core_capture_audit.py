"""Report validation using diagnostic records, not historical trading evidence."""
from pathlib import Path
import json
import tempfile
import unittest
from tools.audit_auto_core import audit


class CaptureAuditChecks(unittest.TestCase):
    def test_missing_data_is_not_a_zero_trade_backtest(self):
        with tempfile.TemporaryDirectory() as folder:
            report = audit(Path(folder) / 'absent.jsonl')
        self.assertEqual(report['status'], 'BLOCKED_MISSING_RAW_CAPTURE')
        for key in ('simulated_entry_orders', 'closed_trades', 'net_profit',
                    'max_equity_drawdown', 'win_rate', 'profit_factor'):
            self.assertIsNone(report[key])

    def test_incomplete_capture_cannot_publish_native_metrics_as_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            capture = Path(folder) / 'incomplete.jsonl'
            capture.write_text(json.dumps({'seq': 1, 'event': 'TESTER_CORE_METRICS',
                'trades': 0, 'net_profit': 0, 'max_equity_drawdown': 0}) + '\n')
            report = audit(capture)
        self.assertTrue(report['status'].startswith('BLOCKED'))
        self.assertIsNone(report['closed_trades'])
        self.assertIsNone(report['net_profit'])

    def test_duplicate_sequence_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            capture = Path(folder) / 'unordered.jsonl'
            capture.write_text((json.dumps({'seq': 1, 'event': 'DIAGNOSTIC'}) + '\n') * 2)
            with self.assertRaisesRegex(ValueError, 'sequence'):
                audit(capture)

    def test_recovery_shard_cannot_be_reported_as_full_historical_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            capture = Path(folder)/'restarted.jsonl'
            capture.write_text(json.dumps({'seq': 1, 'event': 'AUTO_CORE_RECOVERY', 'recovered_ticks': 22})+'\n')
            with self.assertRaisesRegex(ValueError, 'not a standalone'):
                audit(capture)


if __name__ == '__main__':
    unittest.main()
