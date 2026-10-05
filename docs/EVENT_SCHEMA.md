# Event schema v0.1

All replay input is JSONL, explicit UTC `time`, chronological order, decimal prices/costs as strings (no binary JSON floats). Optional `event_id` must be unique. `symbol`, if present, is the canonical XAUUSD name; broker alias belongs in native capture metadata.

| kind | Required fields | Meaning |
|---|---|---|
| bar | time, opened_at, timeframe, open/high/low/close | Closed bar, available no earlier than open+timeframe duration. Late delivery retains late availability. |
| tick | time, bid, ask; tick_index for equal-time ties | Actual quotes, bid<=ask; explicit capture ordering for equal timestamps. |
| setup | time, setup_id, source, side, confirmed=true, fill_state, fvg=[low,high], ob=[low,high], bos=[{id,entry,zone}] | A sourced annotation of missing zone/linkage formulas, available now. Never silently generated from general SMC/ICT definitions. |
| structure | time, setup_id, source; bos_broken / ifvg_confirmed booleans | Sourced structural confirmation, not an independently implemented inversion threshold. OB10-pip penetration is measured from quotes. |

Prices/times must be valid. Bars must be strictly advancing and non-overlapping within a timeframe. BOS IDs are globally unique to prevent replaying consumed first touches under a new setup. Orders of input rows are preserved; OHLC does not generate fictitious ticks.

Output rows contain seq, time, event, rule and spec_version. Important events:

- BIG_CANDLE_CONFIRMED and FVG_CONFIRMED: candidate timestamp AND availability timestamp; complete/partial fill status at delayed confirmation.
- BOS_CANDIDATE_QUALIFIED/BREAK: qualification before break and an explicit ambiguous same-bar order flag. No zone inferred.
- SETUP_ANNOTATED/STRUCTURE_ANNOTATED: source attribution and explicit annotation boundary.
- CORE_PLAN/BOS_FIRST_TOUCH/PAPER_ENTRY: selected levels, observed quote, actual modeled entry, legs and NY alignment.
- PAPER_EXIT/BE_MOVED: fill, net closed USD PnL, daily profit latch, deduplicated setup stop count.
- OB_BROKEN/REVERSE_ARMED: linked original setup and original filled entry; no reversal based only on SL.
- ENTRY_BLOCKED/EXECUTION_UNRESOLVED: exact unresolved policy or guard.
- NY_RANGE_OBSERVATION/NY_CONTEXT: supporting context, not a mandatory entry filter.

NY records require explicit Tehran offset and endpoint/scan-end configuration for definitive bias. Complete eight-bar M15 range coverage is required. No EMA/RSI/trend replacement exists for H1. Both-side breaks remain ambiguous.

Paper fills use configured executable quotes and slippage; TP target/quote behavior and commission are explicit assumptions. Stop fills use the current executable quote with adverse slippage, exposing gaps. First touches during news or a guard are consumed. Quote gaps crossing a BOS without an observed quote inside its allowance consume the level and block its entry with an unresolved fill reason. No skipped-touch favorable fills are invented.

Open-position strategy expiry/reset restoration, swap, broker currency conversion, hedging/netting and autonomous zone association are not implemented. These belong to approved configuration/native execution follow-up, not historical profitability claims.

