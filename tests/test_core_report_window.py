"""Reporting fixtures only; these are not historical orders or performance."""
from datetime import datetime,timezone
import unittest
from tools.report_core_policy_runs import server_window,validate_deal_window

class CoreReportWindowChecks(unittest.TestCase):
    def deal(self, at):
        return {'deal_time_msc':int(datetime.fromisoformat(at).replace(tzinfo=timezone.utc).timestamp()*1000),
                'server_time':'2026-10-09T23:58:59.103'} # OnTester logging time is deliberately different.

    def test_warmup_deal_not_hidden_by_end_of_test_event_time(self):
        with self.assertRaisesRegex(ValueError,'outside measured'):
            validate_deal_window({1:[self.deal('2026-10-06T23:59:59.999')]},server_window('2026-10-07','2026-10-10'))

    def test_entry_and_exit_must_both_be_inside_no_censoring(self):
        window=server_window('2026-10-07','2026-10-10')
        validate_deal_window({1:[self.deal('2026-10-07T00:00:00'),self.deal('2026-10-09T23:59:59.999')]},window)
        with self.assertRaises(ValueError):
            validate_deal_window({1:[self.deal('2026-10-07'),self.deal('2026-10-10')]},window)

    def test_explicit_increasing_naive_broker_times_required(self):
        for a,b in [('2026-10-07',None),('2026-10-10','2026-10-07'),('2026-10-07T00:00:00Z','2026-10-10T00:00:00Z')]:
            with self.assertRaises(ValueError):server_window(a,b)
        self.assertIsNone(server_window(None,None))

if __name__=='__main__':unittest.main()
