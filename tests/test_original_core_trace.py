"""Synthetic diagnostic fixtures, never historical trades or broker results."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tools.trace_original_core import trace


class OriginalTraceChecks(unittest.TestCase):
    def run_trace(self, state='PARTIAL', prior_partial=False, consumed=False):
        rows=[]
        for bid,level in [('low','4143'),('high','4146')]:
            rows.append(dict(event='CORE_SETUP_CANDIDATE',fvg_id='fixture-F',bos_id=bid,
                qualified_at='2026-10-01T00:00:01.000Z',candidate_at='2026-10-01T00:00:00.000Z',
                fvg_available_at='2026-10-01T00:01:00.000Z',side='BUY',bos_level=level,
                entry_reference=str(float(level)+.5),fvg=['4141','4147'],ob=['4147','4149'],
                fill_state='UNFILLED',startup_history=False,first_return_consumed=False,tick_index=1))
        ret=dict(event='BOS_FIRST_DIRECTIONAL_RETURN',bos_id='high',break_quote='bid',retest_quote='bid',
                 tick_index=1,time='2026-10-01T00:01:00.000Z',server_time='2026-10-01T03:01:00.000',
                 entry_reference='4146.5',previous_quote='4147.1',observed_quote='4146.5',exact_quote=True)
        if consumed:rows.append({**ret,'bos_id':'low','tick_index':0,'entry_reference':'4143.5','observed_quote':'4143.5'})
        rows.append(dict(event='EXPERIMENTAL_GROUP_FINALIZED',fvg_id='fixture-F',members='low;high',
                         reason='PARTIAL_NOT_APPROVED' if prior_partial else '',tick_index=1,
                         time=ret['time'],server_time=ret['server_time']))
        rows.append(dict(event='CORE_FVG_VALIDITY_CHANGED',fvg_id='fixture-F',source='observed_bid',fill_state=state,tick_index=1))
        rows.append(dict(event='TICK',synthetic_fixture=True,tick_index=1,bid='4146.5',ask='4146.72',time=ret['time'],server_time=ret['server_time']))
        rows.append(ret)
        rows.append(dict(event='CORE_CONTROLLER_SUMMARY',controller_halted=False,processed_ticks=1,tester_experiment=1))
        rows.append(dict(event='TICK_CAPTURE_SUMMARY',capture_halted=False,terminal_cursor_evidence_valid=True,emitted_ticks=1))
        with TemporaryDirectory() as d:
            p=Path(d)/'synthetic.jsonl'
            p.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
            return trace(p)

    def test_same_tick_confirmation_is_not_silently_excluded(self):
        r=self.run_trace()
        self.assertEqual(r['strict_fvg_gate_returns'],0)
        self.assertEqual(r['first_touch_fvg_gate_returns'],1)
        self.assertEqual(len(r['selected_post_confirmation_returns']),1)

    def test_full_never_qualifies(self):
        self.assertEqual(self.run_trace(state='FULL')['first_touch_fvg_gate_returns'],0)

    def test_preexisting_partial_is_not_first_touch_permission(self):
        self.assertEqual(self.run_trace(prior_partial=True)['first_touch_fvg_gate_returns'],0)

    def test_consumed_extreme_cannot_be_replaced_by_the_other_return(self):
        r=self.run_trace(consumed=True)
        self.assertEqual(r['first_touch_fvg_gate_returns'],0)
        self.assertEqual(r['groups'][0]['structural_blocker'],'FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION')


if __name__=='__main__':unittest.main()
