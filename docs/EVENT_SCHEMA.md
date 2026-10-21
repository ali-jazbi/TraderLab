# Event schema v0.2

## Owner §55 additional Core eligibility gate

`FVG_CONFIRMED` / `CORE_FVG_CONFIRMED` retain existing weak-body and FULL
observations. Added `c2_ohlc` stores real C2 OHLC at the original ten-following-
close availability; BOS detection and qualification remain separate.
`CORE_SETUP_ELIGIBILITY` records `fvg_id`, `eligible`, `body_pips`, `witness_ids`
and `reasons` for the additional Body80 + pre-C2-contained-BOS gate. Python uses
an ID array; Native uses its existing semicolon-separated ID convention.
Python `CORE_PACKAGE_ELIGIBILITY` records the scoped package check; Native
rechecks before package planning, including the operator path.

Reasons: `C2_BODY_BELOW_80_PIPS`, `NO_VALID_PREFVG_BOS`, `BOS_OUTSIDE_FVG`;
missing source OHLC blocks with `C2_OHLC_UNAVAILABLE`. Only the BOS candle must
precede C2; qualification retains the existing before-Break predicate and must
be known at the evaluation cutoff. No added qualification-before-C2 condition.
Passing this additional gate is not a tradable-package approval. Existing gap
size/fill, membership, selection, first-return and execution guards still apply.
FULL remains blocked. PARTIAL remains blocked in the strict path and allowed
only by the unchanged experimental Tester mask where explicitly configured.
No detection or consumed-return history is removed/reset by the new gate.

All replay input is JSONL, explicit UTC `time`, chronological order, decimal prices/costs as strings (no binary JSON floats). Optional `event_id` must be unique. `symbol`, if present, is the canonical XAUUSD name; broker alias belongs in native capture metadata.

| kind | Required fields | Meaning |
|---|---|---|
| bar | time, opened_at, timeframe, open/high/low/close | Closed bar, available no earlier than open+timeframe duration. Late delivery retains late availability. |
| tick | time, bid, ask; tick_index for equal-time ties | Actual quotes, bid<=ask; explicit capture ordering for equal timestamps. |
| setup | time, setup_id, source, side, confirmed=true, fill_state, fvg=[low,high], ob=[low,high], bos=[{id,entry,zone}] | A sourced annotation of missing zone/linkage formulas, available now. Never silently generated from general SMC/ICT definitions. |
| structure | time, setup_id, source; bos_broken / ifvg_confirmed booleans | Sourced structural confirmation, not an independently implemented inversion threshold. OB10-pip penetration is measured from quotes. |

Native capture rows additionally preserve `server_time`, `server_utc_offset_seconds`, canonical UTC `time` with `Z`, `strategy_time` as Tehran wall time with its explicit numeric offset (for example `2026-10-06T12:30:00.123+03:30`), and `tehran_utc_offset_seconds` where known. Null/unconfigured offsets remain explicit and are rejected for replay import; the LiteFinance seasonal offset diagnostic never rewrites history. Server captures at GMT+2 or GMT+3 are normalized through UTC before Tehran strategy time is derived.

Native TICK `symbol` records the exact configured broker alias (for example XAUUSD_o); the preceding canonical-symbol statement applies to authored replay annotations, not native raw metadata. Native `timestamp_precision` distinguishes second-precision lifecycle observations from exact market milliseconds. Loss-aware TICK adds time_msc, broker_time_seconds, millisecond_ordinal, flags, last, volume and volume_real. Equal timestamps preserve distinct database occurrences via tick_index and ordinal, including identical raw records. [LOSS_AWARE_CAPTURE](LOSS_AWARE_CAPTURE.md) defines the start/recovery/error/ambiguity/summary schema, counters and run05 acceptance. New captures require final summary/deinit and no ambiguity/API errors before normalization; broker_feed_complete remains null. Legacy sequence continuity alone does not prove complete tick delivery.

