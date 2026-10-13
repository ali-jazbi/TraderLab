# Core Demo readiness — 2026-10-13

**Integration prepared; automatic setups and broker dispatch remain BLOCKED.**
TL_DEMO_DISPATCH_REVIEWED=false, gateway Start(false), default magic0, empty calendar
and lead0. Keep terminal **Algo Trading OFF**. No order was submitted. Reverse is
disabled; Real/Contest always rejected. Owner provenance remains canonical §§51–52;
directional-return wording remains our documented reading of prior examples.

## Implemented / partially implemented / blocked

| Scope | State and evidence |
|---|---|
| Chronological native controller | Implemented: as-of candles, original qualification, Big/FVG/C3-or-C1 OB, wick containment, stable IDs, first directional return/consumption, FULL invalidation and actionable pair reports on M1/M5/M15/H1/H4. Legacy logs preserved. |
| Automatic grouping | Blocked: geometry does not prove package membership/finalization or cross-timeframe association. Every pair reports IDs, times/prices, reasons and minimum evidence. No invented expiry. |
| Core lifecycle bridge | Prepared: two0.01 legs per selected BOS entry, raw-BOS selection/shared dual SL/TP reference, actual-fill single SL40, broker TP1/BE, NET costs/daily guards, explicit calendars/news, durable plans/consumption/intents, position reconciliation and emergency closure. No automatic promotion or transport execution. |
| Fault checks | Deterministic Python/native reducer and source checks cover reject/partial/conflicting deals, restart duplicates, missed ticks, delayed quotes, blocked groups/PARTIAL and news deadlines. Actual native transport crashes, compensation, file-journal restart and broker SL/BE/news behavior require a reviewed terminal test. |

Reported baseline terminal runs at60654a2 passed StrategyChecks and DemoGatewayChecks
with failures0/lockedtrue. User-reported runtime: Demo/USD/HEDGING, XAUUSD_o BID,
tick0.01, minimum/step0.01, free margin1000 USD. This is not execution of the new Core
script; margin1000 is not a fixed input. Identity/filling/stops/freeze/margin/volume
must be rechecked on future requests.

## Genuine October7 market-only batch

Accepted **279,320 ticks / 1,875 closed bars**; no annotations or fabricated trades.

| Observation | Count |
|---|---:|
| Big Candles / FVGs / full-candle OBs | 218 / 30 / 30 |
| BOS qualifications / closed-bar confirmations | 1,295 / 1,047 |
| Candidate BOS/FVG pairs | 1,172 |
| Same-timeframe / cross-timeframe blocked pairs | 383 / 789 |
| Bid intrabar breaks / directional-return diagnostics | 1,020 / 1,964 |
| Fully approved Core setups / simulated trades | **0 / 0** |
| Completed simulated wins / losses | 0 / 0 (empty population) |
| Win rate / PnL / drawdown | **Unavailable** |

At relationship creation: FULL787, PARTIAL374, UNFILLED11. At batch end: FULL1159,
PARTIAL4, UNFILLED9. Overlapping pair reasons:438 returns consumed before FVG,
909 consumed returns overall,715 missed exact Bid returns and31 startup-history
qualifications. These are diagnostic pairs, not unique tradable setups.

Full local actionable outputs, excluded from commits:
work/core-pipeline-final-oct07-20261013/case-001/core-candidates.json and .csv;
report.json, events.jsonl and batch/code/config/spec/journal hashes alongside.
Input SHA256:2b6b1d99b95f3007f790bc1bf9477d7225af8d9c4986934cfe4414f3fbdd2417.
Original raw visual SHA256:0f105703e67b4ce619cbd61dc675776ffac81fac7f64f8fcfdf116018969642f.
Both unchanged. Reproduce into a fresh output directory:

    python tools/batch_backtest.py --events work/automatic-input-20261011.jsonl --config configs/production.template.json --out work/core-next-oct07

### Exact chart examples — observed server UTC+3

- **M1 BUY:** BOS ID M1:BUY:2026-10-07T03:10:00+00:00; FVG ID
  M1:BUY:2026-10-07T03:25:00+00:00; OB same FVG ID plus:C3.
  BOS4141.82, planned4142.32, FVG4139.60–4142.19, OB4142.19–4143.85.
  Qualified06:13:01.663; break06:25:50.736; first **Bid** directional return
  06:28:51.731,4142.33→4142.32 exact. FVG formed06:27:00.101, confirmed
  06:36:00.045 PARTIAL, laterFULL. Return consumed before safe availability;
  no retroactive fill. Earlier Ask return is a separate observation lane.
- **M5 SELL:** BOS ID M5:SELL:2026-10-07T02:05:00+00:00; FVG ID
  M5:SELL:2026-10-07T04:30:00+00:00; OB suffix:C1.
  BOS4140.24, planned4139.74, FVG4139.67–4141.76, OB4141.76–4143.04.
  Break06:06:25.538; first Bid upward return06:12:53.153,
  4139.71→4139.84 **missed exact quote**. FVG confirmed08:25:01.010 UNFILLED.
  Even unfilled geometry cannot revive this consumed opportunity.

