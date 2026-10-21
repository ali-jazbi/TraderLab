# TraderLab strategy specification v0.2

Status: detection, event logging, deterministic paper replay and isolated DISABLED
DEMO gateway preparation. No broker orders submitted.

Authority: the user-supplied [canonical document](sources/canonical-strategy.fa.md), sections 1–55 (later explicit owner amendments take precedence in their scopes). Local PDFs reviewed: BOS (16 pages), Order Block (11 pages), and Report-10180632 (7 pages; account performance, not detection rules). Their hashes are retained in the owner-wick and Body80 source evidence. Embedded `chatgpt-content-reference` markers are preserved but are not independently retrievable citations. `Explicit`, `Reference`, `Formalization`, `Old source` and `Unresolved` distinguish claims and implementation scope.

Newer explicit corrections take precedence (canonical §2). The latest source messages retrieved from the referenced chat agree with §§15, 35–39. The earlier assistant interpretation of reversal at the iFVG midpoint/edge is superseded by the original Core entry price.

| Rule ID | Canonical sections | Final behavior | Status |
|---|---|---|---|
| UNIT-01 | 1 | XAUUSD; one strategy pip = 0.1 price units, independent of broker point/digits | Explicit |
| TF-01 | 3 | No mandatory H4-first; Big Candle/OB observations on available timeframes; H1 structure and cross-timeframe association unresolved | Explicit / unresolved H1 |
| BIG-01 | 4 | abs(close-open) >= 2 × average bodies of 10 preceding + 10 following bars, excluding candidate | Explicit |
| BIG-02 | 4 | Momentum = Big Candle; detect only after all ten following bars close | Explicit / formalization |
| FVG-01 | 5 | Bullish: C3.low > C1.high; bearish: C3.high < C1.low; wick-to-wick gap, C2 impulse | Reference / formalization |
| FVG-02 | 6 | gap >=20 pips (2.0 price units), inclusive | Explicit |
| FVG-03 | 7 | Fully filled FVG invalidates Core; partial fill policy is unresolved | Explicit / unresolved |
| CORE-ELIGIBILITY-01 | 55 | Additional body(C2)/0.1 >=80 and at least one qualified directional-wick BOS whose candle precedes C2 and whose wick lies inside the FVG. Qualification retains its existing before-Break predicate and must be available at evaluation; it need not precede C2. Detection history, Big Candle availability and final grouping remain independent. | Explicit owner instruction and timing clarification, 2026-10-21 |
| OB-01 | 8 | Three-candle structure; Sell C1, Buy C3; full candle [Low,High], including wicks | Explicit amendment §51 |
| BOS-01 | 9 | Bullish candidate must have a later close < candidate.low BEFORE its high breaks; bearish mirror close > high before low breaks | Reference |
| BOS-WICK-01 | 54 | BUY High must exceed max(Open,Close); SELL Low must be below min(Open,Close). Compare actual broker tick units where supplied; no extra minimum wick size. Additional to BOS-01; rejected seeds cannot qualify in either detector/tracker. | Explicit new owner amendment; Oct15 first negative label conflicts with captured 0.05 upper wick and remains unresolved |
| BOS-02 | 10 | Buy level=qualifying candidate High; Sell level=Low; must be inside valid FVG; price containment confirmed; grouping/activation unresolved | Explicit / unresolved packages |
| BOS-AGE-01 | 53 | M1 requires a rapid reaction; a structurally valid old BOS may no longer authorize entry. No exact numerical cutoff confirmed. M15/H1/H4 retain longer validity; no new M5 or higher-TF numeric expiry. Preserve detection history. | Explicit qualitative amendment; Native TESTER-only60/120 first-return and pre-dispatch guards implemented; default0 unchanged; production cutoff unresolved |
| TOUCH-01 | 11–13,52 | First directional return after qualified wick break (reading of prior examples); Buy=BOS+5 pips, Sell=BOS-5; no extra close; restricted return consumed; verified Bid-chart observation separate from Ask Buy/Bid Sell execution | Interpretation / explicit / runtime quote verification |
| SELECT-01 | 14 | For >=3 BOS, select highest and lowest candidates | Explicit |
| SELECT-02 | 15 | 10 <= distance <=20: Buy highest, Sell lowest; 20 < distance <=40: both | Explicit |
| SELECT-03 | 15 | <10 unresolved; >40 independent 30-pip SL only old unconfirmed context | Unresolved / old source |
| SIZE-01 | 17 | Each entry 0.02 lot: 0.01 TP1 + 0.01 TP2 | Explicit example / old context |
| TP-01 | 18–19 | Fixed 60/100 pips; dual Buy references highest entry, dual Sell lowest | Explicit |
| SL-01 | 21 | Dual >20–40: Buy lowest BOS-30 pips; Sell highest BOS+30 pips | Explicit |
| SL-02 | 21 | Single Core SL distance=40 pips; actual executed fill anchor | Explicit amendment §52 |
| BE-01 | 22,52 | After TP1, remaining half SL Buy entry+5 / Sell entry-5; dual uses shared TP reference without requiring single-anchor config; single anchor unresolved | Explicit amendment §52 / unresolved single anchor |
| DAY-01 | 23 | Stop count by setup; dual entry stops count once; mixed SL/TP still counts one; two stopped setups halt new entries | Explicit |
| DAY-02 | 24 | Closed daily USD profit >=100 latches; continue until first subsequent stop; NET profit; Sydney-open through NY-close using sourced DST calendar | Explicit amendment §52 / runtime calendar required |
| TREND-01 | 25 | Valid counter-H4 setup permitted; no mandatory trend filter | Explicit |
| NEWS-01 | 26 | Block Core/Reverse +/-15 minutes around CPI/NFP/FOMC; every position closed by event minus3 minutes; source/coverage required | Explicit amendment §52 / execution input |
| NY-01 | 27–32 | Tehran time, M15 10:30–12:30 range; wick >=30 pips above => Buy bias; below => Sell bias | Explicit |
| NY-02 | 31–32 | Bias is context, not entry or mandatory rejection; both-side break and London/NY cutoffs unresolved | Explicit / unresolved |
| REV-01 | 33–38 | Executed Core + actual stop + broken BOS + OB penetration >=10 pips by wick + confirmed iFVG and one/two momentum closes beyond OB required; bearish close described, no bullish mirror approved | Explicit amendment §52 / incomplete inversion |
| REV-02 | 39–41 | Reverse at the original planned Core/BOS entry price, opposite side, exact observed retest; actual Core fill does not move this anchor; no immediate reverse just for SL | Explicit |
| REV-03 | 42–43,52 | TP60/100 and split retained; single Reverse SL40 from actual executed fill; no Reverse activation approved | Explicit amendment §52 / blocked inversion |
| REV-04 | 44–45 | Dual-parent reverse entry count and reverse stop accounting unresolved | Unresolved |
| SCOPE-01 | 47 | No EMA, RSI, MACD, ATR stop, dynamic TP, added trailing, grid, martingale, recovery by loss, additional session gate | Explicit |
| CLAIM-01 | 50 | 90% win-rate claim is not a rule or acceptance criterion | Source claim only |

