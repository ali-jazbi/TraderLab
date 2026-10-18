"""Policy fixtures, not historical trades or owner amendments."""
import unittest
from decimal import Decimal as D
from tools.audit_discovery_groups import members
from traderlab.retests import FirstReturn
from traderlab.detection import instant
from pathlib import Path

class DiscoveryChecks(unittest.TestCase):
    def row(self, **kw):
        return dict(bos_id='B',bos_timeframe='M15',fvg_timeframe='M15',qualified_at='2026-10-08T00:00:00Z',
            candidate_at='2026-10-07T23:00:00Z',fvg_candidate_at='2026-10-08T00:45:00Z',
            fvg_available_at='2026-10-08T03:30:00Z',break_at='2026-10-08T00:49:52Z',
            first_return_consumed=False,bos_level='4114.87')|kw

    def test_fresh_selection_is_asof_not_return_outcome(self):
        old=self.row(bos_id='old',first_return_consumed=True)
        fresh=self.row(bos_id='fresh')
        self.assertEqual([r['bos_id'] for r in members([old,fresh],1)],['fresh'])
        self.assertEqual(members([self.row(qualified_at='2026-10-08T03:31:00Z')],1),[])

    def test_impulse_membership_no_arbitrary_age_expiry(self):
        old=self.row(candidate_at='2026-09-21T00:00:00Z')
        self.assertEqual(len(members([old],2)),1)
        for br in ['2026-10-08T00:44:59.999Z','2026-10-08T01:00:00Z',None]:
            self.assertEqual(members([self.row(break_at=br)],2),[])
        self.assertEqual(len(members([self.row(break_at='2026-10-08T00:45:00Z')],2)),1)

    def test_independent_stream_never_resets_canonical_consumption(self):
        r=self.row(first_return_consumed=True)
        self.assertEqual(members([r],2),[])
        self.assertEqual(len(members([r],3)),1)
        self.assertEqual(members([r],3,{'B'}),[])
        self.assertTrue(r['first_return_consumed'])
        canonical=FirstReturn('BUY',D('4115.37'));study=FirstReturn('BUY',D('4115.37'))
        at=instant('2026-10-08T00:49:54Z')
        canonical.advance(D('4115.45'),at,1);canonical.advance(D('4115.31'),at,2)
        self.assertIsNotNone(canonical.result);self.assertIsNone(study.result)
        arm=instant('2026-10-08T03:30:00Z')
        study.advance(D('4129'),arm,3)
        self.assertIsNotNone(study.advance(D('4115.37'),instant('2026-10-08T06:00:00Z'),4))
        self.assertIsNone(study.advance(D('4115.37'),arm,5))

    def test_equal_price_alias_selected_by_qualification_not_future(self):
        a=self.row(bos_id='later',qualified_at='2026-10-08T00:30:00Z')
        b=self.row(bos_id='earlier')
        self.assertEqual([r['bos_id'] for r in members([a,b],1)],['earlier'])

    def test_native_lock_and_selection_source_contracts(self):
        root=Path(__file__).resolve().parents[1]
        gateway=(root/'mt5/Include/TraderLab/DemoGateway.mqh').read_text()
        self.assertIn('const bool TL_DEMO_DISPATCH_REVIEWED=false',gateway)
        controller=(root/'mt5/Include/TraderLab/CoreController.mqh').read_text()
        self.assertIn('p.plan.count==2 && entry==p.plan.entry2',controller)
        self.assertIn('if(armed) r=bos[b].study_return',controller)
        self.assertIn('!bos[b].study_armed',controller)
        self.assertIn('recovering || consumption.Consume(key,tick.time_msc)',controller)

    def test_calendar_extension_does_not_allow_unreviewed_holdout(self):
        from datetime import date
        from tools.prepare_auto_tester import prepare
        root=Path(__file__).resolve().parents[1]
        with self.assertRaises(ValueError):prepare(root,date(2026,10,14),date(2026,10,18),3,'unreviewed')

    def test_post_test_deal_export_includes_tester_end_liquidation(self):
        source=(Path(__file__).resolve().parents[1]/'mt5/TraderLab.mq5').read_text()
        export=source.split('double OnTester()',1)[1].split('void OnDeinit',1)[0]
        self.assertIn('HistorySelect(0,TimeCurrent()+PeriodSeconds(PERIOD_D1))',export)
        self.assertIn('owned_positions[p]==position',export)
        self.assertIn('owned_by_original_entry',export)

if __name__=='__main__':unittest.main()
