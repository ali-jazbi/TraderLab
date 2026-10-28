import hashlib
import unittest

from traderlab.recovery_rebuild import (
    build_rows, encode_revision, frames, input_row, known_emergency, replay_rows, validate_revision)


class RecoveryRebuildTests(unittest.TestCase):
    def setUp(self):
        self.old = [(100000, 3997.55, 3997.77, 0., 0, 1030, 0.),
                    (100706, 3997.58, 3997.80, 0., 0, 1030, 0.)]

    def test_explicit_metadata_revision_and_insertions_preserve_actual_rows(self):
        current = [self.old[0][:5]+(1158,0.),
                   (100500,3997.56,3997.78,0.,0,1158,0.),
                   self.old[1][:5]+(1158,0.),
                   (100800,3997.59,3997.81,0.,0,1030,0.)]
        self.assertEqual(validate_revision(self.old,current),2)
        rows = build_rows(current,[[] for _ in range(5)])
        self.assertEqual(sum(r.startswith('T|') for r in rows),3)
        self.assertEqual(rows[2],input_row('T',-1,1,1,current[1]))
        self.assertEqual(rows[1],'BASE_COMMIT')

    def test_price_change_deletion_reorder_and_unknown_metadata_still_block(self):
        for current in (self.old[:1],self.old[::-1],
                        [self.old[0],(100706,3997.59,3997.81,0.,0,1030,0.)],
                        [self.old[0],self.old[1][:5]+(1028,0.)]):
            with self.subTest(current=current),self.assertRaises(ValueError):
                validate_revision(self.old,current)

    def test_baseline_multiplicity_cannot_be_reinterpreted(self):
        with self.assertRaises(ValueError):
            validate_revision(self.old,[self.old[0],self.old[0],self.old[1]])

    def test_same_ms_identical_occurrences_preserved(self):
        current = [self.old[0],self.old[1],self.old[1]]
        rows=build_rows(current,[[] for _ in range(5)])
        self.assertIn('T|-1|1|1|100706|',rows[2])
        self.assertIn('T|-1|2|2|100706|',rows[3])
        rows=build_rows([self.old[0],self.old[0]], [[] for _ in range(5)],1)
        self.assertIn('T|-1|1|2|100000|',rows[2])

    def test_candle_available_only_after_close(self):
        ticks=[self.old[0],(119999,4000.,4000.2,0.,0,6,0.),
               (120000,4000.,4000.2,0.,0,6,0.)]
        bar=dict(time=60,open=3990.,high=4001.,low=3989.,close=4000.,
                 tick_volume=2,spread=20,real_volume=0)
        rows=build_rows(ticks,[[bar],[],[],[],[]])
        b=next(r for r in rows if r.startswith('B|'))
        self.assertTrue(b.startswith('B|0|2|1|120000|'))
        self.assertLess(rows.index(b),len(rows)-1)

    def test_append_only_committed_replay_and_subsequent_live_append(self):
        original=['AUTO_CORE_INPUT_V1|scope',input_row('Z',-1,0,0,self.old[0]),'BASE_COMMIT']
        old_bytes=encode_revision([],2166136261,'a'*64)  # exercise framing separately
        self.assertEqual(len(frames(old_bytes)[0]),2)
        rows=build_rows(self.old,[[] for _ in range(5)])
        ident=hashlib.sha256('\n'.join(rows).encode()).hexdigest()
        selected=original+['HISTORY_REBUILD_BEGIN|'+ident]+rows+['HISTORY_REBUILD_COMMIT|'+ident]
        self.assertEqual(replay_rows(selected),rows)
        live=input_row('T',-1,2,1,(100900,3998.,3998.2,0.,0,6,0.))
        self.assertEqual(replay_rows(selected+[live]),rows+[live])
        self.assertEqual(selected[:len(original)],original)
        for bad in (selected[:-1],selected[:-1]+['HISTORY_REBUILD_COMMIT|'+'b'*64],
                    selected[:-1]+['HISTORY_REBUILD_BEGIN|'+'b'*64]):
            with self.assertRaises(ValueError): replay_rows(bad)

    def test_torn_and_corrupt_frames_rejected(self):
        data=encode_revision(['BASE_COMMIT'],2166136261,'a'*64)
        for bad in (data[:-1],data[:12],data[:15]+b'!'+data[16:]):
            with self.assertRaises(ValueError): frames(bad)

    def test_resume_is_not_a_generic_emergency_or_unknown_order_reset(self):
        row='EMERGENCY|invalid_asof_closed_bar|XAUUSD_o|HALT|0.00000000|0.00000000|0.00000000|0|0|1793167408'
        self.assertTrue(known_emergency(row))
        for bad in (row.replace('invalid_asof_closed_bar','OPERATOR_EMERGENCY_STOP'),
                    row.replace('EMERGENCY','D1'),row.replace('HALT','UNKNOWN'),
                    row.replace('|0.00000000|','|0.01000000|',1),row.replace('XAUUSD_o','EURUSD')):
            self.assertFalse(known_emergency(bad))


if __name__=='__main__': unittest.main()
