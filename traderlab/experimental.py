"""TESTER/paper only. Frozen membership hypotheses are not owner-confirmed strategy."""
from collections import Counter
from .replay import Engine, Setup
from .strategy import Bos, Zone, core_plan, entry_reference, Unresolved, number, PIP
from .detection import instant

POLICIES = ("same_frame_at_confirmed_availability", "all_frames_at_confirmed_availability")

class ExperimentalEngine(Engine):
    def __init__(self, config):
        if config.get("backtest_only") is not True or config.get("broker_execution_enabled") is not False:
            raise ValueError("EXPERIMENTAL grouping is backtest-only; broker execution forbidden")
        self.policy = config.get("experimental_grouping")
        if self.policy not in POLICIES:
            raise ValueError("Explicit experimental grouping policy required")
        super().__init__(config)
        self.finalized = set()
        self.group_rejections = Counter()
        self.startup_time = None
        self.accepted_groups = 0

    def accept(self, event):
        if event["kind"] not in ("tick", "bar"):
            raise ValueError("Experimental discovery accepts genuine market records only, no annotations")
        if event["kind"] == "tick":
            self.startup_time = self.startup_time or instant(event["time"])
            self.finalize(instant(event["time"]))
        super().accept(event)

    def finalize(self, now):
        if len(self.finalized) == len(self.automatic.gaps):
            return
        for key,g in self.automatic.gaps.items():
            if key in self.finalized:
                continue
            self.finalized.add(key)
            if g["available_at"] > now:
                raise ValueError("Experimental group cannot use a future confirmed FVG")
            histories = [h for h in self.retests.histories.values()
                         if h.side == g["side"] and h.qualified_at is not None and h.qualified_at <= now
                         and g["zone"][0] <= h.level <= g["zone"][1]
                         and (self.policy == POLICIES[1] or h.bar.timeframe == g["timeframe"])]
            members = [Bos(self.retests.identity(h.bar.timeframe,h.side,h.bar.opened),
                           entry_reference(h.side,h.level),Zone(h.level,h.level),h.level) for h in histories]
            reason = None
            plan = None
            if not members: reason = "NO_QUALIFIED_CONTAINED_BOS_AT_CONFIRMATION"
            elif g["fill_state"] != "UNFILLED": reason = "PARTIAL_NOT_APPROVED" if g["fill_state"] == "PARTIAL" else "FULL_OR_UNKNOWN_FVG_INVALID"
            elif g["zone"][1]-g["zone"][0] < 20*PIP: reason = "FVG_BELOW_20_PIPS"
            elif len({b.level for b in members}) != len(members): reason = "AMBIGUOUS_EQUAL_BOS_LEVELS"
            else:
                try:
                    plan = core_plan(g["side"],members,self.config)
                    if len(plan.entries) == 1: reason = "SINGLE_BE_ANCHOR_UNRESOLVED"
                    else:
                        for b in plan.entries:
                            h = self.retests.histories[b.id]
                            if h.qualified_at <= self.startup_time: reason = "STARTUP_HISTORY_NOT_EXECUTION_PROOF"
                            elif h.lanes["bid"]["returns"]["bid"].result: reason = "FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION"
                except Unresolved as error: reason = str(error)
            details = {"fvg_id":key,"members":[b.id for b in members],"policy":self.policy,
                       "accepted":reason is None,"reason":reason,"demo_execution_approved":False}
            self.emit("EXPERIMENTAL_GROUP_FINALIZED","EXPERIMENTAL_NOT_OWNER_CONFIRMED",**details)
            if reason:
                self.group_rejections[reason] += 1
                continue
            setup = Setup("EXPERIMENTAL:"+key,g["side"],members,Zone(*g["zone"]),Zone(*g["ob"]),
                          "EXPERIMENTAL_NOT_OWNER_CONFIRMED",now,g["fill_state"],plan=plan)
            self.setups[setup.id] = setup
            self.accepted_groups += 1
            for b in plan.entries:
                self.core_returns[b.id] = self.retests.histories[b.id].lanes["bid"]["returns"]["bid"]
                self.core_available_order[b.id] = self.input_sequence + 1

    def before_core_entries(self, tick):
        # Match native: consumption cannot select the first array member of ambiguous FVGs.
        for key,ret in self.core_returns.items():
            r = ret.result
            if not r or r["first_return_order"] != self.input_sequence:
                continue
            matches = [s for s in self.setups.values() if s.fill == "UNFILLED" and s.plan
                       and (number(tick["bid"])>=s.fvg.high if s.side=="BUY" else number(tick["bid"])<=s.fvg.low)
                       and any(b.id == key for b in s.plan.entries)]
            if len(matches)>1:
                self.consumed_bos.add(key)
                self.emit("EXPERIMENTAL_FIRST_RETURN_BLOCKED","EXPERIMENTAL_NOT_OWNER_CONFIRMED",
                          bos_id=key,reason="AMBIGUOUS_MULTIPLE_FVG_PACKAGES_NO_ARBITRARY_SELECTION")

    def open_entry(self, setup, bos, plan, tick, reverse):
        if reverse:
            raise ValueError("Reverse remains disabled")
        if number(tick["ask"])-number(tick["bid"]) > number(self.config["max_spread_price"]):
            self.blocked(setup.id,"PAIR_QUOTE_TIME_SPREAD_OR_SLIPPAGE_GUARD")
            return
        super().open_entry(setup,bos,plan,tick,False)
