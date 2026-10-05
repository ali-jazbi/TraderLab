"""Pure rules. Section numbers refer to docs/sources/canonical-strategy.fa.md."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

PIP = Decimal("0.1")  # UNIT-01, canonical §1; never use broker _Point.
LEG_LOTS = Decimal("0.01")


def number(value: Any) -> Decimal:
    if isinstance(value, (bool, float)):
        raise ValueError("Prices/costs must be decimal strings or integers, not floats/bools")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid decimal: {value!r}") from None
    if not result.is_finite():
        raise ValueError("Non-finite decimal")
    return result


class Unresolved(ValueError):
    def __init__(self, question: str):
        self.question = question
        super().__init__(f"TODO_STRATEGY_UNRESOLVED:{question}")


def required(config: dict, key: str):
    value = config.get(key)
    if value is None:
        raise Unresolved(key)
    return value


def choice(config: dict, key: str, options: tuple[str, ...]) -> str:
    value = required(config, key)
    if value not in options:
        raise ValueError(f"{key}: expected one of {options}")
    return value


def direction(value: str) -> int:
    if value not in ("BUY", "SELL"):
        raise ValueError("Direction must be BUY or SELL")
    return 1 if value == "BUY" else -1


@dataclass(frozen=True)
class Zone:
    low: Decimal
    high: Decimal

    @classmethod
    def read(cls, values: list):
        if len(values) != 2:
            raise ValueError("Zone must contain [low, high]")
        zone = cls(*(number(v) for v in values))
        if zone.low > zone.high:
            raise ValueError("Zone low exceeds high")
        return zone


@dataclass(frozen=True)
class Bos:
    id: str
    entry: Decimal
    zone: Zone


@dataclass(frozen=True)
class Plan:
    side: str
    entries: tuple[Bos, ...]
    stop: Decimal
    target1: Decimal
    target2: Decimal
    reference: Decimal


def select_bos(side: str, candidates: list[Bos]) -> tuple[Bos, ...]:
    """SELECT-01/02: only the explicit >=10..40 branches (§§14–15)."""
    direction(side)
    if not candidates:
        raise ValueError("A setup requires BOS annotations")
    if len({b.id for b in candidates}) != len(candidates):
        raise ValueError("Duplicate BOS IDs")
    if len(candidates) == 1:
        return (candidates[0],)
    ordered = sorted(candidates, key=lambda b: (b.entry, b.id))
    lowest, highest = ordered[0], ordered[-1]
    distance = (highest.entry - lowest.entry) / PIP
    if distance < 10:
        raise Unresolved("bos_distance_lt10")
    if distance <= 20:
        return (highest if side == "BUY" else lowest,)
    if distance <= 40:
        # Order follows retracement sequence. Simultaneous touches remain explicit.
        return (highest, lowest) if side == "BUY" else (lowest, highest)
    raise Unresolved("bos_distance_gt40")


def core_plan(side: str, candidates: list[Bos], config: dict) -> Plan:
    chosen = select_bos(side, candidates)
    sign = direction(side)
    reference = max(b.entry for b in chosen) if sign == 1 else min(b.entry for b in chosen)
    if len(chosen) == 2:
        stop = min(b.entry for b in chosen) - 30 * PIP if sign == 1 else max(b.entry for b in chosen) + 30 * PIP
    else:
        distance = number(required(config, "single_core_sl_pips"))
        if distance <= 0:
            raise ValueError("single_core_sl_pips must be positive")
        stop = chosen[0].entry - sign * distance * PIP
    return Plan(side, chosen, stop, reference + sign * 60 * PIP,
                reference + sign * 100 * PIP, reference)


def reverse_plan(side: str, original_entry: Decimal, config: dict) -> Plan:
    sign = direction(side)
    distance = number(required(config, "breaker_sl_pips"))
    if distance <= 0:
        raise ValueError("breaker_sl_pips must be positive")
    bos = Bos("reverse", original_entry, Zone(original_entry, original_entry))
    return Plan(side, (bos,), original_entry - sign * distance * PIP,
                original_entry + sign * 60 * PIP, original_entry + sign * 100 * PIP,
                original_entry)


def breakeven(plan: Plan, original_entry: Decimal, config: dict) -> Decimal:
    anchor = original_entry
    if len(plan.entries) > 1:
        mode = choice(config, "multi_entry_be_reference", ("own_entry", "shared_reference"))
        anchor = original_entry if mode == "own_entry" else plan.reference
    return anchor + direction(plan.side) * 5 * PIP


def ob_broken(original_side: str, ob: Zone, observed: Decimal) -> bool:
    return observed <= ob.low - 10 * PIP if direction(original_side) == 1 else observed >= ob.high + 10 * PIP


@dataclass
class DailyGuard:
    key: str = ""
    closed_profit: Decimal = Decimal(0)
    profit_reached: bool = False
    stopped_setups: set[str] = field(default_factory=set)
    halted: bool = False

    def reset(self, key: str):
        if key != self.key:
            self.key = key
            self.closed_profit = Decimal(0)
            self.profit_reached = False
            self.stopped_setups.clear()
            self.halted = False

    def close(self, setup: str, pnl: Decimal, stopped: bool):
        # DAY-02: evaluate a subsequent stop against the latch BEFORE this close.
        previously_reached = self.profit_reached
        self.closed_profit += pnl
        if stopped:
            self.stopped_setups.add(setup)
            self.halted |= previously_reached or len(self.stopped_setups) >= 2
        self.profit_reached |= self.closed_profit >= Decimal(100)

