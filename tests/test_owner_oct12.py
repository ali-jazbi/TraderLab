"""Owner amendments relayed directly by project owner on 2026-10-12 (§52).

Synthetic quotes/calendars test implementation, not historical strategy performance.
"""
import copy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from traderlab.replay import Engine
from traderlab.session import session_day, news_block
from traderlab.automatic import AutomaticRelationships
from traderlab.demo_gateway import DemoLedger
from traderlab.strategy import Bos, Zone, core_plan, breakeven, Unresolved
from traderlab.detection import Bar, instant
from test_strategy import config, setup_event, tick, bar_event, D, ROOT


def at(price, stamp, ask=None):
    return {**tick(price, 0, ask), 'time': stamp}


class OwnerOct12Checks(unittest.TestCase):
    def test_actual_fill_sl_for_both_sides_with_real_observed_spread_and_modeled_slippage(self):
        for side, below, touch, ask, expected_fill, expected_stop in (
                ('BUY','4146.01','4146','4146.2','4146.3','4142.3'),
                ('SELL','4145.99','4146','4146.2','4145.9','4149.9')):
            cfg=config(); cfg['buy_touch_quote']='bid'; cfg['slippage_pips']='1'
            e=Engine(cfg);e.accept(setup_event(side=side,entries=('4146',)))
            e.accept(tick(below,1));e.accept(tick(touch,2,ask))
            self.assertEqual((e.positions[0].entry,e.positions[0].stop),(D(expected_fill),D(expected_stop)))
            row=next(x for x in e.events if x['event']=='PAPER_ENTRY')
            self.assertEqual(row['planned_entry'],'4146')
            self.assertNotEqual(row['planned_entry'],row['filled_entry'])

    def test_dual_be_reuses_highest_buy_lowest_sell_planned_tp_reference(self):
        for side, expected in (('BUY','4147'),('SELL','4142')):
            candidates=[Bos(str(x),D(x)+(D('.5') if side=='BUY' else -D('.5')),
                            Zone(D(x),D(x)),D(x)) for x in ('4146','4143')]
            plan=core_plan(side,candidates,{})
            self.assertEqual(breakeven(plan,D('9999'),{}),D(expected))
            self.assertEqual(plan.target1,plan.reference+(D('6') if side=='BUY' else -D('6')))
        cfg=config();cfg['be_entry_anchor']=None
        e=Engine(cfg);e.accept(setup_event(entries=('4146','4143')))
        e.accept(tick('4146.01',1));e.accept(tick('4146',2));e.accept(tick('4152',3))
        self.assertTrue(e.positions)
        self.assertEqual(e.positions[1].stop,D('4146.5'))
        self.assertTrue(any(x['event']=='BE_MOVED' for x in e.events))

    def test_containment_uses_wick_not_planned_offset(self):
        for side, level in (('BUY','4116'),('SELL','4111')):
            s=setup_event(side=side);s['fvg']=['4111','4116']
            s['bos']=[{'id':'B','level':level,'zone':[level,level]}]
            e=Engine(config());e.accept(s)
            self.assertIsNotNone(e.setups['S'].plan)
        s['bos']=[{'id':'B','level':'4110.99','zone':['4110.99','4110.99']}]
        with self.assertRaisesRegex(ValueError,'wick tip'): Engine(config()).accept(s)

    def test_qualified_bos_relationship_does_not_wait_for_closed_break_or_require_preformation_bos(self):
        a=AutomaticRelationships();b=Bar.read(bar_event(21))
        base={'side':'BUY','timeframe':'M1','candidate_at':b.opened,'available_at':b.available}
        observations=[{**base,'event':'FVG_CONFIRMED','zone':[D('4140'),D('4148')],'fill_state':'UNFILLED'},
                      {**base,'event':'OB_CONFIRMED','anchor_at':b.opened,'zone':[D('4148'),D('4149')]},
                      {**base,'event':'BOS_CANDIDATE_QUALIFIED','level':D('4143')}]
        pair=next(x for x in a.accept(b,observations) if x['event']=='AUTO_SETUP_BLOCKED')
        self.assertEqual(pair['preformation_bos_count'],0)
        self.assertTrue(pair['credibility_is_qualitative'])
        self.assertFalse(any('preformation_required' in r for r in pair['reasons']))
        self.assertIn('TODO_STRATEGY_UNRESOLVED:package_grouping',pair['reasons'])

    def test_later_closed_break_does_not_erase_preformation_qualification_clock(self):
        a=AutomaticRelationships();b=Bar.read(bar_event(21))
        candidate={'event':'BOS_CANDIDATE_QUALIFIED','side':'BUY','timeframe':'M1',
                   'candidate_at':instant('2026-10-05T00:01:00Z'),'level':D('4143')}
        a.accept(b,[candidate]);key=a.identity(candidate);qualified=a.bos[key]['qualified_at']
        later=Bar.read(bar_event(22))
        a.accept(later,[{**candidate,'event':'BOS_CONFIRMED','available_at':later.available}])
        self.assertEqual(a.bos[key]['qualified_at'],qualified)
        self.assertEqual(a.bos[key]['available_at'],later.available)

    def calendar(self):
        return {'source':'Synthetic DST-varying calendar; not approved live hours',
                'session_definition':'Sydney_open_to_New_York_close',
                'coverage_start':'2026-10-04T00:00:00Z','coverage_end':'2026-10-07T00:00:00Z',
                'sessions':[{'id':'A','sydney_open':'2026-10-04T21:00:00Z','new_york_close':'2026-10-05T21:00:00Z','available_at':'2026-10-04T00:00:00Z'},
                            {'id':'B','sydney_open':'2026-10-05T22:00:00Z','new_york_close':'2026-10-06T21:00:00Z','available_at':'2026-10-04T00:00:00Z'}]}

    def test_calendar_trading_days_no_invented_hours_and_gaps_fail_closed(self):
        cfg={'trading_day_calendar':self.calendar()}
        self.assertEqual(session_day(cfg,instant('2026-10-05T20:59:59Z')),'A')
        self.assertEqual(session_day(cfg,instant('2026-10-05T22:00:00Z')),'B')
        with self.assertRaises(Unresolved): session_day(cfg,instant('2026-10-05T21:30:00Z'))
        with self.assertRaises(Unresolved): session_day({},instant('2026-10-05T22:00:00Z'))
        cfg['trading_day_calendar']['sessions'][1]['sydney_open']='2026-10-05T20:00:00Z'
        with self.assertRaises(ValueError): session_day(cfg,instant('2026-10-05T22:00:00Z'))

    def news_engine(self):
        cfg=config();cfg['commission_usd_per_lot_per_side']='5'
        cfg['news_calendar']['events']=[{'name':'CPI','scheduled_at':'2026-10-05T07:05:00Z','available_at':'2026-10-05T06:00:00Z'}]
        e=Engine(cfg);e.accept(setup_event(entries=('4146',),stamp='2026-10-05T06:40:00Z'))
        e.accept(at('4146.01','2026-10-05T06:40:01Z'));e.accept(at('4146','2026-10-05T06:40:02Z'))
        return e

    def test_partial_allow_config_cannot_approve_an_unconfirmed_owner_rule(self):
        cfg=config();cfg['config_status']='OWNER_RULES_WITH_TEST_RUNTIME_INPUTS'
        cfg['trading_day_calendar']=self.calendar()
        cfg['partial_fill_policy']='allow_any_partial'
        e=Engine(cfg);e.accept(setup_event(entries=('4146',)));e.accept(tick('4146.01',1));e.accept(tick('4146',2))
        self.assertFalse(e.positions)
        self.assertTrue(any('owner_partial_fill_permission' in x.get('reason','') for x in e.events))
        self.assertIn('S-0',e.consumed_bos)

    def test_news_forces_every_paper_leg_closed_at_observed_deadline_net_costs(self):
        e=self.news_engine();e.accept(at('4147','2026-10-05T07:02:00Z'))
        self.assertFalse(any(p.open for p in e.positions))
        exits=[x for x in e.events if x['event']=='PAPER_EXIT']
        self.assertEqual(len(exits),2)
        self.assertTrue(all(x['exit_reason']=='NEWS_FORCE_CLOSE' and x['deadline_met'] for x in exits))
        self.assertEqual(e.daily.closed_profit,D('1.8'))
        self.assertFalse(e.daily.stopped_setups)

    def test_missing_deadline_quote_never_backdates_closure(self):
        e=self.news_engine();e.accept(at('4147','2026-10-05T07:02:00.001Z'))
        self.assertEqual(e.execution_block,'NEWS_CLOSE_DEADLINE_MISSED')
        self.assertTrue(any(x['event']=='NEWS_CLOSE_DEADLINE_MISSED' for x in e.events))
        exits=[x for x in e.events if x['event']=='PAPER_EXIT']
        self.assertTrue(all(not x['deadline_met'] and x['time']=='2026-10-05T07:02:00.001000Z' for x in exits))

    def test_quote_gap_through_entire_news_window_still_marks_deadline_breach(self):
        e=self.news_engine();e.accept(at('4147','2026-10-05T07:21:00Z'))
        self.assertFalse(any(p.open for p in e.positions))
        self.assertEqual(e.execution_block,'NEWS_CLOSE_DEADLINE_MISSED')
        self.assertTrue(any(x['event']=='NEWS_CLOSE_DEADLINE_MISSED' for x in e.events))

    def test_simultaneous_news_and_price_exit_rejects_paper_chronology(self):
        e=self.news_engine()
        with self.assertRaisesRegex(ValueError,'NEWS_PRICE_EXIT_ORDER_UNRESOLVED'):
            e.accept(at('4142','2026-10-05T07:02:00Z'))
        self.assertFalse(any(x['event']=='PAPER_EXIT' for x in e.events))

    def test_momentum_close_waits_for_ten_following_bars_and_never_arms_reverse(self):
        e=Engine(config());s=setup_event(stamp='2026-10-05T00:00:00Z',entries=('4146',))
        e.accept(s)
        for i in range(20):
            args=('4140','4141','4139','4141')
            if i==10: args=('4144','4145','4133','4134')
            e.accept(bar_event(i,*args))
        self.assertFalse(any(x['event']=='REVERSAL_MOMENTUM_CLOSE_DIAGNOSTIC' for x in e.events))
        e.accept(bar_event(20,'4140','4141','4139','4141'))
        evidence=next(x for x in e.events if x['event']=='REVERSAL_MOMENTUM_CLOSE_DIAGNOSTIC')
        self.assertEqual(evidence['close'],'4134')
        self.assertFalse(evidence['tradable_reverse'])
        self.assertFalse(e.setups['S'].reverse_armed)

    def test_reverse_news_policy_is_confirmed_and_contradiction_rejected(self):
        e=self.news_engine();cfg=e.config
        self.assertTrue(news_block(cfg,instant('2026-10-05T07:05:00Z'),True))
        cfg={**cfg,'news_reverse_policy':'allow'}
        with self.assertRaises(ValueError): Engine(cfg)

    def test_native_gateway_is_isolated_compile_locked_with_one_dispatch_site(self):
        src=(ROOT/'mt5/Include/TraderLab/DemoGateway.mqh').read_text(encoding='utf-8')
        ea=(ROOT/'mt5/TraderLab.mq5').read_text(encoding='utf-8')
        self.assertNotIn('DemoGateway',ea)
        self.assertIn('TL_DEMO_DISPATCH_REVIEWED=false',src)
        self.assertEqual(src.count('OrderSend('),1)
        for token in ('ACCOUNT_TRADE_MODE_DEMO','OrderCalcMargin','OrderCheck','FILE_COMMON',
                      'FileFlush','DEMO_IDENTITY_REQUIRED','UNKNOWN_DISPATCH_NO_AUTOMATIC_RETRY',
                      'RepairActualFillStops','SubmitReviewedCorePair','INCOMPLETE_CANONICAL_PAIR','CloseAllDemoPositions','NEWS_DEADLINE_MISSED'):
            self.assertIn(token,src)
        self.assertLess(src.index('if(!Claim(intent))'),src.index('OrderSend('))
        self.assertNotIn('OrderSendAsync',src)
        self.assertIn('return called && (retcode==0 || retcode==TRADE_RETCODE_DONE)',src)
        self.assertEqual(src.count('TLDemoCheckPassed(checked,check.retcode)'),2)
        self.assertNotIn('check.retcode!=TRADE_RETCODE_DONE',src)