Prices/times must be valid. Bars must be strictly advancing and non-overlapping within a timeframe. BOS IDs are globally unique to prevent replaying consumed first touches under a new setup. Orders of input rows are preserved; OHLC does not generate fictitious ticks.

Output rows contain seq, time, event, rule and spec_version. Important events:

- BIG_CANDLE_CONFIRMED and FVG_CONFIRMED: candidate timestamp AND availability timestamp; complete/partial fill status at delayed confirmation.
- BOS_CANDIDATE_QUALIFIED/BREAK: qualification before break and an explicit ambiguous same-bar order flag. No zone inferred.
- SETUP_ANNOTATED/STRUCTURE_ANNOTATED: source attribution and explicit annotation boundary.
- CORE_PLAN/BOS_FIRST_TOUCH/PAPER_ENTRY: selected levels, observed quote, planned Core/BOS entry, actual modeled fill, legs and NY alignment. Execution PnL/costs use actual fill; REV-02 retest uses planned Core entry.
- PAPER_EXIT/BE_MOVED: fill, net closed USD PnL, daily profit latch, deduplicated setup stop count.
- OB_BROKEN/REVERSE_ARMED: linked original setup, planned Core entry anchor and actual Core fill as separate values; no reversal based only on SL. Touching a slipped fill alone does not trigger REV-02. If consecutive executable quotes cross the planned retest without an exact observed quote, emit `EXECUTION_UNRESOLVED`, consume that first retest and do not invent a fill. This is execution-data protection, not a new strategy rule.
- ENTRY_BLOCKED/EXECUTION_UNRESOLVED: exact unresolved policy or guard.
- BROKER_CAPABILITY_SNAPSHOT/BROKER_CONFIG_BLOCKED/BROKER_TIME_OFFSET: runtime instrument/account snapshot and explicit capability/time validation. LiteFinance's documented ±30-minute margin/leverage-change window is recorded as broker metadata; it does not change NEWS-01's ±15-minute strategy rule.
- REQUEST_ALLOWED/REQUEST_RATE_WARNING/REQUEST_RATE_BLOCKED/REQUEST_PENDING/REQUEST_ACCEPTED/REQUEST_REJECTED/REQUEST_TIMEOUT/REQUEST_RECONCILED: reserved request lifecycle vocabulary for a future gateway; timeout remains unknown until authoritative reconciliation. Only confirmed no-execution may become eligible for explicit retry. The current diagnostic EA has no order-send site.
- NY_RANGE_OBSERVATION/NY_CONTEXT: supporting context, not a mandatory entry filter.

NY records require explicit Tehran offset and endpoint/scan-end configuration for definitive bias. Complete eight-bar M15 range coverage is required. No EMA/RSI/trend replacement exists for H1. Both-side breaks remain ambiguous.

Paper fills use configured executable quotes and slippage; TP target/quote behavior and commission are explicit assumptions. Stop fills use the current executable quote with adverse slippage, exposing gaps. First touches during news or a guard are consumed. Quote gaps crossing a BOS without an exact observed reference quote consume the level and block its entry with an unresolved fill reason. No skipped-touch favorable fills are invented.

Open-position strategy expiry/reset restoration, realized swap, broker currency conversion, hedging/netting and autonomous zone association are not implemented. Stop gap exits use the first observed executable quote plus explicit adverse slippage; TP fill policy is an explicit paper config, not an assertion about future liquidity. Pending-order gap semantics are documented but not modeled because Core entry remains direct on observed BOS touch. See [LiteFinance broker notes](BROKER_LITEFINANCE.md).

Tester-only TICK_CAPTURE_START_DEFERRED is a known second-precision lifecycle event (environment=strategy_tester, until=first_ontick, first_callback_history_is_baseline=true). It does not replace TICK_CAPTURE_START or certify valid tick capture. Missing first callback records TICK_CAPTURE_ERROR(reason=tester_no_first_tick). See [historical tester capture](HISTORICAL_TESTER_CAPTURE.md).

