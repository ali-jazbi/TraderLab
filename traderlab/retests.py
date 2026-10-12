"""Chronological BOS evidence; first-return reading, not new owner confirmation.

No setup promotion. Unknown quote policies are separate diagnostic lanes.
"""
from dataclasses import dataclass, field

from .strategy import direction, entry_reference, number


@dataclass
class FirstReturn:
    side: str
    reference: object
    previous: object = None
    outbound_at: object = None
    result: dict | None = None

    def advance(self, price, at, order, tick_index=None):
        if self.result is not None:
            return None
        sign = direction(self.side)
        beyond = sign * (price - self.reference) > 0
        if beyond and self.outbound_at is None:
            self.outbound_at = at
        if (self.previous is not None and self.outbound_at is not None and
                sign * (self.previous - self.reference) > 0 and
                sign * (price - self.reference) <= 0):
            self.result = {'first_return_at': at, 'first_return_order': order,
                           'tick_index': tick_index, 'previous_quote': self.previous,
                           'observed_quote': price, 'exact_quote': price == self.reference,
                           'outbound_at': self.outbound_at, 'consumed': True}
            return self.result
        self.previous = price
        return None


@dataclass
class History:
    bar: object
    side: str
    qualified_at: object = None
    lanes: dict = field(default_factory=dict)

    @property
    def level(self):
        return self.bar.high if self.side == 'BUY' else self.bar.low


class HistoricalRetests:
    def __init__(self, break_quote=None):
        if break_quote not in (None, 'bid', 'ask'):
            raise ValueError('observation_price_side must be bid, ask or null')
        self.break_quote = break_quote
        self.histories = {}
        self.active = {}

    @staticmethod
    def identity(timeframe, side, candidate_at):
        return f'{timeframe}:{side}:{candidate_at.isoformat()}'

    def accept_bar(self, bar, observations):
        # Bars become usable at delivery, never at their historical opening time.
        for o in observations:
            if o['event'] not in ('BOS_CANDIDATE_QUALIFIED', 'BOS_CONFIRMED', 'BOS_REJECTED'):
                continue
            key = self.identity(o['timeframe'], o['side'], o['candidate_at'])
            h = self.histories.get(key)
            if h is None:
                continue
            if o['event'] == 'BOS_CANDIDATE_QUALIFIED':
                h.qualified_at = bar.available
                for lane in h.lanes.values():
                    if lane['state'] == 'CANDIDATE':
                        lane['state'] = 'QUALIFIED'
            else:
                # A closed wick proves a past break, NOT a new current tick break.
                for lane in h.lanes.values():
                    if lane['state'] in ('CANDIDATE', 'QUALIFIED'):
                        lane.update(state='BLOCKED', reason='intrabar_break_unobserved')
                o['intrabar_history'] = self.snapshot(key)
        for side in ('BUY', 'SELL'):
            key = self.identity(bar.timeframe, side, bar.opened)
            h = History(bar, side)
            for quote in ((self.break_quote,) if self.break_quote else ('bid', 'ask')):
                h.lanes[quote] = {'state': 'CANDIDATE', 'break_at': None,
                                 'returns': {q: FirstReturn(side, entry_reference(side, h.level))
                                             for q in ('bid', 'ask')}}
            self.histories[key] = h
            self.active[key] = h

    def snapshot(self, key):
        h = self.histories.get(key)
        if h is None:
            return None
        return {q: {'state': lane['state'], 'break_at': lane['break_at'],
                    'reason': lane.get('reason'),
                    'returns': {p: r.result for p, r in lane['returns'].items()}}
                for q, lane in h.lanes.items()}

    def accept_tick(self, tick, at, order):
        prices = {q: number(tick[q]) for q in ('bid', 'ask')}
        emitted = []
        finished = []
        for key, h in self.active.items():
            for quote, lane in h.lanes.items():
                if lane['state'] == 'BLOCKED':
                    continue
                if lane['break_at'] is None:
                    if direction(h.side) * (prices[quote] - h.level) <= 0:
                        continue
                    if h.qualified_at is None:
                        lane.update(state='BLOCKED', reason='tick_break_before_qualification')
                        continue
                    lane.update(state='BROKEN', break_at=at)
                    emitted.append({'event': 'BOS_INTRABAR_BREAK', 'rule': 'BOS-01/BOS-02',
                                    'bos_id': key, 'side': h.side, 'timeframe': h.bar.timeframe,
                                    'candidate_at': h.bar.opened, 'break_at': at,
                                    'qualified_at': h.qualified_at, 'break_quote': quote,
                                    'observed_quote': prices[quote], 'level': h.level,
                                    'tick_index': tick.get('tick_index'), 'diagnostic_only': True})
                for retest_quote, retest in lane['returns'].items():
                    outbound = retest.outbound_at
                    result = retest.advance(prices[retest_quote], at, order, tick.get('tick_index'))
                    if outbound is None and retest.outbound_at is not None:
                        lane['state'] = 'OUTBOUND'
                    if result:
                        emitted.append({'event': 'BOS_FIRST_DIRECTIONAL_RETURN', 'rule': 'TOUCH-01',
                                        'bos_id': key, 'side': h.side, 'timeframe': h.bar.timeframe,
                                        'break_quote': quote, 'retest_quote': retest_quote,
                                        'entry_reference': retest.reference, **result,
                                        'reason': 'TODO_STRATEGY_UNRESOLVED:association_and_activation',
                                        'diagnostic_only': True})
                if all(r.result is not None for r in lane['returns'].values()):
                    lane['state'] = 'CONSUMED'
            if all(l['state'] in ('BLOCKED', 'CONSUMED') for l in h.lanes.values()):
                finished.append(key)
        for key in finished:
            del self.active[key]  # Terminal evidence remains in histories for late FVG/OB linking.
        return emitted
