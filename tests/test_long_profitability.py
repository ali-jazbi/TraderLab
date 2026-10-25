"""Accounting/clock fixtures only; no strategy changes or profitability claims."""
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.report_long_profitability import monthly_results, calendar_execution_checks, native_month_tick_crosscheck


class LongProfitabilityChecks(unittest.TestCase):
    def test_complete_native_month_counts_match_without_discarding_partial_april(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.jsonl'
            path.write_text('\n'.join(['{"event":"TICK","server_time":"2026-04-07T01:00:00"}']+
                [f'{{"event":"TICK","server_time":"2026-{m:02d}-01T01:00:00"}}' for m in range(5,11)]+
                ['{"event":"TESTER_CORE_DEAL","server_time":"2026-10-23T23:59:00"}'])+'\n')
            coverage=dict(months=[dict(month=f'2026.{m:02d}.01',callbacks=1) for m in range(4,11)])
            result=native_month_tick_crosscheck(path,coverage)
            self.assertTrue(result['matches'])
            self.assertEqual(len(result['months']),6)
            self.assertEqual(result['all_captured_ticks_by_server_month']['2026-04'],1)
            self.assertEqual(result['all_captured_ticks_by_server_month']['2026-10'],1)

    def test_a_whole_missing_month_is_rejected_even_without_generated_tick_warning(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.jsonl'
            path.write_text('\n'.join(f'{{"event":"TICK","server_time":"2026-{m:02d}-01T01:00:00"}}' for m in (5,7,8,9,10))+'\n')
            coverage=dict(months=[dict(month=f'2026.{m:02d}.01',callbacks=1) for m in range(5,11)])
            with self.assertRaisesRegex(ValueError,'histogram differs'):
                native_month_tick_crosscheck(path,coverage)

    def test_month_end_costs_and_setup_legs_reconcile_without_reassigning_cash(self):
        positions=[];deals={}
        for key,setup,entry,exit,profit in [
            ('1','A','2026-04-30T23:59:00','2026-05-01T00:05:00','2'),
            ('2','A','2026-04-30T23:59:00','2026-05-01T00:10:00','3'),
            ('3','B','2026-05-04T01:00:00','2026-05-04T01:30:00','-1'),
            ('4','B','2026-05-04T01:00:00','2026-05-04T01:30:00','-2')]:
            from decimal import Decimal
            positions.append(dict(position=key,setup=setup,entry_time=entry,exit_time=exit,
                                  net=str(Decimal(profit)-Decimal('.05'))))
            deals[key]=[dict(actual_server_time=entry,net='-.05'),dict(actual_server_time=exit,net=profit)]
        result=monthly_results(dict(positions=deals),dict(actual_positions=positions,position_performance=dict(net='1.80')))
        self.assertEqual(result[0]['cash_net'],'-0.10')
        self.assertEqual(result[1]['cash_net'],'1.90')
        self.assertEqual(result[0]['first_entry_setup_cohort']['count'],1)
        self.assertEqual(result[0]['first_entry_setup_cohort']['net'],'4.90')
        self.assertEqual(result[1]['first_entry_setup_cohort']['net'],'-3.10')
        self.assertEqual(sum(v['first_entry_setup_cohort']['count'] for v in result),2)

    def test_news_entry_window_and_actual_closure_deadline_are_checked_separately(self):
        epoch=lambda value:int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp())
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'calendar.csv'
            path.write_text(f"DAY|2026-05-08|{epoch('2026-05-08T00:00:00')}|{epoch('2026-05-09T00:00:00')}|0\n"
                            f"NEWS|NFP|{epoch('2026-05-08T12:30:00')}|0|{epoch('2026-04-03T12:30:00')}\n")
            positions=[dict(position='late-entry',entry_time='2026-05-08T15:20:00',exit_time='2026-05-08T15:21:00'),
                       dict(position='late-exit',entry_time='2026-05-08T14:00:00',exit_time='2026-05-08T15:28:00')]
            result=calendar_execution_checks(dict(actual_positions=positions),dict(calendar_file=str(path)))
            self.assertFalse(result['valid'])
            self.assertEqual({v['reason'] for v in result['violations']},
                             {'ENTRY_DURING_NEWS_RESTRICTION','POSITION_OPEN_AFTER_NEWS_DEADLINE'})
            positions[1]['exit_time']='2026-05-08T15:27:00'
            self.assertTrue(calendar_execution_checks(dict(actual_positions=positions[1:]),dict(calendar_file=str(path)))['valid'])