## Implementation boundaries

`traderlab/detection.py` and `mt5/Include/TraderLab/Detection.mqh` implement confirmed bars and diagnostic BOS candidates. Wick levels and full OB candle bounds are automatic. `automatic.py` validates same-timeframe and cross-timeframe geometric containment and actual candle fill states, with stable pair IDs. Cross-timeframe pairs retain the FVG's own C3/C1 OB without ranking or inferred association. Unapproved association/grouping stays diagnostic-only; these pairs do not call `Engine.add_setup`.

`traderlab/strategy.py` implements selection/plans/daily guards. `traderlab/replay.py` consumes time-ordered closed bars, ticks and explicitly sourced setup/structure annotations. Zone annotation is the interim input boundary for missing formulas, not an alternative detector or an invented signal. A supplied setup is never retroactively traded before its availability timestamp.

The native EA logs actual MT5 ticks, closed bars, Big Candle/FVG and candidate BOS observations, plus broker capabilities and explicitly configured timestamps. Python replay keeps `planned_core_entry` separate from `actual_core_fill`: reverse retests use the planned level while PnL and costs use the actual fill. If adjacent executable quotes cross the retest price without observing it exactly, replay records an unresolved execution-data gap and consumes that first retest; it does not create a fill or alter REV-02. Native order execution and Python/MQL5 execution parity are pending. Broker-specific execution facts are kept in [BROKER_LITEFINANCE.md](BROKER_LITEFINANCE.md), not added as strategy rules. The offline paper model is independently executable without installing MT5.

