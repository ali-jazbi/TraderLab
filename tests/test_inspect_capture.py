import json
from pathlib import Path
import tempfile
import unittest

from tools.inspect_capture import inspect_capture


def event(seq, event_name, server_time, utc_time, strategy_time, **details):
    return {
        "seq": seq,
        "time": utc_time,
        "server_time": server_time,
        "server_utc_offset_seconds": 10800,
        "strategy_time": strategy_time,
        "tehran_utc_offset_seconds": 12600,
        "event": event_name,
        **details,
    }


def valid_capture():
    return [
        event(1, "EA_INIT", "2026-07-01T12:00:00.123", "2026-07-01T09:00:00.123Z",
              "2026-07-01T12:30:00.123+03:30", mode="detection_only",
              broker_orders_enabled=False, broker_symbol="XAUUSD.pro"),
        event(2, "BROKER_CAPABILITY_SNAPSHOT", "2026-07-01T12:00:01.000",
              "2026-07-01T09:00:01.000Z", "2026-07-01T12:30:01.000+03:30",
              broker_symbol="XAUUSD.pro", strategy_pip="0.1", digits=2,
              point=0.01, tick_size=0.01, tick_value_profit=1.0, tick_value_loss=1.0,
              contract_size=100, volume_min=0.01, volume_max=100, volume_step=0.01,
              volume_limit=100, stops_level=0, freeze_level=0, trade_mode=4,
              order_mode=127, filling_mode=3, account_currency="USD", account_margin_mode=2,
              account_leverage=500, account_trade_mode=0, account_trade_allowed=True,
              account_trade_expert=True, account_hedge_allowed=True,
              swap_long=-1.0, swap_short=-1.0),
        event(3, "TICK", "2026-07-01T12:00:02.123", "2026-07-01T09:00:02.123Z",
              "2026-07-01T12:30:02.123+03:30", kind="tick", symbol="XAUUSD.pro",
              tick_index=1, bid="4146.4", ask="4146.6", spread_price="0.2"),
        event(4, "CLOSED_BAR", "2026-07-01T12:00:03.000", "2026-07-01T09:00:03.000Z",
              "2026-07-01T12:30:03.000+03:30", kind="bar", symbol="XAUUSD.pro",
              opened_at="2026-07-01T08:59:00.000Z", timeframe="M1"),
    ]


class CaptureInspectorChecks(unittest.TestCase):
    def inspect_rows(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            return inspect_capture(path)

    def test_valid_capture_checks_timestamp_symbol_capabilities_and_spread(self):
        result = self.inspect_rows(valid_capture())

        self.assertEqual(result["errors"], [])
        self.assertEqual(result["symbol"], "XAUUSD.pro")
        self.assertEqual(len(result["ticks"]), 1)
        self.assertEqual(str(result["spreads"][0]), "0.2")
        self.assertEqual(result["offsets"], [10800])

    def test_millisecond_mismatch_and_static_symbol_are_rejected(self):
        rows = valid_capture()
        rows[2]["time"] = "2026-07-01T09:00:02.124Z"
        rows[2]["symbol"] = "XAUUSD"

        result = self.inspect_rows(rows)

        self.assertTrue(any("does not match" in error for error in result["errors"]))
        self.assertTrue(any("symbol differs" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
