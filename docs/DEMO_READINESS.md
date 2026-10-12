# DEMO readiness — owner §52, 2026-10-12

**Automatic setup approval and broker execution remain BLOCKED.** The isolated
DEMO gateway is default DISABLED, compile-time locked and not connected to the
capture EA. Answers have owner provenance in [canonical §52](sources/canonical-strategy.fa.md)
and [STRATEGY_SPEC](STRATEGY_SPEC.md).

## Implemented

- BOS candle wick-tip containment in FVG, independent of offset entry price. Qualified
  BOSs associate before later closed-bar break logs. Preformation BOS/gap credibility
  are qualitative, never mandatory ranking.
- Ten following closed bars still confirm Big Candle/FVG. No additional Close or Big
  Candle break gate. Earlier qualification is allowed; consumed first directional
  returns never reset at confirmation. Directional return remains a reading of prior
  owner examples, not a new direct confirmation.
- Single SL40 from actual paper execution quote plus explicit adverse modeled slippage;
  dual BE+5 reuses shared highest Buy / lowest Sell planned TP reference. Conflicting
  planned-SL, own-entry dual-BE, gross profit and Reverse news exemptions are rejected.
- NET daily profit, sourced Sydney-open/NY-close UTC calendar with DST/availability;
  paired stopped setup counted once. Fixed reset remains synthetic-test only.
- Verified Bid-chart signal separated from Ask Buy/Bid Sell and broker actual fills.
  Unobserved references never create fills. Production chart mode must be verified.
- News restrictions cover Reverse; paper closes every leg at observed exit quotes.
  Late quotes log deadline breaches; concurrent news/SL/TP rejects the case.
  Bearish confirmed momentum-close diagnostics do not enable Reverse.
- Isolated native gateway: account/volume/margin checks, durable duplicates, restart
  reconciliation, rejection handling, emergency/news closure. [Contract](DEMO_GATEWAY.md).

## Real October 7 historical batch

Market-only XAUUSD_o → XAUUSD adapter preserves broker metadata. Accepted:
**279,320 genuine ticks / 1,875 closed bars**, no setup annotations.

| Result | Count |
|---|---:|
| Confirmed Big Candles | 218 |
| Confirmed FVGs / full-candle C3/C1 OBs | 30 / 30 |
| BOS qualifications / closed-bar confirmations | 1,295 / 1,047 |
| Confirmed necessary wick-tip/FVG geometric pairs | 1,172 |
| Blocked same-timeframe / cross-timeframe pairs | 383 / 789 |
| Bid-lane intrabar breaks / directional-return diagnostics | 1,020 / 1,964 |
| Fully approved automatic setups / simulated trades | **0 / 0** |

Overlapping pair reasons: **787 FULL invalidities**, **374 PARTIAL blockers**,
**438 first returns consumed before FVG confirmation**, **385 package-grouping
blockers**, **789 cross-timeframe blockers**. These are diagnostic events/pairs,
not unique tradable opportunities. Only 11 pairs were UNFILLED at relationship
creation; this alone does not establish a complete eligible setup.

Other actual rejections: 1,557 bodies below twice average, 126 gaps below20 pips,
62 absent wick gaps, 2,291 breaks before qualification and 148 ambiguous same-bar
qualification/break order. Validation was not weakened to manufacture trades.
**Win rate, historical PnL and drawdown are unavailable, not zero performance.**

Full local evidence: `work/owner52-confirmed-batch-20261012/batch.json` and
`case-001/`. Large files are not committed. Reproduce with a fresh output directory:

```powershell
python tools/batch_backtest.py --events work/automatic-input-20261011.jsonl --config configs/production.template.json --out work/owner52-next-batch
```

Input SHA256: `2b6b1d99b95f3007f790bc1bf9477d7225af8d9c4986934cfe4414f3fbdd2417`.
Original visual tester raw SHA256:
`0f105703e67b4ce619cbd61dc675776ffac81fac7f64f8fcfdf116018969642f`.
Both remain unchanged. Batch carries code/config/spec and journal hashes.

## Minimum remaining owner decisions

| Priority | Exact remaining decision | Scope |
|---|---|---|
| 1 | How are multiple qualifying BOSs/FVGs grouped and when is the group final? Which cross-timeframe combinations/candle identities form the package? | Automatic promotion; containment itself is answered |
| 2 | Is PARTIAL FVG ever eligible; if so what exact penetration invalidates it? | PARTIAL stays blocked even if production config says allow |
| 3 | Does single-entry BE+5 use actual fill or planned reference? | Single BE only; dual BE and SL anchor are answered |

Preserved Big Candle definition makes confirmation the earliest safe availability;
no extra gate afterward. Earlier returns stay consumed. If provisional entry before
ten following closes is intended, that definition must explicitly change; future
closes cannot be observed early. Group expiry/restart policy, <10/>40-pip selection
and profitable BE-stop counting remain unresolved for their branches. Reverse stays
disabled pending complete inversion/association, momentum sequence, unsupported
bullish mirror, paired-parent and stop-count rules. H1 mathematical structure and NY
double-break/cutoff remain diagnostic. [All scoped questions](OPEN_QUESTIONS.md).

## Execution inputs and engineering blockers

- Sourced session calendar with DST, news coverage/availability and deadline monitoring;
  no fixed hours or news schedule invented.
- Active Demo identity, applicable broker agreement, verified chart mode, USD hedging,
  symbol/tick/volume/stops/freeze/filling properties, server offset and current margin.
- Observed commissions/financing, explicit paper slippage/TP policies. NET is confirmed,
  actual costs required; OHLC cannot prove executable fills.
- No native package controller, durable BOS consumption bridge or native TP1/BE
  controller connected. Guard booleans cannot replace reviewed integration.
- Native crash/timeout/reject/partial-fill/compensation tests, actual-fill SL repair,
  account-wide news closure and fresh Python/native parity need terminal evidence.
  Python gateway tests use a separate injected test transport.

## Verification and next MT5 step

**Executed:** 141 Python tests passed. MetaEditor: TraderLab 0 errors / 1 existing
warning; StrategyChecks and DemoGatewayChecks 0 errors / 0 warnings.
**UNVERIFIED:** native script execution, fresh historical parity and gateway broker
runtime behavior. No orders submitted. Core capture EA/native detection sources are
unchanged; native strategy policy integration is pending.

**Next:** LiteFinance Demo/XAUUSD_o: run compiled read-only `StrategyChecks` and
`DemoGatewayChecks`, save Journal (`failures=0`, `dispatch_locked=true`), then fresh
normal/stress October7 captures and comparator in [NATIVE_RETESTS](NATIVE_RETESTS.md).
[Exact installation](DEMO_GATEWAY.md). Keep execution disabled. Resolve the owner
questions above and supply calendars before the separate reviewed Demo execution
milestone.
