import copy
import unittest
from tools.compare_core_policies import compare


class StudyPolicyTests(unittest.TestCase):
    def source(self, exact=False, full=False, partial=True, other_consumed=True, bid='100.10', ask='100.32'):
        return {'sha256':'fixture','ticks':1,'groups':[{
            'fvg_id':'g','confirmation_server':'before','fill_at_confirmation':'PARTIAL' if partial else 'UNFILLED',
            'fvg':[99,104], 'selected_ids':['M1:SELL:a','M1:SELL:b'], 'structural_blocker':'FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION',
            'selected_at_confirmation':{'M1:SELL:a':{'consumed':other_consumed,'startup':False},'M1:SELL:b':{'consumed':False,'startup':False}},
            'post_confirmation_returns':[{'bos_id':'M1:SELL:b','tick_index':1,'server_time':'now','entry_reference':'100',
                'observed_tick':{'bid':bid,'ask':ask},'exact_quote':exact,'selected_by_frozen_extremes':True,
                'fill_after_return_tick':'FULL' if full else 'PARTIAL' if partial else 'UNFILLED'}]}]}

    def counts(self, source): return [len(r['quote_candidates']) for r in compare(source)['variants']]

    def test_independent_masks_and_baseline(self):
        self.assertEqual(self.counts(self.source()),[0,0,0,0,0,0,0,1])
        self.assertEqual(self.counts(self.source(partial=False)),[0,0,0,0,0,1,0,1])
        self.assertEqual(self.counts(self.source(exact=True,bid='100',ask='100.22')),[0,0,0,0,0,0,1,1])

    def test_full_never_resurrected_and_crossing_bounded(self):
        self.assertEqual(self.counts(self.source(full=True)),[0]*8)
        self.assertEqual(self.counts(self.source(bid='100.51',ask='100.73')),[0]*8)
        self.assertEqual(self.counts(self.source(bid='100.50',ask='100.72'))[-1],1)

    def test_buy_actual_ask_and_spread_in_crossing_budget(self):
        s=self.source(bid='99.8',ask='100.51')
        g=s['groups'][0];g['selected_ids']=['M1:BUY:a','M1:BUY:b']
        g['selected_at_confirmation']={k.replace('SELL','BUY'):v for k,v in g['selected_at_confirmation'].items()}
        g['post_confirmation_returns'][0]['bos_id']='M1:BUY:b'
        self.assertEqual(self.counts(s),[0]*8)

    def test_no_hindsight_reselection_or_multiple_fvg_choice(self):
        s=self.source();s['groups'][0]['post_confirmation_returns'][0]['selected_by_frozen_extremes']=False
        self.assertEqual(self.counts(s),[0]*8)
        s=self.source();s['groups'].append(copy.deepcopy(s['groups'][0]));s['groups'][1]['fvg_id']='other'
        self.assertEqual(self.counts(s),[0]*8)

    def test_this_consumed_or_startup_never_rearmed(self):
        for key in ['consumed','startup']:
            s=self.source();s['groups'][0]['selected_at_confirmation']['M1:SELL:b'][key]=True
            self.assertEqual(self.counts(s),[0]*8)

    def test_unknown_fvg_not_permission(self):
        s=self.source();s['groups'][0]['fill_at_confirmation']='UNKNOWN'
        self.assertEqual(self.counts(s),[0]*8)
