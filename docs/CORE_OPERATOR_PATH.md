# Operator-approved Core: MT5 chart path

Automatic package discovery remains blocked by canonical §§51–52: the complete
BOS membership and its finalization are not defined. The chart panel implements
OPERATOR_APPROVED_CORE; it does not claim automatic discovery.

## Use the existing EA

1. Keep Algo Trading OFF. The existing142 Core checks passed in the actual MT5
   terminal; do not repeat them. Seven new final-send checks also passed there.
2. Attach TraderLab to LiteFinance DEMO / XAUUSD_o. Set InpBrokerSymbol=XAUUSD_o,
   verified server/Tehran UTC offsets, and an explicit Core magic. Keep
   InpRequestCoreDemoExecution=false. InpCorePanel=true displays the review panel;
   InpCoreOperatorPackages defaults to TraderLab-core-packages.csv.
3. Use FVG arrows, then BOS arrows. The panel displays real detector IDs, broker
   candle times, wick/entry prices, full C3/C1 OB bounds, FVG fill and consumption.
   Add/remove BOS selects complete membership for that FVG, with no inferred
   timeframe restriction. Enter operator name and chart-review evidence in the
   two boxes; Review / approve previews canonical entry/SL/TP/BE. Click it again
   to confirm. Prices are never editable. The scoped approval file is created in
   MQL5/Files, flushed and reloaded without restarting the EA.
4. Only a fresh dual package (>20 to <=40 strategy pips), UNFILLED FVG and future
   exact first directional return can use the complete known BE branch. Single
   BE and PARTIAL remain blocked. Startup/consumed returns cannot be rearmed.
5. Supply InpCoreCalendarFile: a sourced UTC Sydney-open/NY-close and CPI/NFP/FOMC
   coverage file (including DST and availability). Header and rows:

       SYDNEY_NY_NEWS|source|coverage_start_epoch|coverage_end_epoch
       DAY|day_id|sydney_open_epoch|ny_close_epoch|known_epoch
       NEWS|CPI_or_NFP_or_FOMC|event_epoch|0|known_epoch

   These are placeholders, not approved hours or news evidence. The file reloads
   each service cycle; malformed/expired coverage blocks entries and requires
   emergency closure if execution is reviewed/enabled. Set a reviewed positive
   InpNewsClosureLeadSeconds. Closure is due before event minus 3 minutes.
   Sourced packets are now installed for October13/14; choose one packet only.
   Adjacent day windows overlap under the published local clocks and DST;
   automatic day allocation is unresolved. Changing a persisted day to an
   overlapping/mutated window fails closed, including after restart.
6. Supply reviewed InpCorePairMaxMilliseconds, InpCoreMaxSpreadPrice (price units)
   and InpCoreMaxSlippagePoints (broker points). Defaults are UNSET. First leg
   requires the exact genuine first-return quote. Second leg is the same execution
   episode, using an actually observed quote inside those explicit budgets.
   Read-only terminal-history validation rejects intervening FVG fills, history
   lag/errors or reordering; capture still owns tick emission/cursor validation.
   Actual broker fills are reconciled and checked. Incomplete/unknown outcomes
   persist a halt and attempt authoritative Demo liquidation, without retrying.
7. The compile lock is still CLOSED. The separate CoreDemo.activation.patch is
   not applied. Review this Core route's checks, calendar and execution budgets
   before any separately reviewed activation. REAL/CONTEST always fail closed.

After TP1 broker evidence, the existing lifecycle moves leg2 to the shared BE+5.
Deal callbacks rescan broker history before BE; restart checks actual positions
and protective levels. Emergency management continues when new entries are
halted. The panel STOP persists through restart; Algo OFF/compiled lock cannot
send liquidation orders, so inspect the Trade tab manually in that state.

## Actual verification

