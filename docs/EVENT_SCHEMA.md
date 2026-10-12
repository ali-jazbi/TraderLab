# Event schema v0.2

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
