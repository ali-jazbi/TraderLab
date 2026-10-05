"""Explicit calendar snapshots and supporting NY observations (§§26–32)."""

from datetime import timedelta

from .detection import Bar, instant
from .strategy import PIP, Unresolved, number, required


def news_block(config: dict, now, reverse: bool) -> bool:
    calendar = required(config, "news_calendar")
    if not calendar.get("source"):
        raise ValueError("news_calendar needs a source")
    if not instant(calendar["coverage_start"]) <= now <= instant(calendar["coverage_end"]):
        raise Unresolved("news_calendar_coverage")
    blocked = False
    for event in calendar["events"]:
        if event["name"] not in ("CPI", "NFP", "FOMC"):
            raise ValueError("Only the canonical CPI/NFP/FOMC calendar is supported")
        announced = instant(event["available_at"])
        scheduled = instant(event["scheduled_at"])
        if now >= announced and abs(now - scheduled) <= timedelta(minutes=15):
            blocked = True
        elif now < announced and abs(now - scheduled) <= timedelta(minutes=15):
            raise Unresolved("news_snapshot_not_available_in_time")
    if blocked and reverse:
        policy = required(config, "news_reverse_policy")
        if policy not in ("block", "allow"):
            raise ValueError("news_reverse_policy must be block or allow")
        return policy == "block"
    return blocked


class NYBias:
    def __init__(self, config: dict):
        self.config = config
        self.day = ""
        self.high = self.low = None
        self.coverage: set[int] = set()
        self.up = self.down = False
        self.status = "NO_BIAS"

    def accept(self, bar: Bar) -> dict | None:
        if bar.timeframe != "M15":
            return None
        offset = self.config.get("tehran_utc_offset_seconds")
        if offset is None:
            self.status = "UNRESOLVED"
            return {"event": "NY_CONTEXT", "rule": "NY-01", "status": self.status,
                    "todo": "tehran_utc_offset_seconds"}
        local = bar.opened + timedelta(seconds=int(offset))
        day, minute = local.date().isoformat(), local.hour * 60 + local.minute
        if day != self.day:
            self.day, self.high, self.low = day, None, None
            self.coverage = set()
            self.up = self.down = False
            self.status = "NO_BIAS"
        # Endpoint semantics are required before treating the observation as a definitive bias.
        endpoint = self.config.get("ny_range_endpoint_policy")
        if endpoint not in (None, "bar_open_half_open"):
            raise ValueError("Supported NY endpoint policy: bar_open_half_open")
        if 630 <= minute < 750:
            self.high = bar.high if self.high is None else max(self.high, bar.high)
            self.low = bar.low if self.low is None else min(self.low, bar.low)
            self.coverage.add(minute)
            return {"event": "NY_RANGE_OBSERVATION", "rule": "NY-01", "high": self.high,
                    "low": self.low, "complete": self.coverage == set(range(630, 750, 15)),
                    "provisional": endpoint is None}
        if minute < 750 or self.high is None:
            return None
        end = self.config.get("ny_london_scan_end_minute")
        if end is not None and not 750 < int(end) <= 1440:
            raise ValueError("London scan end must be after Iran12:30 and <=24:00")
        if endpoint is None or end is None or self.coverage != set(range(630, 750, 15)):
            self.status = "UNRESOLVED"
            return {"event": "NY_CONTEXT", "rule": "NY-02", "status": self.status,
                    "todo": "ny_range_endpoint_policy/ny_london_scan_end_minute/range_coverage"}
        if minute >= int(end):
            return None
        self.up |= bar.high >= self.high + 30 * PIP
        self.down |= bar.low <= self.low - 30 * PIP
        self.status = "AMBIGUOUS_BOTH_SIDES" if self.up and self.down else "BUY" if self.up else "SELL" if self.down else "NO_BIAS"
        return {"event": "NY_CONTEXT", "rule": "NY-02", "status": self.status,
                "hard_filter": False, "high_broken": self.up, "low_broken": self.down}