Tester-only TESTER_STRESS_CONFIG and TESTER_STRESS_SUMMARY are known second-precision lifecycle diagnostics. Config specifies enabled, skip_callbacks and scheduling/timer policies; summary specifies callbacks_seen, skipped_callbacks and deferred_timer_calls. They precede final TICK_CAPTURE_SUMMARY and do not certify valid capture by themselves. See [tester stress capture comparison](TESTER_STRESS_CAPTURE.md).


## Owner amendment 2026-10-11

Input `symbol=XAUUSD_o` is accepted only with explicit `symbol_aliases` mapping to XAUUSD. Original `broker_symbol` is retained in emitted events and diagnostics; no quote/timestamp/order transformation occurs. New sourced BOS annotations may supply `{id,level,zone}`: level is the wick tip; planned entry derives as level+0.5 Buy / level-0.5 Sell. A supplied `entry` must agree. Legacy sourced `{id,entry,zone}` remains an explicit planned-price annotation, not a detected level.

BOS_CONFIRMED / BOS_REJECTED include candle timestamp, level and reason. OB_CONFIRMED records full [Low,High] on each observed timeframe. BIG_CANDLE_REJECTED / FVG_REJECTED make failed closed-candle checks visible. FVG_VALIDITY_CHANGED records later full/partial penetration from actual closed candles. AUTO_SETUP_BLOCKED records stable BOS/FVG pair identity, direction/timeframe, actual BOS/FVG/OB levels, availability, directional entry reference, fill state and all blockers. `geometry_confirmed=true` and `diagnostic_only=true` do not authorize paper entry. One BOS may appear in multiple blocked pairs; these are not trades.

Core touch is the exact observed planned reference; symmetric expanded-zone touch is superseded. Adjacent quotes crossing the reference without observing it consume the opportunity and block fabricated entry. SL distance is fixed40 for single Core/Reverse; `single_core_sl_anchor` and `single_reverse_sl_anchor` require explicit planned/filled choice. Only a real modeled executable quote supplies a filled anchor.

## Chronological Core diagnostics — 2026-10-12

- `BOS_INTRABAR_BREAK`: stable `bos_id=TF:SIDE:candidate_open_UTC`, prior `qualified_at`, genuine `break_at`, `break_quote`, `observed_quote`, wick `level`, and `tick_index`. No closed-bar logging time is substituted for this tick occurrence.
- `BOS_FIRST_DIRECTIONAL_RETURN`: break/return quote lane, entry reference, outbound time, first return time/input order, occurrence index, adjacent quotes, `exact_quote` and `consumed=true`. Both exact and missed returns terminate that lane. These are diagnostic-only and never authorize an entry.
- Closed-bar BOS observations identify `confirmation_source=closed_bar_wick`; Python attaches `intrabar_history`. Native identifies `intrabar_break_at=null` because its full tick lifecycle is pending.
- `AUTO_SETUP_BLOCKED` carries retained intrabar history, including previously consumed returns. Late relationship discovery does not rearm them. Missing quote policy uses separately labeled diagnostic lanes and no approved executable choice.
- Annotated Core `BOS_FIRST_TOUCH` now has `directional_return=true`; missed return emits `EXECUTION_UNRESOLVED` with no fill. Source-only annotations begin unarmed at their availability; stable observed BOS IDs reuse retained history. Same-millisecond input order is significant.

## Native first-return stream — 2026-10-12

Native `BOS_TRACKER_CLOSED_BAR` supplies as-of bars before `before_tick_index`, separately from original timer-driven `CLOSED_BAR`. Native intrabar break and directional-return events share stable BOS identity, include both diagnostic observation lanes, exact server/UTC milliseconds and `tick_index`/`millisecond_ordinal`. Raw ticks are cursor-accepted history only. `BOS_TRACKER_SUMMARY` is explicitly coarse lifecycle precision; `BOS_TRACKER_HALTED` stops detection while leaving raw tick capture active. Comparator rejects halted or unreconciled detection evidence. Automatic promotion remains absent. See [native contracts, parity scope and MT5 steps](NATIVE_RETESTS.md); the earlier native parity limitation described above belongs to commit b5b00f3 and is superseded in implementation, not in verified runtime evidence.

