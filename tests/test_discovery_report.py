"""Synthetic report fixtures only, never historical trades or performance evidence."""
from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path
import tempfile
import unittest

from tools.report_discovery_study import analyze, performance
from tools.audit_discovery_groups import audit_armed_returns


class DiscoveryReportChecks(unittest.TestCase):
    def fixture(self, root):
        files=root/'native-files';files.mkdir()
        (files/'study-plans-fixture.dat').write_text('PLAN|EXPERIMENTAL:test|EX1|EX2|1|1|1|1|100|100|96\n')
        (files/'study-gateway-fixture.dat').write_text(
            'EX1|test|XAUUSD_o|RECONCILED|0.01|96.2|106|1|1|1000\n'
            'EX2|test|XAUUSD_o|RECONCILED|0.01|96.2|110|1|1|1000\n'
            'BEX2|MOD:2:EX2|XAUUSD_o|RECONCILED|0.0|100.7|110|1|0|1002\n')
        positions={}
        for i in (1,2):
            positions[str(i)]=[
                dict(entry_kind=0,deal_time_msc=11800100,comment='TL:EX'+str(i),price=100.2,
                     net=-.05,volume=.01,actual_server_time='2026-10-08T09:00:00.100'),
                dict(entry_kind=1,deal_time_msc=11802100 if i==1 else 11803100,
                     comment='tp' if i==1 else 'sl',reason=5 if i==1 else 4,
                     price=106 if i==1 else 100.7,net=5.8 if i==1 else .5,volume=.01,
                     actual_server_time='2026-10-08T09:00:02.100')]
        return dict(archive=str(root),run='fixture',positions=positions,
                    inputs={'InpServerUtcOffsetSeconds':'10800'},
                    events=[dict(event='CORE_TESTER_DISPATCH_RESULT',submitted=True,
                        setup_id='EXPERIMENTAL:test',actual_signal_quote={'time_msc':11800100},
                        server_time='2026-10-08T09:00:00.100',frozen_group={'server_time':'2026-10-08T08:00:00'})],
                    measured_server_window=['2026-10-08','2026-10-09'],group_reasons={},
                    first_return_reasons={},dispatch_results={},native_report_metrics={})

    def test_actual_fill_protection_costs_and_utc_be_journal(self):
        with tempfile.TemporaryDirectory() as t:
            r=analyze(self.fixture(Path(t)))
            self.assertEqual(r['protections_verified'],2)
            self.assertEqual(r['setup_performance']['net'],'6.20')
            self.assertEqual(len(r['be_reconciled']),1)
            self.assertEqual(r['maximum_actual_open_lots'],'0.02')

    def test_wrong_stop_or_unclosed_leg_is_not_performance(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.fixture(Path(t));bad=deepcopy(r);bad['positions']['2'].pop()
            with self.assertRaisesRegex(ValueError,'Incomplete'):analyze(bad)
            bad=deepcopy(r);bad['positions']['1'][0]['price']=100.3
            with self.assertRaisesRegex(ValueError,'SL / shared TP'):analyze(bad)

    def test_net_unit_statistics_keep_losers_and_flats(self):
        r=performance(map(D,['6','-4','0']))
        self.assertEqual((r['net'],r['net_unit_profit_factor'],r['losses'],r['flat']),('2','1.5',1,1))

    def test_armed_return_uses_actual_post_arm_ticks_once(self):
        rows=[dict(event='CORE_SETUP_CANDIDATE',bos_id='M1:BUY:B',bos_level='100'),
              dict(event='EXPERIMENTAL_GROUP_FINALIZED',accepted=True,selected_bos_ids='M1:BUY:B',tick_index=2)]
        for i,price in enumerate(['101','100.6','100.4','100.5'],1):
            rows.append(dict(event='TICK',tick_index=i,bid=price,server_time=str(i)))
        rows.append(dict(event='EXPERIMENTAL_ARMED_FIRST_RETURN',bos_id='M1:BUY:B',tick_index=3,
                         server_time='3',previous_quote=100.6,observed_quote=100.4))
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'fixture.jsonl';p.write_text('\n'.join(json.dumps(r,separators=(',',':')) for r in rows))
            self.assertEqual(audit_armed_returns(p)['returns_checked'],1)
            rows[-1]['tick_index']=4
            p.write_text('\n'.join(json.dumps(r,separators=(',',':')) for r in rows))
            with self.assertRaisesRegex(ValueError,'mismatch'):audit_armed_returns(p)


if __name__=='__main__':unittest.main()
