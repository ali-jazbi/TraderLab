"""Canonical-example software checks; no invented historical trading opportunity."""
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
import tempfile
import unittest
from traderlab.core_packages import Package, resolve, read_packages, first_return_issue
from traderlab.detection import instant

class OperatorPackagesChecks(unittest.TestCase):
    def example(self):
        p=Package.read('PACKAGE|Example|Operator|Canonical16and51|1000|F|F:C3|B1;B2')
        bos={key:{'side':'BUY','level':price,'qualified_at':datetime.fromtimestamp(900,timezone.utc),
                  'candidate_at':datetime.fromtimestamp(800,timezone.utc)}
             for key,price in (('B1','4146'),('B2','4143'))}
        gaps={'F':{'side':'BUY','available_at':datetime.fromtimestamp(950,timezone.utc),
                   'fill_state':'UNFILLED','zone':['4142','4147'],
                   'candidate_at':datetime.fromtimestamp(920,timezone.utc),
                   'c2_ohlc':{'open':'4140','high':'4150','low':'4139','close':'4148'}}}
        return p,bos,gaps,datetime.fromtimestamp(1001,timezone.utc)
    def test_complete_operator_membership_produces_original_dual_plan(self):
        p,b,g,t=self.example();r=resolve(p,b,g,t);plan=r['plan']
        self.assertFalse(r['automatic_discovery']);self.assertIsNone(r['execution_block'])
        self.assertEqual((plan.reference,plan.stop,plan.target1,plan.target2),(D('4146.5'),D('4140'),D('4152.5'),D('4156.5')))
        self.assertEqual([x.id for x in plan.entries],['B1','B2'])
    def test_no_same_frame_inference_or_price_input_is_used(self):
        p,b,g,t=self.example();b['B1']['timeframe']='M1';b['B2']['timeframe']='M15';g['F']['timeframe']='H4'
        self.assertEqual(len(resolve(p,b,g,t)['plan'].entries),2)
        with self.assertRaises(ValueError):Package.read('PACKAGE|X|Op|Source|1000|F|F:C3|B1|4146')
    def test_unobserved_wrong_ob_late_qualification_and_startup_fail_closed(self):
        p,b,g,t=self.example()
        for mutate in ('missing','startup','late','outside'):
            p,b,g,t=self.example()
            if mutate=='missing': del b['B1']
            elif mutate=='startup':b['B1']['startup_history']=True
            elif mutate=='late':b['B1']['qualified_at']=datetime.fromtimestamp(1001,timezone.utc)
            else:b['B1']['level']='4150'
            with self.assertRaises(ValueError):resolve(p,b,g,t)
        p,b,g,t=self.example()
        with self.assertRaises(ValueError):resolve(Package.read('PACKAGE|X|Op|Src|1000|F|F:C1|B1;B2'),b,g,t)
    def test_partial_full_future_approval_and_single_be_are_not_bypassed(self):
        p,b,g,t=self.example()
        for fill in ('PARTIAL','FULL','UNKNOWN'):
            g['F']['fill_state']=fill
            with self.assertRaises(ValueError):resolve(p,b,g,t)
        p,b,g,t=self.example()
        with self.assertRaises(ValueError):resolve(p,b,g,datetime.fromtimestamp(1000.999,timezone.utc))
        p=Package.read('PACKAGE|X|Op|Src|1000|F|F:C3|B1')
        self.assertEqual(resolve(p,b,g,t)['execution_block'],'TODO_STRATEGY_UNRESOLVED:single_be_anchor')
    def test_membership_scope_duplicate_epoch_strict_and_no_implicit_approval(self):
        for line in ('PACKAGE|X|Op|Src|1000x|F|F:C3|B1','PACKAGE|X|Op|Src|1000|F|F:C3|B1;B1'):
            with self.assertRaises(ValueError):Package.read(line)
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/'packages.csv';f.write_text('CORE_OPERATOR_PACKAGES_V1|XAUUSD_o\n',encoding='utf-8')
            self.assertEqual(read_packages(f,'XAUUSD_o'),[])
            with self.assertRaises(ValueError):read_packages(f,'XAUUSD')
            f.write_text('CORE_OPERATOR_PACKAGES_V1|XAUUSD_o\nPACKAGE|X|Op|Src|1000|F|F:C3|B1\nPACKAGE|Y|Op|Src|1000|F|F:C3|B1\n',encoding='utf-8')
            with self.assertRaises(ValueError):read_packages(f,'XAUUSD_o')
    def test_rejected_real_observation_can_never_be_rearmed_by_review(self):
        p,b,g,t=self.example();b['B1']['first_return_at']=datetime.fromtimestamp(950,timezone.utc)
        with self.assertRaisesRegex(ValueError,'consumed before operator'):resolve(p,b,g,t)
        c={'startup_history':False,'fill_state':'UNFILLED','first_return_consumed':True,
           'exact_quote':True,'break_at':'2026-10-07T03:25:50.736Z',
           'first_return_at':'2026-10-07T03:28:51.731Z','fvg_available_at':'2026-10-07T03:36:00.045Z'}
        self.assertEqual(first_return_issue(c),'FIRST_RETURN_BEFORE_CONFIRMED_AVAILABILITY')
        c['first_return_at']='2026-10-07T03:37:00.123Z'
        self.assertIsNone(first_return_issue(c))
        c['exact_quote']=False;self.assertEqual(first_return_issue(c),'MISSED_EXACT_SIGNAL_QUOTE_NO_FILL')

if __name__=='__main__':unittest.main()