Minimum evidence: owner package candle/timeframe mapping, complete BOS member IDs
and finalization/activation time. PARTIAL also needs explicit permission/invalidation.
Consumed/FULL cases cannot be approved retroactively.

## Actual native/Python comparison

Legacy Oct7 accepted closed-bar IDs/geometry/fill observations match:
1295 qualifications,1047 confirmations,218 Big,30 FVG and30 OB on1875 bars.
**105 startup-history bars** are diagnostic warmup, not live entry proof.

Actual TraderLab-live-run05.jsonl prefix:3318 ticks,130 tracker bars, **67/67**
native/Python break/return events match exact timestamps/quotes/occurrences.
Prefix SHA256:dfe01b09e192eb260be064e3bbc4a3c494e9e9834fe1f6ca81d1c4bc524a06c8,
2434254 bytes. No final summaries: completeness/accepted capture NOT_ESTABLISHED.
No fresh Core run exists. Full native/Python strategy/fill-lifecycle parity remains
**NOT_ESTABLISHED**. compare_existing_detectors.py reports this scope; the strict
compare_native_retests.py still requires complete accepted captures.
Local evidence:work/core-existing-parity.json.

## Remaining decisions and engineering inputs

1. Exact BOS/FVG/OB package membership, permitted timeframe mapping, complete group
   and finalization. Wick containment is already answered.
2. PARTIAL permission/threshold only for that branch. Select a specifically approved
   UNFILLED package for the smallest path; no config approves PARTIAL.
3. Single BE planned versus actual fill anchor. Dual shared BE is answered.
   Profitable BE-stop counting, <10/>40 selection and undefined lifetime branches
   remain blocked.
4. Sourced Sydney-open/NY-close UTC/DST calendar, explicit news coverage/availability,
   verified server offset, positive operational deadline lead, actual costs and
   reviewed freshness/spread/slippage handling. No fixed hours/defaults.
5. Native locked runtime/fault/restart evidence and actual SL/BE/news/deadline
   reconciliation before unlock. Market legs are non-atomic; failed second leg must
   halt and reconcile liquidation. Unknown outcomes never automatically retry.

Native calendar: pipe-separated UTF8 in MQL5/Files. Header:
SYDNEY_NY_NEWS|source|coverage_start_utc_epoch|coverage_end_utc_epoch.
DAY|id|sydney_open_utc_epoch|ny_close_utc_epoch|available_utc_epoch.
NEWS|CPI-or-NFP-or-FOMC|scheduled_utc_epoch|0|available_utc_epoch.
Explicitly covered periods may have no news; unknown coverage blocks. No fixture
pretends to establish production session hours.

## Exact next MT5 actions — no activation

1. Keep Algo Trading OFF on LiteFinance Demo/XAUUSD_o. Compile/install TraderLab,
   Include/TraderLab and three scripts: StrategyChecks, DemoGatewayChecks,
   **CorePipelineChecks**. Run scripts and save Journal; each must print failures0,
   new Core script dispatch_lockedtrue/orders0. Core checks only reducers and its
   own labeled synthetic calendar; this is not broker runtime certification.
2. Fresh Strategy Tester: XAUUSD_o, Every tick based on real ticks, Oct7→Oct8 2026.
   Set InpBrokerSymbol=XAUUSD_o, InpServerUtcOffsetSeconds=10800,
   InpTehranUtcOffsetSeconds=12600 (the prior capture's explicit offsets).
   Keep InpCoreMagic=0, InpCoreCalendarFile empty, InpNewsClosureLeadSeconds=0,
   InpTesterStress=false; its skip count is ignored. Choose a fresh InpLogFile.
   Require CORE lock/summary lockedtrue/approved0, no controller
   or capture halt, complete terminal cursor evidence.
3. Second fresh filename, InpTesterStress=true, InpTesterStressSkipCallbacks=8.
   Compare normal/stress
   authoritative TICK sequences and compare complete normal native retests.
   Inspect the two BOS IDs above and CORE_SETUP_CANDIDATE reasons. CORE candle
   availability uses BOS_TRACKER_CLOSED_BAR; legacy timer bars are a separate stream.
4. Separately review a complete UNFILLED Core package, source calendars and single
   BE anchor (or approved dual package). Verify native reject/timeout/partial-pair/
   restart/SL/BE/emergency/news paths. Refresh broker properties and live quote proof.
   Only then request a **separate Demo-only activation review**. This commit cannot
   unlock dispatch. Never enable Real.

Compilation is not script execution or transport certification. Current check totals
are 151 Python tests passed; TraderLab compiled with0 errors/1 existing version
warning, all three scripts with0 errors/0 warnings. Commit SHA is in the final report.
New script execution awaits terminal evidence.
