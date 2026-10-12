"""Synthetic paper accounting tests, not historical profitability evidence."""
import json
from pathlib import Path
import tempfile
import unittest

from traderlab.backtest import batch
from traderlab.automatic import AutomaticRelationships
from traderlab.detection import Bar
from test_strategy import ROOT, config, setup_event, tick, bar_event, D


class BatchChecks(unittest.TestCase):
    def execute(self, rows, cfg=None, annotations=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            events = root/'events.jsonl'; conf = root/'config.json'
            events.write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf-8')
            conf.write_text(json.dumps(cfg or config()), encoding='utf-8')
            return batch([events], conf, root/'out', annotations)

    def paired(self, exit_price):
        return [setup_event(), tick('4146.01', 0), tick('4146', 1), tick('4143', 2),
                tick(exit_price, 3)]

    def test_paired_tp_evidence_and_tick_equity_drawdown(self):
        report = self.execute(self.paired('4156'))
        r = report['cases'][0]['results']
        self.assertEqual((r['simulated_trades'], r['fully_closed_trades'], r['wins']), (2, 2, 2))
        self.assertEqual(r['realized_pnl_usd'], D('38'))
        self.assertEqual(r['max_tick_equity_drawdown_usd'], D('6'))
        self.assertEqual(report['historical_automatic_trades'], 0)
        self.assertEqual(len(r['trades'][0]['exits']), 2)
        self.assertEqual(r['trades'][0]['entry']['observed_spread'], '0')
        self.assertGreater(r['trades'][0]['entry']['input_order'], 0)

    def test_paired_stop_and_breakeven_single_lifecycle(self):
        r = self.execute(self.paired('4140'))['cases'][0]['results']
        self.assertEqual(r['realized_pnl_usd'], D('-18'))
        self.assertEqual(r['max_tick_equity_drawdown_usd'], D('18'))
        self.assertEqual(r['win_rate'], 0)
        rows = [setup_event(entries=('4146',)), tick('4146.01', 0), tick('4146', 1),
                tick('4152', 2), tick('4146.5', 3)]
        r = self.execute(rows)['cases'][0]['results']
        self.assertEqual(r['realized_pnl_usd'], D('6.5'))
        self.assertEqual([e['exit_reason'] for e in r['trades'][0]['exits']], ['TP1', 'BE_STOP'])

    def test_partial_closures_do_not_enter_win_rate_or_force_liquidation(self):
        rows = [setup_event(entries=('4146',)), tick('4146.01', 0), tick('4146', 1), tick('4152', 2)]
        r = self.execute(rows)['cases'][0]['results']
        self.assertEqual((r['fully_closed_trades'], r['open_legs']), (0, 1))
        self.assertIsNone(r['win_rate'])
        self.assertEqual(r['realized_pnl_usd'], D('6'))
        self.assertEqual(r['trades'][0]['fully_closed'], False)

    def test_spread_slippage_and_commissions_are_accounted_from_quotes(self):
        cfg = config(); cfg['slippage_pips'] = '1'
        cfg['commission_usd_per_lot_per_side'] = '5'
        rows = [setup_event(entries=('4146',)), tick('4145.9', 0, '4146.1'),
                tick('4145.8', 1, '4146'), tick('4156', 2, '4156.2')]
        r = self.execute(rows, cfg)['cases'][0]['results']
        entry = r['trades'][0]['entry']
        self.assertEqual((entry['ask'], entry['filled_entry'], entry['observed_spread']),
                         ('4146', '4146.1', '0.2'))
        self.assertEqual(r['realized_pnl_usd'], D('15.6'))
        self.assertEqual(r['max_tick_equity_drawdown_usd'], D('0.7'))

    def test_sell_directional_return_has_mirrored_targets_and_exit_evidence(self):
        rows = [setup_event(side='SELL', entries=('4143',)), tick('4142.99', 0),
                tick('4143', 1), tick('4133', 2)]
        r = self.execute(rows)['cases'][0]['results']
        self.assertEqual((r['simulated_trades'], r['realized_pnl_usd']), (1, D('16')))
        self.assertEqual(r['trades'][0]['entry']['side'], 'SELL')
        self.assertEqual([e['price'] for e in r['trades'][0]['exits']], ['4137.0', '4133.0'])

    def test_broker_constraints_block_incompatible_canonical_lots(self):
        cfg = config(); cfg['runtime_capabilities']['volume_min'] = '0.02'
        rows = [setup_event(entries=('4146',)), tick('4146.01', 0), tick('4146', 1)]
        r = self.execute(rows, cfg)['cases'][0]['results']
        self.assertEqual(r['simulated_trades'], 0)
        self.assertIn('BROKER_CONFIG_BLOCKED:canonical_0.01_lot_unrepresentable',
                      r['rejection_reasons'])

    def test_no_trades_has_no_performance_and_missing_policy_is_blocked(self):
        r = self.execute([tick('4146', 1)], annotations=False)['cases'][0]['results']
        self.assertFalse(r['performance_available'])
        for key in ('win_rate', 'realized_pnl_usd', 'max_tick_equity_drawdown_usd'):
            self.assertIsNone(r[key])
        cfg = config(); cfg['partial_fill_policy'] = None
        r = self.execute([setup_event(entries=('4146',)), tick('4146.01', 0), tick('4146', 1)], cfg)['cases'][0]['results']
        self.assertEqual(r['simulated_trades'], 0)
        self.assertTrue(any('partial_fill_policy' in k for k in r['rejection_reasons']))

    def test_outbound_and_missed_return_never_fabricate_fill(self):
        rows = [setup_event(entries=('4146',)), tick('4145.9', 1), tick('4146', 2)]
        self.assertEqual(self.execute(rows)['simulated_trades'], 0)
        rows += [tick('4146.1', 3), tick('4145.9', 4), tick('4146', 5)]
        r = self.execute(rows)['cases'][0]['results']
        self.assertEqual(r['simulated_trades'], 0)
        self.assertIn('first_return_crossed_without_exact_quote', r['rejection_reasons'])

    def test_reverse_requires_every_condition_and_keeps_planned_reference(self):
        s = setup_event(entries=('4146.5',)); s['ob']=['4141','4143'];s['fvg']=['4143','4147']
        rows = [s, tick('4146.51', 0), tick('4146.5', 1), tick('4140', 2)]
        self.assertEqual(self.execute(rows)['simulated_trades'], 1)
        rows += [{'kind':'structure','time':'2026-10-05T07:00:03Z','setup_id':'S',
                  'source':'Synthetic test only', 'bos_broken':True, 'ifvg_confirmed':True}, tick('4146.5',4)]
        r = self.execute(rows)['cases'][0]['results']
        self.assertEqual(r['simulated_trades'], 1)
        self.assertTrue(any('momentum_close' in k for k in r['rejection_reasons']))
        self.assertFalse(any(t['entry']['reverse'] for t in r['trades']))

    def test_rejected_input_does_not_publish_partial_profit(self):
        rows = self.paired('4156') + [tick('4145', 1)]
        report = self.execute(rows)
        self.assertEqual(report['rejected_cases'], 1)
        self.assertIsNone(report['cases'][0]['results'])
        self.assertIsNone(report['realized_pnl_usd'])
        report = self.execute([setup_event()], annotations=False)
        self.assertEqual(report['rejected_cases'], 1)

    def test_deterministic_independent_batch_and_no_duplicate_or_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); cfg=ROOT/'configs/fixture.example.json'
            source=ROOT/'tests/canonical-buy.jsonl'
            a=batch([source],cfg,root/'a',True); b=batch([source],cfg,root/'b',True)
            self.assertEqual(a,b)
            self.assertEqual((root/'a/batch.json').read_bytes(),(root/'b/batch.json').read_bytes())
            other=root/'copy.jsonl';other.write_bytes(source.read_bytes())
            c=batch([source,other],cfg,root/'c',True)
            self.assertEqual(c['simulated_trades'],4)
            self.assertEqual(c['realized_pnl_usd'],D('76'))
            with self.assertRaises(ValueError):batch([source,source],cfg,root/'d',True)
            with self.assertRaises(ValueError):batch([source],cfg,root/'a',True)

    def test_execution_flag_must_be_explicitly_disabled(self):
        cfg=config();cfg['broker_execution_enabled']=True
        with self.assertRaises(ValueError): self.execute([],cfg)

    def test_cross_timeframe_containment_stays_blocked_and_not_ranked(self):
        a=AutomaticRelationships();b=Bar.read(bar_event(21))
        base={'timeframe':'H4','side':'BUY','candidate_at':b.opened,'available_at':b.available,
              'zone':[D('4140'),D('4148')],'fill_state':'UNFILLED'}
        a.accept(b,[{**base,'event':'FVG_CONFIRMED'},{**base,'event':'OB_CONFIRMED',
                    'anchor_at':b.opened,'zone':[D('4148'),D('4149')]}])
        observations=a.accept(b,[{**base,'event':'BOS_CONFIRMED','timeframe':'M1','level':D('4143')}])
        cross=next(e for e in observations if e['event']=='CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED')
        self.assertEqual((cross['bos_timeframe'],cross['fvg_timeframe'],cross['ob_timeframe']),('M1','H4','H4'))
        self.assertIn('TODO_STRATEGY_UNRESOLVED:cross_timeframe_association',cross['reasons'])
        self.assertTrue(cross['diagnostic_only'])
        self.assertFalse(any(e['event']=='AUTO_SETUP_CONFIRMED' for e in observations))
        self.assertEqual(a.accept(b,[]),[])


if __name__ == '__main__':
    unittest.main()
