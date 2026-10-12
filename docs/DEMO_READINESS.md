# DEMO readiness — 2026-10-12

**BLOCKED: automatic setup approval and MT5 DEMO execution.** No broker submission
path exists. Production policies remain null; fixture choices are synthetic modeling
assumptions, not owner confirmations.

## Implemented

- Big Candle/FVG/OB and qualified BOS diagnostics on M1/M5/M15/H1/H4. Confirmation
  still requires ten subsequent closed bars. No future candle is used early.
- Chronological break, outbound movement and first directional return. Missed
  crossings consume without filling; late confirmation never resets return history.
  Directional return remains a reading of prior examples, not new owner confirmation.
- Same-timeframe and cross-timeframe containment with stable IDs and actual candle
  fill states. Each FVG retains its own full C3 Buy/C1 Sell OB; no independent OB
  association, timeframe ranking or automatic promotion was invented.
- Existing paper engine reused: single/paired entries, 0.02 lot split into two legs,
  shared dual SL/targets, single 40-pip SL, TP60/100, BE+5, daily/news guards and NY
  context. Reverse requires executed/stopped Core, observed OB penetration and sourced
  BOS/iFVG confirmations. Dual-parent reverse remains blocked.
- Entry/exit quote and tick-order evidence, explicit slippage/commission/TP model,
  volume/tick-grid and aggregate directional constraints. No spread cap was invented.
- Independent batch cases with journals, hashes and blockers. One trade is one BOS
  entry with two legs; win rate includes only fully closed entries. USD drawdown
  values open legs at observed exit-side quotes after paid entry fees. No forced
  liquidation, swap, or portfolio aggregation of independent files.

Code: [relationships](../traderlab/automatic.py), [paper engine](../traderlab/replay.py),
[batch accounting](../traderlab/backtest.py). Full rules: [STRATEGY_SPEC](STRATEGY_SPEC.md).

## Real October 7 replay

XAUUSD_o explicitly adapted to XAUUSD with broker metadata retained. Accepted input:
**279,320 ticks / 1,875 closed bars**. Unresolved quote policies produce separate
diagnostic lanes; lane events are not unique tradable setups.

| Result | Count |
|---|---:|
| Confirmed Big Candles | 218 |
| Confirmed FVGs / associated C3/C1 OBs | 30 / 30 |
| Closed-bar BOS confirmations / qualifications | 1,047 / 1,295 |
| Blocked same-timeframe containment pairs | 303 |
| Blocked cross-timeframe containment pairs | 668 |
| Automatic valid setups / simulated trades | **0 / 0** |

Overlapping pair reasons: 659 FULL invalidities, 301 PARTIAL blockers, 476 late
availability warnings, 669 consumed-return diagnostics. These are diagnostic counts,
not unique opportunities. **Historical win rate, PnL and drawdown are unavailable.**
Synthetic test profits are not historical results.

Local report: `work/demo-readiness-batch-20261012-A/batch.json` and `case-001/`.
Normalized input SHA256:
`2b6b1d99b95f3007f790bc1bf9477d7225af8d9c4986934cfe4414f3fbdd2417`.
Original visual tester raw SHA256:
`0f105703e67b4ce619cbd61dc675776ffac81fac7f64f8fcfdf116018969642f`.
Neither file is modified or committed; replay does not establish new native parity.

```powershell
python tools/batch_backtest.py --events work/automatic-input-20261011.jsonl --config configs/production.template.json --out work/demo-readiness-next
```

Supply multiple files for independent cases; state is not carried between them.
Choose a fresh output directory. Default market-only mode rejects annotations.
`--allow-annotations` labels the entire case sourced simulation, never automatic
historical approval. Supply reviewed annotations and explicit paper policies;
`configs/fixture.example.json` is for synthetic tests only.

## Minimum exact owner questions, in order

1. **Association/grouping (§9–10,14–15,51):** Which BOS candle, FVG impulse and
   C3/C1 OB form a package? Which timeframe combinations are allowed, which BOSs
   belong together, and when is their group final? Containment alone is insufficient.
2. **Activation (§11–13; Q-LIFETIME):** Must FVG/OB be confirmed at break or first
   return? Can later confirmation associate with an earlier BOS? What starts/ends
   package validity? Consumed returns remain consumed.
3. **PARTIAL (§7):** Is partial penetration tradable? If conditional, what exact
   observed threshold invalidates it?
4. **Quotes (§13,39):** Which Bid/Ask detects structural break, Buy/Sell return and
   invalidation? A crossing without an exact observed quote cannot fabricate a fill.
5. **Risk anchors (§21–22,42):** Is single Core/Reverse 40-pip SL from planned
   reference or actual fill? Is dual BE+5 from each entry or the common reference?

Also required before unrestricted automated paper runs: daily reset zone/minute,
net/gross profit, BE-stop counting (§23–24), news source/coverage/reverse handling
(§26), and restart/day-boundary policy. Automatic reversals additionally need exact
iFVG/BOS inversion and dual-parent/count rules (§35–45). <10/>40 distances stay
blocked; H1 structure and NY ambiguities stay diagnostic rather than invented gates.
See [OPEN_QUESTIONS](OPEN_QUESTIONS.md). Already resolved wick levels, full OB bounds,
pip size, 40-pip distance and inclusive 20-pip boundary must not be re-asked.

## Native audit and DEMO infrastructure

Source audit against `6301d2e`: both detectors preserve wick qualification, 20-pip
FVG, full C3/C1 OB and ten-following-bar confirmation. Native has recovered-tick,
as-of-bar break/return tracking on five timeframes alongside legacy timer-driven
closed-bar diagnostics. Compare explicit availability timestamps, not log order alone.

This milestone changes **no MQL5/capture files**. Cross-timeframe pair reports and
simulated positions/accounting are Python only. Fresh native runtime parity and
MQL compilation in this milestone are **UNVERIFIED**. Python: **123 tests passed**,
including 13 batch regressions for costs, constraints, exits, reverse and determinism.

Verified runtime account/symbol/cost/calendar values are still needed. Paper capability
checks do not model stops/freeze levels, margin, hedging/netting, currency conversion
or swap. A future DEMO gateway needs durable request accounting, restart-safe position
reconciliation and one guarded dispatch path; in-memory guards are insufficient.

**Next MT5 step:** execute `StrategyChecks`, then fresh October 7 normal and tester-only
stress captures with the existing native code. Follow the exact parameters/comparator
in [NATIVE_RETESTS](NATIVE_RETESTS.md). Require zero tracker halts, reconciled ticks and
comparison of both audited BOS examples; preserve all raw files. This verifies
detection only. Owner answers precede automatic paper approval; a separate reviewed
execution milestone precedes DEMO orders.