## Canonical regression examples (§49)

1. Buy BOS4146/4143: both entries; shared SL4140; shared TP1=4152 / TP2=4156. Under an explicitly supplied USD100-per-price-unit-per-lot contract with zero costs, full stops=-18 and full targets=+38 USD. Those broker assumptions are fixture-only.
2. Exactly20 pips: one entry, Buy highest / Sell lowest. Exactly40 belongs to two-entry case. <10 and >40 remain blocked.
3. Stopped planned Buy4146.5; actual fill may differ (for example4146.7 after slippage). FVG4143–4147, BOS4145.5–4146.5, OB4141–4143. Wick4140 meets OB penetration threshold. Planned4146.5 remains the Reverse reference, not actual fill4146.7. Under §52 wick-only evidence cannot arm Reverse: momentum Close and complete inversion evidence are required. General single Reverse SL40 uses actual fill.

## Rule → code → executable regression

All checks below are in `tests/test_strategy.py`; the canonical section mapping is in the first table. Native helper coverage is in `mt5/StrategyChecks.mq5`; actual compilation and script execution are separate verification steps.

| Rules | Actual Python implementation | Regression method |
|---|---|---|
| UNIT-01, SELECT-01/02, SL-01, TP-01 | strategy.PIP / select_bos / core_plan | test_dual_buy_and_sell_levels, test_distance_boundaries, test_extremes_and_single_sl_unresolved |
| BIG-01/02, FVG-01/02 | detection.big_candle / fvg / Detector.accept | test_ten_future_bars_and_geometry, test_body_threshold_inclusive |
| FVG-03 | Detector.accept / Engine.tick | test_filled_before_delayed_confirmation, test_full_fill_blocks_core_and_no_temporary_config_fallback, test_partial_policy_missing_consumes_touch |
| BOS-01 | Detector.accept diagnostic candidates | test_bos_qualification_must_precede_break |
| OB-01, BOS-02 | Engine.add_setup sourced zones; OB bounds are [Low,High] on each observed timeframe | test_invalid_time_duplicate_zone_and_gap; automatic relationship promotion remains unresolved |
| TOUCH-01, SIZE-01 | HistoricalRetests / FirstReturn / Engine.tick / open_entry | test_full_tp_38_and_first_touch, test_news_first_touch_not_retried |
| BE-01 | strategy.breakeven / Engine.close_positions | test_be_and_ob_threshold, test_full_tp_38_and_first_touch |
| DAY-01/02 | DailyGuard / Engine.day_key / daily_pnl / close_positions | test_daily_stops_grouped_and_profit_latched, test_full_sl_18_counts_once_no_auto_reverse, test_daily_guard_blocks_pending_second_entry, test_cumulative_profit_does_not_reset_with_the_day |
| NEWS-01 | session.news_block / Engine.prerequisites | test_news_bounds_and_no_coverage, test_news_first_touch_not_retried |
| NY-01/02 | session.NYBias | test_ny_wick_threshold_and_both_sides, test_ny_cutoff_unknown_and_missing_range, test_soft_ny_bias_does_not_reject_counter_setup |
| REV-01/02/03 | strategy.ob_broken / reverse_plan / Engine.arm_reverse / structure | test_wick_only_reverse_now_requires_momentum_close_evidence, test_reverse_requires_every_condition_and_sl_anchor, test_annotation_no_reverse_without_executed_core, test_disabled_reverse_preserves_planned_anchor_despite_actual_fill_sl |
| REV-04 | Engine.arm_reverse explicit block | test_dual_parent_reversal_remains_unresolved |
| Unresolved config and execution | Engine.prerequisites / accept / tick | test_missing_config_never_silently_trades, test_costs_and_quote_spread_are_explicit, test_equal_time_ticks_require_capture_sequence, test_cross_day_open_positions_stay_unresolved |
| Reproducibility | replay.run / json_line / digest | test_deterministic_journal_and_manifest |

