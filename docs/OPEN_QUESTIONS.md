# Unresolved decisions

Unresolved production inputs remain null. Owner-confirmed §52 policies now have explicit resolved values. Fixture values are modeling assumptions, never approvals of strategy rules.

2026-10-18: the project owner authorizes separate historical discovery experiments,
including fresh/impulse membership, post-confirmation arming and actual-fill single
BE. These do not resolve the production questions below. See the fixed
[study definitions](CORE_DISCOVERY_STUDY_20261018.md); default policy0 is unchanged.

| ID | Question / required input | Blocking scope | Canonical section |
|---|---|---|---|
| Q-ASSOCIATION | Wick-tip containment is confirmed. How are multiple eligible BOSs/FVGs grouped/finalized and cross-timeframe packages selected? C3/C1 identity is preserved; the old chart mismatch remains unexplained. | Automatic package promotion, not price containment | 9–10,14–15,51–52 |
| Q-H1 | What mathematical H1 structure rule is required? | H1 observation only | 3 |
| Q-PARTIAL | Does any partial FVG fill retain validity? | Core after partial penetration | 7 |
| Q-DISTANCE | What happens at <10 and >40 pips? | These selection branches | 15 |
| Q-SINGLE-BE | Single-entry BE entry anchor: actual executed entry versus planned reference? Dual BE is resolved to the shared TP reference. | Single paper BE until explicitly supplied; do not re-ask dual reference | 22,52.3 |
| Q-SESSION-CALENDAR | Supply a sourced Sydney-opening/New-York-closing calendar with UTC instants, DST and availability times; do not invent session hours. | Trading-day accounting and entries | 24,52.3 |
| Q-DAY-OVERLAP | With sourced local Sydney opening and New York closing, adjacent day windows overlap during DST. Which day owns that overlap and when does the daily counter reset? Separate one-day packets are prepared; automatic rollover stays blocked. | Multi-day rollover; does not block one controlled day | 52.3 |
| Q-NET-COSTS | NET basis is confirmed. Supply USD contract/commission and actual fees/financing from broker evidence. | Cost-complete performance and gateway reconciliation | 24,52.3 |
| Q-CHART-EXECUTION | Verify SYMBOL_CHART_MODE and broker quote/deal metadata. Supported implementation observes exact Bid-chart signal, buys at observed Ask / sells at Bid, with actual broker fills separate. LAST charts unsupported. | Execution implementation input, not a terminology question for owner | 13,39,52.2 |
| Q-BROKER-RUNTIME | Exact symbol alias, tick/volume grid, account mode, currency and contract must be captured from the active MT5 account; dynamic values can change. | Broker preflight and PnL | 1,20 |
| Q-BROKER-TIME | Explicit server and Tehran UTC offsets must be supplied for each capture. LiteFinance GMT+2/+3 seasonal schedule is documented; transition-day/time configuration needs runtime validation. | Timestamp normalization and session analysis | broker |
| Q-BROKER-AGREEMENT | Confirm the applicable LiteFinance legal entity and current account-specific agreement/limits before Demo execution. | Broker gateway enablement | broker |
| Q-COSTS | Observed spread, commission, slippage and realized TP/limit fills; keep paper assumptions explicit. | Paper execution; never guessed from OHLC | execution |
| Q-NEWS | Supply a reliable CPI/NFP/FOMC calendar with coverage and announcement availability, plus deadline monitoring. Reverse restriction and all-position closure by event minus3 minutes are confirmed. | New entries and deadline-safe position management | 26,52.4 |
| Q-NY-CUTOFF | London-only scan end / NY start, range endpoint inclusivity? | Definitive NY bias; provisional observations only | 29–32 |
| Q-NY-DOUBLE | Both range sides break: what bias wins? | Bias becomes ambiguous, no hard entry gate | 32 |
| Q-IFVG | Define the complete inversion/association and one/two-momentum sequence. Bearish close beyond OB is confirmed; bullish mirror and missing numerical conditions are not. Retain original >=10-pip penetration. | All Reverse submission disabled | 35–38,52.4 |
| Q-REV-DUAL | Which entries reverse for two-entry Core? | Dual-parent reversal | 44 |
| Q-REV-COUNT | Does reverse stop add a stopped setup or share parent's count? | Reverse with daily guards | 45 |
| Q-BE-STOP | Does a profitable BE stop count as a Daily Stop? | New entries after that event if unknown | 22–24 |
| Q-SIMULTANEOUS | Ordering when a single tick closes TP and SL and crosses $100? | Halt with unresolved reason; no fabricated chronology | execution |
| Q-LIFETIME | Group finalization/expiry and restart/day-boundary restoration remain unspecified. The retained ten-following-bar definition gives earliest safe confirmed availability; earlier consumed returns stay consumed. No additional Close or Big Candle break gate. Earlier provisional entry would need an explicit amendment to that definition. | Automatic grouping and durable lifecycle; no retroactive fills | 4,11–13,52.2 |