October7 original Core capture remains unchanged (SHA256
6dc73e240c26cc0969f4abaf78c3a0efaa69d44157deab40ef079fdacd22dd0f):
279320 ticks,1172 relations,0 UNFILLED exact returns after confirmation,0 trades.
885 consumed observations were PARTIAL/FULL,16 startup,7 missed,1 too early.
This historical day cannot be turned into an eligible trade by operator approval.
Successful prior smoke/AutoPilot orders are transport evidence only; not repeated.
October14: the real terminal journal confirms142/142 previous Core checks at
09:05:00.464 server time. Only the seven NEW final-send checks were executed for
this change, with InpOnlySendBoundaryChecks=true: failures=0,checks=7,
dispatch_locked=true,broker_orders_sent=0,09:42:16.538 server time.
The seven focused Python path contracts passed. MetaEditor compiled the EA
(0 errors,1 existing version warning) and CorePipelineChecks (0 errors/0 warnings).
The fix rechecks account permissions, the exact vetted quote and both deadlines
AFTER OrderCheck and the flushed intent, directly before the sole send site.
An expired/changed observation records known non-submission and never retries.

## One controlled Demo trial, separately reviewed activation

Load mt5/activation/CoreDemo.trial.locked.set into the EA Inputs. It keeps the
request FALSE; the separate activation patch remains unapplied. Preserve the
existing InpCoreMagic, supply a NEW InpLogFile, and verify the offsets before OK.
Use the updated EA, one chart and one newly approved package, with no other bots
or manual positions on this Demo account. These are proposed strict trial caps,
not strategy changes, measured latency bounds or broker performance guarantees:

| Exact input | Proposal | Evidence / engineering choice |
|---|---:|---|
| InpCorePairMaxMilliseconds |1000| Two sequential responses at the observed maximum100.884ms total201.768ms; approximately5 times that sample, including local preflight. A slower episode fails closed, rather than widening the cap. |
| InpCoreMaxSpreadPrice |0.22| All11736 reviewed live quotes; historical p95 also0.22. Reject wider spreads, including historical p99=0.52. |
| InpCoreMaxSlippagePoints |0| Three actual matched entry deals had zero slippage. This requests no tolerance, and also checks actual deals; market execution can still slip and require emergency liquidation. |
| InpNewsClosureLeadSeconds |120| Begin at event minus5 minutes, verify all closed before minus3. Trial allowance for up to4 Core positions:4×15seconds plus timer/coarse-clock allowances, with additional margin. It is not a guaranteed completion deadline. |

Measurements and raw hashes: configs/core-demo-measurements-20261013.json.
The broker's published processing ranges are in the
[client agreement](https://www.litefinance.org/uploads/documents/pdf-litefinance/litefinance-client-agreement-fa.pdf?v=5e48f9eb).
The October14 CPI time was rechecked against the
[BLS calendar](https://www.bls.gov/schedule/2026/10_sched.htm):12:30UTC;
entry restrictions12:15–12:45UTC, closure starts12:25UTC and must finish before
12:27UTC. The supplied October14 day ends21:00UTC; do not reuse it after expiry.

Activation requires a separate review of CoreDemo.activation.patch, then compiling
the SAME EA with that one lock change. Only then set InpRequestCoreDemoExecution=true
and enable Algo Trading/Allow Algo Trading. There is no Inputs override for the lock.
Real/Contest and Reverse remain prohibited. Verify JOURNAL OK,PAIR LIMITS OK,CALENDAR_OK.
Approve ONLY a fresh, nonstartup, unconsumed,UNFILLED complete genuine two-BOS package
from the panel (>20 to <=40pips); approve after activation/restart, before the return.
The October14 inspected panel had a FULL H1 FVG and startup BOS; the package file
contained only its header. Neither that panel state nor October7 supplies a trade.

Terminal acceptance ON THE FIRST GENUINE TRADE, not a prerequisite synthetic trade:
verify two distinct .01 positions/deals for the selected BOS, canonical shared SL
and TP1/TP2; after an actual TP1 exit verify the remaining leg's SL at shared BE+5.
Restart the SAME EA with the SAME magic/journals and a NEW log name: no reopening,
same position IDs/protection. Exercise EMERGENCY STOP on remaining actual exposure;
verify Trade tab empty and persistent halt. These actual paired/BE/restart/closure
outcomes are not yet observed. Second-order failure/partial/unknown outcomes have
deterministic coverage; do not provoke live failures or invent a setup to test them.
