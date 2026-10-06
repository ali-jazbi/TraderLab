"""Broker capability checks and a deterministic, non-trading request guard."""

from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
from typing import Callable, Any

from .strategy import LEG_LOTS, number

SHORT_WINDOW_MS = 300_000
LONG_WINDOW_MS = 3_600_000
SHORT_LIMIT = 1_000
LONG_LIMIT = 10_000


def server_to_utc(server_time: str | datetime, server_utc_offset_seconds: int) -> datetime:
    """Normalize a naive broker wall-clock using only its explicitly supplied offset."""
    if isinstance(server_utc_offset_seconds, bool) or not isinstance(server_utc_offset_seconds, int):
        raise ValueError("server_utc_offset_seconds must be an explicit integer")
    value = datetime.fromisoformat(server_time) if isinstance(server_time, str) else server_time
    if value.tzinfo is not None:
        raise ValueError("server_time must be a naive broker wall-clock; UTC is supplied separately")
    return (value - timedelta(seconds=server_utc_offset_seconds)).replace(tzinfo=timezone.utc)


def validate_capture_timestamp(server_time: str | datetime, recorded_utc: str | datetime,
                               server_utc_offset_seconds: int) -> datetime:
    """Require the recorded UTC instant to exactly match server time and offset."""
    expected = server_to_utc(server_time, server_utc_offset_seconds)
    recorded = (datetime.fromisoformat(recorded_utc.replace("Z", "+00:00"))
                if isinstance(recorded_utc, str) else recorded_utc)
    if recorded.tzinfo is None or recorded.utcoffset() != timedelta(0):
        raise ValueError("recorded timestamp must be explicit UTC")
    if recorded != expected:
        raise ValueError("recorded UTC does not match server timestamp plus configured offset")
    return expected


def tehran_time(utc_time: datetime, tehran_utc_offset_seconds: int) -> datetime:
    if utc_time.tzinfo is None or utc_time.utcoffset() != timedelta(0):
        raise ValueError("utc_time must be timezone-aware UTC")
    if isinstance(tehran_utc_offset_seconds, bool) or not isinstance(tehran_utc_offset_seconds, int):
        raise ValueError("tehran_utc_offset_seconds must be explicitly configured")
    return utc_time.astimezone(timezone(timedelta(seconds=tehran_utc_offset_seconds)))


def litefinance_expected_offset_seconds(utc_time: datetime) -> int | None:
    """Public calendar rule; transition Sundays remain explicitly unverified."""
    if utc_time.tzinfo is None or utc_time.utcoffset() != timedelta(0):
        raise ValueError("utc_time must be timezone-aware UTC")

    def last_sunday(year: int, month: int) -> date:
        first_next = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        last = first_next - timedelta(days=1)
        return last - timedelta(days=(last.weekday() + 1) % 7)

    spring, autumn = last_sunday(utc_time.year, 3), last_sunday(utc_time.year, 10)
    if utc_time.date() in (spring, autumn):
        return None
    return 3 * 3600 if spring < utc_time.date() < autumn else 2 * 3600


def diagnose_server_offset(server_time: str | datetime, configured_seconds: int) -> str:
    utc = server_to_utc(server_time, configured_seconds)
    expected = litefinance_expected_offset_seconds(utc)
    if expected is None:
        return "TRANSITION_DAY_UNVERIFIED"
    return "MATCH" if configured_seconds == expected else "MISMATCH"


def capability_issues(capabilities: dict[str, Any], price_levels=(),
                      requested_volume: Any = 2 * LEG_LOTS,
                      current_directional_volume: Any = 0) -> list[str]:
    """Check canonical legs, aggregate exposure, and price grid without rounding."""
    try:
        minimum = number(capabilities["volume_min"])
        maximum = number(capabilities["volume_max"])
        step = number(capabilities["volume_step"])
        limit = number(capabilities["volume_limit"])
    except (KeyError, ValueError) as error:
        return [f"BROKER_CAPABILITY_UNAVAILABLE:{error}"]
    if minimum <= 0 or maximum < minimum or step <= 0 or limit < 0:
        return ["BROKER_CAPABILITY_INVALID:volume_limits"]
    lots = LEG_LOTS
    issues = []
    if not minimum <= lots <= maximum or (lots - minimum) % step:
        issues.append("BROKER_CONFIG_BLOCKED:canonical_0.01_lot_unrepresentable")
    requested = number(requested_volume)
    current = number(current_directional_volume)
    if requested < 0 or current < 0:
        return issues + ["BROKER_CAPABILITY_INVALID:negative_directional_volume"]
    if limit and current + requested > limit:
        issues.append("BROKER_CONFIG_BLOCKED:aggregate_directional_volume_limit_exceeded")
    try:
        tick_size = number(capabilities["tick_size"])
        if tick_size <= 0:
            raise ValueError("tick_size must be positive")
    except (KeyError, ValueError) as error:
        issues.append(f"BROKER_CAPABILITY_UNAVAILABLE:{error}")
    else:
        if any(number(price) % tick_size for price in price_levels):
            issues.append("BROKER_CONFIG_BLOCKED:canonical_price_grid_unrepresentable")
    return issues


def price_grid_compatible(price_levels, tick_size: Any) -> bool:
    tick = number(tick_size)
    if tick <= 0:
        raise ValueError("tick_size must be positive")
    return all(number(price) % tick == 0 for price in price_levels)