## Batch paper evidence — 2026-10-12

`CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED` uses the same blocked pair contract as
`AUTO_SETUP_BLOCKED`, with explicit `bos_timeframe`, `fvg_timeframe`, `ob_timeframe`
and unresolved cross-timeframe association. It pairs an observed BOS with an FVG
and that FVG's own C3/C1 OB, not an inferred independent OB. No ranking or promotion.

`PAPER_ENTRY` adds stable `trade_id`, its two `position_ids`, observed Bid/Ask/spread,
modeled slippage and entry commission, `input_order` and optional `tick_index`.
`PAPER_EXIT` records those quote/order fields plus observed stop/target; `BE_MOVED`
records input order/index. These are simulated events only. Batch reports include
entries/exits, blockers, hashes and per-case tick-valued equity. Win rate uses fully
closed entries; no trades means null performance. Rejected cases cannot publish
partial results. See [readiness and batch invocation](DEMO_READINESS.md).

## Owner §52 events and input contracts — 2026-10-12

- `BOS_FVG_GEOMETRY_CONFIRMED` records wick-tip containment, not automatic package approval.
  Blocked pairs now include qualified BOSs before closed-break diagnostics; credibility count
  is qualitative and never a required filter. `formation_at` records C3 delivery separately
  from ten-following-bar confirmation. Grouping remains unresolved; earlier BOS
  qualification itself is allowed. `signal_quote` identifies the selected observation
  lane. `FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION` checks that lane's retained
  first return against confirmed availability, never a different lane's earlier return.
- `NEWS_FORCE_CLOSE` is a paper exit with observed quote, deadline and deadline_met.
  `NEWS_CLOSE_DEADLINE_MISSED` forbids backdating and blocks subsequent entries. Ambiguous
  concurrent price/news exits reject the batch case. Reverse news exemption is rejected.
- `trading_day_calendar` requires source, coverage_start/end, session_definition
  `Sydney_open_to_New_York_close`, and nonoverlapping sessions with id, sydney_open,
  new_york_close and available_at (all explicit UTC). This carries calendar/DST evidence;
  it is not a fixed session-hour rule.
- `REVERSAL_MOMENTUM_CLOSE_DIAGNOSTIC` records actual confirmed bearish Big Candle close
  beyond an annotated OB. It approves neither inversion nor a Reverse trade. All Reverse
  submission remains disabled. Broker gateway evidence is separate from native tick capture.
# Native Core additions — 2026-10-13

CORE_BOS/CORE_BIG_CANDLE/CORE_FVG/CORE_OB events apply existing rules to recovered
ticks/as-of candles. Legacy diagnostics remain separate. CORE_SETUP_CANDIDATE and
CORE_FIRST_RETURN_BLOCKED include stable BOS/FVG/OB identities, timeframes, candle/
availability/break/return timestamps, prices, fill state, quote evidence, reasons
and minimal approval evidence. Geometry alone is not a tradable setup.
CORE_BOS_CONSUMED records durability and historical context; association never rearms.

CORE_FVG_VALIDITY_CHANGED is monotonic diagnostic penetration. Source observed_bid
distinguishes genuine tick evidence from own-timeframe closed-bar evidence. PARTIAL
is unapproved; FULL invalid. Python relationship validity updates on closed bars;
tick-by-tick Core fill parity requires a fresh capture and is not claimed from legacy
logs. CORE_LOCK_STATUS and CORE_CONTROLLER_SUMMARY are second-precision lifecycle
records. TICK, closed-bar and market Core events retain strict millisecond validation.
No startup history or recovered quote is labeled a live executable signal.
