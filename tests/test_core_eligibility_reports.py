"""Census stages and fresh-deal comparison; these are synthetic unit records."""
from decimal import Decimal as D
import unittest
from tools.audit_core_eligibility import summarize
from tools.report_body80_study import compare


class EligibilityReportChecks(unittest.TestCase):
    def test_census_keeps_detection_body_permission_and_fill_distinct(self):
        row=dict(timeframe='M1',server_available_at='2026-10-07T00:00:00',body_pips=D('79.9'),
                 has_valid_prior_bos=True,witnesses=[{'id':'B'}],core_eligibility=False,
                 non_full_eligible=False,strict_unfilled_eligible=False,fill_at_confirmation='UNFILLED',
                 reasons=['C2_BODY_BELOW_80_PIPS'])
        values=[row,dict(row,body_pips=D(80),core_eligibility=True,non_full_eligible=True,
                        fill_at_confirmation='PARTIAL',reasons=[])]
        r=summarize(values,'2026-10-07','2026-10-10')['M1']
        self.assertEqual((r['total_fvgs'],r['body_ge_80'],r['new_filter_pass'],r['new_filter_non_full'],
                          r['new_filter_strict_unfilled']),(2,1,1,1,0))
        self.assertEqual(summarize(values,'2026-10-14','2026-10-17')['M1']['total_fvgs'],0)

    def test_trade_diff_uses_entry_identity_not_later_winner_or_ticket(self):
        p=dict(setup='F',planned='100',leg=1,entry_time='2026-10-07T00:00',side=1,position='10',net='-4')
        q=dict(p,position='20',net='6');r=dict(p,entry_time='2026-10-07T01:00')
        d=compare(dict(actual_positions=[p]),dict(actual_positions=[q,r]))
        self.assertEqual((len(d['removed']),len(d['added']),d['same_entry_count']),(0,1,1))
        self.assertEqual(compare(dict(actual_positions=[]),dict(actual_positions=[]))['added'],[])