@dataclass
class RollingRequestGuard:
    """In-memory deterministic reference; counts every call reaching dispatch."""
    attempts: deque[int] = field(default_factory=deque)

    def _prune(self, now_ms: int) -> None:
        if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
            raise ValueError("now_ms must be a nonnegative monotonic integer")
        while self.attempts and now_ms - self.attempts[0] >= LONG_WINDOW_MS:
            self.attempts.popleft()

    def decision(self, now_ms: int) -> str:
        self._prune(now_ms)
        short_count = sum(now_ms - stamp < SHORT_WINDOW_MS for stamp in self.attempts)
        long_count = len(self.attempts)
        if short_count >= SHORT_LIMIT or long_count >= LONG_LIMIT:
            return "REQUEST_RATE_BLOCKED"
        if short_count + 1 == SHORT_LIMIT or long_count + 1 == LONG_LIMIT:
            return "REQUEST_RATE_WARNING"
        return "REQUEST_ALLOWED"

    def record_dispatch(self, now_ms: int) -> str:
        state = self.decision(now_ms)
        if state == "REQUEST_RATE_BLOCKED":
            return state
        self.attempts.append(now_ms)
        return state


@dataclass
class RequestRecord:
    request_id: str
    payload_hash: str
    state: str
    attempt_count: int = 0
    rate_state: str | None = None
    last_response: Any = None
    attempt_ids: list[str] = field(default_factory=list)


class BrokerRequestGateway:
    """Idempotent testable gateway; sender injection is for simulation only.

    A sender return value is stored as a response and leaves the request pending.
    Only explicit reconciliation can advance it to accepted/rejected/reconciled.
    """

    def __init__(self, guard: RollingRequestGuard | None = None):
        self.guard = guard or RollingRequestGuard()
        self.requests: dict[str, RequestRecord] = {}

    @staticmethod
    def _fingerprint(payload: Any) -> str:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(body.encode()).hexdigest()

    def submit(self, request_id: str, payload: Any, now_ms: int,
               sender: Callable[[Any], Any]) -> RequestRecord:
        fingerprint = self._fingerprint(payload)
        previous = self.requests.get(request_id)
        if previous:
            if previous.payload_hash != fingerprint:
                raise ValueError("REQUEST_ID_PAYLOAD_CONFLICT")
            return previous
        record = RequestRecord(request_id, fingerprint, "REQUEST_ALLOWED")
        self.requests[request_id] = record
        return self._dispatch(record, payload, now_ms, sender)

    def retry(self, request_id: str, payload: Any, now_ms: int,
              sender: Callable[[Any], Any]) -> RequestRecord:
        record = self.requests[request_id]
        if record.payload_hash != self._fingerprint(payload):
            raise ValueError("REQUEST_ID_PAYLOAD_CONFLICT")
        if record.state not in ("REQUEST_REJECTED", "REQUEST_RATE_BLOCKED"):
            raise ValueError("REQUEST_RETRY_REQUIRES_RECONCILED_NO_EXECUTION_OR_RATE_BLOCK")
        return self._dispatch(record, payload, now_ms, sender)

    def _dispatch(self, record: RequestRecord, payload: Any, now_ms: int,
                  sender: Callable[[Any], Any]) -> RequestRecord:
        rate_state = self.guard.record_dispatch(now_ms)
        record.rate_state = rate_state
        if rate_state == "REQUEST_RATE_BLOCKED":
            record.state = rate_state
            return record
        record.attempt_count += 1
        record.attempt_ids.append(f"{record.request_id}:attempt:{record.attempt_count}")
        record.state = "REQUEST_PENDING"
        try:
            record.last_response = sender(payload)
        except Exception:
            # Once dispatch was reached, the outcome is unknown and must fail closed.
            record.state = "REQUEST_TIMEOUT"
        return record

    def reconcile(self, request_id: str, state: str, evidence: dict[str, Any]) -> RequestRecord:
        allowed = {"REQUEST_ACCEPTED", "REQUEST_REJECTED", "REQUEST_RECONCILED"}
        if state not in allowed:
            raise ValueError("Unsupported reconciliation state")
        record = self.requests[request_id]
        if record.state not in ("REQUEST_PENDING", "REQUEST_ACCEPTED", "REQUEST_TIMEOUT"):
            raise ValueError("Only pending/accepted/timeout requests can be reconciled")
        if not evidence.get("source") or not evidence.get("evidence_id"):
            raise ValueError("Reconciliation requires authoritative source and evidence_id")
        found_broker_object = any(evidence.get(k) for k in ("order_id", "deal_id", "position_id"))
        if state == "REQUEST_RECONCILED" and not found_broker_object:
            raise ValueError("REQUEST_RECONCILED requires an order/deal/position identifier")
        if state == "REQUEST_REJECTED" and (evidence.get("no_execution") is not True or found_broker_object):
            raise ValueError("REQUEST_REJECTED requires authoritative confirmation of no execution")
        if state == "REQUEST_ACCEPTED" and not evidence.get("server_retcode"):
            raise ValueError("REQUEST_ACCEPTED requires the server retcode; it does not prove a position exists")
        record.last_response = evidence
        record.state = state
        return record
