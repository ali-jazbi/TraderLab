"""Read-only audit of the October19 owner feedback. Never selects trades or fixes a feed."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROBOT = 'M1:BUY:2026-10-13T17:49:00+00:00'
POSITIVE_PROXY = 'M1:BUY:2026-10-13T17:24:00+00:00'
NEGATIVE_PROXY = 'M1:BUY:2026-10-13T18:19:00+00:00'
GAPS = ('M1:BUY:2026-10-13T18:05:00+00:00', 'M1:BUY:2026-10-13T18:06:00+00:00')
FIELDS = ('open', 'high', 'low', 'close')


def at(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def alignment(bars, feedback):
    """Rank joint OHLC correspondence; no numerical threshold can approve equivalence."""
    day = {at(b['opened_at']): b for b in bars if b['opened_at'].startswith('2026-10-13')}
    positive, negative = feedback['positive'], feedback['negative']
    separation = at(negative['displayed_time']) - at(positive['displayed_time'])
    ranked = []
    for opened, first in day.items():
        second = day.get(opened + separation)
        if second is None:
            continue
        delta = [D(s['ohlc'][k])-D(b[k]) for s, b in ((positive, first), (negative, second)) for k in FIELDS]
        ranked.append(dict(positive_native_utc=opened.isoformat(), negative_native_utc=second['opened_at'],
                           absolute_ohlc_error=str(sum(map(abs, delta))), screenshot_minus_native=list(map(str, delta))))
    ranked.sort(key=lambda r: D(r['absolute_ohlc_error']))
    return dict(status='UNCONFIRMED_FEED_CORRESPONDENCE', timezone_confirmed=False,
                price_equivalence_confirmed=False, exact_joint_matches=sum(D(r['absolute_ohlc_error']) == 0 for r in ranked),
                common_offsets_examined=len(ranked), best_correspondences=ranked[:5],
                warning='Both screenshots constrain the same55-minute separation. Ranking is diagnostic, never price correction or owner-label transfer.')


def audit(capture, feedback):
    references = [json.loads((ROOT/'docs/reports/auto-core-discovery-20261018'/n/'results.json').read_text())[0]
                  for n in ('final-training', 'final-holdout')]
    selected = {}
    for r in references:
        for e in r['events']:
            if e['event'] == 'CORE_TESTER_DISPATCH_RESULT' and e['submitted']:
                for key in e['frozen_group']['selected_bos_ids'].split(';'):
                    selected[key] = e['setup_id']
    ids = set(selected) | {ROBOT, POSITIVE_PROXY, NEGATIVE_PROXY}
    bars, events, ticks, counts = [], [], [], Counter()
    all_bars = {}
    digest = hashlib.sha256()
    for line in capture.open('rb'):
        digest.update(line)
        if b'"event":"TICK"' in line:
            server = line.split(b'"server_time":"', 1)[1][:23]
            if b'2026-10-13T20:10' <= server < b'2026-10-13T22:00' or b'2026-10-14T03:59:55' <= server < b'2026-10-14T04:00:03':
                ticks.append(json.loads(line))
            continue
        if b'"event":"BOS_TRACKER_CLOSED_BAR"' in line:
            r = json.loads(line); all_bars[(r['timeframe'], at(r['opened_at']))] = r
            if r['timeframe'] == 'M1' and '2026-10-13' <= r['opened_at'][:10] <= '2026-10-14': bars.append(r)
        if b'"event":"CORE_BOS_' in line and b'"timeframe":"M1"' in line:
            r = json.loads(line)
            if '2026-10-13' <= r['server_time'][:10] <= '2026-10-14': counts[(r['server_time'][:10], r['event'])] += 1
        if any(key.encode() in line for key in ids) or any(key.encode() in line for key in GAPS):
            if b'"event":"TESTER_CORE_DEAL"' not in line: events.append(json.loads(line))
    if digest.hexdigest() != references[1]['raw_sha256']: raise ValueError('Capture differs from the verified native holdout')
    index = {at(b['opened_at']): b for b in bars}
    cases = {}
    for key in (ROBOT, POSITIVE_PROXY, NEGATIVE_PROXY):
        opened = at(key.split(':', 2)[2]); b = index[opened]
        qualified = next((e for e in events if e.get('bos_id') == key and e['event'] == 'CORE_BOS_CANDIDATE_QUALIFIED'), None)
        qbar = index[at(qualified['time']).replace(second=0, microsecond=0)-timedelta(minutes=1)] if qualified else None
        relevant = [e for e in events if e.get('bos_id') == key and (e['event'] != 'CORE_SETUP_CANDIDATE' or e.get('fvg_id') in GAPS)]
        returned = next((e for e in relevant if e['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN'
                         and e['break_quote'] == e['retest_quote'] == 'bid'), None)
        return_ticks = [t for t in ticks if returned and abs((at(t['time'])-at(returned['time'])).total_seconds()) <= 3]
        observed = [t for t in ticks if opened <= at(t['time']) < opened+timedelta(minutes=1)]
        tick_ohlc = dict(zip(FIELDS, (observed[0]['bid'], str(max(D(t['bid']) for t in observed)),
                                     str(min(D(t['bid']) for t in observed)), observed[-1]['bid'])))
        if any(D(tick_ohlc[k]) != D(b[k]) for k in FIELDS): raise ValueError('Captured candle differs from actual Bid ticks')
        cases[key] = dict(candle=b, prior=index.get(opened-timedelta(minutes=1)), following=index.get(opened+timedelta(minutes=1)),
                          qualification_candle=qbar, qualification_predicate=bool(qbar and D(qbar['close']) < D(b['low'])),
                          events=relevant, tick_ohlc=tick_ohlc, tick_ohlc_verified=True, observed_tick_count=len(observed),
                          local_return_tick_window=return_ticks,
                          owner_label_transfer='NOT_PERMITTED_WITHOUT_FEED_MATCH')
    similarities = []
    for key, setup in selected.items():
        tf, side, opened = key.split(':', 2); opened = at(opened)
        b = all_bars.get((tf, opened)); step = {'M1':60, 'M5':300, 'M15':900, 'H1':3600, 'H4':14400}[tf]
        prior = all_bars.get((tf, opened-timedelta(seconds=step)))
        if not b or not prior: raise ValueError('Missing actual selected-candle context')
        not_prior_extreme = D(b['high']) <= D(prior['high']) if side == 'BUY' else D(b['low']) >= D(prior['low'])
        similarities.append(dict(bos_id=key, setup=setup, candle=b, prior=prior,
                                 not_above_prior_high_or_below_prior_low=not_prior_extreme,
                                 owner_validity='UNKNOWN; this is NOT an approved pivot rejection rule'))
    entry = next(e for e in references[1]['events'] if e.get('setup_id') == 'EXPERIMENTAL:'+GAPS[0] and e['submitted'])
    deal_ids = {p['id'] for p in json.loads((ROOT/'docs/reports/auto-core-discovery-20261018/final-holdout/performance.json').read_text())[0]['actual_positions'] if p['setup'] == entry['setup_id']}
    actual_deals = {p: ds for p, ds in references[1]['positions'].items() if any(d['comment'].removeprefix('TL:') in deal_ids for d in ds)}
    proof = dict(base_commit='375a1e21234deae17d5c4718253ba380148a1115', raw=str(capture), raw_sha256=digest.hexdigest(),
                 feed_symbol='XAUUSD_o', server_utc_offset_seconds=10800, iran_utc_offset_seconds=12600,
                 feedback=feedback, alignment=alignment(bars, feedback), cases=cases, actual_dispatch=entry,
                 closed_m1_window=[b for b in bars if '2026-10-13T17:10' <= b['opened_at'] < '2026-10-13T18:31'],
                 actual_native_deals=actual_deals,
                 nearby_gaps=[e for e in events if e.get('fvg_id') in GAPS and e['event'] in ('EXPERIMENTAL_GROUP_FINALIZED', 'CORE_FVG_VALIDITY_CHANGED')],
                 m1_counts=[dict(server_day=d, event=e, count=n) for (d,e),n in sorted(counts.items())],
                 generated_m1_candidates=dict(count=2*len(bars), bars=len(bars), scope='Two seeds per observed M1 close; diagnostic seeds are not valid structural BOS.'),
                 other_executed_setups_context=similarities,
                 execution_or_strategy_changes=False, demo='LOCKED', reverse_real_contest='FORBIDDEN')
    return proof, bars, ticks


def plot(proof, bars, ticks, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as md
    from matplotlib.patches import Rectangle
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    def server(iso): return at(iso).replace(tzinfo=None)+timedelta(hours=3)
    def candles(ax, start, end):
        chosen = [b for b in bars if start <= server(b['opened_at']).isoformat()[:19] <= end]
        for b in chosen:
            x=md.date2num(server(b['opened_at']));o,h,l,c=map(lambda k:float(b[k]), FIELDS)
            color='#20856c' if c>=o else '#cc4d52'
            ax.vlines(x,l,h,color=color,linewidth=1)
            ax.add_patch(Rectangle((x-.32/1440,min(o,c)),.64/1440,max(abs(c-o),.015),facecolor=color,edgecolor=color))
        ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M'));ax.grid(alpha=.15);ax.set_ylabel('XAUUSD_o Bid')
        return chosen
    fig=plt.figure(figsize=(17,10),layout='constrained');gs=fig.add_gridspec(2,2,height_ratios=[1.45,1])
    ax=fig.add_subplot(gs[0,:]);candles(ax,'2026-10-13T20:10:00','2026-10-13T21:55:00')
    for key,label,color,y in ((POSITIVE_PROXY,'20:24 server: owner-positive PROXY, feed unconfirmed','#2367b1',4166),
                              (ROBOT,'20:49 server =21:19 Iran: ACTUAL ROBOT','#a73238',4168),
                              (NEGATIVE_PROXY,'21:19 server: screenshot1 PROXY; native REJECTED','#744f9f',4170)):
        b=proof['cases'][key]['candle'];x=server(b['opened_at']);ax.axvline(x,color=color,alpha=.5)
        ax.annotate(label,xy=(x,float(b['high'])),xytext=(x,y),ha='left',fontsize=9,color=color,arrowprops={'arrowstyle':'->','color':color})
    for available,low,high,color,label in [('21:16',4151.58,4154.20,'#48a9bd','FVG1'),('21:17',4154.70,4159.96,'#d69c39','FVG2')]:
        begin=md.date2num(datetime.fromisoformat('2026-10-13T'+available+':00'));end=md.date2num(datetime(2026,10,13,21,55))
        ax.add_patch(Rectangle((begin,low),end-begin,high-low,facecolor=color,alpha=.16));ax.text(end,low,label,ha='right',color=color)
    for available,low,high,color,label in [('21:16',4154.20,4161.44,'#48a9bd','OB1 C3'),('21:17',4159.96,4162.94,'#d69c39','OB2 C3')]:
        begin=md.date2num(datetime.fromisoformat('2026-10-13T'+available+':00'));end=md.date2num(datetime(2026,10,13,21,55))
        ax.add_patch(Rectangle((begin,low),end-begin,high-low,fill=False,edgecolor=color,linestyle='--'));ax.text(end,high,label,ha='right',va='bottom',color=color)
    ax.set_ylim(4146,4171.5);ax.set_title('Genuine M1 candles, October13 2026 | SERVER UTC+03 | Iran = server+00:30\nShading starts at CONFIRMED availability; screenshot proxies are NOT accepted feed matches')
    for n,key,start,end in ((0,ROBOT,'20:46','20:54'),(1,POSITIVE_PROXY,'20:21','20:29')):
        a=fig.add_subplot(gs[1,n]);candles(a,'2026-10-13T'+start+':00','2026-10-13T'+end+':00')
        b=proof['cases'][key]['candle'];q=proof['cases'][key]['qualification_candle'];x=server(b['opened_at'])
        a.axvline(x,color='#333',linestyle=':');a.axhline(float(b['low']),color='#777',linestyle='--',label='Candidate Low')
        a.scatter(server(q['opened_at']),float(q['close']),s=60,color='#264ea0',zorder=5,label='Qualification Close')
        a.set_title(f"{'Actual robot' if n==0 else 'Owner-positive PROXY'} | H={b['high']} L={b['low']}\nQualification Close={q['close']} < Low; no pivot rule inferred",fontsize=10);a.legend(loc='lower left',fontsize=8)
    fig.savefig(out/'candles-server-time.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(15,10),layout='constrained')
    windows=[('2026-10-13T21:05:58','2026-10-13T21:06:00',4153.51,'October13 actual robot: outbound break is NOT entry'),
             ('2026-10-13T21:06:13','2026-10-13T21:06:22',4157.99,'October13 positive proxy: first return consumed BEFORE FVG formation/confirmation'),
             ('2026-10-14T03:59:59','2026-10-14T04:00:02.500',4153.51,'October14 actual robot: Bid crossing, actual Ask fill4153.64 at04:00:01.473')]
    for a,(start,end,ref,title) in zip(axes,windows):
        ts=[t for t in ticks if start<=t['server_time']<=end]
        for lane,color in [('bid','#227ba5'),('ask','#bb5b3a')]:a.plot([datetime.fromisoformat(t['server_time'])for t in ts],[float(t[lane])for t in ts],'.-',ms=3,lw=.7,color=color,label=lane)
        a.axhline(ref,ls='--',color='#333',label=f'Existing entry reference {ref:.2f}')
        if ref==4157.99:
            a.axhline(4157.49,ls=':',color='#744f9f',label='BOS wick4157.49; NOT a new entry rule')
            a.axvline(datetime(2026,10,13,21,6,14,504000),ls=':',color='#777',label='Actual Bid break21:06:14.504')
            a.scatter(datetime(2026,10,13,21,6,16,897000),4157.99,s=65,color='#111',zorder=6,label='Consumed first return21:06:16.897')
        if start.startswith('2026-10-14'):a.scatter(datetime(2026,10,14,4,0,1,473000),4153.64,s=100,marker='*',color='#111',zorder=6,label='Native deal fill')
        a.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S.%f'));a.tick_params(axis='x',labelsize=8);a.set_title(title);a.set_ylabel('Observed quote');a.grid(alpha=.2);a.legend(fontsize=8)
    fig.suptitle('SERVER UTC+03 | Only captured ticks; connecting lines do not create quotes or fills\nPositive proxy FVG geometry available21:08:00.142;10-following-bar confirmation21:17:00.154',fontsize=12)
    fig.savefig(out/'quote-chronology.png',dpi=160);plt.close(fig)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path);p.add_argument('--plot',action='store_true');a=p.parse_args()
    feedback=json.loads((ROOT/'docs/sources/owner-bos-feedback-20261019.json').read_text())
    proof,bars,ticks=audit(a.capture,feedback);a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'evidence.json').write_text(json.dumps(proof,indent=2))
    if a.plot:plot(proof,bars,ticks,a.out)
    print(json.dumps(dict(alignment=proof['alignment'],m1_counts=proof['m1_counts']),indent=2))
