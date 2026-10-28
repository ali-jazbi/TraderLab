"""Offline, flat/no-Core-orders recovery repair. Never submits broker requests.

Retains every old frame and consumption/execution ledger. Appends a committed
replay of authoritative terminal history, including ticks missed while offline.
An incomplete append fails closed in the native reader. Normal capture continues
to compare ALL raw fields strictly; this is not a relaxed tick cursor.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import struct


def fnv(data, chain=2166136261):
    for byte in data:
        chain = ((chain ^ byte) * 16777619) & 0xffffffff
    return chain


def frames(data):
    result = []; offset = 0; chain = 2166136261
    while offset < len(data):
        if len(data)-offset < 12:
            raise ValueError('torn recovery frame')
        size, expected = struct.unpack_from('<II', data, offset)
        if not 1 <= size <= 16384 or len(data)-offset < size+12:
            raise ValueError('invalid recovery length')
        payload = data[offset+8:offset+8+size]
        commit, = struct.unpack_from('<I', data, offset+8+size)
        chain = fnv(payload, chain)
        if commit != 0x41434A31 or chain != expected:
            raise ValueError('recovery checksum/commit mismatch')
        result.append(payload.decode('utf-8')); offset += size+12
    return result, chain


def replay_rows(rows):
    selected = 1; pending = None; revision = None
    for i, row in enumerate(rows[1:], 1):
        if row.startswith('HISTORY_REBUILD_BEGIN|'):
            if pending is not None or len(row.split('|')[1]) != 64:
                raise ValueError('invalid rebuild begin')
            pending = row.split('|')[1]; selected = i+1
        elif row.startswith('HISTORY_REBUILD_COMMIT|'):
            if pending is None or row.split('|')[1] != pending:
                raise ValueError('invalid rebuild commit')
            revision = pending; pending = None
    if pending is not None:
        raise ValueError('uncommitted rebuild')
    return [r for r in rows[selected:] if r != 'HISTORY_REBUILD_COMMIT|'+str(revision)]


def tick_fields(row):
    f = row.split('|')
    return (int(f[4]), float(f[5]), float(f[6]), float(f[7]),
            int(f[8]), int(f[9]), float(f[10]))


def tick_key(t):
    return t[:5]+t[6:]


def known_emergency(row):
    fields=row.split('|')
    return (len(fields)==10 and fields[:4]==['EMERGENCY','invalid_asof_closed_bar','XAUUSD_o','HALT'] and
            fields[4] in ('0','0.0','0.00000000') and fields[5:7]==[fields[4]]*2 and
            fields[7:9]==['0','0'] and fields[9].isdigit() and int(fields[9])>0)


def validate_revision(old, current):
    """No deletions, quote mutations, reorders or baseline multiplicity changes.

    Only the specifically observed 128-bit metadata revision is eligible for
    this EXPLICIT offline rebuild, never ordinary equality/deduplication.
    Added historical occurrences are replayed, not suppressed or synthesized.
    """
    if not old or not current:
        raise ValueError('empty history')
    if any(t[0] <= 0 or not (0 < t[1] <= t[2]) for t in current):
        raise ValueError('invalid historical tick')
    if any(b[0] < a[0] for a, b in zip(current, current[1:])):
        raise ValueError('history reordering')
    baseline = old[0][0]
    original_seed = [t for t in old if t[0] == baseline]
    new_seed = [t for t in current if t[0] == baseline]
    if len(original_seed) != len(new_seed):
        raise ValueError('startup baseline multiplicity changed')
    j = 0; metadata = 0
    for saved in old:
        while j < len(current) and tick_key(current[j]) != tick_key(saved):
            j += 1
        if j == len(current):
            raise ValueError('recorded market tick missing/mutated/reordered')
        if (current[j][5] ^ saved[5]) & ~128:
            raise ValueError('unreviewed raw flag mutation')
        metadata += current[j][5] != saved[5]; j += 1
    return metadata


def input_row(kind, frame, index, ordinal, tick, bar=None):
    ms,bid,ask,last,volume,flags,real = tick
    values = [kind,frame,index,ordinal,ms,format(bid,'.17g'),format(ask,'.17g'),
              format(last,'.17g'),volume,flags,format(real,'.17g')]
    values += ([int(bar['time'])]+[format(float(bar[k]),'.17g') for k in ('open','high','low','close')]+
               [int(bar[k]) for k in ('tick_volume','spread','real_volume')]) if bar is not None else [0]*8
    return '|'.join(map(str, values))


def build_rows(ticks, bars, seed_count=None):
    seed_ms = ticks[0][0]; rows = []; start = 0
    while start < len(ticks) and ticks[start][0] == seed_ms and (seed_count is None or start < seed_count):
        rows.append(input_row('Z',-1,0,0,ticks[start])); start += 1
    if seed_count is not None and start != seed_count:
        raise ValueError('original startup snapshot changed')
    rows.append('BASE_COMMIT'); cursors = [0]*5; ordinal = start; prev = seed_ms
    for index, tick in enumerate(ticks[start:], 1):
        ordinal = ordinal+1 if tick[0] == prev else 1; prev = tick[0]
        for frame, seconds in enumerate((60,300,900,3600,14400)):
            while cursors[frame] < len(bars[frame]):
                bar = bars[frame][cursors[frame]]
                if (int(bar['time'])+seconds)*1000 > tick[0]:
                    break
                rows.append(input_row('B',frame,index,ordinal,tick,bar)); cursors[frame] += 1
        rows.append(input_row('T',-1,index,ordinal,tick))
    return rows


def encode_revision(rows, chain, revision):
    result = bytearray()
    for row in ['HISTORY_REBUILD_BEGIN|'+revision, *rows, 'HISTORY_REBUILD_COMMIT|'+revision]:
        payload = row.encode(); chain = fnv(payload, chain)
        result += struct.pack('<II',len(payload),chain)+payload+struct.pack('<I',0x41434A31)
    return result


def rebuild(root, namespace, archive):
    import MetaTrader5 as mt5
    root = root.resolve(); expected = Path.home()/'TraderLabDemoForward/BODY80-AGE120-20261025'
    if root != expected.resolve() or namespace != '91496222-2026102501-3212750896':
        raise ValueError('unreviewed deployment identity')
    common = Path(os.environ['APPDATA'])/'MetaQuotes/Terminal/Common/Files'
    paths = {kind: common/f'AUTO_CORE_DEMO-{kind}-{namespace}.dat'
             for kind in ('inputs','consumed','plans','gateway','plans-wal','intents-wal')}
    # Must be run with the EA detached: MT5 holds these files exclusively.
    with paths['inputs'].open('r+b') as stream:
        original = stream.read(); saved, chain = frames(original); old_rows = replay_rows(saved)
        if not saved[0].startswith('AUTO_CORE_INPUT_V1|91496222:LiteFinance-MT5-Demo:XAUUSD_o:2026102501:'):
            raise ValueError('wrong recovery scope')
        ledgers = {k:p.read_bytes() for k,p in paths.items() if k != 'inputs'}
        for kind in ('plans','gateway','consumed'):
            text = ledgers[kind].decode('utf-8-sig')
            if any(line.startswith(('PLAN|','HALT|')) for line in text.splitlines()):
                raise ValueError('existing plan/halt requires broker reconciliation; no rebuild')
            if kind == 'gateway' and any(not line.startswith('SCOPE|') for line in text.splitlines() if line):
                raise ValueError('gateway has execution history; no rebuild')
        for kind, allowed in (('plans-wal',('DAY|','DEMO_BALANCE|')),('intents-wal',())):
            contents,_ = frames(ledgers[kind])
            if contents[0] != saved[0] or any(not line.startswith(allowed) for line in contents[1:]):
                raise ValueError('existing plan/intent/unknown outcome; no rebuild')
        if not mt5.initialize(str(root/'terminal64.exe'), portable=True):
            raise RuntimeError(mt5.last_error())
        try:
            info = mt5.terminal_info(); account = mt5.account_info()
            if (not info.connected or info.trade_allowed or Path(info.data_path).resolve()!=root or
                account.login != 91496222 or account.server != 'LiteFinance-MT5-Demo' or
                account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO or account.currency != 'USD' or
                mt5.positions_get() != () or mt5.orders_get() != ()):
                raise ValueError('need connected bound Demo, Algo OFF, flat account and no pending orders')
            old = [tick_fields(r) for r in old_rows if r.startswith(('Z|','T|'))]
            if not old: raise ValueError('no original baseline')
            quote = mt5.symbol_info_tick('XAUUSD_o')
            date = lambda ms: datetime.fromtimestamp(ms/1000, timezone.utc)
            raw = mt5.copy_ticks_range('XAUUSD_o',date(old[0][0]),date(quote.time_msc)+timedelta(seconds=1),mt5.COPY_TICKS_ALL)
            if raw is None or mt5.last_error()[0] != 1: raise RuntimeError(mt5.last_error())
            ticks = [(int(t['time_msc']),float(t['bid']),float(t['ask']),float(t['last']),int(t['volume']),int(t['flags']),float(t['volume_real']))
                     for t in raw if old[0][0] <= int(t['time_msc']) <= quote.time_msc]
            metadata = validate_revision(old,ticks)
            bars = []; old_bars = {i:{} for i in range(5)}
            for row in old_rows:
                if row.startswith('B|'):
                    f=row.split('|'); old_bars[int(f[1])][int(f[11])] = tuple(map(float,f[12:16]))
            for frame, tf in enumerate((mt5.TIMEFRAME_M1,mt5.TIMEFRAME_M5,mt5.TIMEFRAME_M15,mt5.TIMEFRAME_H1,mt5.TIMEFRAME_H4)):
                if not old_bars[frame]: raise ValueError('missing original closed-bar baseline')
                history = mt5.copy_rates_range('XAUUSD_o',tf,date(min(old_bars[frame])*1000),date(ticks[-1][0]))
                if history is None or mt5.last_error()[0] != 1: raise RuntimeError(mt5.last_error())
                actual = {int(b['time']):tuple(float(b[k]) for k in ('open','high','low','close')) for b in history}
                if any(actual.get(t)!=ohlc for t,ohlc in old_bars[frame].items()):
                    raise ValueError('previously recorded candle OHLC changed; no rebuild')
                bars.append(history)
            seed_count=sum(r.startswith('Z|') for r in old_rows)
            rows = build_rows(ticks,bars,seed_count)
            digest = hashlib.sha256(('\n'.join(rows)+'\n').encode()).hexdigest()
            addition = encode_revision(rows,chain,digest)
            revised,_ = frames(original+addition)
            if replay_rows(revised) != rows: raise ValueError('revision validation failed')
            # Preserve originals before any append. Never reset or replace ledgers.
            archive.mkdir(parents=True,exist_ok=False)
            (archive/paths['inputs'].name).write_bytes(original)
            for kind,data in ledgers.items(): (archive/paths[kind].name).write_bytes(data)
            if any(paths[k].read_bytes()!=data for k,data in ledgers.items()):
                raise ValueError('concurrent ledger change')
            stream.seek(0)
            if stream.read()!=original: raise ValueError('concurrent input journal change')
            stream.seek(0,2); stream.write(addition); stream.flush(); os.fsync(stream.fileno())
            result = dict(revision=digest, original_sha256=hashlib.sha256(original).hexdigest(),
                original_records=len(old), revised_records=len(ticks), metadata_revisions=metadata,
                inserted_pre_cursor_ticks=sum(t[0]<=old[-1][0] for t in ticks)-len(old),
                offline_ticks_replayed=sum(t[0]>old[-1][0] for t in ticks),
                source='MT5_COPY_TICKS_ALL', broker_orders_submitted=0,
                all_execution_and_consumption_ledgers_unchanged=True,
                first_msc=ticks[0][0], last_msc=ticks[-1][0], archive=str(archive))
            (archive/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            return result
        finally:
            mt5.shutdown()


def resume_fixed_fault(root, namespace, archive):
    """Append a receipt for ONLY the reproduced inverted-range restart fault.

    No generic halt reset, order retry, removal of records or daily-budget reset.
    An operator stop, any execution intent or any open exposure forbids repair.
    """
    import MetaTrader5 as mt5
    root=root.resolve()
    if root != (Path.home()/'TraderLabDemoForward/BODY80-AGE120-20261025').resolve() or namespace!='91496222-2026102501-3212750896':
        raise ValueError('unreviewed deployment identity')
    common=Path(os.environ['APPDATA'])/'MetaQuotes/Terminal/Common/Files'
    paths={k:common/f'AUTO_CORE_DEMO-{k}-{namespace}.dat' for k in ('inputs','consumed','gateway','plans-wal','intents-wal')}
    saved={k:p.read_bytes() for k,p in paths.items()}
    inputs,_=frames(saved['inputs']); replay_rows(inputs)
    revisions=[r.split('|')[1] for r in inputs if r.startswith('HISTORY_REBUILD_BEGIN|')]
    if not revisions: raise ValueError('verified history rebuild required')
    revision=revisions[-1]; cause='invalid_asof_closed_bar'
    consumed=saved['consumed'].decode('utf-8-sig').splitlines()
    halts=[r for r in consumed if r.startswith('HALT|')]
    if not halts or any(not r.startswith('HALT|'+cause+'|') for r in halts) or any(r.startswith('RESUME|') for r in consumed):
        raise ValueError('not an exclusively technical halt')
    plans,_=frames(saved['plans-wal'])
    if any(not r.startswith(('DAY|','DEMO_BALANCE|')) for r in plans[1:]):
        raise ValueError('existing plans/risk halt; no resume')
    intents,chain=frames(saved['intents-wal'])
    if not intents[1:] or any(not known_emergency(r) for r in intents[1:]):
        raise ValueError('other emergency/execution/unknown outcome; no resume')
    if any(not r.startswith('SCOPE|') and not known_emergency(r)
           for r in saved['gateway'].decode('utf-8-sig').splitlines() if r):
        raise ValueError('broker execution ledger has another outcome')
    if not mt5.initialize(str(root/'terminal64.exe'),portable=True): raise RuntimeError(mt5.last_error())
    try:
        t=mt5.terminal_info(); a=mt5.account_info()
        if (not t.connected or t.trade_allowed or Path(t.data_path).resolve()!=root or a.login!=91496222 or
            a.server!='LiteFinance-MT5-Demo' or a.trade_mode!=mt5.ACCOUNT_TRADE_MODE_DEMO or
            mt5.positions_get()!=() or mt5.orders_get()!=()): raise ValueError('resume requires flat bound Demo and Algo OFF')
        # Exclusive handles are held by the EA. Opening both before any append
        # also rejects a concurrent EA; the gateway receipt is committed first,
        # leaving the controller halted if the second write is interrupted.
        with paths['intents-wal'].open('r+b') as ledger, paths['consumed'].open('r+b') as consumption, paths['gateway'].open('r+b') as gateway:
            if any(paths[k].read_bytes()!=data for k,data in saved.items()): raise ValueError('concurrent journal change')
            archive.mkdir(parents=True,exist_ok=False)
            for k,data in saved.items(): (archive/paths[k].name).write_bytes(data)
            now=int(datetime.now(timezone.utc).timestamp())
            row=f'RECOVERY_RESUME|{cause}|XAUUSD_o|RESUME_{revision}|0.00000000|0.00000000|0.00000000|0|0|{now}'.encode()
            next_chain=fnv(row,chain)
            ledger.seek(0,2); ledger.write(struct.pack('<II',len(row),next_chain)+row+struct.pack('<I',0x41434A31))
            ledger.flush(); os.fsync(ledger.fileno())
            gateway.seek(0,2); gateway.write(row+b'\r\n'); gateway.flush(); os.fsync(gateway.fileno())
            consumption.seek(0,2); consumption.write(f'RESUME|{cause}|{revision}\r\n'.encode())
            consumption.flush(); os.fsync(consumption.fileno())
            result=dict(resumed_fixed_fault=cause,revision=revision,broker_orders_submitted=0,original_records_preserved=True)
            (archive/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            return result
    finally: mt5.shutdown()


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal-root',type=Path,required=True)
    parser.add_argument('--namespace',required=True)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--resume-fixed-fault',action='store_true')
    args=parser.parse_args()
    operation=resume_fixed_fault if args.resume_fixed_fault else rebuild
    print(json.dumps(operation(args.terminal_root,args.namespace,args.archive),indent=2))
