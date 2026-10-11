"""Audit reproductions: four known Core defects remain explicit expected failures.

Fixture annotations assume an already qualified/broken and available setup solely
to isolate direction handling. They are not historical setup approvals. Entry
dispatch is mocked: these checks cannot create fills, trades or PnL.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from traderlab.replay import Engine


class FirstRetestAudit(unittest.TestCase):
    def engine(self, side):
        root = Path(__file__).resolve().parents[1]
        cfg = json.loads((root / 'configs/fixture.example.json').read_text(encoding='utf-8'))
        engine = Engine(cfg)
        engine.open_entry = Mock(name='entry_dispatch_must_not_create_a_fill')
        reference = '4142.32' if side == 'BUY' else '4139.74'
        engine.accept({'kind': 'setup', 'time': '2026-10-05T07:00:00Z',
                       'setup_id': 'unit', 'side': side, 'confirmed': True,
                       'source': 'unit fixture assumes available setup; not historical evidence',
                       'fill_state': 'UNFILLED', 'fvg': ['4130', '4150'],
                       'ob': ['4120', '4122'],
                       'bos': [{'id': 'unit-bos', 'entry': reference,
                                'zone': [reference, reference]}]})
        return engine

    def quote(self, engine, side, price, second):
        # Zero-spread fixture isolates the configured quote's directional logic.
        engine.accept({'kind': 'tick', 'time': f'2026-10-05T07:00:{second:02d}Z',
                       'bid': price, 'ask': price})
        self.assertFalse(engine.positions)

    def outbound_must_not_consume(self, side, before, outbound):
        engine = self.engine(side)
        self.quote(engine, side, before, 1)
        self.quote(engine, side, outbound, 2)
        self.assertNotIn('unit-bos', engine.consumed_bos)
        engine.open_entry.assert_not_called()

    # Remove expectedFailure when the audited production defect is actually fixed.
    @unittest.expectedFailure
    def test_buy_outbound_exact_is_not_first_return(self):
        self.outbound_must_not_consume('BUY', '4142.24', '4142.32')

    @unittest.expectedFailure
    def test_buy_outbound_gap_is_not_first_return(self):
        self.outbound_must_not_consume('BUY', '4142.24', '4142.33')

    @unittest.expectedFailure
    def test_sell_outbound_exact_is_not_first_return(self):
        self.outbound_must_not_consume('SELL', '4139.80', '4139.74')

    @unittest.expectedFailure
    def test_sell_outbound_gap_is_not_first_return(self):
        self.outbound_must_not_consume('SELL', '4139.80', '4139.63')

    def test_missed_directional_returns_consume_without_fills_or_retries(self):
        for side, previous, current, reference in (
                ('BUY', '4142.33', '4142.30', '4142.32'),
                ('SELL', '4139.71', '4139.84', '4139.74')):
            with self.subTest(side=side):
                engine = self.engine(side)
                self.quote(engine, side, previous, 1)
                self.quote(engine, side, current, 2)
                self.assertIn('unit-bos', engine.consumed_bos)
                engine.open_entry.assert_not_called()
                self.quote(engine, side, reference, 3)
                engine.open_entry.assert_not_called()

    def test_exact_directional_returns_dispatch_once(self):
        for side, previous, reference in (
                ('BUY', '4142.33', '4142.32'), ('SELL', '4139.73', '4139.74')):
            with self.subTest(side=side):
                engine = self.engine(side)
                self.quote(engine, side, previous, 1)
                self.quote(engine, side, reference, 2)
                self.assertIn('unit-bos', engine.consumed_bos)
                engine.open_entry.assert_called_once()
                self.quote(engine, side, reference, 3)
                engine.open_entry.assert_called_once()


if __name__ == '__main__':
    unittest.main()
