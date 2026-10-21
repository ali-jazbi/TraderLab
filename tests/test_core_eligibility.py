"""Independent numerical §55 fixtures; never a reconstruction of the owner image."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from traderlab.core_eligibility import core_eligibility
from traderlab.detection import Bar, Detector, TIMEFRAMES
import test_experimental_auto as fixture
from test_experimental_auto import utc


class CoreEligibilityChecks(unittest.TestCase):
    def example(self, body='8'):
        t=datetime(2026,10,1,tzinfo=timezone.utc)
        gap=dict(side='BUY',candidate_at=t,available_at=t+timedelta(minutes=11),
                 zone=[D('4146'),D('4150')],
                 c2_ohlc=dict(open=D('4146'),close=D('4146')+D(body),high=D('4160'),low=D('4130')))
        bos=[dict(id='B',side='BUY',candidate_at=t-timedelta(minutes=3),
                  qualified_at=t,level=D('4148'))]
        return gap,bos

    def test_79_9_pips_rejected(self):
        g,b=self.example('7.99');self.assertEqual(core_eligibility(g,b).reasons,('C2_BODY_BELOW_80_PIPS',))

    def test_exact_80_inclusive(self):
        g,b=self.example();self.assertTrue(core_eligibility(g,b).eligible)

    def test_100_pips(self):
        g,b=self.example('10');self.assertTrue(core_eligibility(g,b).eligible)

    def test_no_prior_bos(self):
        g,b=self.example();self.assertEqual(core_eligibility(g,[]).reasons,('NO_VALID_PREFVG_BOS',))

    def test_valid_prior_bos_inside(self):
        g,b=self.example();r=core_eligibility(g,b);self.assertEqual(r.witness_ids,('B',));self.assertTrue(r.eligible)

    def test_after_and_same_c2_bos_do_not_satisfy(self):
        g,b=self.example()
        for delta in (0,1):
            b[0]['candidate_at']=g['candidate_at']+timedelta(seconds=delta)
            self.assertIn('NO_VALID_PREFVG_BOS',core_eligibility(g,b).reasons)

    def test_large_wicks_small_body(self):
        g,b=self.example('1');self.assertIn('C2_BODY_BELOW_80_PIPS',core_eligibility(g,b).reasons)

    def test_late_or_unqualified_bos_and_outside_are_distinct(self):
        g,b=self.example();b[0]['qualified_at']=g['available_at']+timedelta(milliseconds=1)
        self.assertEqual(core_eligibility(g,b).reasons,('NO_VALID_PREFVG_BOS',))
        b[0]['qualified_at']=None;self.assertFalse(core_eligibility(g,b).eligible)
        g,b=self.example();b[0]['level']=D('4150.01')
        self.assertEqual(core_eligibility(g,b).reasons,('BOS_OUTSIDE_FVG',))

    def test_sell_mirror_boundaries_and_no_invented_lookback(self):
        g,b=self.example('-8');g['side']=b[0]['side']='SELL'
        b[0]['candidate_at']-=timedelta(days=300)
        for level in g['zone']:
            b[0]['level']=level;self.assertTrue(core_eligibility(g,b).eligible)

    def test_permission_does_not_mutate_detection_and_missing_ohlc_blocks(self):
        g,b=self.example('1');before=deepcopy((g,b));core_eligibility(g,b);self.assertEqual((g,b),before)
        del g['c2_ohlc'];self.assertIn('C2_OHLC_UNAVAILABLE',core_eligibility(g,b).reasons)

    def test_all_timeframes_wait_ten_closes_and_keep_weak_fvg(self):
        for tf,seconds in TIMEFRAMES.items():
            for body in ('4','8'):
                d=Detector();start=datetime(2026,10,1,tzinfo=timezone.utc);observations=[]
                for i in range(21):
                    o,c,lo,hi=(D('100'),D('100.1'),D('99.9'),D('100.2')) if i<10 else (D('110'),D('110.1'),D('109.9'),D('110.2'))
                    if i==10:o,c,lo,hi=D('100'),D('100')+D(body),D('99.9'),D('111')
                    opened=start+timedelta(seconds=i*seconds)
                    out=d.accept(Bar(tf,opened,opened+timedelta(seconds=seconds),o,hi,lo,c))
                    if i<20:self.assertFalse(any(e['event']=='FVG_CONFIRMED' for e in out))
                    observations+=out
                gaps=[e for e in observations if e['event']=='FVG_CONFIRMED']
                self.assertEqual(len(gaps),1);self.assertEqual(gaps[0]['c2_ohlc']['close']-gaps[0]['c2_ohlc']['open'],D(body))

    def test_gate_runs_before_package_and_does_not_prune_members(self):
        e=fixture.ExperimentalChecks().engine();g=e.automatic.gaps['F'];g['c2_ohlc']['close']=D('4147.99')
        e.finalize(utc(1000));self.assertEqual(e.accepted_groups,0)
        self.assertEqual(e.group_rejections['C2_BODY_BELOW_80_PIPS'],1)
        self.assertEqual(len(e.retests.histories),2);self.assertEqual(len(e.automatic.gaps),1)
        e=fixture.ExperimentalChecks().engine();old=list(e.retests.histories)[1];h=e.retests.histories.pop(old);h.bar.opened=utc(950)
        e.retests.histories[e.retests.identity(h.bar.timeframe,h.side,h.bar.opened)]=h
        e.finalize(utc(1000));self.assertEqual(e.accepted_groups,1)
        self.assertEqual(len(next(iter(e.setups.values())).plan.entries),2)

    def test_owner_clarification_qualification_may_follow_c2(self):
        g,b=self.example();b[0]['qualified_at']=g['candidate_at']+timedelta(seconds=1)
        self.assertTrue(core_eligibility(g,b).eligible)

    def test_executed_native_vectors_match_python_including_binary_boundaries(self):
        report=Path(__file__).resolve().parents[1]/'docs/reports/body80-20261021/native-checks.json'
        native=json.loads(report.read_text())
        self.assertEqual((native['checks'],native['failures']),(219,0))
        for row in native['cases']:
            g,b=self.example();name=row['case']
            if name=='79.9':g['c2_ohlc']['close']=D('4153.99')
            elif name=='100':g['c2_ohlc']['close']=D('4156')
            elif name=='no_bos':b=[]
            elif name=='after_c2':b[0]['candidate_at']=g['candidate_at']+timedelta(seconds=1)
            elif name=='same_c2':b[0]['candidate_at']=g['candidate_at']
            elif name=='small_body_large_wicks':g['c2_ohlc']['close']=D('4147')
            elif name=='outside':b[0]['level']=D('4150.01')
            elif name=='lower_edge':b[0]['level']=D('4146')
            elif name=='upper_edge':b[0]['level']=D('4150')
            elif name=='unqualified':b[0]['qualified_at']=None
            elif name=='future_qualification':b[0]['qualified_at']=g['available_at']+timedelta(milliseconds=1)
            elif name=='qualification_after_c2':b[0]['qualified_at']=g['candidate_at']+timedelta(milliseconds=1)
            elif name.startswith('binary_'):
                _,side,cents=name.split('_');n=D(cents)/100
                if side=='buy':g['c2_ohlc'].update(open=D('4092')+n,close=D('4100')+n)
                else:
                    g['side']=b[0]['side']='SELL'
                    g['c2_ohlc'].update(open=D('4100')+n,close=D('4092')+n)
            elif name.startswith('one_decimal_unit_'):
                g['c2_ohlc'].update(open=D('4092.03'),close=D('4100.02999999') if 'below' in name else D('4100.03000001'))
            elif name in ('sell_no_lookback','decimal_exact_80'):
                g['side']=b[0]['side']='SELL';b[0]['candidate_at']-=timedelta(days=300)
                g['c2_ohlc']['close']=D('4138')
                if name=='decimal_exact_80':g['c2_ohlc'].update(open=D('4146.13'),close=D('4138.13'))
            elif name=='missing_c2':del g['c2_ohlc']
            result=core_eligibility(g,b)
            with self.subTest(case=name):
                self.assertEqual(result.eligible,row['eligible'])
                self.assertEqual(list(result.reasons),row['reasons'])
                if result.body_pips is not None:self.assertEqual(result.body_pips,D(str(row['body_pips'])))


if __name__=='__main__':unittest.main()
