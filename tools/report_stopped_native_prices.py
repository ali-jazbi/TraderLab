"""Reconstruct interrupted Native fills, without inventing absent deal costs."""
from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict
import hashlib
import json
import re

OUT = Path('docs/reports/long-history-20261023')
evidence = OUT / 'partial-native-trade-evidence.txt'
text = evidence.read_text(encoding='utf-8-sig')
deals = {}
exits = {}
for line in text.splitlines():
    m = re.search(r'(2026\.\d\d\.\d\d \d\d:\d\d:\d\d).*deal #(\d+) (buy|sell) ([\d.]+) XAUUSD_o at ([\d.]+) done', line)
    if m:
        at, ticket, side, volume, price = m.groups()
        assert int(ticket) not in deals
        deals[int(ticket)] = dict(time=at, side=side, volume=volume, price=price)
    m = re.search(r'(?:stop loss|take profit) triggered #(\d+).*\[#(\d+) ', line)
    if m:
        entry, close = map(int, m.groups())
        assert close not in exits
        exits[close] = entry
gateway = OUT / 'partial-gateway-journal.txt'
capability = json.loads((OUT/'partial-broker-capability.json').read_text(encoding='utf-8'))
assert capability['account_currency'] == 'USD' and D(str(capability['contract_size'])) == D(100)
ids = []
setup_by_intent = {}
for line in gateway.read_text().splitlines():
    cells = line.split('|')
    if len(cells) > 3 and cells[3] == 'INTENT' and cells[0].startswith('EX'):
        ids.append(cells[0])
        setup_by_intent[cells[0]] = cells[1].rsplit(':', 2)[0]
entry_tickets = sorted(set(deals) - set(exits))
# The final INTENT was rejected (Market closed), with no Native deal.
assert len(ids) == len(entry_tickets) + 1
assert 'failed market buy 0.01 XAUUSD_o' in text and '[Market closed]' in text
intent_by_ticket = dict(zip(entry_tickets, ids[:-1]))
assert set(exits.values()) == set(entry_tickets)
assert len(deals) == 24 and len(entry_tickets) == 12
rows = []
setups = defaultdict(lambda: D(0))
months = defaultdict(lambda: D(0))
balance = peak = D('1000')
max_dd = max_dd_pct = D(0)
for close in sorted(exits):
    ticket = exits[close]
    a, b = deals[ticket], deals[close]
    assert a['side'] != b['side'] and a['volume'] == b['volume']
    # Runtime BROKER_CAPABILITY_SNAPSHOT: contract_size=100, account_currency=USD.
    pnl = (D(b['price']) - D(a['price'])) * (1 if a['side'] == 'buy' else -1) * D(a['volume']) * D(str(capability['contract_size']))
    setup = setup_by_intent[intent_by_ticket[ticket]]
    setups[setup] += pnl
    month = b['time'][:7].replace('.', '-')
    months[month] += pnl
    balance += pnl
    peak = max(peak, balance)
    max_dd = max(max_dd, peak-balance)
    max_dd_pct = max(max_dd_pct, (peak-balance)/peak*100)
    rows.append(dict(entry_ticket=ticket, exit_ticket=close, setup=setup,
                     entry=a, exit=b, price_pnl_usd=str(pnl)))
positive = sum((v for v in setups.values() if v > 0), D(0))
negative = -sum((v for v in setups.values() if v < 0), D(0))
result = dict(verdict='INSUFFICIENT_EVIDENCE', native_completed=False,
              measured_from='2026-04-24', stopped_server_time='2026-08-06T23:48:58.917',
              closed_positions=len(rows), actual_deals=len(deals), independent_setup_ids=len(setups),
              open_positions_reconciled_from_native_log=0,
              winning_setups=sum(v > 0 for v in setups.values()),
              losing_setups=sum(v < 0 for v in setups.values()),
              price_based_setup_win_rate_percent='60',
              price_pnl_usd=str(sum(setups.values(), D(0))),
              positive_setup_price_pnl_usd=str(positive), negative_setup_price_pnl_usd=str(-negative),
              price_based_setup_profit_factor=str(positive/negative),
              gross_closed_balance_drawdown_usd=str(max_dd),
              gross_closed_balance_drawdown_percent=str(max_dd_pct),
              net_profit_after_all_costs_usd=None, equity_drawdown=None,
              commission=None, swap=None, fees=None,
              caveat='Actual executed entry/exit prices include realized spread and slippage; commissions, swap and fees were not recovered. Price PnL, PF, WR and balance drawdown are not net Native statistics. Execution halted on 2026-05-07 after Market closed; later zero activity is not evidence of strategy performance.',
              months=[dict(month=m, closed_price_pnl_usd=str(months[m]),
                           valid_active_full_month=False,
                           note='Execution halted May 7; June onward has no new dispatches in preserved gateway journal.' if m >= '2026-05' else 'Measurement begins April 24.')
                      for m in ['2026-04','2026-05','2026-06','2026-07','2026-08']],
              setup_price_pnl_usd={k:str(v) for k,v in setups.items()}, positions=rows,
              evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
              gateway_sha256=hashlib.sha256(gateway.read_bytes()).hexdigest())
(OUT/'partial-price-performance.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('positions','setup_price_pnl_usd')}, indent=2))