## Broker facts already recorded

LiteFinance is the intended broker profile. Support-confirmed account permissions and published agreement constraints are documented separately in [BROKER_LITEFINANCE.md](BROKER_LITEFINANCE.md). These facts do not resolve dynamic runtime properties or strategy questions.

No item requires an invented ICT/SMC convention. Confirmations belong in a dated spec amendment; parameterizing a rule does not make it confirmed.


## Resolved by owner amendment 2026-10-11 — do not re-ask

- Q-OB-BOUNDS: full reference candle [Low,High], wicks included; Buy C3 / Sell C1 preserved.
- BOS price bounds: Buy High wick tip / Sell Low wick tip with the original qualification rules; no pivot heuristic.
- H4-first is not mandatory. No numerical timeframe ranking was approved.
- Core reference: BOS+5 pips Buy / BOS-5 pips Sell. Unobserved crossed quotes do not create entries; restricted first touch consumes BOS.
- Q-SINGLE-SL and single Q-REV-SL distance: 40 pips; §52 subsequently resolved the anchor to actual fill.

The owner chart's 4114 / [4111,4116] / [4104,4111] has no supplied candle identities or timeframe mapping. Preserve it; do not invent the missing association or substitute C1 for confirmed Buy C3.

## Historical first-return boundary before owner §52 — 2026-10-12

The directional-return interpretation is a documented reading of prior examples, not newly direct owner-confirmed wording. Physical first-return chronology is now retained per BOS: late FVG/OB confirmation cannot reset consumed history. Q-LIFETIME and Q-ASSOCIATION still govern whether a qualified/broken BOS may associate with an FVG unformed/unconfirmed at its break and when a complete setup activates. Bid/Ask trigger selection and PARTIAL eligibility remain explicit unresolved policies. Automatic promotion stays blocked; no new cross-timeframe or activation rule is inferred. See [implementation evidence](FIRST_RETEST_AUDIT.md).

## Resolved by owner §52 (2026-10-12) — do not re-ask

Source: project owner's direct relay in this chat following 906f9db, not a new assistant interpretation.
Wick-tip/FVG containment; qualitative preformation BOS and larger-gap credibility;
no additional Close/Big-Candle break gate; single SL40 from actual fill; dual BE from
shared TP reference; Sydney-open to NY-close trading day with calendar/DST; NET daily
profit; paired setup counts once; Reverse news restriction and every-position closure
by event minus3 minutes; bearish momentum Close beyond OB. Original >=20-pip FVG
threshold survives. Partial and grouping remain blocked. Ten-following-bar confirmation
is preserved: earlier BOS qualification is allowed, but an already consumed return
cannot be revived once the FVG becomes confirmed.
Bid/Ask belongs to broker implementation and must not be re-asked as owner terminology.

The dated section above records the older audit state; §52 and the current table supersede its
resolved risk/news/quote questions. See [DEMO_READINESS](DEMO_READINESS.md) and
[isolated gateway safety and manual checks](DEMO_GATEWAY.md).

## 2026-10-13 engineering evidence — do not re-ask owner

The user reports StrategyChecks and DemoGatewayChecks failures0 at60654a2,
dispatch_lockedtrue, DEMO/USD/HEDGING, XAUUSD_o BID chart, tick size0.01,
minimum/step0.01 and free margin1000 USD. These are reported terminal observations;
margin and properties require fresh checks before each future dispatch.
Native integration now exists, but grouping/finalization, PARTIAL permission and
single BE anchor remain unanswered. An owner-approved dual package can use the
answered shared BE rule; no grouping shortcut is approved. New CorePipelineChecks
runtime and native broker fault handling still need terminal evidence.
See [current report and exact next actions](DEMO_READINESS.md).

2026-10-17: user permits historical experiments for crossing≤5pips, non-FULL FVG
and independent consumed-member handling. This is permission to study fixed
interpretations, not owner confirmation of grouping/PARTIAL or deployment approval.
