"""Source safety contracts for the locked native route; not MT5 transport evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / "mt5/Include/TraderLab"


class OperatorPathContracts(unittest.TestCase):
    def test_valid_restart_journal_retains_management_when_pair_reconciliation_fails(self):
        s = (HEADERS / "DemoGateway.mqh").read_text(encoding="utf-8")
        start = s[s.index("bool Start("):s.index("bool Reconcile()")]
        self.assertLess(start.index('"LEDGER_SCOPE_MISMATCH"'), start.index("bool proof=Reconcile()"))
        self.assertLess(start.index('"CORRUPT_LEDGER_FAIL_CLOSED"'), start.index("bool proof=Reconcile()"))
        self.assertIn("TLDemoStartupManagement(true,proof,halted)", start)
        self.assertIn('if(!proof) EmergencyStop("STARTUP_RECONCILIATION_FAILED:', start)
        self.assertIn("return management_ready", start)
        self.assertNotIn("return Reconcile()", start)
        self.assertIn("!halted && reconciled && Permissions()", s)
        lifecycle = (HEADERS / "CoreLifecycle.mqh").read_text(encoding="utf-8")
        self.assertIn("if(gateway.Halted()) halted=true", lifecycle)
        service = lifecycle[lifecycle.index("void Service()"):lifecycle.index("bool ObserveDeal")]
        self.assertIn("gateway.CanManage()", service)
        self.assertIn('gateway.CloseAllDemoPositions("core-persistent-emergency")', service)

    def test_actual_send_rechecks_quote_account_and_deadlines_after_flushed_intent(self):
        s = (HEADERS / "DemoGateway.mqh").read_text(encoding="utf-8")
        dispatch = s[s.index("bool Dispatch("):s.index("bool Quote(")]
        claim = dispatch.index("if(!Claim(intent))")
        guard = dispatch.index("TLDemoSendBoundary(boundary")
        send = dispatch.index("bool sent=OrderSend(")
        self.assertLess(claim, guard)
        self.assertLess(guard, send)
        self.assertIn("bool boundary_ok=Permissions()", dispatch[claim:guard])
        blocked = dispatch[guard:send]
        self.assertIn('intent.state="REJECTED"', blocked)
        self.assertIn("if(!Save(intent))", blocked)
        self.assertIn('return Fail("FINAL_SEND_BOUNDARY_CHANGED_NO_ORDER")', blocked)
        self.assertEqual(s.count("OrderSend(request,result)"), 1)
        self.assertIn("const bool TL_DEMO_DISPATCH_REVIEWED=false", s)

    def test_locked_trial_profile_uses_evidence_without_changing_strategy_or_magic(self):
        import json
        from decimal import Decimal
        profile = dict(line.split("=", 1) for line in
                       (ROOT / "mt5/activation/CoreDemo.trial.locked.set").read_text().splitlines())
        evidence = json.loads((ROOT / "configs/core-demo-measurements-20261013.json").read_text())
        self.assertEqual(profile["InpRequestCoreDemoExecution"], "false")
        self.assertNotIn("InpCoreMagic", profile)  # Preserve existing durable namespace.
        self.assertNotIn("InpLogFile", profile)  # Must be unique for every attach.
        self.assertEqual(Decimal(profile["InpCoreMaxSpreadPrice"]),
                         Decimal(evidence["live"]["spread_price"]["max"]))
        self.assertEqual(Decimal(profile["InpCoreMaxSlippagePoints"]),
                         max(map(Decimal, evidence["broker"]["matched_entry_fill_slippage_price"])))
        self.assertGreater(Decimal(profile["InpCorePairMaxMilliseconds"]),
                           2 * Decimal(evidence["broker"]["orders"]["open"]["max_ms"]))
        self.assertGreater(int(profile["InpNewsClosureLeadSeconds"]), 4 * 15 + 2)

    def test_panel_approves_detector_membership_and_never_submits_an_order(self):
        s = (HEADERS / "CoreController.mqh").read_text(encoding="utf-8")
        panel = s[s.index("void PanelEvent"):s.index("void PanelClose")]
        for token in ("PanelDraft", "consumption.FreezePackage", "packages.Append",
                      "OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY", '"automatic_discovery'):
            self.assertIn(token, panel)
        self.assertNotIn("book.Begin", panel)
        self.assertNotIn("OrderSend", panel)
        self.assertIn("FIRST_RETURN_CONSUMED_BEFORE_OPERATOR_APPROVAL", s)
        self.assertIn('if(bos[b].startup)', s)
        self.assertIn("consumption.Seen(ids[i])", s)
        self.assertIn('consumption.Stop("OPERATOR_EMERGENCY_STOP"', panel)
        self.assertIn('book.Emergency("RESTORED_OPERATOR_EMERGENCY_STOP")', s)

    def test_second_leg_has_a_bounded_execution_context_not_a_second_signal(self):
        s = (HEADERS / "DemoGateway.mqh").read_text(encoding="utf-8")
        self.assertIn("leg==1 && !TLDemoReturnQuote", s)
        self.assertIn("leg==2 && !pair_first_filled", s)
        self.assertIn("PAIR_FVG_NO_LONGER_UNFILLED", s)
        self.assertIn("vetted_leg==2 && !PairHistory", s)
        self.assertIn("CopyTicksRange(symbol,ticks,COPY_TICKS_ALL", s)
        self.assertNotIn("TLSameTick", s)
        self.assertIn("ACTUAL_FILL_EXCEEDS_REVIEWED_SLIPPAGE", s)
        self.assertIn("PAIR_BUDGET_EXPIRED_AFTER_BROKER_RESPONSE", s)
        self.assertIn("TLDemoIntentDealEntry(intents[i].opportunity", s)
        self.assertIn("HistoryDealGetString(ticket,DEAL_SYMBOL)==intents[i].symbol", s)
        self.assertIn("EmergencyStop(\"INCOMPLETE_CANONICAL_PAIR\")", s)
        self.assertIn("CloseAllDemoPositions(\"failed-pair:", s)

    def test_emergency_management_is_independent_of_permission_to_open(self):
        s = (HEADERS / "CoreLifecycle.mqh").read_text(encoding="utf-8")
        service = s[s.index("void Service()"):s.index("bool ObserveDeal")]
        self.assertIn("gateway.CanManage()", service)
        self.assertNotIn("gateway.CanDispatch()", service)
        self.assertIn('gateway.CloseAllDemoPositions("core-persistent-emergency")', service)
        self.assertIn("calendar.Load(calendar_file)", service)
        self.assertLess(s.index("daily.Close(trades[i].setup"), s.index('if(unknown_be_stop)'))

    def test_deal_callbacks_reconcile_history_before_be(self):
        c = (HEADERS / "CoreController.mqh").read_text(encoding="utf-8")
        handler = c[c.index("void Transaction"):c.index("void Summary")]
        self.assertIn("book.DealsChanged()", handler)
        self.assertNotIn("book.ObserveDeal(trans.deal)", handler)
        s = (HEADERS / "CoreLifecycle.mqh").read_text(encoding="utf-8")
        reconcile = s[s.index("bool ReconcileDeals"):s.index("bool MoveBE")]
        self.assertLess(reconcile.index("tickets[i]=HistoryDealGetTicket"), reconcile.index("ObserveDeal(tickets[i])"))
        self.assertLess(reconcile.index("restoring=true"), reconcile.index("ObserveDeal(tickets[i])"))
        self.assertIn("if(!restoring && !MoveBE", s)
        self.assertIn("if(is_be) trades[i].be_sent=true", s)

    def test_calendar_rows_and_execution_deadlines_are_explicit(self):
        s = (HEADERS / "CoreLifecycle.mqh").read_text(encoding="utf-8")
        for token in ("TLCoreEpoch", "StringSplit(line,'|',fields)!=5", "end==0",
                      "events[i].scheduled-900", "days[i].end", "coverage_end", "calendar.EntryUntil(now)"):
            self.assertIn(token, s)
        s = (ROOT / "mt5/TraderLab.mq5").read_text(encoding="utf-8")
        for token in ("InpCorePairMaxMilliseconds=0", "InpCoreMaxSpreadPrice=0",
                      "InpCoreMaxSlippagePoints=-1", "InpRequestCoreDemoExecution=false"):
            self.assertIn(token, s)


if __name__ == "__main__":
    unittest.main()
