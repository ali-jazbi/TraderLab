import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from traderlab.forward_calendar import packet, publish, sessions

UTC = timezone.utc


class ForwardCalendarTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 25, 18, tzinfo=UTC)
        self.snapshot = dict(valid=True, error=0, server_offset=7200,
                             observed_utc=int(self.now.timestamp()), events=[])
        # Official upcoming BLS / Fed dates, not strategy-selection examples.
        for code, host, utc in (
                ('fed-interest-rate-decision', 'federalreserve.gov', '2026-10-28T18:00:00+00:00'),
                ('fomc-press-conference', 'federalreserve.gov', '2026-10-28T18:30:00+00:00'),
                ('nonfarm-payrolls', 'bls.gov', '2026-11-06T13:30:00+00:00'),
                ('consumer-price-index-mm', 'bls.gov', '2026-11-10T13:30:00+00:00')):
            self.snapshot['events'].append(dict(code=code, source='https://www.'+host,
                server_time=int(datetime.fromisoformat(utc).timestamp())+7200, time_mode=0))

    def test_actual_snapshot_dst_conversion_and_news_dedup(self):
        self.snapshot['events'].append(copy.deepcopy(self.snapshot['events'][0]))
        data = packet(self.snapshot, self.now)
        self.assertEqual(data.count('NEWS|FOMC|1793210400|'), 1)
        self.assertIn('MT5_USD_PRIMARY_FORWARD_V1', data)
        # Observation time is never renewed by the publisher.
        self.assertTrue(data.splitlines()[0].endswith(f"|{self.snapshot['observed_utc']}|{self.snapshot['observed_utc']+180}"))

    def test_old_future_failed_incomplete_unknown_clock_block(self):
        mutations = [dict(observed_utc=int(self.now.timestamp())-180),
                     dict(observed_utc=int(self.now.timestamp())+1), dict(valid=False),
                     dict(error=5401), dict(server_offset=10800), dict(events=[])]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                packet(self.snapshot | mutation, self.now)

    def test_actual_mixed_utc_and_server_values_require_exact_primary_evidence(self):
        snapshot=copy.deepcopy(self.snapshot)
        snapshot['events'][0]['server_time']=1793210400  # actual MT5 rate decision already UTC
        cpi=copy.deepcopy(snapshot['events'][-1]); cpi['code']='consumer-price-index-nsa'
        cpi['server_time']=1794317400  # actual NSA variant already UTC
        snapshot['events'].append(cpi)
        data=packet(snapshot,self.now)
        self.assertIn('NEWS|FOMC|1793210400|',data)
        self.assertNotIn('NEWS|FOMC|1793203200|',data)
        for bad in (1793210401,1793214000,1793296800):
            snapshot['events'][0]['server_time']=bad
            with self.assertRaisesRegex(ValueError,'PRIMARY_EVENT_CLOCK_MISMATCH'):
                packet(snapshot,self.now)

    def test_nonprimary_source_and_nontimed_values_block(self):
        for mutation in (dict(source='https://bls.gov.attacker.example'), dict(time_mode=1)):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot['events'][0].update(mutation)
            with self.assertRaises(ValueError):
                packet(snapshot, self.now)

    def test_sessions_no_overlap_across_both_dst_transitions(self):
        for month, days in ((3, (7, 8, 9)), (4, (4, 5, 6)), (10, (3, 4, 5, 24, 25, 26)), (11, (1, 2, 3))):
            for day in days:
                rows = sessions(datetime(2026, month, day, tzinfo=UTC))
                self.assertTrue(all(a < b for _, a, b in rows))
                self.assertTrue(all(rows[i][2] <= rows[i+1][1] for i in range(len(rows)-1)))
                for ident, a, b in rows:
                    self.assertEqual(datetime.fromtimestamp(a, UTC).astimezone(__import__('zoneinfo').ZoneInfo('Australia/Sydney')).hour, 7)

    def test_failure_replaces_valid_packet_without_changing_native_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = root/'TraderLab-forward-native.json'
            native.write_text(json.dumps(self.snapshot))
            self.assertEqual(publish(root, self.now), 'VERIFIED')
            before = native.read_bytes()
            self.assertIn('STALE', publish(root, datetime(2026, 10, 26, tzinfo=UTC)))
            self.assertEqual((root/'TraderLab-forward-calendar.csv').read_text(), 'INVALID\n')
            self.assertEqual(native.read_bytes(), before)

    def test_release_uses_one_real_send_site_and_account_bound_opt_in(self):
        root = Path(__file__).resolve().parents[1]
        policy = (root/'mt5/Include/TraderLab/FirstTouchPolicy.mqh').read_text()
        self.assertIn('AccountInfoInteger(ACCOUNT_LOGIN)==91496222', policy)
        self.assertIn('#ifdef TRADERLAB_DEMO_FORWARD_RELEASE', policy)
        production = '\n'.join(p.read_text() for p in (root/'mt5/Include/TraderLab').glob('*.mqh'))
        self.assertEqual(production.count('OrderSend('), 1)
        self.assertNotIn('OfflineBroker.mqh', production)
        self.assertNotIn('#define MQLInfoInteger', production)
        self.assertIn('TL_DEMO_DAY_BALANCE*0.98', policy)
        self.assertIn('AccountInfoDouble(ACCOUNT_EQUITY)*0.01', production)


if __name__ == '__main__':
    unittest.main()
