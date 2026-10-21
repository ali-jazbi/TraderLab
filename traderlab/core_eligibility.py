"""Owner §55: Core permission only; never suppress FVG/BOS detection history."""
from dataclasses import dataclass
from decimal import Decimal

from .strategy import PIP, number


@dataclass(frozen=True)
class CoreEligibility:
    body_pips: Decimal | None
    witness_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def eligible(self):
        return not self.reasons


def core_eligibility(gap, candidates, cutoff=None):
    """Candidates are §9/§54-qualified records, not arbitrary chart levels.

    Owner clarification: only the BOS candle must precede C2's open.
    Qualification-before-Break remains the detector's existing predicate;
    qualification need not precede C2, but must be known at the cutoff.
    Break/first-return handling and final membership/selection remain separate.
    The caller supplies the existing same/cross-frame association scope.
    """
    cutoff = cutoff or gap['available_at']
    c2 = gap.get('candidate_at')
    ohlc = gap.get('c2_ohlc')
    prices = (number(ohlc['open']), number(ohlc['close'])) if ohlc else None
    body = abs(prices[1] - prices[0]) / PIP if prices and min(prices) > 0 else None
    reasons = []
    if body is None:
        reasons.append('C2_OHLC_UNAVAILABLE')
    elif body < 80:
        reasons.append('C2_BODY_BELOW_80_PIPS')
    prior = [b for b in candidates if c2 is not None and b.get('candidate_at') is not None
             and b['candidate_at'] < c2 and b.get('qualified_at') is not None
             and b['qualified_at'] <= cutoff
             and b['side'] == gap['side']]
    witnesses = tuple(b['id'] for b in prior
                      if number(gap['zone'][0]) <= number(b['level']) <= number(gap['zone'][1]))
    if not prior:
        reasons.append('NO_VALID_PREFVG_BOS')
    elif not witnesses:
        reasons.append('BOS_OUTSIDE_FVG')
    return CoreEligibility(body, witnesses, tuple(reasons))
