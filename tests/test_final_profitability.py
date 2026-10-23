"""Synthetic assessment fixtures, never historical performance or risk approval."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.report_final_profitability import html_costs, sample_units, verdict
from tools.report_core_policy_runs import native_tick_quality, audit


class FinalAssessmentChecks(unittest.TestCase):
    def setUp(self):
        self.criteria=dict(net_profit_gt=0,profit_factor_gt='1.2',maximum_drawdown=dict(unit='usd',value=20),
                           minimum_independent_setups=30,minimum_separate_windows=2)
        self.windows=[dict(name=str(i),net='10',setup_profit_factor='1.5',independent_setup_count=20,
                           drawdown_usd='10',drawdown_percent='1') for i in range(2)]

    def test_native_success_cannot_replace_missing_cost_or_independence_evidence(self):
        result=verdict(self.windows,self.criteria,dict(native_capture=True,all_costs=False,independence=False))
        self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['reasons'],['all_costs','independence'])
        criteria=deepcopy(self.criteria);criteria['maximum_drawdown']=None
        self.assertEqual(verdict(self.windows,criteria,dict(complete=True))['status'],'INSUFFICIENT_EVIDENCE')

    def test_fail_and_pass_require_sufficient_verified_sample_first(self):
        self.assertEqual(verdict(self.windows,self.criteria,dict(complete=True))['status'],'PASS')
        self.windows[0].update(net='-1',setup_profit_factor='1.20',drawdown_usd='21')
        result=verdict(self.windows,self.criteria,dict(complete=True))
        self.assertEqual(result['status'],'FAIL');self.assertEqual(len(result['reasons']),3)
        self.windows[0]['independent_setup_count']=1;self.windows[1]['independent_setup_count']=1
        self.assertEqual(verdict(self.windows,self.criteria,dict(complete=True))['status'],'INSUFFICIENT_EVIDENCE')
        self.windows[0]['independent_setup_count']=None
        self.assertEqual(verdict(self.windows,self.criteria,dict(complete=True))['status'],'INSUFFICIENT_EVIDENCE')

    def test_legs_and_shared_impulse_do_not_become_independent_setups(self):
        a=dict(setup='EXPERIMENTAL:M5:BUY:2026-10-19T00:00:00+00:00',net='1',
               entry_time='2026-10-19T01:00:00',exit_time='2026-10-19T01:10:00')
        b=dict(a,net='-2')
        c=dict(a,setup='EXPERIMENTAL:M15:BUY:2026-10-19T00:00:00+00:00',net='3',
               entry_time='2026-10-19T02:00:00',exit_time='2026-10-19T02:10:00')
        result=sample_units([a,b,c])
        self.assertEqual((result['position_legs'],result['unique_setups']),(3,2))
        self.assertEqual(len(result['overlap_or_shared_impulse_clusters']),1)
        self.assertEqual(result['overlap_or_shared_impulse_clusters'][0]['net'],'2')
        self.assertIsNone(result['independent_sample_size_verified'])

    def test_costs_exclude_deposit_and_missing_fee_column_is_not_fee_proof(self):
        rows=[['Time','Deal','Type','Direction','Commission','Swap','Profit'],
              ['2026.10.19 00:00:00','1','balance','','0','0','1000'],
              ['2026.10.19 01:00:00','2','buy','in','-0.02','0','0'],
              ['2026.10.19 02:00:00','3','sell','out','0','-0.01','0.20']]
        html='<table>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in rows)+'</table>'
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.html';path.write_text(html,encoding='utf-8')
            result=html_costs(path,'0.17')
            self.assertEqual(result['deal_rows'],2)
            self.assertEqual(result['commission'],'-0.02')
            self.assertFalse(result['explicit_fee_column'])
            self.assertFalse(result['historical_broker_costs_independently_verified'])
            with self.assertRaises(ValueError): html_costs(path,'0.18')

    def test_agent_fallback_overrides_optimistic_html_quality_and_is_not_double_counted(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp);log=folder/'terminal/Tester/Agent-local/logs/test.log'
            log.parent.mkdir(parents=True)
            self.assertFalse(native_tick_quality(folder)['real_ticks_only_verified'])
            log.write_text('generating based on real ticks\n',encoding='utf-16')
            self.assertTrue(native_tick_quality(folder)['real_ticks_only_verified'])
            with log.open('a',encoding='utf-16') as f:
                f.write('2026.10.16 - real ticks absent for 192 minutes out of 1378 total minute bars\n')
                f.write('real ticks absent for 192 minutes of 27540 total minute bars, every tick generation used\n')
            result=native_tick_quality(folder)
            self.assertFalse(result['real_ticks_only_verified'])
            self.assertEqual(result['maximum_reported_missing_minutes'],192)
            self.assertEqual(len(result['warning_evidence']),2)
            (folder/'native.html').write_text('<table><tr><td>History Quality:</td><td>100% real ticks</td></tr></table>',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'generated-tick fallback'):
                audit(folder)
