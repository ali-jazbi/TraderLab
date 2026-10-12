"""Synthetic regression inputs only; never historical trades or performance."""
import copy
from dataclasses import replace
from decimal import Decimal as D
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_strategy import bar_event, config, setup_event, tick, prime_return
from traderlab.automatic import AutomaticRelationships
from traderlab.detection import Bar, Detector
from traderlab.replay import Engine
from traderlab.strategy import Bos, Unresolved, Zone, core_plan, entry_reference, reverse_plan

ROOT = Path(__file__).resolve().parents[1]


def window(timeframe='M1', mirror=False):
    bars = []
    for i in range(21):
        args = ('4140', '4141', '4139', '4141') if i < 10 else ('4143', '4145', '4143', '4144')
        if i == 10:
            args = ('4140', '4147', '4140', '4146')
        b = Bar.read(bar_event(i, *args, timeframe=timeframe))
        if mirror:
            b = replace(b, open=10000-b.open, high=10000-b.low, low=10000-b.high, close=10000-b.close)
        bars.append(b)
    return bars


class ConfirmedAmendmentChecks(unittest.TestCase):
    def test_wick_bos_levels_both_directions_and_rejected_order(self):
        for mirror, side, level in ((False, 'BUY', D('100')), (True, 'SELL', D('9900'))):
            d = Detector()
            bars = [Bar.read(bar_event(i, *args)) for i, args in enumerate(
                [('95','100','90','96'), ('92','99','88','89'), ('96','101','95','100')])]
            if mirror:
                bars = [replace(b, open=10000-b.open, high=10000-b.low, low=10000-b.high, close=10000-b.close) for b in bars]
            d.accept(bars[0]); d.accept(bars[1]); result = d.accept(bars[2])
            bos = next(o for o in result if o['event']=='BOS_CONFIRMED' and o['side']==side)
            self.assertEqual(bos['level'], level)
        d = Detector(); d.accept(Bar.read(bar_event(0,'95','100','90','96')))
        rejected = d.accept(Bar.read(bar_event(1,'92','101','88','89')))
        self.assertTrue(any(o['event']=='BOS_REJECTED' and o['reason']=='same_bar_order_ambiguous' for o in rejected))

    def test_full_candle_ob_buy_c3_sell_c1_no_h4_gate(self):
        for tf in ('M1','M5','M15','H1','H4'):
            for mirror, side, index in ((False,'BUY',11),(True,'SELL',9)):
                d = Detector(); bars = window(tf,mirror)
                for b in bars[:20]:
                    self.assertFalse(any(o['event']=='FVG_CONFIRMED' for o in d.accept(b)))
                result = d.accept(bars[20])
                ob = next(o for o in result if o['event']=='OB_CONFIRMED')
                self.assertEqual(ob['side'],side)
                self.assertEqual(ob['zone'],[bars[index].low,bars[index].high])
                self.assertEqual(ob['available_at'],bars[20].available)

    def test_directional_entry_and_dual_raw_level_distance_sl(self):
        self.assertEqual(entry_reference('BUY',D('4114')),D('4114.5'))
        self.assertEqual(entry_reference('SELL',D('4114')),D('4113.5'))
        entries=[Bos(str(x),entry_reference('BUY',D(x)),Zone(D(x),D(x)),D(x)) for x in ('4146','4143')]
        plan=core_plan('BUY',entries,{})
        self.assertEqual((plan.stop,plan.target1,plan.target2),(D('4140'),D('4152.5'),D('4156.5')))

    def test_single_40_pip_distances_do_not_approve_anchor(self):
        b=Bos('B',D('4114.5'),Zone(D('4114'),D('4114')),D('4114'))
        cfg=config()
        for key in ('single_core_sl_anchor','single_reverse_sl_anchor'):
            bad={**cfg,key:None}
            with self.assertRaises(Unresolved):
                core_plan('BUY',[b],bad) if key=='single_core_sl_anchor' else reverse_plan('SELL',b.entry,bad)
        self.assertEqual(core_plan('BUY',[b],cfg).stop,D('4110.5'))
        self.assertEqual(reverse_plan('SELL',b.entry,cfg).stop,D('4118.5'))
        self.assertEqual(reverse_plan('SELL',b.entry,{**cfg,'breaker_sl_pips':None}).stop,D('4118.5'))
        with self.assertRaises(ValueError): core_plan('BUY',[b],{**cfg,'single_core_sl_pips':'30'})

    def test_restricted_first_touch_and_quote_jump_are_consumed(self):
        for missing_anchor in (False,True):
            cfg=config()
            if missing_anchor: cfg['single_core_sl_anchor']=None
            else: cfg['news_calendar']=None
            e=Engine(cfg); s=setup_event(entries=('4114.5',))
            s['bos']=[{'id':'B','level':'4114','zone':['4114','4114']}]
            s['fvg']=['4111','4116'];s['ob']=['4104','4111'];e.accept(s);prime_return(e)
            e.accept(tick('4114.5',1));self.assertIn('B',e.consumed_bos);self.assertFalse(e.positions)
            e.config.update(config()); e.accept(tick('4114.5',2));self.assertFalse(e.positions)
        e=Engine(config());s=setup_event(entries=('4114.5',));e.accept(s)
        e.accept(tick('4115',1));e.accept(tick('4114',2));e.accept(tick('4114.5',3))
        self.assertFalse(e.positions);self.assertIn('S-0',e.consumed_bos)

    def test_filled_sl_anchor_uses_actual_quote_plus_explicit_slippage(self):
        cfg={**config(),'single_core_sl_anchor':'filled','slippage_pips':'2'}
        e=Engine(cfg);e.accept(setup_event(entries=('4146.5',)));prime_return(e);e.accept(tick('4146.3',1,'4146.5'))
        self.assertEqual(e.positions[0].entry,D('4146.7'))
        self.assertEqual(e.positions[0].stop,D('4142.7'))

    def test_alias_is_explicit_preserves_original_and_same_ms_ticks(self):
        cfg={**config(),'symbol_aliases':{'XAUUSD_o':'XAUUSD'}};e=Engine(cfg)
        row={**tick('4146',1),'symbol':'XAUUSD_o','tick_index':1,'time':'2026-10-05T07:00:01.123Z'}
        original=copy.deepcopy(row);e.accept(row);e.accept({**row,'tick_index':2})
        self.assertEqual(row,original);self.assertEqual(e.last_tick[1]['broker_symbol'],'XAUUSD_o')
        self.assertEqual(e.last_tick[0].microsecond,123000)
        with self.assertRaises(ValueError): Engine(config()).accept(row)

    def test_relationships_no_future_cross_timeframe_or_duplicate_promotion(self):
        b=window()[-1];a=AutomaticRelationships()
        gap={'event':'FVG_CONFIRMED','timeframe':'M1','side':'BUY','candidate_at':b.opened,
             'available_at':b.available,'zone':[D('4111'),D('4116')],'fill_state':'UNFILLED'}
        ob={**gap,'event':'OB_CONFIRMED','zone':[D('4104'),D('4111')],'anchor_at':b.opened}
        bos={**gap,'event':'BOS_CONFIRMED','level':D('4114')}
        self.assertFalse(any(o['event']=='AUTO_SETUP_BLOCKED' for o in a.accept(b,[bos])))
        emitted=a.accept(b,[gap,ob]);self.assertEqual(sum(o['event']=='AUTO_SETUP_BLOCKED' for o in emitted),1)
        self.assertTrue(next(o for o in emitted if o['event']=='AUTO_SETUP_BLOCKED')['diagnostic_only'])
        self.assertEqual(a.accept(b,[]),[])
        other=AutomaticRelationships();other.accept(b,[gap,ob])
        self.assertFalse(any(o['event']=='AUTO_SETUP_BLOCKED' for o in other.accept(b,[{**bos,'timeframe':'M5'}])))
        outside=other.accept(b,[{**bos,'level':D('4117')}])
        self.assertFalse(any(o['event']=='AUTO_SETUP_BLOCKED' for o in outside))
        self.assertIn('no_confirmed_same_timeframe',outside[0]['reason'])

    def test_actual_closed_bar_fill_invalidates_relationship_and_is_terminal(self):
        a=AutomaticRelationships();b=window()[-1]
        gap={'event':'FVG_CONFIRMED','timeframe':'M1','side':'BUY','candidate_at':b.opened,
             'available_at':b.available,'zone':[D('4141'),D('4143')],'fill_state':'UNFILLED'}
        a.accept(b,[gap,{**gap,'event':'OB_CONFIRMED','zone':[D('4143'),D('4145')],'anchor_at':b.opened}])
        low=Bar.read(bar_event(21,'4141','4145','4140','4143'))
        out=a.accept(low,[{**gap,'event':'BOS_CONFIRMED','level':D('4142'),'candidate_at':low.opened}])
        blocked=next(o for o in out if o['event']=='AUTO_SETUP_BLOCKED')
        self.assertIn('FVG_FULL_FILL_INVALID',blocked['reasons'])
        a.accept(b,[]);self.assertEqual(next(iter(a.gaps.values()))['fill_state'],'FULL')

    def test_diagnostic_cli_deterministic_rejects_annotations_no_profit_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'input.jsonl';p.write_text(json.dumps({**tick('4114',1),'symbol':'XAUUSD_o'})+'\n')
            hashes=[]
            for i in range(2):
                out=root/str(i)
                r=subprocess.run([sys.executable,str(ROOT/'tools/automatic_backtest.py'),'--events',str(p),
                                  '--config',str(ROOT/'configs/production.template.json'),'--out',str(out)],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)
                report=json.loads((out/'summary.json').read_text());hashes.append(report['journal_sha256'])
                self.assertNotIn('closed_profit_usd',report);self.assertFalse(report['performance_available'])
            self.assertEqual(*hashes)
            p.write_text(json.dumps(setup_event())+'\n')
            r=subprocess.run([sys.executable,str(ROOT/'tools/automatic_backtest.py'),'--events',str(p),
                              '--config',str(ROOT/'configs/production.template.json'),'--out',str(root/'bad')],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertFalse((root/'bad').exists())


if __name__ == '__main__': unittest.main()
