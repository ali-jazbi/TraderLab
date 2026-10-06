# Event schema v0.1

All replay input is JSONL, explicit UTC `time`, chronological order, decimal prices/costs as strings (no binary JSON floats). Optional `event_id` must be unique. `symbol`, if present, is the canonical XAUUSD name; broker alias belongs in native capture metadata.

| kind | Required fields | Meaning |
|---|---|---|
| bar | time, opened_at, timeframe, open/high/low/close | Closed bar, available no earlier than open+timeframe duration. Late delivery retains late availability. |
| tick | time, bid, ask; tick_index for equal-time ties | Actual quotes, bid<=ask; explicit capture ordering for equal timestamps. |
| setup | time, setup_id, source, side, confirmed=true, fill_state, fvg=[low,high], ob=[low,high], bos=[{id,entry,zone}] | A sourced annotation of missing zone/linkage formulas, available now. Never silently generated from general SMC/ICT definitions. |
| structure | time, setup_id, source; bos_broken / ifvg_confirmed booleans | Sourced structural confirmation, not an independently implemented inversion threshold. OB10-pip penetration is measured from quotes. |

Native capture rows additionally preserve `server_time`, `server_utc_offset_seconds`, canonical UTC `time` with `Z`, `strategy_time` as Tehran wall time with its explicit numeric offset (for example `2026-10-06T12:30:00.123+03:30`), and `tehran_utc_offset_seconds` where known. Null/unconfigured offsets remain explicit and are rejected for replay import; the LiteFinance seasonal offset diagnostic never rewrites history. Server captures at GMT+2 or GMT+3 are normalized through UTC before Tehran strategy time is derived.

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

Paper fills use configured executable quotes and slippage; TP target/quote behavior and commission are explicit assumptions. Stop fills use the current executable quote with adverse slippage, exposing gaps. First touches during news or a guard are consumed. Quote gaps crossing a BOS without an observed quote inside its allowance consume the level and block its entry with an unresolved fill reason. No skipped-touch favorable fills are invented.

Open-position strategy expiry/reset restoration, realized swap, broker currency conversion, hedging/netting and autonomous zone association are not implemented. Stop gap exits use the first observed executable quote plus explicit adverse slippage; TP fill policy is an explicit paper config, not an assertion about future liquidity. Pending-order gap semantics are documented but not modeled because Core entry remains direct on observed BOS touch. See [LiteFinance broker notes](BROKER_LITEFINANCE.md).
