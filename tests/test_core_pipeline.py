"""Deterministic reporting/source contracts. Not native broker execution evidence."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from traderlab.candidates import core_candidates, write_candidates
from traderlab.detection import instant
from tools.compare_existing_detectors import closed_signature, compare_closed
from tools.compare_native_retests import compare_rows
from test_native_retests import comparator_fixture
import test_inspect_capture as capture_checks

ROOT=Path(__file__).resolve().parents[1]
class CandidateChecks(unittest.TestCase):
    def engine(self):
        at=instant('2026-10-07T03:36:00.123Z')
        returned={'first_return_at':instant('2026-10-07T03:28:51.731Z'),'exact_quote':False,
                  'previous_quote':'4142.34','observed_quote':'4142.30'}
        event={'event':'AUTO_SETUP_BLOCKED','setup_id':'B~F','bos_id':'B','fvg_id':'F','bos_timeframe':'M1',
               'fvg_timeframe':'M1','side':'BUY','candidate_at':instant('2026-10-07T03:10:00Z'),
               'bos_level':'4141.82','entry_reference':'4142.32','fill_state':'PARTIAL',
               'reasons':['TODO_STRATEGY_UNRESOLVED:package_grouping']}
        gap={'id':'F','candidate_at':instant('2026-10-07T03:25:00Z'),'formation_at':instant('2026-10-07T03:27:00Z'),
             'available_at':at,'ob_anchor_at':instant('2026-10-07T03:26:00Z'),'zone':['4139.60','4142.19'],
             'ob':['4142.19','4143.85'],'fill_state':'FULL'}
        return SimpleNamespace(events=[event],automatic=SimpleNamespace(gaps={'F':gap},bos={'B':{'qualified_at':at}}),
                               retests=SimpleNamespace(snapshot=lambda _: {'bid':{'break_at':instant('2026-10-07T03:25:50.736Z'),
                                                   'returns':{'bid':returned}}}))
    def test_final_state_does_not_promote_or_rearm_consumed_candidate(self):
        r=core_candidates(self.engine(),10800)[0]
        self.assertEqual((r['fill_at_relationship'],r['fill_at_end']),('PARTIAL','FULL'))
        for reason in ('FVG_FULL_FILL_INVALID_AT_END','FIRST_RETURN_CONSUMED_NO_RETROACTIVE_APPROVAL','MISSED_EXACT_SIGNAL_QUOTE_NO_FILL'):
            self.assertIn(reason,r['reasons'])
        self.assertFalse(r['fully_approved']);self.assertFalse(r['broker_execution_enabled'])
        self.assertEqual(r['server_wall_time']['first_return'],'2026-10-07T06:28:51.731')
        self.assertEqual(r['server_wall_time']['fvg_confirmation'],'2026-10-07T06:36:00.123')
        self.assertTrue(any('complete BOS member IDs' in x for x in r['minimal_evidence']))
    def test_unknown_offset_is_not_fabricated_and_warmup_is_distinguished(self):
        e=self.engine();r=core_candidates(e,None,e.automatic.bos['B']['qualified_at'])[0]
        self.assertTrue(r['startup_history'])
        self.assertTrue(all(v is None for v in r['server_wall_time'].values()))
        self.assertIn('STARTUP_HISTORY_NOT_EXECUTION_PROOF',r['reasons'])
    def test_cross_frame_approval_requires_exact_package_evidence(self):
        e=self.engine();e.events[0]['fvg_timeframe']='M5'
        r=core_candidates(e)[0]
        self.assertTrue(any('exact BOS/FVG timeframes' in x for x in r['minimal_evidence']))
    def test_export_preserves_ids_prices_quotes_and_determinism(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);write_candidates(self.engine(),p,10800)
            before=(p/'core-candidates.json').read_bytes()
            write_candidates(self.engine(),p,10800)
            self.assertEqual(before,(p/'core-candidates.json').read_bytes())
            r=json.loads(before)[0];self.assertEqual(r['ob_id'],'F:C3')
            csv=(p/'core-candidates.csv').read_text(encoding='utf-8')
            self.assertIn('4141.82',csv);self.assertIn('06:28:51.731',csv)

class ParityScopeChecks(unittest.TestCase):
    def test_explicit_prefix_all_candidates_does_not_accept_capture(self):
        rows,cfg=comparator_fixture();rows=rows[:-1]
        with self.assertRaises(ValueError):compare_rows(rows,cfg)
        r=compare_rows(rows,cfg,diagnostic_prefix=True,all_candidates=True)
        self.assertTrue(r['matches']);self.assertFalse(r['evidence_complete'])
        self.assertEqual(r['capture_acceptance'],'NOT_ESTABLISHED')
    def test_prefix_tick_linking_stays_strict(self):
        rows,cfg=comparator_fixture();rows=copy.deepcopy(rows[:-1])
        r=next(x for x in rows if x['event']=='BOS_FIRST_DIRECTIONAL_RETURN')
        r['observed_quote']='9999'
        with self.assertRaisesRegex(ValueError,'genuine dispatch tick'):
            compare_rows(rows,cfg,diagnostic_prefix=True,all_candidates=True)
    def test_geometry_signature_ignores_native_extra_body_but_not_zone(self):
        r={'event':'FVG_CONFIRMED','timeframe':'M1','candidate_at':'2026-10-07T03:25:00Z',
           'side':'BUY','zone':['4139.60','4142.19'],'fill_state':'PARTIAL'}
        self.assertEqual(closed_signature(r),closed_signature({**r,'body':'3.10000000'}))
        self.assertNotEqual(closed_signature(r),closed_signature({**r,'zone':['4139.60','4142.20']}))

class NativeIntegrationContracts(unittest.TestCase):
    def test_only_review_locked_dispatch_and_no_reverse_or_real(self):
        folder=ROOT/'mt5/Include/TraderLab'
        source='\n'.join(p.read_text(encoding='utf-8') for p in folder.glob('*.mqh'))
        self.assertEqual(source.count('OrderSend('),1)
        self.assertNotIn('OrderSendAsync',source);self.assertNotIn('CTrade',source)
        self.assertIn('TL_DEMO_DISPATCH_REVIEWED=false',source)
        self.assertIn('request_execution && TL_DEMO_DISPATCH_REVIEWED',source)
        self.assertIn('mode==ACCOUNT_TRADE_MODE_DEMO',source)
        # Tester transport was introduced at 202b794; both branches still require DEMO.
        self.assertIn('tester_mode?(bool)MQLInfoInteger(MQL_TESTER):!MQLInfoInteger(MQL_TESTER)',source)
        self.assertIn('&& TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE))',source)
        controller=(folder/'CoreController.mqh').read_text(encoding='utf-8')
        self.assertIn('Automatic membership remains unresolved',controller)
        self.assertIn('OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY',controller)
        self.assertLess(controller.index('consumption.Consume'),controller.index('book.Begin'))
    def test_lifecycle_uses_position_identifier_deal_costs_and_persisted_plan(self):
        source=(ROOT/'mt5/Include/TraderLab/CoreLifecycle.mqh').read_text(encoding='utf-8')
        for token in ('DEAL_POSITION_ID','POSITION_IDENTIFIER','DEAL_COMMISSION','DEAL_SWAP','DEAL_FEE',
                      'HistoryDealSelect','CORE_PARTIAL_OR_CONFLICTING_FILL','CORE_UNRESTORED_DEAL_PLAN',
                      'restoring=true','CORE_BE_FAILED_OR_UNRESOLVED','calendar.Day','daily.Close'):
            self.assertIn(token,source)
        self.assertLess(source.index('FileFlush(plan_file); // Persist approved plan'),source.index('gateway.SubmitReviewedCorePair'))
        self.assertIn('gateway.MoveBreakEven(trades[i].id2,ticket',source)
    def test_core_summary_coarse_precision_does_not_relax_market_ticks(self):
        inspector=capture_checks.CaptureInspectorChecks()
        rows=inspector.shutdown_capture(timestamp_precision='seconds')
        rows[-1]['event']='CORE_CONTROLLER_SUMMARY'
        self.assertFalse(inspector.inspect_rows(rows)['errors'])
        rows[-1]['event']='TICK';rows[-1]['kind']='tick';rows[-1]['symbol']='XAUUSD.pro'
        self.assertTrue(inspector.inspect_rows(rows)['errors'])

if __name__=='__main__':unittest.main()
