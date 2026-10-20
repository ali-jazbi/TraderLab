"""Owner labels + immutable market facts; conflicts are evidence, not overrides."""
from dataclasses import replace
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from traderlab.detection import Bar, Detector, has_bos_wick, fvg
from traderlab.retests import HistoricalRetests
from traderlab.strategy import Bos, Zone, select_bos, entry_reference, core_plan
from tools.audit_owner_wick import project_groups, inspect
from test_strategy import bar_event
import tempfile

ROOT = Path(__file__).resolve().parents[1]


class OwnerReferenceCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT/'tests/fixtures/owner-reference-cases.json').read_text(encoding='utf-8'))

    def test_all_owner_bos_labels_remain_traceable_and_conflicts_are_not_fudged(self):
        conflicts = []
        for case in self.fixture['cases']:
            if case['kind'] != 'bos':
                continue
            with self.subTest(case=case['id']):
                bar = Bar.read(case['bar'])
                actual = has_bos_wick(bar, case['side'], case['tick_size'])
                self.assertEqual(actual, case['rule_expected'])
                if case['alignment'] == 'MATCHED':
                    self.assertEqual(actual, case['owner_expected'])
                else:
                    self.assertEqual(case['alignment'], 'OHLC_LABEL_CONFLICT')
                    self.assertNotEqual(actual, case['owner_expected'])
                    conflicts.append(case['id'])
        self.assertEqual(conflicts, ['owner-oct15-bos1'])

    def test_real_negative_label_has_five_broker_ticks_not_a_zero_shadow(self):
        case = self.fixture['cases'][0]; b = Bar.read(case['bar'])
        self.assertFalse(case['owner_expected'])
        self.assertEqual((b.high-max(b.open,b.close))/D(case['tick_size']), D(5))
        self.assertTrue(has_bos_wick(b,'BUY',case['tick_size']))
        ticks = [r for r in self.fixture['tick_ohlc_evidence']
                 if r['server_time'].startswith('2026-10-15T04:57:')]
        self.assertEqual(D(ticks[0]['bid']),b.open)
        self.assertEqual(max(D(t['bid']) for t in ticks),b.high)
        self.assertEqual(min(D(t['bid']) for t in ticks),b.low)
        self.assertEqual(D(ticks[-1]['bid']),b.close)

    def test_all_fvg_reference_cases_are_discovered_from_data(self):
        for case in self.fixture['cases']:
            if case['kind']!='fvg': continue
            with self.subTest(case=case['id']):
                result=fvg(*(Bar.read(c) for c in case['candles']))
                self.assertEqual(result is not None,case['owner_expected'])
                if result:
                    self.assertEqual([result[1].low,result[1].high],[D(x) for x in case['zone']])

    def test_native_tracker_and_both_detectors_share_broker_grid_predicate(self):
        rules=(ROOT/'mt5/Include/TraderLab/Rules.mqh').read_text()
        native=(ROOT/'mt5/Include/TraderLab/Detection.mqh').read_text()
        tracker=(ROOT/'mt5/Include/TraderLab/Retests.mqh').read_text()
        stream=(ROOT/'mt5/Include/TraderLab/NativeRetestStream.mqh').read_text()
        self.assertIn('MathRound(wick/step)',rules)
        self.assertIn('MathMax(bar.open,bar.close)',rules)
        self.assertIn('MathMin(bar.open,bar.close)',rules)
        self.assertIn('TLHasBosWick(bar,side,price_step)',native)
        self.assertIn('TLHasBosWick(bar,history[n+s].side,price_step)',tracker)
        self.assertIn('SYMBOL_TRADE_TICK_SIZE',native)
        self.assertIn('SYMBOL_TRADE_TICK_SIZE',stream)

    def test_directional_shadow_and_broker_grid_no_arbitrary_minimum(self):
        b = Bar.read(bar_event(0,'100','100','90','95'))
        self.assertFalse(has_bos_wick(b,'BUY','.01'))
        self.assertTrue(has_bos_wick(replace(b,high=D('100.01')),'BUY','.01'))
        self.assertFalse(has_bos_wick(replace(b,high=D('100.000000001')),'BUY','.01'))
        self.assertTrue(has_bos_wick(replace(b,high=D('100.000000001')),'BUY'))
        b = replace(b,open=D('90'),close=D('95'))
        self.assertFalse(has_bos_wick(b,'SELL','.01'))
        self.assertTrue(has_bos_wick(replace(b,low=D('89.99')),'SELL','.01'))
        self.assertFalse(has_bos_wick(replace(b,low=D('89.999999999')),'SELL','.01'))
        with self.assertRaises(ValueError): has_bos_wick(b,'BUY',0)

    def test_no_shadow_seed_never_qualifies_or_breaks_in_either_python_path(self):
        d=Detector('.01'); h=HistoricalRetests('bid','.01')
        bars=[Bar.read(bar_event(i,*v)) for i,v in enumerate(
            [('100','100','90','95'),('92','99','88','89'),('96','101','95','100')])]
        observed=[]
        for b in bars:
            events=d.accept(b);observed.extend(events);h.accept_bar(b,events)
        key=h.identity('M1','BUY',bars[0].opened)
        self.assertIsNone(h.histories[key].qualified_at)
        self.assertEqual(h.histories[key].lanes['bid']['reason'],'directional_wick_missing')
        self.assertNotIn(key,h.active)
        own=[e for e in observed if e.get('candidate_at')==bars[0].opened and e.get('side')=='BUY']
        self.assertEqual([e['event'] for e in own],['BOS_REJECTED'])
        self.assertEqual(own[0]['reason'],'directional_wick_missing')

    def test_shadow_does_not_replace_close_before_break_qualification(self):
        d=Detector('.01'); b=Bar.read(bar_event(0,'95','100','90','96'));d.accept(b)
        events=d.accept(Bar.read(bar_event(1,'96','101','95','100')))
        rejection=next(e for e in events if e.get('candidate_at')==b.opened and e.get('side')=='BUY')
        self.assertFalse(rejection['qualified_before_break'])
        self.assertTrue(any(e.get('reason')=='break_before_qualification' for e in events))

    def test_oct15_both_observed_wicks_and_qualification_remain_fvg_unchanged(self):
        d=Detector('.01');events=[]
        for row in self.fixture['closed_m1_window']: events.extend(d.accept(Bar.read(row)))
        for case in self.fixture['cases'][:2]:
            b=Bar.read(case['bar'])
            own=[e for e in events if e.get('candidate_at')==b.opened and e.get('side')=='BUY']
            self.assertTrue(any(e['event']=='BOS_CANDIDATE_QUALIFIED' for e in own))
            self.assertTrue(any(e['event']=='BOS_CONFIRMED' for e in own))
        f=self.fixture['cases'][2]
        target=Bar.read(f['candles'][1]).opened
        gap=next(e for e in events if e['event']=='FVG_CONFIRMED' and e['candidate_at']==target)
        self.assertEqual(gap['zone'],[D(x) for x in f['zone']])
        self.assertEqual(gap['available_at'].isoformat(),'2026-10-15T02:22:00.094000+00:00')
        ob=next(e for e in events if e['event']=='OB_CONFIRMED' and e['candidate_at']==target)
        self.assertEqual(ob['zone'],[D(x) for x in f['ob_canonical']])
        c1=Bar.read(f['candles'][0])
        self.assertEqual((c1.low,c1.high),(D('4138.43'),D('4140.30')))
        self.assertEqual(f['owner_sl_approx'],'4136.5')  # feedback only, not a risk override
        members=[]
        for case in self.fixture['cases'][:2]:
            b=Bar.read(case['bar'])
            if has_bos_wick(b,'BUY',case['tick_size']):
                members.append(Bos(case['id'],entry_reference('BUY',b.high),Zone(b.high,b.high),b.high))
        plan=core_plan('BUY',members,{})
        self.assertEqual([b.entry for b in plan.entries],[D('4143.76'),D('4141.63')])
        self.assertEqual((plan.stop,plan.target1,plan.target2),(D('4138.13'),D('4149.76'),D('4153.76')))

    def test_extremes_and_entry_count_recompute_from_valid_members(self):
        # Explicit synthetic structure, not a fabricated historical trade.
        bars=[Bar.read(bar_event(i,*v)) for i,v in enumerate(
            [('104','104','98','100'),('101','102','98','100'),('99','100','97','98')])]
        def member(i):
            return Bos(str(i),bars[i].high,Zone(bars[i].high,bars[i].high))
        self.assertEqual(len(select_bos('BUY',[member(i) for i in range(3)])),2)
        valid=[member(i) for i,b in enumerate(bars) if has_bos_wick(b,'BUY','.01')]
        result=select_bos('BUY',valid)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].entry,D('102'))

    def test_archive_projection_retains_valid_alias_after_invalid_earliest_member(self):
        # Synthetic as-of reducer fixture; no ticks, fills or profitability.
        ids=['M1:BUY:2026-10-05T00:00:00+00:00','M1:BUY:2026-10-05T00:01:00+00:00',
             'M1:BUY:2026-10-05T00:02:00+00:00']
        key='M1:BUY:2026-10-05T00:03:00+00:00'
        before=dict(seeds={k:dict(allowed=i!=0) for i,k in enumerate(ids)},
            qualified={k:dict(time=f'2026-10-05T00:0{i+3}:00Z',level='104' if i<2 else '100')
                       for i,k in enumerate(ids)},
            groups={key:dict(server_time='2026-10-05T04:00:00',all_geometric_members=';'.join(ids),
                members=';'.join((ids[0],ids[2])),selected_bos_ids=';'.join((ids[0],ids[2])),
                accepted=True,fill_at_confirmation='PARTIAL')})
        result=project_groups(before,'2026-10-05','2026-10-06')
        self.assertEqual(result['changes'][0]['after_selected'],[ids[1],ids[2]])
        self.assertEqual(result['missing_ohlc_ids'],[])
        self.assertEqual(result['groups_with_selection_changed'],1)
        self.assertIn('NOT_NATIVE_TRADES',result['scope'])

    def test_archive_wick_counts_require_actual_broker_metadata(self):
        bar={**bar_event(0,'100','100','90','95'), 'event':'BOS_TRACKER_CLOSED_BAR',
             'server_time':'2026-10-05T03:01:00.000'}
        key='M1:BUY:2026-10-05T00:00:00+00:00'
        old=dict(event='CORE_BOS_CANDIDATE_QUALIFIED',bos_id=key,
                 server_time='2026-10-05T03:02:00.000')
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'capture.jsonl'
            p.write_text('\n'.join(json.dumps(r) for r in [dict(event='BROKER_CAPABILITY_SNAPSHOT',tick_size=.01),bar,old])+'\n')
            result=inspect(p,'2026-10-05','2026-10-06')
            self.assertEqual(result['measured_no_wick_seeds_by_timeframe'],{'M1':1})
            self.assertEqual(result['measured_qualified_removed_ids'],[key])
            p.write_text(json.dumps(bar)+'\n')
            with self.assertRaisesRegex(ValueError,'Missing genuine broker'):
                inspect(p,'2026-10-05','2026-10-06')


if __name__=='__main__': unittest.main()
