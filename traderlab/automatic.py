"""Automatic historical relationships, diagnostic only until association is approved.

No cross-timeframe search, ranking, grouping, retrospective entries or synthetic ticks.
"""
from .strategy import PIP, direction


class AutomaticRelationships:
    def __init__(self):
        self.retests = None
        self.gaps = {}
        self.bos = {}
        self.seen_pairs = set()

    @staticmethod
    def identity(observation):
        return f"{observation['timeframe']}:{observation['side']}:{observation['candidate_at'].isoformat()}"

    def accept(self, bar, observations):
        result = []
        # Only actual closed candles on the gap's own timeframe update its fill.
        for gap in self.gaps.values():
            if gap['timeframe'] != bar.timeframe:
                continue
            low, high = gap['zone']
            full = bar.low <= low if gap['side'] == 'BUY' else bar.high >= high
            partial = bar.low < high if gap['side'] == 'BUY' else bar.high > low
            old = gap['fill_state']
            if full:
                gap['fill_state'] = 'FULL'
            elif partial and old != 'FULL':
                gap['fill_state'] = 'PARTIAL'
            if old != gap['fill_state']:
                result.append({'event': 'FVG_VALIDITY_CHANGED', 'rule': 'FVG-03',
                               'fvg_id': gap['id'], 'fill_state': gap['fill_state']})
        anchors = {self.identity(o): o for o in observations if o['event'] == 'OB_CONFIRMED'}
        new_bos, new_gaps = set(), set()
        for o in observations:
            if o['event'] == 'FVG_CONFIRMED':
                key = self.identity(o)
                self.gaps[key] = {**o, 'id': key, 'ob': anchors[key]['zone'],
                                  'ob_anchor_at': anchors[key]['anchor_at']}
                new_gaps.add(key)
            elif o['event'] == 'BOS_CONFIRMED':
                key = self.identity(o)
                self.bos[key] = dict(o)
                new_bos.add(key)
                contains = any(g['timeframe'] == o['timeframe'] and g['side'] == o['side'] and
                               g['zone'][0] <= o['level'] <= g['zone'][1] for g in self.gaps.values())
                result.append({'event': 'BOS_RELATIONSHIP_DIAGNOSTIC', 'rule': 'BOS-02',
                               'bos_id': key, 'level': o['level'],
                               'reason': 'association_unresolved' if contains else
                               'no_confirmed_same_timeframe_fvg_contains_level_at_break'})
        # Pair on known geometry only. Containment is necessary, not proof of
        # strategy association or of which BOSs belong to one trade package.
        for bos_id, bos in self.bos.items():
            gap_ids = self.gaps if bos_id in new_bos else sorted(new_gaps)
            for gap_id in gap_ids:
                gap = self.gaps[gap_id]
                if bos['timeframe'] != gap['timeframe'] or bos['side'] != gap['side']:
                    continue
                if not gap['zone'][0] <= bos['level'] <= gap['zone'][1]:
                    continue
                key = (bos_id, gap_id)
                if key in self.seen_pairs:
                    continue
                self.seen_pairs.add(key)
                reasons = ['TODO_STRATEGY_UNRESOLVED:association_and_bos_grouping']
                if gap['fill_state'] == 'FULL':
                    reasons = ['FVG_FULL_FILL_INVALID']
                elif gap['fill_state'] == 'PARTIAL':
                    reasons.append('TODO_STRATEGY_UNRESOLVED:partial_fill_policy')
                if bos['available_at'] < gap['available_at']:
                    reasons.append('TODO_STRATEGY_UNRESOLVED:touch_history_before_setup_availability')
                history = self.retests.snapshot(bos_id) if self.retests else None
                if history and any(r is not None for lane in history.values() for r in lane['returns'].values()):
                    reasons.append('FIRST_DIRECTIONAL_RETURN_ALREADY_CONSUMED_DIAGNOSTIC')
                result.append({'event': 'AUTO_SETUP_BLOCKED', 'rule': 'BOS-02/FVG-03/OB-01',
                               'setup_id': f'{bos_id}|{gap_id}', 'bos_id': bos_id, 'fvg_id': gap_id,
                               'timeframe': bos['timeframe'], 'side': bos['side'],
                               'candidate_at': bos['candidate_at'], 'bos_available_at': bos['available_at'],
                               'fvg_available_at': gap['available_at'], 'bos_level': bos['level'],
                               'entry_reference': bos['level'] + direction(bos['side']) * 5 * PIP,
                               'fvg': gap['zone'], 'ob': gap['ob'], 'ob_anchor_at': gap['ob_anchor_at'],
                               'fill_state': gap['fill_state'], 'geometry_confirmed': True,
                               'intrabar_history': history,
                               'diagnostic_only': True, 'reasons': reasons})
        return result
