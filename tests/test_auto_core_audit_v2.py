"""Policy regressions; synthetic identities only, never historical trade evidence."""
from copy import copy
from decimal import Decimal as D
from tests import test_experimental_auto as fixtures
from traderlab.experimental import POLICIES
import unittest

utc = fixtures.utc


class AuditChecks(unittest.TestCase):
    def engine(self, policy=POLICIES[0]):
        return fixtures.ExperimentalChecks().engine(policy)

    def duplicate(self, e, original, name, qualified):
        h = copy(original)
        h.bar = copy(original.bar)
        h.bar.opened = utc(name)
        h.qualified_at = utc(qualified)
        key = e.retests.identity(h.bar.timeframe, h.side, h.bar.opened)
        e.retests.histories[key] = h
        return key, h

    def test_delayed_finalization_does_not_import_later_qualification(self):
        e = self.engine()
        original = next(iter(e.retests.histories.values()))
        key, h = self.duplicate(e, original, 720, 1001)
        h.level = D('4145')
        e.finalize(utc(1002))
        finalized = next(x for x in e.events if x['event'] == 'EXPERIMENTAL_GROUP_FINALIZED')
        self.assertNotIn(key, finalized['members'])
        self.assertEqual(finalized['frozen_at'], '1970-01-01T00:16:40Z')

    def test_future_fvg_validation_does_not_mutate_freeze_state(self):
        e = self.engine()
        with self.assertRaises(ValueError):
            e.finalize(utc(999))
        self.assertEqual(e.finalized, set())
        e.finalize(utc(1000))
        self.assertEqual(e.accepted_groups, 1)

    def test_baseline_equal_levels_remain_blocked(self):
        e = self.engine()
        self.duplicate(e, next(iter(e.retests.histories.values())), 720, 950)
        e.finalize(utc(1000))
        self.assertEqual(e.group_rejections['AMBIGUOUS_EQUAL_BOS_LEVELS'], 1)

    def test_equal_level_v1_is_order_independent_and_keeps_extremes(self):
        for reverse in (False, True):
            e = self.engine(POLICIES[2])
            original_key, original = next(iter(e.retests.histories.items()))
            key, _ = self.duplicate(e, original, 720, 950)
            if reverse:
                e.retests.histories = dict(reversed(list(e.retests.histories.items())))
            e.finalize(utc(1000))
            self.assertEqual(e.accepted_groups, 1)
            event = next(x for x in e.events if x['event'] == 'EXPERIMENTAL_GROUP_FINALIZED')
            self.assertIn(original_key, event['members'])
            self.assertNotIn(key, event['members'])
            self.assertIn(key, event['all_geometric_members'])
            self.assertEqual(set(event['selected_bos_ids']), set(event['members']))

    def test_consumed_representative_cannot_be_replaced_by_fresh_alias(self):
        e = self.engine(POLICIES[2])
        original = next(iter(e.retests.histories.values()))
        _, fresh = self.duplicate(e, original, 720, 950)
        original.lanes = {'bid': {'returns': {'bid': copy(original.lanes['bid']['returns']['bid'])}}}
        original.lanes['bid']['returns']['bid'].result = {'consumed': True}
        self.assertIsNone(fresh.lanes['bid']['returns']['bid'].result)
        e.finalize(utc(1000))
        self.assertEqual(e.group_rejections['FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION'], 1)

    def test_promoted_setup_cannot_forget_closed_bar_fill_or_recover_from_full(self):
        e = self.engine()
        e.finalize(utc(1000))
        setup = next(iter(e.setups.values()))
        for state in ('PARTIAL', 'FULL', 'UNFILLED'):
            e.automatic.gaps['F']['fill_state'] = state
            e.sync_closed_fill()
            self.assertEqual(setup.fill, state if state != 'UNFILLED' else 'FULL')


if __name__ == '__main__':
    unittest.main()
