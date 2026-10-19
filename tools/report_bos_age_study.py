"""Reconcile six NEW real-tick Tester runs; never subtract old trades or invent fills."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

from tools.compare_core_market_prefix import fingerprint
from tools.report_core_policy_runs import audit
from tools.report_discovery_study import analyze

ROOT = Path(__file__).resolve().parents[1]
OWNER_BOS = 'M1:BUY:2026-10-13T17:16:00+00:00'


def deal_signature(result):
    return sorted((d['deal_time_msc'], d['entry_kind'], d['price'], d['volume'], d['net'], d['reason'], d['comment'])
                  for rows in result['positions'].values() for d in rows)


def calendar_proof(folder, original, end):
    actual = folder/'native-files/TraderLab-auto-tester-calendar.csv'
    before = Path(original['archive'])/'native-files/TraderLab-auto-tester-calendar.csv'
    a, b = actual.read_text().splitlines(), before.read_text().splitlines()
    relevant = lambda rows: [s for s in rows if s.startswith('NEWS|') or
                            (s.startswith('DAY|') and s.split('|')[1] < end)]
    if relevant(a) != relevant(b) or a[0].split('|')[:3] != b[0].split('|')[:3]:
        raise ValueError('Calendar rules changed inside warm-up/measured window')
    return dict(warmup_and_measured_days_identical=True, all_news_identical=True,
                actual_sha256=hashlib.sha256(actual.read_bytes()).hexdigest(),
                original_sha256=hashlib.sha256(before.read_bytes()).hexdigest(),
                scope_note='Existing reviewed packet extends only future coverage after the training window; no evaluated day or news changes')


def observations(raw, window):
    structural = hashlib.sha256(); count = Counter(); rejected = []; example = []
    names = {'CORE_BOS_CANDIDATE_QUALIFIED', 'CORE_BOS_CONFIRMED', 'CORE_BOS_REJECTED',
             'BOS_INTRABAR_BREAK', 'BOS_FIRST_DIRECTIONAL_RETURN', 'EXPERIMENTAL_GROUP_FINALIZED'}
    with raw.open('rb') as source:
        for line in source:
            if b'"event":"TICK"' in line:
                continue
            if not any(s in line for s in (b'CORE_BOS_', b'BOS_INTRABAR_BREAK', b'BOS_FIRST_DIRECTIONAL_RETURN',
                                           b'EXPERIMENTAL_GROUP_FINALIZED', b'EXPERIMENTAL_FIRST_RETURN', OWNER_BOS.encode())):
                continue
            r = json.loads(line)
            if r['event'] in names:
                canonical = {k:v for k,v in r.items() if k != 'seq'}
                structural.update((json.dumps(canonical, sort_keys=True, separators=(',', ':'))+'\n').encode())
                count[r['event']] += 1
            if r.get('bos_id') == OWNER_BOS:
                example.append(r)
            if r['event'] == 'EXPERIMENTAL_FIRST_RETURN' and window[0] <= r['server_time'] < window[1] and r['reason'].startswith('EXPERIMENTAL_M1_BOS_AGE_'):
                if r['age_allowed'] or r['signal_ready']:
                    raise ValueError('Age rejection has contradictory signal state')
                rejected.append(r)
    return dict(structural_sha256=structural.hexdigest(), counts=dict(count),
                first_return_age_rejections=rejected, owner2016_events=example)


def verify_actual_ages(result, performance):
    cap = int(result['inputs']['InpExperimentalM1MaxAgeMinutes'])
    proof = []
    for e in result['events']:
        if e['event'] != 'CORE_TESTER_DISPATCH_RESULT' or not e['submitted']:
            continue
        tf, _, candle = e['bos_id'].split(':', 2)
        born = int(datetime.fromisoformat(candle).timestamp()*1000)+10800000
        actual = e['actual_signal_quote']['time_msc']-born
        if actual != e['bos_age_ms'] or e['m1_max_age_minutes'] != cap:
            raise ValueError('Age metadata differs from genuine signal tick')
        if cap and tf == 'M1' and not 0 <= actual <= cap*60000:
            raise ValueError('Expired M1 order was submitted')
        proof.append(dict(bos_id=e['bos_id'], setup=e['setup_id'], server_time=e['server_time'],
                          age_ms=actual, timeframe=tf, cap_minutes=cap))
    # Each actual deal fill, including leg2, must independently satisfy the age cap.
    for position in performance['actual_positions']:
        key = position['position']
        rows = result['positions'].get(key, result['positions'].get(str(key), []))
        d = next(d for d in rows if d['entry_kind'] == 0)
        dispatch = [e for e in result['events'] if e['event'] == 'CORE_TESTER_DISPATCH_RESULT' and
                    e['submitted'] and e['setup_id'] == position['setup'] and
                    e['actual_signal_quote']['time_msc'] == d['deal_time_msc']]
        if len(dispatch) != 1:
            raise ValueError('Actual fill lacks its unique current-tick dispatch')
        tf, _, candle = dispatch[0]['bos_id'].split(':', 2)
        born = int(datetime.fromisoformat(candle).timestamp()*1000)+10800000
        if cap and tf == 'M1' and not 0 <= d['deal_time_msc']-born <= cap*60000:
            raise ValueError('Actual M1 fill exceeded its age cap')
    return proof


def report(archive, out, label):
    if label not in ('training', 'holdout'):
        raise ValueError('Fixed requested windows only')
    start, end = ('2026-10-07', '2026-10-10') if label == 'training' else ('2026-10-14', '2026-10-17')
    original = json.loads((ROOT/f'docs/reports/auto-core-discovery-20261018/final-{label}/results.json').read_text())[0]
    old_raw = next((Path(original['archive'])/'native-files').glob('*.jsonl'))
    if out.exists() and any(out.iterdir()):
        raise ValueError('Refuse overwriting a prior result directory')
    out.mkdir(parents=True, exist_ok=True)
    print('Fingerprint original '+label, flush=True)
    cached = out.parent/f'{label}-source-fingerprint.json'
    if cached.exists():
        source = json.loads(cached.read_text())
        if source['source_raw_sha256'] != original['raw_sha256']:
            raise ValueError('Original fingerprint cache belongs to another source')
        reference = source['market']
    else:
        reference = fingerprint(old_raw)
    results, performances = [], []
    base_structure = None
    for cap in (0, 60, 120):
        folder = archive/f'{label}-AGE{cap}'
        print('Audit '+folder.name, flush=True)
        result = audit(folder, start, end)
        if int(result['inputs']['InpExperimentalM1MaxAgeMinutes']) != cap:
            raise ValueError('Wrong tested age input')
        allowed_changes = {'InpLogFile', 'InpExperimentalM1MaxAgeMinutes'}
        left = {k:v for k,v in result['inputs'].items() if k not in allowed_changes}
        right = {k:v for k,v in original['inputs'].items() if k not in allowed_changes}
        if left != right:
            raise ValueError('Non-age study input changed')
        performance = analyze(result)
        proof = verify_actual_ages(result, performance)
        calendar = calendar_proof(folder, original, end)
        raw = next((folder/'native-files').glob('*.jsonl'))
        market = fingerprint(raw)
        if market != reference:
            raise ValueError('Genuine ordered market history differs from baseline')
        diagnostic = observations(raw, result['measured_server_window'])
        if cap == 0:
            if deal_signature(result) != deal_signature(original):
                raise ValueError('AGE0 changed original actual deals')
            base_structure = diagnostic['structural_sha256']
        elif diagnostic['structural_sha256'] != base_structure:
            raise ValueError('Age policy changed detection/grouping/consumption history')
        target = out/f'AGE{cap}'
        target.mkdir()
        for f in folder.iterdir():
            if f.suffix.lower() in ('.html', '.png', '.set', '.ini'):
                shutil.copy2(f, target/f.name)
        check = dict(cap_minutes=cap, original_market_identical=True, age0_original_deals_identical=cap == 0,
                     market=market, calendar=calendar, **diagnostic, submitted_ages=proof)
        performance['m1_max_age_minutes'] = cap
        (target/'verification.json').write_text(json.dumps(check, indent=2)+'\n')
        # Persist each completed run before moving to the next large raw file.
        (target/'results.json').write_text(json.dumps([result], indent=2)+'\n')
        (target/'performance.json').write_text(json.dumps([performance], indent=2)+'\n')
        results.append(result); performances.append(performance)
        print(folder.name, performance['executed_unique_setups'], performance['position_performance'],
              performance['native_report_metrics']['Equity Drawdown Maximal:'], flush=True)
    (out/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    (out/'performance.json').write_text(json.dumps(performances, indent=2)+'\n')
    (out/'market-reference.json').write_text(json.dumps(reference, indent=2)+'\n')
    return performances


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--window', required=True, choices=('training', 'holdout'))
    args = parser.parse_args()
    report(args.archive, args.out, args.window)
