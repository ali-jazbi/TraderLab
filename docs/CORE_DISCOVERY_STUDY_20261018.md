# Prespecified discovery study (not owner-confirmed strategy)

Base 41a4214. Measured server dates October7–9 only; all earlier genuine state is
warm-up with orders disabled. Baseline0 and mask7 remain frozen references from
that commit. No TP/SL/lot/spread/slippage/tolerance/news/session tuning.

Fixed profiles, defined before inspecting new trade outcomes:

1. FRESH_CONFIRMED: same-frame qualified wick containment, only globally unconsumed
   BOS members as-of FVG confirmed availability. Freeze that membership once.
2. IMPULSE_GLOBAL: same as1, additionally the actual qualified Bid wick break must
   have occurred during that FVG's C2 impulse candle. No numerical lookback/expiry.
3. IMPULSE_ARMED: same impulse association, but an independent BOS-level return
   stream starts at the first eligible confirmed package. Pre-activation canonical
   consumption remains recorded and never reset; this hypothesis ignores it only
   in its separate experiment. The study BOS is consumed once, even on restrictions,
   FULL, ambiguous packages or missed execution. Later packages never rearm it.

All profiles use mask7's actual-quote crossing <=5pips and non-FULL permission.
Single BE is explicitly EXPERIMENTAL actual executed leg fill +/-5pips; dual BE
retains the canonical shared TP reference. Single SL remains40pips from actual
fill; paired SL/TP and two0.01 legs unchanged. Unresolved <10/>40 distance branches
stay blocked. No arbitrary choice among multiple eligible packages.

The study removes ONLY the operational one-new-setup/day reservation limit.
Canonical two-stopped-setups and net100-then-stop remain, plus the existing
0.04-lot/open-risk/margin/news/session guards. Conservative experimental BE-stop
accounting counts every SL once per setup, including a profitable BE exit.
Both extra assumptions are isolated to the named TESTER profiles.

STRUCTURAL_VALID is confirmed geometry/membership/selection; SIGNAL_READY requires
a newly observed directional return; EXECUTION_READY requires the original gateway
and actual successful two-leg receipts. These are separate evidence stages.

Research selection is prespecified by least departure:1, then2, then3. If a profile
is positive, validate the first positive in that order, not the maximum-PnL profile,
on previously unused October14–16 data. Do not tune a losing profile's thresholds.
All failures remain in the ledger. No automatic Demo, Real, Contest or Reverse.