class DurableDemoChecks(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.path=Path(self.directory.name)/'ledger.sqlite'
        self.identity={'login':123,'server':'Synthetic-Demo','symbol':'XAUUSD_o'}
        self.snapshot={**self.identity,'account_trade_mode':'DEMO','connected':True,'trade_allowed':True,'expert_allowed':True,
                       'margin_mode':'HEDGING','currency':'USD','reconciled':True,'history_complete':True,
                       'directional_volume':'0','exact_observed_quote':True,'margin_check_passed':True,'order_check_passed':True,
                       'capabilities':config()['runtime_capabilities']}
        self.payload={'action':'CORE','opportunity':'BOS:first-return:leg1','volume':'0.01','price':'4146',
                      'stop':'4142','target':'4152','reverse':False,'fill_state':'UNFILLED',
                      'guards':dict.fromkeys(('strategy','first_touch','session','news','daily','quote'),True)}

    def tearDown(self): self.directory.cleanup()

    def test_disabled_real_contest_scope_margin_and_unapproved_guards_never_send(self):
        called=[];ledger=DemoLedger(self.path,self.identity)
        with self.assertRaises(ValueError): ledger.submit('I1',self.payload,self.snapshot,called.append)
        ledger.close();ledger=DemoLedger(self.path,self.identity,True,True)
        for changes in ({'account_trade_mode':'REAL'},{'account_trade_mode':'CONTEST'},{'login':124},
                        {'margin_check_passed':False},{'order_check_passed':False},{'reconciled':False},
                        {'currency':'EUR'},{'margin_mode':'NETTING'}):
            with self.assertRaises(ValueError):ledger.submit('I1',self.payload,{**self.snapshot,**changes},called.append)
        for changes in ({'reverse':True},{'fill_state':'PARTIAL'},{'guards':{}},{'volume':'0.02'}):
            with self.assertRaises(ValueError):ledger.submit('I1',{**self.payload,**changes},self.snapshot,called.append)
        self.assertEqual(called,[]);ledger.close()

    def test_crash_after_send_commit_duplicate_restart_and_account_binding(self):
        calls=[];ledger=DemoLedger(self.path,self.identity,True,True)
        def timeout(payload):calls.append(payload);raise TimeoutError('synthetic unknown outcome')
        self.assertEqual(ledger.submit('I1',self.payload,self.snapshot,timeout),'UNKNOWN');ledger.close()
        ledger=DemoLedger(self.path,self.identity,True,True)
        self.assertEqual(ledger.submit('I1',self.payload,self.snapshot,calls.append),'UNKNOWN')
        self.assertEqual(len(calls),1)
        with self.assertRaises(ValueError): ledger.submit('I1',{**self.payload,'target':'4153'},self.snapshot,calls.append)
        with self.assertRaises(ValueError): ledger.submit('I2',{**self.payload,'opportunity':'other'},self.snapshot,calls.append)
        with self.assertRaises(ValueError): ledger.reconcile({**self.snapshot,'history_complete':False},[])
        self.assertFalse(ledger.reconcile(self.snapshot,[])) # absence is never rejection
        self.assertTrue(ledger.reconcile(self.snapshot,[{'intent_id':'I1','source':'synthetic MT5 deal evidence','deal_id':9}]))
        with self.assertRaises(Exception): ledger.submit('I2',self.payload,self.snapshot,calls.append)
        ledger.close()
        with self.assertRaises(ValueError): DemoLedger(self.path,{**self.identity,'login':456},True,True)

    def test_rejection_and_partial_fill_emergency_persist_without_automatic_retry(self):
        ledger=DemoLedger(self.path,self.identity,True,True);calls=[]
        def rejected(payload): calls.append(payload);return {'definitive_no_execution':True,'retcode':'rejected'}
        self.assertEqual(ledger.submit('I1',self.payload,self.snapshot,rejected),'REJECTED')
        self.assertEqual(ledger.submit('I1',self.payload,self.snapshot,rejected),'REJECTED')
        self.assertEqual(len(calls),1)
        ledger.halt('operator emergency');ledger.close();ledger=DemoLedger(self.path,self.identity,True,True)
        with self.assertRaises(ValueError): ledger.submit('I2',{**self.payload,'opportunity':'other'},self.snapshot,rejected)
        # Emergency stop blocks entries, while reviewed liquidation uses actual position evidence.
        close={'action':'CLOSE','opportunity':'emergency:position:77','position_id':77,'symbol':'XAUUSD_o','volume':'0.01'}
        with self.assertRaises(ValueError):ledger.submit('C77',close,self.snapshot,rejected)
        snap={**self.snapshot,'positions':[{'ticket':77,'symbol':'XAUUSD_o','volume':'0.01'}]}
        self.assertEqual(ledger.submit('C77',close,snap,rejected),'REJECTED')
        ledger.close()
        partial=DemoLedger(Path(self.directory.name)/'partial.sqlite',self.identity,True,True)
        self.assertEqual(partial.submit('I1',self.payload,self.snapshot,lambda p:{'partial':True}),'ACK')
        partial.close();partial=DemoLedger(Path(self.directory.name)/'partial.sqlite',self.identity,True,True)
        with self.assertRaises(ValueError):partial.submit('I2',{**self.payload,'opportunity':'other'},self.snapshot,rejected)
        partial.close()

    def test_competing_instances_use_transactional_unique_opportunity(self):
        a=DemoLedger(self.path,self.identity,True,True);b=DemoLedger(self.path,self.identity,True,True)
        calls=[]
        a.submit('I1',self.payload,self.snapshot,lambda p: calls.append(p) or {'definitive_no_execution':True})
        with self.assertRaises(Exception): b.submit('I2',self.payload,self.snapshot,calls.append)
        self.assertEqual(len(calls),1);a.close();b.close()
