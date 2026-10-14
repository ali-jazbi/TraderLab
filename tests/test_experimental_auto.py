"""New experimental policy cases only. Fixtures are not historical trades."""
from datetime import datetime, timezone
from decimal import Decimal as D
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from traderlab.experimental import ExperimentalEngine, POLICIES
from traderlab.retests import FirstReturn
from tools.prepare_auto_tester import prepare

ROOT=Path(__file__).resolve().parents[1]
def utc(n): return datetime.fromtimestamp(n,timezone.utc)

class ExperimentalChecks(unittest.TestCase):
    def engine(self,policy=POLICIES[0],other_frame=False):
        c=json.loads((ROOT/"configs/fixture.example.json").read_text())
        c.update(backtest_only=True,broker_execution_enabled=False,experimental_grouping=policy,
                 config_status="EXPERIMENTAL_TEST_ONLY",buy_touch_quote="bid",sell_touch_quote="bid")
        e=ExperimentalEngine(c);e.now=utc(1000);e.startup_time=utc(800)
        for i,level in enumerate(("4146","4143")):
            tf="M5" if i==1 and other_frame else "M1"
            bar=SimpleNamespace(timeframe=tf,opened=utc(600+i*60))
            h=SimpleNamespace(bar=bar,side="BUY",level=D(level),qualified_at=utc(900),
                 lanes={"bid":{"returns":{"bid":FirstReturn("BUY",D(level)+D(".5"))}}})
            e.retests.histories[e.retests.identity(tf,"BUY",bar.opened)]=h
        e.automatic.gaps["F"]={"id":"F","side":"BUY","timeframe":"M1","available_at":utc(1000),
                               "zone":(D("4142"),D("4147")),"ob":(D("4147"),D("4150")),"fill_state":"UNFILLED"}
        return e

    def test_only_explicit_paper_backtests_can_use_grouping(self):
        c=json.loads((ROOT/"configs/fixture.example.json").read_text())
        with self.assertRaises(ValueError): ExperimentalEngine(c)
        c.update(backtest_only=True,experimental_grouping="arbitrary")
        with self.assertRaises(ValueError): ExperimentalEngine(c)
        c.update(experimental_grouping=POLICIES[0],broker_execution_enabled=True)
        with self.assertRaises(ValueError): ExperimentalEngine(c)

    def test_frozen_membership_creates_original_dual_plan_no_manual_approval(self):
        e=self.engine();e.finalize(utc(1000));e.finalize(utc(1001))
        self.assertEqual(e.accepted_groups,1)
        p=next(iter(e.setups.values())).plan
        self.assertEqual((p.stop,p.reference,p.target1,p.target2),(D("4140"),D("4146.5"),D("4152.5"),D("4156.5")))
        self.assertEqual(len(e.positions),0)
        self.assertEqual(sum(x["event"]=="EXPERIMENTAL_GROUP_FINALIZED" for x in e.events),1)

    def test_same_and_cross_frame_hypotheses_are_distinct_and_labeled(self):
        e=self.engine(other_frame=True);e.finalize(utc(1000))
        self.assertEqual(e.accepted_groups,0)
        self.assertEqual(e.group_rejections["SINGLE_BE_ANCHOR_UNRESOLVED"],1)
        e=self.engine(POLICIES[1],True);e.finalize(utc(1000))
        self.assertEqual(e.accepted_groups,1)
        self.assertFalse(e.events[-1]["demo_execution_approved"])

    def test_partial_full_consumed_and_future_inputs_never_become_trades(self):
        for state in ("PARTIAL","FULL"):
            e=self.engine();e.automatic.gaps["F"]["fill_state"]=state;e.finalize(utc(1000))
            self.assertEqual(e.accepted_groups,0)
        e=self.engine();h=next(iter(e.retests.histories.values()))
        h.lanes["bid"]["returns"]["bid"].result={"consumed":True,"first_return_at":utc(950)}
        e.finalize(utc(1000))
        self.assertEqual(e.group_rejections["FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION"],1)
        self.assertIsNotNone(h.lanes["bid"]["returns"]["bid"].result)
        e=self.engine();e.automatic.gaps["F"]["available_at"]=utc(1001)
        with self.assertRaises(ValueError):e.finalize(utc(1000))

    def test_annotations_are_forbidden_even_with_backtest_opt_in(self):
        e=self.engine()
        with self.assertRaises(ValueError):e.accept({"kind":"setup"})

    def test_native_transport_and_calendar_are_isolated_from_demo(self):
        ea=(ROOT/"mt5/TraderLab.mq5").read_text()
        self.assertIn("(InpExperimentalAutoCoreTester>0 && !MQLInfoInteger(MQL_TESTER))",ea)
        self.assertIn('#property tester_file "TraderLab-auto-tester-calendar.csv"',ea)
        gateway=(ROOT/"mt5/Include/TraderLab/DemoGateway.mqh").read_text()
        self.assertIn("if(experimental_tester && !MQLInfoInteger(MQL_TESTER))",gateway)
        self.assertIn("const bool TL_DEMO_DISPATCH_REVIEWED=false",gateway)
        self.assertEqual(gateway.count("OrderSend(request,result)"),1)
        self.assertIn('tester_mode?0:FILE_COMMON',gateway)
        cal=(ROOT/"mt5/Include/TraderLab/CoreLifecycle.mqh").read_text()
        self.assertIn('error="EXPERIMENTAL_CALENDAR_TESTER_ONLY"',cal)
        self.assertIn('return Ready() && gateway.ExecutionLimitsReady() && gateway.CanDispatch()',cal)

    def test_tester_calendar_cannot_claim_unreviewed_history_or_escape_output(self):
        from tools.prepare_auto_tester import prepare
        from datetime import date
        with self.assertRaises(ValueError):
            prepare(ROOT,date(2026,8,1),date(2026,10,14),1,'unsafe')
        with self.assertRaises(ValueError):
            prepare(ROOT,date(2026,9,21),date(2026,10,14),1,'../unsafe')

if __name__=="__main__":unittest.main()
