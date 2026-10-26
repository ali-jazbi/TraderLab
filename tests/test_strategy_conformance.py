"""Owner acceptance examples; synthetic arithmetic, never historical fills/PnL."""
from decimal import Decimal as D
import unittest

from traderlab.detection import Bar
from traderlab.strategy import (Bos, Zone, DailyGuard, Unresolved, core_plan, select_bos,
                               entry_reference, reverse_plan, breakeven,
                               bearish_ob_momentum, breaker_block)
from tests.test_strategy import bar_event, config, setup_event
from traderlab.replay import Engine


def members(side, levels):
    return [Bos(str(i), entry_reference(side, D(p)), Zone(D(p), D(p)), D(p))
            for i, p in enumerate(levels)]


class StrategyConformance(unittest.TestCase):
    def test_legacy_example_and_current_offset_are_distinct(self):
        legacy = [Bos(p, D(p), Zone(D(p), D(p))) for p in ('4146', '4143')]
        old = core_plan('BUY', legacy, {})
        self.assertEqual((old.stop, old.target1, old.target2), (D('4140'), D('4152'), D('4156')))
        # Example's explicit contract assumption:100 oz/lot, 0.01/leg, no costs/BE path.
        loss = sum((D('4140')-b.entry)*D('.02')*100 for b in legacy)
        profit = sum(((old.target1-b.entry)+(old.target2-b.entry))*D('.01')*100 for b in legacy)
        self.assertEqual((loss, profit), (D('-18'), D('38')))
        for side, expected in (
                ('BUY', ('4146.5', '4143.5', '4140', '4152.5', '4156.5', '4147')),
                ('SELL', ('4142.5', '4145.5', '4149', '4136.5', '4132.5', '4142'))):
            plan = core_plan(side, members(side, ('4146', '4143')), {})
            actual = (plan.entries[0].entry, plan.entries[1].entry, plan.stop,
                      plan.target1, plan.target2, breakeven(plan, D('9999'), {}))
            self.assertEqual(actual, tuple(map(D, expected)))
        current=core_plan('BUY',members('BUY',('4146','4143')), {})
        self.assertEqual(sum((current.stop-b.entry)*D('.02')*100 for b in current.entries),D('-20'))

    def test_distances_on_raw_wicks_and_unsupported_branches(self):
        for side in ('BUY', 'SELL'):
            for distance, count in ((10,1), (20,1), (30,2), (40,2)):
                low = str(D('4146')-D(distance)/10)
                chosen = select_bos(side, members(side, ('4146', low)))
                self.assertEqual(len(chosen), count)
                self.assertEqual(chosen[0].level, D('4146') if side=='BUY' else D(low))
            for low in ('4145.01', '4141.99'):
                with self.assertRaises(Unresolved):
                    core_plan(side, members(side, ('4146', low)), {})
        for wrong in ('30', '50'):
            with self.assertRaises(ValueError):
                core_plan('BUY', members('BUY', ('4146',)), {'single_core_sl_pips':wrong})

    def test_reverse_reference_4146_5_no_second_offset_and_no_sl_only_permission(self):
        p = reverse_plan('SELL', D('4146.5'), {})
        self.assertEqual((p.entries[0].entry,p.stop,p.target1,p.target2),
                         (D('4146.5'),D('4150.5'),D('4140.5'),D('4136.5')))
        base = dict(original_side='BUY', executed=True, stopped=True, entries=1,
                    bos_broken=True, order_block_broken=True, ifvg_confirmed=True, momentum_close=True)
        self.assertIn('association_sequence_and_daily_count', breaker_block(**base))
        for flag, expected in (('executed','CORE_EXECUTION_REQUIRED'),
                               ('stopped','CORE_ACTUAL_SL_REQUIRED'),
                               ('bos_broken','REVERSE_BOS_BREAK_REQUIRED'),
                               ('order_block_broken','REVERSE_OB_10_PIP_BREAK_REQUIRED'),
                               ('momentum_close','REVERSE_CONFIRMED_MOMENTUM_OB_BREAK_CLOSE_REQUIRED'),
                               ('ifvg_confirmed','REVERSE_IFVG_REQUIRED')):
            self.assertEqual(breaker_block(**{**base,flag:False}),expected)
        self.assertIn('dual_parent',breaker_block(**{**base,'entries':2}))
        self.assertIn('reverse_buy',breaker_block(**{**base,'original_side':'SELL'}))

    def test_ob_wick_and_new_momentum_close_are_cumulative(self):
        ob = Zone(D('4141'),D('4143'))
        valid = Bar.read(bar_event(10,'4147','4147','4139.9','4140.5'))
        self.assertTrue(bearish_ob_momentum(ob,valid,True))
        self.assertFalse(bearish_ob_momentum(ob,valid,False))
        for prices in (('4140.9','4140.99','4130','4131'), # wholly below OB
                       ('4147','4147','4140.01','4140.5'), # short of10pips
                       ('4147','4147','4139','4141'),      # no close below
                       ('4140','4147','4139','4140.5')):   # bullish close
            self.assertFalse(bearish_ob_momentum(ob,Bar.read(bar_event(10,*prices)),True))

    def test_replay_wholly_below_momentum_does_not_claim_ob_break(self):
        engine=Engine(config());engine.accept(setup_event(stamp='2026-10-05T00:00:00Z',entries=('4146',)))
        # Setup OB low4135. A genuine Big candle entirely BELOW it is not a new OB break.
        for i in range(21):
            prices=('4140','4141','4139','4141')
            if i==10: prices=('4134','4134.9','4123','4124')
            engine.accept(bar_event(i,*prices))
        self.assertFalse(any(e['event']=='REVERSAL_MOMENTUM_CLOSE_DIAGNOSTIC' for e in engine.events))
        self.assertFalse(engine.setups['S'].reverse_armed)

    def test_daily_two_stopped_setups_and_net_profit_latch(self):
        day=DailyGuard();day.reset('Sydney-A')
        for leg in range(4): day.close('one-setup',D('-4.5'),True)
        self.assertEqual(len(day.stopped_setups),1);self.assertFalse(day.halted)
        day.close('second',D('1'),False);day.close('second',D('-1'),True)
        self.assertTrue(day.halted)
        day.reset('Sydney-B');day.close('winner',D('99.99'),False)
        self.assertFalse(day.profit_reached)
        day.close('winner2',D('.01'),False);day.close('winner3',D('10'),False)
        self.assertTrue(day.profit_reached);self.assertFalse(day.halted)
        day.close('stop',D('-4'),True);self.assertTrue(day.halted)


if __name__=='__main__': unittest.main()
