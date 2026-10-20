"""Closed-bar observations; owner amendment 2026-10-11, no swing heuristics."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from .strategy import PIP, Zone, direction, number

TIMEFRAMES = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600, "H4": 14400}


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("Event times must explicitly use UTC (Z or +00:00)")
    return result


@dataclass(frozen=True)
class Bar:
    timeframe: str
    opened: datetime
    available: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal

    @classmethod
    def read(cls, event: dict):
        timeframe = event["timeframe"]
        if timeframe not in TIMEFRAMES:
            raise ValueError("Unsupported timeframe")
        opened, available = instant(event["opened_at"]), instant(event["time"])
        if available < opened + timedelta(seconds=TIMEFRAMES[timeframe]):
            raise ValueError("Bar supplied before it closed")
        values = [number(event[k]) for k in ("open", "high", "low", "close")]
        if values[2] <= 0 or values[2] > min(values[0], values[3]) or values[1] < max(values[0], values[3]) or values[2] > values[1]:
            raise ValueError("Invalid OHLC geometry")
        return cls(timeframe, opened, available, *values)

    @property
    def body(self):
        return abs(self.close - self.open)


def big_candle(window: list[Bar]) -> bool:
    if len(window) != 21:
        raise ValueError("BIG-01 requires exactly 21 closed bars")
    return window[10].body >= sum((b.body for i, b in enumerate(window) if i != 10), Decimal(0)) / 10


def fvg(c1: Bar, c2: Bar, c3: Bar):
    if c3.low > c1.high:
        side, zone = "BUY", Zone(c1.high, c3.low)
    elif c3.high < c1.low:
        side, zone = "SELL", Zone(c3.high, c1.low)
    else:
        return None
    if zone.high - zone.low < 20 * PIP:
        return None
    return side, zone


@dataclass
class Candidate:
    bar: Bar
    side: str
    qualified: bool = False

    @property
    def level(self):
        return self.bar.high if self.side == "BUY" else self.bar.low


def has_bos_wick(bar: Bar, side: str, price_step=None) -> bool:
    """Owner §54: directional shadow, additional to close-before-break.

    Compare broker tick units when supplied, otherwise exact source Decimals.
    One actual price increment is sufficient; no strategy wick-size threshold.
    """
    sign = direction(side)
    def grid(value):
        if price_step is None:
            return value
        step = number(price_step)
        if step <= 0:
            raise ValueError('price_step must be positive')
        return (value / step).to_integral_value(rounding=ROUND_HALF_UP)
    if sign == 1:
        return grid(bar.high) > grid(max(bar.open, bar.close))
    return grid(bar.low) < grid(min(bar.open, bar.close))


class Detector:
    def __init__(self, price_step=None):
        self.price_step = price_step
        self.bars: dict[str, list[Bar]] = {}
        self.candidates: dict[str, list[Candidate]] = {}

    def accept(self, bar: Bar) -> list[dict]:
        history = self.bars.setdefault(bar.timeframe, [])
        if history and (bar.opened <= history[-1].opened or bar.opened < history[-1].opened + timedelta(seconds=TIMEFRAMES[bar.timeframe])):
            raise ValueError("Duplicate, overlapping or out-of-order bars")
        emitted = []
        active = self.candidates.setdefault(bar.timeframe, [])
        retained = []
        for candidate in active:
            old, side = candidate.bar, candidate.side
            crossed = bar.high > old.high if side == "BUY" else bar.low < old.low
            qualifies = bar.close < old.low if side == "BUY" else bar.close > old.high
            if crossed:
                # Qualification on THIS bar cannot prove it preceded an intrabar break.
                emitted.append({"event": "BOS_CANDIDATE_BREAK", "rule": "BOS-01", "side": side,
                                "candidate_at": old.opened, "timeframe": bar.timeframe,
                                "qualified_before_break": candidate.qualified,
                                "same_bar_order_ambiguous": qualifies and not candidate.qualified,
                                "level": candidate.level, "tradable_zone": None})
                emitted.append({"event": "BOS_CONFIRMED" if candidate.qualified else "BOS_REJECTED",
                                "rule": "BOS-01/BOS-02", "side": side,
                                "candidate_at": old.opened, "available_at": bar.available,
                                "timeframe": bar.timeframe, "level": candidate.level,
                                "confirmation_source": "closed_bar_wick",
                                "reason": "qualified_before_break" if candidate.qualified else
                                "same_bar_order_ambiguous" if qualifies else "break_before_qualification"})
            else:
                if qualifies and not candidate.qualified:
                    candidate.qualified = True
                    emitted.append({"event": "BOS_CANDIDATE_QUALIFIED", "rule": "BOS-01", "side": side,
                                    "candidate_at": old.opened, "timeframe": bar.timeframe,
                                    "level": candidate.level, "tradable_zone": None})
                retained.append(candidate)
        # Diagnostic candidates, not a swing heuristic or tradable zone.
        for side in ('BUY', 'SELL'):
            if has_bos_wick(bar, side, self.price_step):
                retained.append(Candidate(bar, side))
            else:
                emitted.append({'event': 'BOS_REJECTED', 'rule': 'BOS-WICK-01/OWNER-54',
                                'side': side, 'candidate_at': bar.opened,
                                'available_at': bar.available, 'timeframe': bar.timeframe,
                                'level': bar.high if side == 'BUY' else bar.low,
                                'reason': 'directional_wick_missing'})
        self.candidates[bar.timeframe] = retained
        history.append(bar)
        if len(history) >= 21:
            window = history[-21:]
            if big_candle(window):
                candidate = window[10]
                emitted.append({"event": "BIG_CANDLE_CONFIRMED", "rule": "BIG-01", "candidate_at": candidate.opened,
                                "available_at": bar.available, "timeframe": bar.timeframe, "body": candidate.body})
                gap = fvg(window[9], candidate, window[11])
                if gap:
                    side, zone = gap
                    # The gap may already be filled while waiting for the ten future bars.
                    following = window[12:]
                    filled = any(b.low <= zone.low for b in following) if side == "BUY" else any(b.high >= zone.high for b in following)
                    partial = any(b.low < zone.high for b in following) if side == "BUY" else any(b.high > zone.low for b in following)
                    emitted.append({"event": "FVG_CONFIRMED", "rule": "FVG-01", "side": side,
                                    "candidate_at": candidate.opened, "available_at": bar.available,
                                    "formation_at": window[11].available,
                                    "timeframe": bar.timeframe, "zone": [zone.low, zone.high],
                                    "fill_state": "FULL" if filled else "PARTIAL" if partial else "UNFILLED",
                                    "tradable_setup": False, "todo": "Q-ASSOCIATION"})
                    anchor = window[11] if side == "BUY" else window[9]
                    emitted.append({"event": "OB_CONFIRMED", "rule": "OB-01", "side": side,
                                    "timeframe": bar.timeframe, "candidate_at": candidate.opened,
                                    "anchor_candle": "C3" if side == "BUY" else "C1",
                                    "anchor_at": anchor.opened, "available_at": bar.available,
                                    "zone": [anchor.low, anchor.high], "tradable_setup": False})
                else:
                    emitted.append({"event": "FVG_REJECTED", "rule": "FVG-01/FVG-02",
                                    "candidate_at": candidate.opened, "timeframe": bar.timeframe,
                                    "reason": "gap_below_20_pips" if window[11].low > window[9].high or
                                    window[11].high < window[9].low else "no_wick_gap"})
            else:
                emitted.append({"event": "BIG_CANDLE_REJECTED", "rule": "BIG-01",
                                "candidate_at": window[10].opened, "timeframe": bar.timeframe,
                                "reason": "body_below_two_times_average"})
        # ponytail: only 21 bars are needed for delayed confirmation; candidates persist until crossed.
        self.bars[bar.timeframe] = history[-21:]
        return emitted