Trend/session hard gates, win-rate promises, invented cross-timeframe associations and all added indicators remain absent. Rule lookup does not convert an unresolved parameter into an approved value.


## Historical 2026-10-11 implementation and provenance (superseded where §52 answers)

Canonical §51 resolves the old BOS/OB bounds and single SL distance questions. The original PDF files were searched in the project, supplied attachment directory and original workspace; none were accessible. Original embedded references remain attribution only. The numerical chart example is preserved in §51.4; no chart OHLC/ticks were manufactured.

`Bos.level` distinguishes confirmed wick level from the directional planned entry. Legacy sourced `entry` annotations remain explicit planned prices (not automatically relabelled as BOS levels). New level annotations derive entry via `entry_reference` and reject conflicting supplied prices. Selection distances and dual SL use raw BOS levels; TP uses planned entry references. Single SL requires explicit planned/filled anchor; filled anchors are applied only after a modeled executable quote fill. Synthetic legacy regression PnL is not performance of the newly amended strategy.

`tools/automatic_backtest.py` accepts market inputs only, rejects setup/structure annotations, preserves broker metadata using the explicit configured symbol alias, and writes reproducible diagnostics without PnL or win rate. All geometric pairs remain blocked while association/grouping is unspecified; no configuration silently approves it. See [historical diagnostic results and MT5 steps](AUTOMATIC_BACKTEST.md).

### First-return implementation amendment (2026-10-12)

The Core directional-return interpretation is the current documented reading of prior owner examples, **not a new direct owner confirmation**. Python retains per-BOS tick break/outbound/consumed history before late FVG/OB association. Outbound movement does not consume; missed directional return consumes without fill. Ten-following-closed-bar confirmation is unchanged. Unknown association/activation still blocks automatic setups. Native now has a separate recovered-tick/as-of-closed-bar lifecycle; genuine MT5/Python parity remains unverified. See [native implementation and verification steps](NATIVE_RETESTS.md). See [audit and implementation evidence](FIRST_RETEST_AUDIT.md).

## Owner §52 implementation (2026-10-12)

The source is the project owner's direct relay of the final owner answers after 906f9db.
Conflicting planned SL, own-entry dual BE, gross daily profit and Reverse-news allowance
are rejected. Missing values for these resolved policies are filled from §52, not guessed.
`core_plan` single stops are only previews; `open_entry` anchors SL40 to the observed
quote plus explicitly modeled slippage. Dual BE uses the same highest Buy / lowest Sell
planned reference as dual TP, including the preserved directional five-pip entry offset.

Qualified BOSs are related to confirmed FVGs without waiting for the later closed-bar
BOS break log. `BOS_FVG_GEOMETRY_CONFIRMED` records owner-approved wick-tip containment.
Preformation BOS count and gap size are qualitative diagnostics, never mandatory ranking.
Qualification before FVG confirmation is permitted for geometric association; it is
not itself an activation failure. The retained Big Candle definition supplies the
earliest safe confirmed availability. There is no extra Close or Big Candle break
gate afterward. A return consumed before that availability cannot become an entry.
Complete package/grouping remains unresolved. Late confirmation never rearms a
consumed return or fills the past. An intended earlier provisional entry would require
an explicit change to the ten-following-bar definition, not future information.

Production day accounting requires a sourced Sydney-open/NY-close UTC calendar with
DST and availability timestamps. Fixed reset clocks remain only in labeled synthetic
fixtures. Profit is NET; two entry stages retain the same setup stop identity. Broker Bid
chart observation is separated from Ask Buy/Bid Sell execution and actual fill evidence;
production requires the runtime chart mode to be verified. This is engineering policy,
not a new owner rule or an assertion that requested and actual fill prices are equal.

