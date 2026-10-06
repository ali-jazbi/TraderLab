"""Deterministic, tick-driven paper engine. Never sends an order to a broker."""

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import SPEC_VERSION
from .broker import capability_issues, price_grid_compatible
from .detection import Bar, Detector, instant
from .session import NYBias, news_block
from .strategy import (Bos, DailyGuard, LEG_LOTS, PIP, Plan, Unresolved, Zone, breakeven,
                       choice, core_plan, direction, number, ob_broken, required, reverse_plan)


def encode(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if is_dataclass(value):
        return {k: encode(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if isinstance(value, set):
        return sorted(encode(v) for v in value)
    return value


def json_line(value):
    return json.dumps(encode(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


@dataclass
class Setup:
    id: str
    side: str
    bos: list[Bos]
    fvg: Zone
    ob: Zone
    source: str
    available: datetime
    fill: str
    plan: Plan | None = None
    unresolved: str | None = None
    planned_core_entry: dict[str, Decimal] = field(default_factory=dict)
    actual_core_fill: dict[str, Decimal] = field(default_factory=dict)
    stopped: set[str] = field(default_factory=set)
    bos_broken: bool = False
    ob_broken: bool = False
    ifvg_confirmed: bool = False
    reverse_armed: bool = False
    reverse_armed_sequence: int | None = None
    reverse_consumed: bool = False


@dataclass
class Position:
    id: str
    setup_id: str
    bos_id: str
    plan: Plan
    entry: Decimal
    stop: Decimal
    target: Decimal
    leg: int
    reverse: bool
    costs_paid: Decimal
    open: bool = True
    be_applied: bool = False


class Engine:
    def __init__(self, config: dict):
        if config.get("mode") != "paper":
            raise ValueError("Phase one supports mode=paper only")
        if config.get("strategy_symbol") != "XAUUSD":
            raise ValueError("Canonical strategy is XAUUSD")
        self.config = config
        self.now = None
        self.input_sequence = 0
        self.events: list[dict] = []
        self.detector = Detector()
        self.ny = NYBias(config)
        self.daily = DailyGuard()
        self.total_closed_profit = Decimal(0)
        self.daily_results: dict[str, dict] = {}
        self.setups: dict[str, Setup] = {}
        self.positions: list[Position] = []
        self.consumed_bos: set[str] = set()
        self.seen_event_ids: set[str] = set()
        self.last_tick = None
        self.execution_block: str | None = None
        self._logged_blocks: set[tuple] = set()

    def emit(self, name: str, rule: str, **details):
        event = {"seq": len(self.events) + 1, "time": self.now, "event": name,
                 "rule": rule, "spec_version": SPEC_VERSION, **details}
        self.events.append(encode(event))

    def blocked(self, setup_id: str, reason: str, context: str = "core"):
        key = (self.daily.key, setup_id, reason, context)
        if key not in self._logged_blocks:
            self._logged_blocks.add(key)
            self.emit("ENTRY_BLOCKED", "SCOPE-01", setup_id=setup_id, context=context,
                      reason=reason, todo=reason.startswith("TODO_STRATEGY_UNRESOLVED"))

    def day_key(self):
        name = required(self.config, "daily_reset_zone")
        minute = required(self.config, "daily_reset_minute")
        if not isinstance(minute, int) or isinstance(minute, bool) or not 0 <= minute < 1440:
            raise ValueError("daily_reset_minute must be an integer in [0,1440)")
        try:
            zone = timezone.utc if name == "UTC" else ZoneInfo(name)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Timezone data unavailable for {name}; supply tzdata before replay") from None
        local = self.now.astimezone(zone) - timedelta(minutes=minute)
        return local.date().isoformat()

    def update_day(self):
        try:
            key = self.day_key()
        except Unresolved:
            return
        if key != self.daily.key:
            if self.daily.key:
                self.daily_results[self.daily.key] = self.daily_result()
            if any(p.open for p in self.positions):
                self.execution_block = "TODO_STRATEGY_UNRESOLVED:positions_across_daily_reset"
            self.daily.reset(key)
            self.emit("DAY_RESET", "DAY-02", day=key, reset_zone=self.config["daily_reset_zone"],
                      reset_minute=self.config["daily_reset_minute"])

    def daily_result(self):
        return {"day": self.daily.key, "closed_profit_usd": self.daily.closed_profit,
                "profit_basis": self.config.get("daily_profit_basis"),
                "profit_reached": self.daily.profit_reached,
                "stopped_setups": len(self.daily.stopped_setups), "halted": self.daily.halted}

    def accept(self, event: dict):
        now = instant(event["time"])
        if self.now is not None and now < self.now:
            raise ValueError("Replay events must be time ordered; sorting future information is forbidden")
        if event.get("symbol", "XAUUSD") != "XAUUSD":
            raise ValueError("Unexpected strategy symbol")
        event_id = event.get("event_id")
        if event_id is not None:
            if event_id in self.seen_event_ids:
                raise ValueError("Duplicate input event ID")
            self.seen_event_ids.add(event_id)
        self.now = now
        self.input_sequence += 1
        self.update_day()
        kind = event["kind"]
        if kind == "bar":
            bar = Bar.read(event)
            for observation in self.detector.accept(bar):
                self.emit(observation.pop("event"), observation.pop("rule"), **observation)
            observation = self.ny.accept(bar)
            if observation:
                self.emit(observation.pop("event"), observation.pop("rule"), **observation)
        elif kind == "setup":
            self.add_setup(event)
        elif kind == "structure":
            self.structure(event)
        elif kind == "tick":
            self.tick(event)
        else:
            raise ValueError(f"Unknown event kind: {kind}")

    def add_setup(self, event: dict):
        setup_id, source = event["setup_id"], event.get("source")
        if not setup_id or setup_id in self.setups or not source:
            raise ValueError("Setups require unique IDs and an explicit annotation source")
        side = event["side"]
        direction(side)
        if event.get("confirmed") is not True:
            raise ValueError("Annotation must explicitly confirm setup validity")
        fill = event["fill_state"]
        if fill not in ("UNFILLED", "PARTIAL", "FULL"):
            raise ValueError("fill_state must be explicit")
        candidates = []
        for item in event["bos"]:
            bos = Bos(item["id"], number(item["entry"]), Zone.read(item["zone"]))
            if not bos.id or not bos.zone.low <= bos.entry <= bos.zone.high:
                raise ValueError("BOS entry must lie within explicitly supplied zone")
            candidates.append(bos)
        if len({b.id for b in candidates}) != len(candidates):
            raise ValueError("Duplicate BOS in annotation")
        known = {b.id for s in self.setups.values() for b in s.bos}
        if known.intersection(b.id for b in candidates):
            raise ValueError("BOS IDs must be globally unique; repeated zones cannot reset first touch")
        setup = Setup(setup_id, side, candidates, Zone.read(event["fvg"]),
                      Zone.read(event["ob"]), source, self.now, fill)
        if setup.fvg.high - setup.fvg.low < 20 * PIP:
            raise ValueError("Annotated FVG violates FVG-02 minimum size")
        if fill == "FULL":
            setup.unresolved = "FVG_FULL_FILL_INVALID"
        else:
            try:
                setup.plan = core_plan(side, candidates, self.config)
            except Unresolved as error:
                setup.unresolved = str(error)
        self.setups[setup.id] = setup
        self.emit("SETUP_ANNOTATED", "OB-01/BOS-02", setup_id=setup.id, side=side, source=source,
                  fvg=setup.fvg, ob=setup.ob, bos=candidates, fill_state=fill,
                  automatic_detection=False)
        if setup.plan:
            self.emit("CORE_PLAN", "SELECT-02/SL-01/TP-01", setup_id=setup.id, plan=setup.plan)
        else:
            self.blocked(setup.id, setup.unresolved or "UNRESOLVED")

    def structure(self, event: dict):
        setup = self.setups[event["setup_id"]]
        if not event.get("source"):
            raise ValueError("Structure confirmation requires an explicit source")
        for key in ("bos_broken", "ifvg_confirmed"):
            if key in event and not isinstance(event[key], bool):
                raise ValueError("Structure confirmations must be boolean")
        setup.bos_broken |= event.get("bos_broken", False)
        setup.ifvg_confirmed |= event.get("ifvg_confirmed", False)
        self.emit("STRUCTURE_ANNOTATED", "REV-01", setup_id=setup.id, source=event["source"],
                  bos_broken=setup.bos_broken, ifvg_confirmed=setup.ifvg_confirmed)
        self.arm_reverse(setup)

    def quote(self, tick: dict, side: str, observation: bool = False):
        key = "observation_price_side" if observation else "buy_touch_quote" if side == "BUY" else "sell_touch_quote"
        selected = choice(self.config, key, ("bid", "ask"))
        return number(tick[selected])

    def touched(self, bos: Bos, price: Decimal):
        policy = choice(self.config, "touch_allowance_policy", ("expand_zone",))
        return bos.zone.low - 5 * PIP <= price <= bos.zone.high + 5 * PIP

    @staticmethod
    def reverse_retested(bos: Bos, price: Decimal):
        # REV-02's clarified anchor is the exact planned Core price. The unresolved
        # Core TOUCH-01 allowance is not reused to substitute a different price.
        return price == bos.entry

    @staticmethod
    def reverse_crossed(bos: Bos, previous: Decimal, current: Decimal):
        # Missing an exact executable quote is a data gap, never a fill at the anchor.
        return previous != bos.entry and current != bos.entry and min(previous, current) < bos.entry < max(previous, current)

    def prerequisites(self, setup: Setup, reverse: bool):
        self.day_key()  # Unknown reset cannot silently disable DailyGuard.
        if self.execution_block:
            raise Unresolved(self.execution_block.split(":", 1)[-1])
        if self.daily.halted:
            return "DAILY_NEW_ENTRIES_HALTED"
        if news_block(self.config, self.now, reverse):
            return "NEWS_WINDOW"
        if not reverse:
            if setup.fill == "FULL":
                return "FVG_FULL_FILL_INVALID"
            if setup.fill == "PARTIAL":
                partial = choice(self.config, "partial_fill_policy", ("allow_any_partial", "block_any_partial"))
                if partial == "block_any_partial":
                    return "FVG_PARTIAL_FILL_BLOCKED_BY_EXPLICIT_CONFIG"
            if setup.plan and len(setup.plan.entries) == 2:
                choice(self.config, "multi_entry_be_reference", ("own_entry", "shared_reference"))
        if required(self.config, "account_currency") != "USD":
            raise Unresolved("account_currency_conversion_to_USD")
        contract = number(required(self.config, "contract_size"))
        commission = number(required(self.config, "commission_usd_per_lot_per_side"))
        slippage = number(required(self.config, "slippage_pips"))
        if contract <= 0 or commission < 0 or slippage < 0:
            raise ValueError("Invalid broker/cost parameters")
        choice(self.config, "tp_fill_policy", ("target", "quote"))
        choice(self.config, "be_entry_anchor", ("filled", "planned"))
        choice(self.config, "daily_profit_basis", ("net", "gross"))
        return None

    def open_entry(self, setup: Setup, bos: Bos, plan: Plan, tick: dict, reverse: bool):
        capabilities = self.config.get("runtime_capabilities")
        if not isinstance(capabilities, dict):
            self.blocked(setup.id, "BROKER_CAPABILITY_UNAVAILABLE:runtime_capabilities")
            return
        current_directional = sum((LEG_LOTS for p in self.positions if p.open and p.plan.side == plan.side), Decimal(0))
        planned_levels = [*(entry.entry for entry in plan.entries), plan.stop, plan.target1, plan.target2]
        issues = capability_issues(capabilities, planned_levels, 2 * LEG_LOTS, current_directional)
        if issues:
            for reason in issues:
                name = "BROKER_CONFIG_BLOCKED" if reason.startswith("BROKER_CONFIG_BLOCKED") else "CONFIG_UNRESOLVED"
                self.emit(name, "UNIT-01", setup_id=setup.id, reason=reason,
                          requested_directional_volume=2 * LEG_LOTS,
                          current_directional_volume=current_directional)
            self.blocked(setup.id, issues[0], "reverse" if reverse else "core")
            return
        try:
            blocked = self.prerequisites(setup, reverse)
        except Unresolved as error:
            blocked = str(error)
        if blocked:
            self.blocked(setup.id, blocked, "reverse" if reverse else "core")
            return
        sign = direction(plan.side)
        fill = number(tick["ask" if sign == 1 else "bid"]) + sign * number(self.config["slippage_pips"]) * PIP
        step = number(capabilities["tick_size"])
        levels = [fill]
        if not price_grid_compatible(levels, step):
            self.emit("BROKER_CONFIG_BLOCKED", "UNIT-01", setup_id=setup.id,
                      reason="canonical_price_grid_unrepresentable", tick_size=step,
                      levels=levels)
            self.blocked(setup.id, "BROKER_PRICE_GRID_UNREPRESENTABLE")
            return
        if sign * (fill - plan.stop) <= 0 or sign * (plan.target1 - fill) <= 0:
            self.blocked(setup.id, "QUOTE_OUTSIDE_VALID_SL_TP_GEOMETRY")
            return
        core_entry_id = next(iter(setup.planned_core_entry), None)
        if not reverse:
            setup.planned_core_entry[bos.id] = bos.entry
            setup.actual_core_fill[bos.id] = fill
            core_entry_id = bos.id
        if core_entry_id is None:
            self.blocked(setup.id, "TODO_STRATEGY_UNRESOLVED:missing_core_entry_reference",
                         "reverse")
            return
        fee = number(self.config["commission_usd_per_lot_per_side"]) * LEG_LOTS
        prefix = f"{setup.id}:{'reverse' if reverse else bos.id}"
        for leg, target in ((1, plan.target1), (2, plan.target2)):
            self.positions.append(Position(f"{prefix}:{leg}", setup.id, bos.id, plan, fill,
                                           plan.stop, target, leg, reverse, fee))
        self.emit("PAPER_ENTRY", "TOUCH-01/SIZE-01" if not reverse else "REV-02",
                  setup_id=setup.id, bos_id=bos.id, side=plan.side, planned_entry=bos.entry,
                  planned_core_entry=setup.planned_core_entry[core_entry_id],
                  actual_core_fill=setup.actual_core_fill[core_entry_id],
                  filled_entry=fill, actual_entry_fill=fill, stop=plan.stop, tp1=plan.target1, tp2=plan.target2,
                  lots=2 * LEG_LOTS, reverse=reverse, ny_context=self.ny.status,
                  bias_alignment="ALIGNED" if self.ny.status == plan.side else "COUNTER_BIAS" if self.ny.status in ("BUY", "SELL") else self.ny.status)

    def close_positions(self, tick: dict):
        exits = []
        for position in self.positions:
            if not position.open:
                continue
            sign = direction(position.plan.side)
            executable = number(tick["bid" if sign == 1 else "ask"])
            stop_hit = sign * (executable - position.stop) <= 0
            tp_hit = sign * (executable - position.target) >= 0
            if not stop_hit and not tp_hit:
                continue
            fill = executable - sign * number(self.config["slippage_pips"]) * PIP if stop_hit else position.target if self.config["tp_fill_policy"] == "target" else executable
            fee = number(self.config["commission_usd_per_lot_per_side"]) * LEG_LOTS
            pnl = sign * (fill - position.entry) * LEG_LOTS * number(self.config["contract_size"]) - position.costs_paid - fee
            exits.append((position, fill, pnl, stop_hit))
        if not exits:
            return
        # A tick does not specify order between simultaneous deal closures. Do not fabricate $100/stop ordering.
        if any(stop for _, _, _, stop in exits) and any(not stop for _, _, _, stop in exits):
            before = self.daily.closed_profit
            after_targets = before + sum((self.daily_pnl(p, pnl) for p, _, pnl, stop in exits if not stop), Decimal(0))
            if not self.daily.profit_reached and before < 100 <= after_targets:
                self.execution_block = "TODO_STRATEGY_UNRESOLVED:simultaneous_close_order"
                self.emit("EXECUTION_UNRESOLVED", "DAY-02", reason=self.execution_block)
        tp1s = []
        for position, fill, pnl, stop_hit in exits:
            position.open = False
            setup = self.setups[position.setup_id]
            stopped = stop_hit
            if stop_hit and position.be_applied:
                policy = self.config.get("be_stop_counts_as_stop")
                if policy is None:
                    self.execution_block = "TODO_STRATEGY_UNRESOLVED:be_stop_counts_as_stop"
                    stopped = False
                elif not isinstance(policy, bool):
                    raise ValueError("be_stop_counts_as_stop must be boolean")
                else:
                    stopped = policy
            count_id = setup.id
            if position.reverse:
                count_policy = required(self.config, "breaker_daily_stop_policy")
                count_id = setup.id if count_policy == "same_setup" else setup.id + ":reverse"
            elif stopped:
                setup.stopped.add(position.bos_id)
            gross_pnl = pnl + position.costs_paid + number(self.config["commission_usd_per_lot_per_side"]) * LEG_LOTS
            self.daily.close(count_id, self.daily_pnl(position, pnl), stopped)
            self.total_closed_profit += pnl
            self.emit("PAPER_EXIT", "TP-01/SL-01/DAY-01", position_id=position.id, setup_id=setup.id,
                      exit_reason="BE_STOP" if position.be_applied and stop_hit else "SL" if stop_hit else "TP1" if position.leg == 1 else "TP2",
                      price=fill, pnl_usd=pnl, gross_pnl_usd=gross_pnl, reverse=position.reverse,
                      trading_day=self.daily.key, daily_profit_basis=self.config["daily_profit_basis"], daily_profit=self.daily.closed_profit,
                      profit_reached=self.daily.profit_reached, stopped_setups=len(self.daily.stopped_setups), halted=self.daily.halted)
            if not stop_hit and position.leg == 1:
                tp1s.append(position)
        for tp1 in tp1s:
            for remaining in self.positions:
                if remaining.open and remaining.setup_id == tp1.setup_id and remaining.bos_id == tp1.bos_id and remaining.reverse == tp1.reverse and remaining.leg == 2:
                    anchor = remaining.entry if self.config["be_entry_anchor"] == "filled" else next(b.entry for b in remaining.plan.entries if b.id == remaining.bos_id)
                    remaining.stop = breakeven(remaining.plan, anchor, self.config)
                    remaining.be_applied = True
                    self.emit("BE_MOVED", "BE-01", position_id=remaining.id, stop=remaining.stop)
        for setup in self.setups.values():
            self.arm_reverse(setup)

    def daily_pnl(self, position: Position, net: Decimal):
        if self.config["daily_profit_basis"] == "net":
            return net
        return net + position.costs_paid + number(self.config["commission_usd_per_lot_per_side"]) * LEG_LOTS

    def arm_reverse(self, setup: Setup):
        if setup.reverse_armed or setup.reverse_consumed:
            return
        if not (setup.planned_core_entry and setup.actual_core_fill and setup.stopped and
                setup.bos_broken and setup.ob_broken and setup.ifvg_confirmed):
            return
        if setup.plan and len(setup.plan.entries) > 1:
            self.blocked(setup.id, "TODO_STRATEGY_UNRESOLVED:breaker_dual_parent", "reverse")
            return
        policy = self.config.get("breaker_daily_stop_policy")
        if policy not in ("same_setup", "separate_setup"):
            self.blocked(setup.id, "TODO_STRATEGY_UNRESOLVED:breaker_daily_stop_policy", "reverse")
            return
        if any(p.open and p.setup_id == setup.id and not p.reverse for p in self.positions):
            return
        try:
            planned_core_entry = next(iter(setup.planned_core_entry.values()))
            reverse_plan("SELL" if setup.side == "BUY" else "BUY", planned_core_entry, self.config)
        except Unresolved as error:
            self.blocked(setup.id, str(error), "reverse")
            return
        setup.reverse_armed = True
        setup.reverse_armed_sequence = self.input_sequence
        self.emit("REVERSE_ARMED", "REV-01/REV-02", setup_id=setup.id,
                  original_entry=planned_core_entry, planned_core_entry=planned_core_entry,
                  actual_core_fill=next(iter(setup.actual_core_fill.values())),
                  automatic_ifvg_detection=False)

    def tick(self, tick: dict):
        bid, ask = number(tick["bid"]), number(tick["ask"])
        if bid <= 0 or ask < bid:
            raise ValueError("Invalid Bid/Ask tick")
        ordinal = tick.get("tick_index")
        if ordinal is not None and (not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1):
            raise ValueError("tick_index must be a positive integer")
        if self.last_tick:
            prior_time, _, prior_ordinal = self.last_tick[:3]
            if self.now == prior_time and (ordinal is None or prior_ordinal is None or ordinal <= prior_ordinal):
                raise ValueError("Equal-time ticks require explicitly increasing tick_index")
            if ordinal is not None and prior_ordinal is not None and ordinal <= prior_ordinal:
                raise ValueError("tick_index must be increasing")
        previous = self.last_tick
        self.last_tick = (self.now, tick, ordinal, self.input_sequence)
        self.close_positions(tick)
        for setup in self.setups.values():
            try:
                price = self.quote(tick, setup.side, observation=True)
                if ob_broken(setup.side, setup.ob, price) and not setup.ob_broken:
                    setup.ob_broken = True
                    self.emit("OB_BROKEN", "REV-01", setup_id=setup.id, observed=price, ob=setup.ob)
                full = price <= setup.fvg.low if setup.side == "BUY" else price >= setup.fvg.high
                partial = price < setup.fvg.high if setup.side == "BUY" else price > setup.fvg.low
                new_fill = "FULL" if full else "PARTIAL" if partial else setup.fill
                if setup.fill != "FULL" and new_fill != setup.fill:
                    setup.fill = new_fill
                    self.emit("FVG_FILL_STATE", "FVG-03", setup_id=setup.id, fill_state=new_fill)
                self.arm_reverse(setup)
                if setup.reverse_armed and not setup.reverse_consumed:
                    planned_core_entry = next(iter(setup.planned_core_entry.values()))
                    plan = reverse_plan("SELL" if setup.side == "BUY" else "BUY", planned_core_entry, self.config)
                    bos = plan.entries[0]
                    reverse_quote = self.quote(tick, plan.side)
                    if self.reverse_retested(bos, reverse_quote):
                        setup.reverse_consumed = True
                        self.open_entry(setup, bos, plan, tick, True)
                    elif (previous and setup.reverse_armed_sequence is not None and
                          previous[3] >= setup.reverse_armed_sequence):
                        old_reverse_quote = self.quote(previous[1], plan.side)
                        if self.reverse_crossed(bos, old_reverse_quote, reverse_quote):
                            setup.reverse_consumed = True
                            self.emit("EXECUTION_UNRESOLVED", "REV-02", setup_id=setup.id,
                                      reason="reverse_retest_crossed_without_observable_exact_quote",
                                      planned_core_entry=planned_core_entry,
                                      previous_executable_quote=old_reverse_quote,
                                      current_executable_quote=reverse_quote,
                                      first_retest_consumed=True)
                if not setup.plan:
                    continue
                for bos in setup.plan.entries:
                    if bos.id in self.consumed_bos:
                        continue
                    touch_price = self.quote(tick, setup.side)
                    if self.touched(bos, touch_price):
                        self.consumed_bos.add(bos.id)
                        self.emit("BOS_FIRST_TOUCH", "TOUCH-01", setup_id=setup.id, bos_id=bos.id, observed=touch_price)
                        self.open_entry(setup, bos, setup.plan, tick, False)
                    elif previous and previous[0] >= setup.available:
                        old_price = self.quote(previous[1], setup.side)
                        crossed = min(old_price, touch_price) < bos.zone.low - 5 * PIP and max(old_price, touch_price) > bos.zone.high + 5 * PIP
                        if crossed:
                            self.consumed_bos.add(bos.id)
                            self.blocked(setup.id, "TODO_STRATEGY_UNRESOLVED:quote_gap_crossed_bos")
            except Unresolved as error:
                self.blocked(setup.id, str(error))


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(event_path: Path, config_path: Path, output: Path):
    config = json.loads(config_path.read_text(encoding="utf-8"), parse_float=Decimal)
    engine = Engine(config)
    with event_path.open(encoding="utf-8") as stream:
        for index, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                engine.accept(json.loads(line, parse_float=Decimal))
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(f"Input line {index}: {error}") from error
    journal = "".join(json_line(e) for e in engine.events)
    package = Path(__file__).parent
    source = package.parent / "docs" / "sources" / "canonical-strategy.fa.md"
    manifest = {"spec_version": SPEC_VERSION, "mode": "paper", "model": "chronological_ticks_with_sourced_annotations",
                "config_sha256": digest(config_path), "input_sha256": digest(event_path), "spec_sha256": digest(source),
                "code_sha256": {p.name: digest(p) for p in sorted(package.glob("*.py"))},
                "journal_sha256": hashlib.sha256(journal.encode()).hexdigest(), "events": len(engine.events),
                "open_legs": sum(p.open for p in engine.positions), "closed_profit_usd": engine.total_closed_profit,
                "last_day_closed_profit_usd": engine.daily.closed_profit,
                "daily_results": [engine.daily_results[k] for k in sorted(engine.daily_results)] + ([engine.daily_result()] if engine.daily.key else []),
                "blocked": sorted({e["reason"] for e in engine.events if e["event"] == "ENTRY_BLOCKED"})}
    output.mkdir(parents=True, exist_ok=True)
    (output / "events.jsonl").write_text(journal, encoding="utf-8", newline="\n")
    (output / "manifest.json").write_text(json.dumps(encode(manifest), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest
