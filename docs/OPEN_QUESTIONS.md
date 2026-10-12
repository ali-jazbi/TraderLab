# Unresolved decisions

Production configuration values remain null until explicitly supplied. Fixture values are modeling assumptions, never approvals of strategy rules.

| ID | Question / required input | Blocking scope | Canonical section |
|---|---|---|---|
| Q-ASSOCIATION | Which candidate/FVG/OB belong together, across or within timeframes; which BOSs form one entry package and when is that group final? | Automatic setup promotion; geometric containment remains diagnostic only | 9–10,46,51 |
| Q-SL-ANCHOR | Is the confirmed 40-pip single Core/Reverse SL measured from planned reference or actual fill? | Single-entry plans / paper entries | 21,42,51 |
| Q-H1 | What mathematical H1 structure rule is required? | H1 observation only | 3 |
| Q-PARTIAL | Does any partial FVG fill retain validity? | Core after partial penetration | 7 |
| Q-DISTANCE | What happens at <10 and >40 pips? | These selection branches | 15 |
| Q-BE | Dual BE anchor: each entry or common reference? | New dual-entry paper positions until supplied | 22 |
| Q-RESET | Daily reset timezone and minute; stop aggregation across midnight? | Daily guards / entries | 24 |
| Q-PROFIT-BASIS | Does closed daily profit include commission/swap or deal profit only? | Profit latch uses explicitly supplied net/gross basis; swap remains unsupported | 24 / execution |
| Q-TOUCH | Which Bid/Ask triggers Buy/Sell and observes invalidation? Directional +5/-5 reference is resolved, not a +/- allowance. REV-02 specifically retests planned Core/BOS price. | Core touch and execution | 13,39 |
| Q-BROKER-RUNTIME | Exact symbol alias, tick/volume grid, account mode, currency and contract must be captured from the active MT5 account; dynamic values can change. | Broker preflight and PnL | 1,20 |
| Q-BROKER-TIME | Explicit server and Tehran UTC offsets must be supplied for each capture. LiteFinance GMT+2/+3 seasonal schedule is documented; transition-day/time configuration needs runtime validation. | Timestamp normalization and session analysis | broker |
| Q-BROKER-AGREEMENT | Confirm the applicable LiteFinance legal entity and current account-specific agreement/limits before Demo execution. | Broker gateway enablement | broker |
| Q-COSTS | Observed spread, commission, slippage and realized TP/limit fills; keep paper assumptions explicit. | Paper execution; never guessed from OHLC | execution |
| Q-NEWS | News source and coverage; reverse restriction; treatment of existing positions? | New entries if calendar unavailable; existing positions not force closed | 26 |
| Q-NY-CUTOFF | London-only scan end / NY start, range endpoint inclusivity? | Definitive NY bias; provisional observations only | 29–32 |
| Q-NY-DOUBLE | Both range sides break: what bias wins? | Bias becomes ambiguous, no hard entry gate | 32 |
| Q-IFVG | General FVG inversion and BOS break numerical semantics? | Reverse requires explicit sourced confirmations | 35,37 |
| Q-REV-DUAL | Which entries reverse for two-entry Core? | Dual-parent reversal | 44 |
| Q-REV-COUNT | Does reverse stop add a stopped setup or share parent's count? | Reverse with daily guards | 45 |
| Q-BE-STOP | Does a profitable BE stop count as a Daily Stop? | New entries after that event if unknown | 22–24 |
| Q-SIMULTANEOUS | Ordering when a single tick closes TP and SL and crosses $100? | Halt with unresolved reason; no fabricated chronology | execution |
| Q-LIFETIME | Setup expiry/restart restoration/duplicate setup identity and trade day policy? | Automatic setup activation/expiry and later native execution | execution |

## Broker facts already recorded

LiteFinance is the intended broker profile. Support-confirmed account permissions and published agreement constraints are documented separately in [BROKER_LITEFINANCE.md](BROKER_LITEFINANCE.md). These facts do not resolve dynamic runtime properties or strategy questions.

No item requires an invented ICT/SMC convention. Confirmations belong in a dated spec amendment; parameterizing a rule does not make it confirmed.


## Resolved by owner amendment 2026-10-11 — do not re-ask

- Q-OB-BOUNDS: full reference candle [Low,High], wicks included; Buy C3 / Sell C1 preserved.
- BOS price bounds: Buy High wick tip / Sell Low wick tip with the original qualification rules; no pivot heuristic.
- H4-first is not mandatory. No numerical timeframe ranking was approved.
- Core reference: BOS+5 pips Buy / BOS-5 pips Sell. Unobserved crossed quotes do not create entries; restricted first touch consumes BOS.
- Q-SINGLE-SL and single Q-REV-SL distance: 40 pips. The remaining question is anchor, not distance.

The owner chart's 4114 / [4111,4116] / [4104,4111] has no supplied candle identities or timeframe mapping. Preserve it; do not invent the missing association or substitute C1 for confirmed Buy C3.

## First-return activation boundary — 2026-10-12

The directional-return interpretation is a documented reading of prior examples, not newly direct owner-confirmed wording. Physical first-return chronology is now retained per BOS: late FVG/OB confirmation cannot reset consumed history. Q-LIFETIME and Q-ASSOCIATION still govern whether a qualified/broken BOS may associate with an FVG unformed/unconfirmed at its break and when a complete setup activates. Bid/Ask trigger selection and PARTIAL eligibility remain explicit unresolved policies. Automatic promotion stays blocked; no new cross-timeframe or activation rule is inferred. See [implementation evidence](FIRST_RETEST_AUDIT.md).
