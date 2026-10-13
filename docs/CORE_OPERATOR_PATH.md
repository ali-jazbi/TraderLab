# Operator-approved Core: MT5 chart path

Automatic package discovery remains blocked by canonical §§51–52: the complete
BOS membership and its finalization are not defined. The chart panel implements
OPERATOR_APPROVED_CORE; it does not claim automatic discovery.

## Use the existing EA

1. Run the updated CorePipelineChecks once (new package/execution/calendar/restart
   checks; no broker transport). Keep Algo Trading OFF.
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
Python software checks and MQL compilation are recorded separately; the added
native assertions and chart interaction must still be executed in the terminal.

Executed for this update:162 Python tests passed; MetaEditor compiled TraderLab
(0 errors,1 preexisting version warning), CorePipelineChecks and StrategyChecks
(each0 errors,0 warnings). No broker order or native script was executed.
