"""Synthetic provider/clock/failure integration, never historical trading results."""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile
import unittest
from traderlab.calendar_service import CalendarUnavailable, prepare, refresh, session, parse_bls, parse_fed, publisher_lock

NOW = datetime(2026, 10, 16, 15, tzinfo=timezone.utc)
PROFILE = {'sydney_open': '07:00', 'new_york_close': '17:00',
           'source': 'https://www.litefinance.org/blog/for-beginners/time-at-forex/'}
BLS = '''<h1>October 2026</h1><table><tr><th>Date</th><th>Time</th><th>Release</th></tr>
<tr><td>Friday, October 2, 2026</td><td>08:30 AM</td><td>Employment Situation for September 2026</td></tr>
<tr><td>Wednesday, October 14, 2026</td><td>08:30 AM</td><td>Consumer Price Index for September 2026</td></tr></table>'''
FED = '''<h1>October 2026</h1><h4>FOMC Meetings</h4><p>2:00 p.m.</p><p>FOMC Minutes</p><p>Meeting of September 15-16</p><p>7</p>
<p>2:30 p.m.</p><p>FOMC Press Conference</p><p>28</p><p>2:00 p.m.</p><p>FOMC Meeting</p><p>Two-day meeting, October 27 - 28</p><p>28</p><h4>Beige Book</h4>'''


def source(url):
    return BLS if 'bls.gov' in url else FED