Paper news exits use actual observed quotes by the three-minute deadline. Late quotes,
including a gap across the entire news window, log a breach and halt later entries;
concurrent news/SL/TP exit ordering rejects the paper case rather than fabricating it.
Bearish momentum-close diagnostics wait for confirmed Big Candles; all Reverse entry
paths remain disabled pending complete inversion/sequence evidence. No bullish mirror.

The native gateway has durable intent records, DEMO identity, margin/volume checks
and a compile-time dispatch lock. The 2026-10-13 milestone connects the chronological
Core controller/lifecycle while keeping the gateway disabled.
See [DEMO_GATEWAY](DEMO_GATEWAY.md) and [current readiness](DEMO_READINESS.md).
Regression coverage: `tests/test_owner_oct12.py`, plus revised legacy assertions whose
unresolved anchors/news policies were expressly superseded by §52.

### Native integration — 2026-10-13, engineering change only

NativeRetestStream supplies as-of closed candles and every accepted terminal-history
tick to CoreController. It reuses the original detector, including ten following
closes; legacy closed-bar diagnostics remain separate. Relationships require original
qualified BOS wick containment and confirmed full-candle C3/C1 OB. Candidate IDs,
availability, first return and rejection evidence are logged. Tick/closed-bar fill
observations are diagnostic; PARTIAL stays blocked. Retests persist independently
of later association. No expiry, ranking or group finalization is inferred.

CoreLifecycle prepares two-leg handling and reconciles broker deals using position
identifiers, paid costs and durable account-scoped plans. Grouping, single BE and
live quote proof cannot be replaced by a successful detector test. Startup candles
establish diagnostic history; recovered ticks are not presently executable proof.
Native reducer tests, compilation and terminal runtime evidence are distinct.

### Operator chart path — 2026-10-13, engineering change only

The existing EA chart displays genuine BOS/FVG/C3-or-C1 OB identities and prices.
Explicit operator membership is previewed, confirmed and persisted; it is not
automatic grouping or new owner confirmation. Consumed/startup returns, PARTIAL
and unknown single BE remain blocked. The minimal supported branch is a dual
package with owner-confirmed shared TP/BE. Two market legs share one original
signal; execution uses explicitly supplied time/spread/slippage budgets, terminal
history checks for intervening FVG penetration, and actual broker deal prices.
No execution default or missing strategy rule is inferred. Demo remains locked,
Real/Contest and Reverse remain blocked. See [short MT5 path](CORE_OPERATOR_PATH.md).

### Automatic target — 2026-10-14, user requirement; not an owner rule

The delivery target is autonomous Core discovery and management; manual BOS/FVG
selection is not the product path. `InpExperimentalAutoCoreTester` permits automatic
membership hypotheses only inside MQL_TESTER (1 same timeframe; 2 all timeframes).
Membership freezes at actual confirmed FVG availability, without expiry or ranking.
These hypotheses, session overlap allocation and ex-post news availability are
explicit backtest assumptions, not amendments to §§51–52. PARTIAL, consumed first
returns, ambiguous membership and unknown single BE remain blocked. Broker Demo
automation stays disabled pending defensible results and assumption review.

### 2026-10-17 user-authorized historical experiments (not owner amendments)

`InpExperimentalCorePolicyMask` independently selects TOUCH_CROSSING=1 (actual
Bid/Ask/fill within five strategy pips), NON_FULL_FVG=2 (PARTIAL permitted,
including PARTIAL at confirmed availability; FULL never), PER_BOS_MEMBERSHIP=4
(consumed selected member vetoes itself; frozen extremes/shared anchors unchanged).
Mask0 retains strict guards. Membership still uses the existing explicitly
experimental same-frame/equal-level policy; no new timeframe rule is confirmed.
Tester warm-up consumes earlier returns without executing or rearming them.
These permissions cannot enable Demo/Real/Contest or Reverse. See the actual
[native policy results](AUTO_CORE_POLICY_RESULTS_20261017.md).
