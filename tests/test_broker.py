from datetime import datetime, timezone
from decimal import Decimal
import unittest

from traderlab.broker import (BrokerRequestGateway, RollingRequestGuard,
                              capability_issues, diagnose_server_offset,
                              litefinance_expected_offset_seconds, price_grid_compatible,
                              server_to_utc, tehran_time)


class RequestGuardChecks(unittest.TestCase):
    def test_short_window_allows_limit_blocks_next_and_expires(self):
        guard = RollingRequestGuard()
        for index in range(999):
            self.assertEqual(guard.record_dispatch(0), "REQUEST_ALLOWED", index)
        self.assertEqual(guard.record_dispatch(0), "REQUEST_RATE_WARNING")
        self.assertEqual(len(guard.attempts), 1000)
        self.assertEqual(guard.record_dispatch(0), "REQUEST_RATE_BLOCKED")
        self.assertEqual(len(guard.attempts), 1000)
        self.assertEqual(guard.record_dispatch(300_000), "REQUEST_ALLOWED")
        self.assertEqual(len(guard.attempts), 1001)  # Keep the hour window while expiring the 5-minute view.

    def test_long_window_limit_blocks_next(self):
        guard = RollingRequestGuard()
        for index in range(9_999):
            self.assertNotEqual(guard.record_dispatch(index * 360), "REQUEST_RATE_BLOCKED", index)
        self.assertEqual(guard.record_dispatch(9_999 * 360), "REQUEST_RATE_WARNING")
        self.assertEqual(len(guard.attempts), 10_000)
        self.assertEqual(guard.record_dispatch(9_999 * 360), "REQUEST_RATE_BLOCKED")
        self.assertEqual(len(guard.attempts), 10_000)
        self.assertEqual(guard.record_dispatch(7_199_640), "REQUEST_ALLOWED")

    def test_timeout_explicit_retry_and_duplicate_idempotency(self):
        gateway = BrokerRequestGateway()
        payload = {"setup_id": "S1", "bos_id": "B1", "entry_id": "E1", "volume": "0.01"}
        calls = []

        def timeout(_):
            calls.append("attempt")
            raise TimeoutError("outcome unknown")

        first = gateway.submit("R1", payload, 0, timeout)
        self.assertEqual(first.state, "REQUEST_TIMEOUT")
        self.assertEqual(first.attempt_count, 1)
        self.assertEqual(gateway.submit("R1", payload, 1, timeout).attempt_count, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(gateway.retry("R1", payload, 2, lambda _: {"retcode": "ok"}).state,
                         "REQUEST_PENDING")
        request = gateway.requests["R1"]
        self.assertEqual(request.attempt_ids, ["R1:attempt:1", "R1:attempt:2"])
        self.assertEqual(len(gateway.guard.attempts), 2)
        self.assertEqual(gateway.submit("R1", payload, 3, lambda _: calls.append("duplicate")).attempt_count, 2)
        self.assertEqual(calls, ["attempt"])
        with self.assertRaisesRegex(ValueError, "PAYLOAD_CONFLICT"):
            gateway.submit("R1", {**payload, "volume": "0.02"}, 3, lambda _: None)
        gateway.reconcile("R1", "REQUEST_ACCEPTED", {"retcode": "server_accepted"})
        self.assertEqual(gateway.requests["R1"].state, "REQUEST_ACCEPTED")
        with self.assertRaisesRegex(ValueError, "broker-state evidence"):
            gateway.reconcile("R1", "REQUEST_RECONCILED", {})
        gateway.reconcile("R1", "REQUEST_RECONCILED", {"deal_id": "D1"})
        self.assertEqual(gateway.requests["R1"].state, "REQUEST_RECONCILED")


class BrokerCapabilityChecks(unittest.TestCase):
    def capabilities(self, **updates):
        return {"volume_min": "0.01", "volume_max": "100", "volume_step": "0.01",
                "volume_limit": "100", "tick_size": "0.01", **updates}

    def test_canonical_leg_and_price_grid(self):
        self.assertEqual(capability_issues(self.capabilities(), ["4146.50", "4140.00"]), [])
        self.assertEqual(capability_issues(self.capabilities(tick_size="0.05"), ["4146.50"]), [])
        issues = capability_issues(self.capabilities(tick_size="0.05"), ["4146.53"])
        self.assertIn("BROKER_CONFIG_BLOCKED:canonical_price_grid_unrepresentable", issues)
        self.assertFalse(price_grid_compatible(["4146.53"], "0.05"))
        self.assertTrue(price_grid_compatible(["4146.50"], "0.05"))

    def test_unsupported_volume_minimum_or_step_blocks_without_rounding(self):
        for caps in (self.capabilities(volume_min="0.02"),
                     self.capabilities(volume_step="0.02", volume_min="0.005")):
            self.assertIn("BROKER_CONFIG_BLOCKED:canonical_0.01_lot_unrepresentable",
                          capability_issues(caps))

    def test_server_offsets_normalize_independently_of_tehran_strategy_time(self):
        summer_server = server_to_utc("2026-07-01T12:00:00", 10_800)
        winter_server = server_to_utc("2026-01-15T11:00:00", 7_200)
        self.assertEqual(tehran_time(summer_server, 12_600).isoformat(), "2026-07-01T12:30:00+03:30")
        self.assertEqual(tehran_time(winter_server, 12_600).isoformat(), "2026-01-15T12:30:00+03:30")
        self.assertEqual(summer_server.hour, winter_server.hour)
        self.assertEqual(diagnose_server_offset("2026-07-01T12:00:00", 10_800), "MATCH")
        self.assertEqual(diagnose_server_offset("2026-01-15T11:00:00", 7_200), "MATCH")
        self.assertEqual(diagnose_server_offset("2026-07-01T12:00:00", 7_200), "MISMATCH")
        self.assertIsNone(litefinance_expected_offset_seconds(
            datetime(2026, 3, 29, 12, tzinfo=timezone.utc)))
        with self.assertRaisesRegex(ValueError, "explicit integer"):
            server_to_utc("2026-07-01T12:00:00", None)
        with self.assertRaisesRegex(ValueError, "naive broker"):
            server_to_utc("2026-07-01T12:00:00Z", 10_800)


if __name__ == "__main__":
    unittest.main()