class CalendarServiceChecks(unittest.TestCase):
    def test_primary_events_use_observed_availability_and_new_york_dst(self):
        bls = parse_bls(BLS, 2026, 10, 'https://www.bls.gov/', NOW)
        fed = parse_fed(FED, 2026, 10, 'https://www.federalreserve.gov/', NOW)
        self.assertEqual({v['name'] for v in bls}, {'CPI', 'NFP'})
        self.assertEqual(bls[1]['scheduled_at'], '2026-10-14T12:30:00+00:00')
        self.assertEqual({v['scheduled_at'] for v in fed}, {'2026-10-07T18:00:00+00:00',
            '2026-10-28T18:00:00+00:00', '2026-10-28T18:30:00+00:00'})
        self.assertTrue(all(v['available_at'] == NOW.isoformat() for v in bls+fed))

    def test_missing_category_is_not_assumed_empty_coverage(self):
        for bad in (BLS.replace('Consumer Price Index', 'OTHER'), '<h1>October 2026</h1>'):
            with self.assertRaises(CalendarUnavailable):
                parse_bls(bad, 2026, 10, '', NOW)
        with self.assertRaises(CalendarUnavailable):
            parse_fed(FED.replace('FOMC Meetings', 'Removed heading'), 2026, 10, '', NOW)

    def test_live_fetch_completion_is_not_backdated_to_request_start(self):
        completed = NOW+timedelta(seconds=20)
        text, manifest = prepare(NOW, date(2026, 10, 19), PROFILE, 900, lambda url: (source(url), completed))
        self.assertEqual(manifest['observed_at'], completed.isoformat())
        self.assertEqual(manifest['fresh_until'], (completed+timedelta(seconds=900)).isoformat())
        self.assertIn('|'+str(int(completed.timestamp()))+'|', text)

    def test_backdated_provider_response_is_rejected(self):
        with self.assertRaisesRegex(CalendarUnavailable, 'CLOCK'):
            prepare(NOW, date(2026, 10, 19), PROFILE, 900, lambda url: (source(url), NOW-timedelta(seconds=1)))

    def test_provider_schema_change_unknown_time_and_wrong_month_block(self):
        with self.assertRaises(CalendarUnavailable):
            parse_bls(BLS.replace('08:30 AM', 'TBA'), 2026, 10, '', NOW)
        with self.assertRaises(CalendarUnavailable):
            parse_fed(FED.replace('<p>7</p>', '<p>TBA</p>'), 2026, 10, '', NOW)
        with self.assertRaises(CalendarUnavailable):
            parse_bls(BLS, 2026, 11, '', NOW)

    def test_empty_forward_window_requires_both_successful_primary_sources(self):
        requested = []
        def fetch(url):
            requested.append(url)
            return source(url)
        text, manifest = prepare(NOW, date(2026, 10, 19), PROFILE, 900, fetch)
        self.assertEqual(len(requested), 2)
        self.assertTrue(text.startswith('SYDNEY_NY_NEWS_V2|'))
        self.assertNotIn('NEWS|CPI', text)
        self.assertEqual(manifest['fresh_until'], (NOW+timedelta(seconds=900)).isoformat())
        self.assertEqual(len(manifest['sources']), 2)

    def test_sydney_and_us_dst_conversions_are_independent(self):
        self.assertEqual(session(date(2026, 10, 19), PROFILE),
            (datetime(2026, 10, 18, 20, tzinfo=timezone.utc), datetime(2026, 10, 19, 21, tzinfo=timezone.utc)))
        self.assertEqual(session(date(2026, 11, 2), PROFILE),
            (datetime(2026, 11, 1, 20, tzinfo=timezone.utc), datetime(2026, 11, 2, 22, tzinfo=timezone.utc)))
        self.assertEqual(session(date(2026, 4, 6), PROFILE)[0], datetime(2026, 4, 5, 21, tzinfo=timezone.utc))

    def test_expired_future_timestamp_weekend_and_unknown_age_are_rejected(self):
        for now, day, age in ((NOW, date(2026, 10, 15), 900), (NOW, date(2026, 10, 17), 900),
                              (NOW, date(2026, 10, 19), 0), (NOW.replace(tzinfo=None), date(2026, 10, 19), 900)):
            with self.assertRaises(CalendarUnavailable):
                prepare(now, day, PROFILE, age, source)

    def test_overlapping_day_never_uses_unapproved_clipping(self):
        previous = {'day': '2026-10-19', 'session_end_utc': '2026-10-19T21:00:00+00:00'}
        with self.assertRaisesRegex(CalendarUnavailable, 'DAY_OVERLAP'):
            prepare(datetime(2026, 10, 19, 21, tzinfo=timezone.utc), date(2026, 10, 20), PROFILE, 900, source, previous)

    def test_same_day_window_mutation_is_rejected_but_weekend_rollover_is_safe(self):
        _, previous = prepare(NOW, date(2026, 10, 16), PROFILE, 900, source)
        mutated = {**previous, 'session_end_utc': '2026-10-16T22:00:00+00:00'}
        with self.assertRaisesRegex(CalendarUnavailable, 'MUTATED'):
            prepare(NOW, date(2026, 10, 16), PROFILE, 900, source, mutated)
        _, monday = prepare(NOW, date(2026, 10, 19), PROFILE, 900, source, previous)
        self.assertEqual(monday['day'], '2026-10-19')

    def test_publisher_refresh_and_outage_invalidate_old_packet_without_losing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'active.csv'
            original = refresh(output, NOW, date(2026, 10, 16), PROFILE, 900, source)
            generations = list((Path(folder)/'calendar-evidence').iterdir())
            self.assertEqual(len(generations), 1)
            def failed(url):
                raise OSError('SYNTHETIC HTTP 403 / timeout')
            with self.assertRaises(OSError):
                refresh(output, NOW+timedelta(seconds=10), date(2026, 10, 16), PROFILE, 900, failed)
            self.assertEqual(output.read_text(), 'INVALID|CALENDAR_SOURCE_UNAVAILABLE\n')
            self.assertEqual(json.loads(output.with_suffix('.service.json').read_text()), original)
            self.assertTrue((generations[0]/'packet.csv').is_file())
            recovered = refresh(output, NOW+timedelta(seconds=20), date(2026, 10, 16), PROFILE, 900, source)
            self.assertEqual(recovered['observed_at'], (NOW+timedelta(seconds=20)).isoformat())
            self.assertTrue(output.read_text().startswith('SYDNEY_NY_NEWS_V2'))

    def test_one_provider_failure_never_publishes_partial_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'active.csv'
            def failed_fed(url):
                return BLS if 'bls.gov' in url else '<html>Temporarily unavailable</html>'
            with self.assertRaises(CalendarUnavailable):
                refresh(output, NOW, date(2026, 10, 16), PROFILE, 900, failed_fed)
            self.assertTrue(output.read_text().startswith('INVALID|'))

    def test_corrupt_metadata_invalidates_packet_and_concurrent_writer_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'active.csv'
            refresh(output, NOW, date(2026, 10, 16), PROFILE, 900, source)
            with publisher_lock(output.with_suffix('.publisher.lock')):
                with self.assertRaises(OSError):
                    refresh(output, NOW, date(2026, 10, 16), PROFILE, 900, source)
            output.with_suffix('.service.json').write_text('{TRUNCATED')
            with self.assertRaises(json.JSONDecodeError):
                refresh(output, NOW, date(2026, 10, 16), PROFILE, 900, source)
            self.assertTrue(output.read_text().startswith('INVALID|'))


if __name__ == '__main__':
    unittest.main()
