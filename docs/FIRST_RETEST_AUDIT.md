# First return versus outbound crossing — audit 2026-10-11

Original audit: 2026-10-11. The reproducible defects below are corrected by the 2026-10-12 implementation section. Broker execution remains disabled; raw captures are unchanged. No historical entry, fill or PnL is inferred.

## Authority reviewed

- `docs/sources/canonical-strategy.fa.md` §9: a later candle must close below the Buy candidate Low (above the Sell candidate High) **before** the structural wick level breaks. This requires a prior qualification close, not a close of the later break candle.
- Canonical §§11–12: one first touch, direct entry, no entry candle-close confirmation. §51.3: Buy BOS+5 strategy pips / Sell BOS-5, exact observed quote, missed crossing consumes the opportunity, restricted first touch consumes BOS. §51.2 retains ten following closed bars before Big Candle confirmation.
- Original pasted canonical source `7a509188-625e-428c-b9fc-24fadedc9d09/Pasted text.txt` preserves the same wording. The preserved Core sections say “first touch” without explicitly spelling out direction. Core FIRST RETURN is the current documented reading of the owner's prior examples adopted for this implementation. It is **not a new direct confirmation from the strategy owner**, nor an independently recovered literal quotation from the preserved Core sections.
- Existing owner/planned-entry reversal explanations (§§39–41 and previously supplied development/review attachments) concern **Reverse** entry. Their return semantics must not be misattributed as an independently recovered original Core quotation.
- `docs/STRATEGY_SPEC.md`, `docs/OPEN_QUESTIONS.md`, Python `detection.py`, `automatic.py`, `replay.py`, native `Detection.mqh` and `TraderLab.mq5` were reviewed. Original BOS/OB PDFs are still inaccessible locally. The referenced original conversation tool exposes only five recent turns with no older-page cursor; these cannot independently recover missing original PDF explanations. No owner is asked to repeat confirmed rules.

The directional interpretation used here is: after a qualified structural break, Buy returns **downward from above** its planned reference; Sell returns **upward from below**. Initial movement outward through the reference is the breakout leg, not the first entry retest. The audit's adjacent crossing check uses those directions and does not interpolate a missing quote.

## Genuine market evidence

All times are **2026-10-07 server UTC+03:00**. Analysis uses the hash-verified normal historical derivative `work/automatic-input-20261011.jsonl`; its complete 279,320-tick / 1,875-candle market sequence was independently matched to the currently present Visual raw capture. Exact rows are retained in `work/directional-retest-20261011.json`; raw files are unchanged.

### M1 BUY, BOS 4141.82, planned reference 4142.32

| Phase | Server time | Genuine quote / candle evidence |
|---|---|---|
| Qualification | 06:13:01.663 | Closed 06:12 M1 C=4139.61 < candidate L=4140.76. |
| Structural break | 06:25:50.736 | Bid=4141.93, Ask=4142.15; qualified BOS High=4141.82 breaks. |
| Ask outbound arrival | 06:25:56.941 | Ask=4142.32, Bid=4142.10, tick 44,203. **Not a retest.** |
| Ask beyond reference | 06:25:57.043 | Ask=4142.33, Bid=4142.11, tick 44,204. |
| **First Ask downward return** | **06:25:57.539 -> 06:25:58.051** | **Ask 4142.33 -> 4142.30**, Bid 4142.11 -> 4142.08. Consecutive tick indices **44,209 -> 44,210**, native seq 46,073 -> 46,074. **No exact 4142.32 quote on this return.** |
| Bid outbound arrival | 06:25:59.543 | Bid=4142.32, Ask=4142.54. **Not a retest.** |
| Closed-bar break logging | 06:26:00.798 | `BOS_CONFIRMED`; not the actual first break time. |
| Bid outbound crossing | 06:26:02.794 -> 06:26:03.098 | Bid 4142.22 -> 4142.35. **Not a return or a missed Buy retest.** |
| FVG geometry observable | 06:27:00.101 | C3 closes: FVG [4139.60,4142.19], full C3 OB [4142.19,4143.85]. Big Candle confirmation still pending. |
| **First Bid downward return** | **06:28:51.432 -> 06:28:51.731** | **Bid 4142.33 -> 4142.32**, Ask 4142.55 -> 4142.54, ticks 44,643 -> 44,644. Exact reference observed; setup confirmation still pending. |
| Big Candle/FVG/OB availability | 06:36:00.045 | Ten following candles have closed; FVG already PARTIAL. |
| Subsequent Bid return | 07:07:05.842 | Bid=4142.32; multiple previous downward returns already occurred. |
| **Second Ask downward return** | **07:07:18.090 -> 07:07:18.392** | Ask 4142.33 -> 4142.32, Bid 4142.11 -> 4142.10, ticks 49,574 -> 49,575. It is **not** the first return after structural break. |

**Consumption:** under the current BOS-relative first-return interpretation, the Ask opportunity is missed and consumed at **06:25:58.051**, with no fill. The later 07:07 exact quote cannot repair it. The Bid first-return opportunity occurs at **06:28:51.731** and is likewise spent before complete setup confirmation, although geometry is then observable. No historical entry is assigned to that observed exact quote. The original audit established these market facts; the 2026-10-12 tracker now retains these consumed states.

**Activation dependency:** whether a qualified/broken BOS may ultimately be associated with an FVG that was still unformed/unconfirmed at its break remains part of canonical §51.5's pending association/activation/lifetime policy. The unavailable confirmation prevents a historical entry at the earlier return. This is not uncertainty about which physical return was first, nor approval to discard that return or reset a consumed BOS when the FVG becomes available. The code must retain the evidence and block unresolved promotion; it cannot silently relabel 07:07 as first return. First RETURN and its direction remain the documented reading of prior examples. No entry close and missed-opportunity consumption are confirmed rules; no new owner confirmation is asserted.

PARTIAL permissibility remains unresolved (§7), but cannot revive an already consumed retest. FULL invalidity is later confirmed by the closed candle at 07:33:01.028, as recorded in the earlier timeline.

### M5 SELL, BOS 4140.24, reference 4139.74

| Phase | Server time | Genuine quote / candle evidence |
|---|---|---|
| Qualification | 05:30:00.154 | Closed M5 C=4146.92 > candidate H=4144.66. |
| Structural Bid break | 06:06:25.538 | Bid=4140.14 < BOS 4140.24; Ask=4140.36. |
| Closed-bar break logging | 06:10:01.068 | Later `BOS_CONFIRMED`. |
| Bid outbound crossing | 06:12:41.338 -> 06:12:41.550 | Bid 4139.80 -> 4139.63. **Not a Sell retest.** |
| Ask outbound crossing | 06:12:46.445 -> 06:12:46.943 | Ask 4139.75 -> 4139.73. **Not a Sell retest.** |
| **First Ask upward return** | **06:12:46.943 -> 06:12:47.038** | **Ask 4139.73 -> 4139.79**, Bid 4139.51 -> 4139.57; consecutive ticks **42,400 -> 42,401**. Missing exact 4139.74 quote. |
| **First Bid upward return** | **06:12:52.850 -> 06:12:53.153** | **Bid 4139.71 -> 4139.84**, Ask 4139.93 -> 4140.06; consecutive ticks **42,416 -> 42,417**. Missing exact 4139.74 quote. |
| Later exact Ask / Bid | 06:13:06.885 / 06:13:28.008 | Subsequent upward returns, not recoveries of the missed first returns. |
| FVG geometry observable | 07:40:00.855 | C3 closes; gap [4139.67,4141.76], Sell C1 OB [4141.76,4143.04]. |
| FVG confirmed available | 08:25:01.010 | UNFILLED; Bid=4132.53, Ask=4132.75. |
| Highest later prices | 10:33:09.657 | Bid=4139.38, Ask=4139.60; neither reaches the reference or FVG lower bound. |

Both quote sides' first directional returns cross without an exact quote and consume their BOS-relative first-return opportunities. General association/activation for this geometric pair remains unapproved; no historical entry was generated. Even an explicit later activation policy would find no post-availability contact through **23:58:59.945**. The gap remains UNFILLED.

## Defects reproduced in fb5aef6 (historical audit)

1. **Core replay lacks direction.** `Engine.touched` uses equality only, and the Core crossing branch uses symmetric `min < reference < max`. An available Buy setup consumes an upward outbound exact touch/cross; a Sell setup consumes a downward outbound touch/cross. Those are not first directional returns. Missing return crossing protection works once the first monitored movement actually is a return, but cannot repair premature consumption. `tests/test_first_retest_audit.py` reproduces all four outbound cases with entry dispatch mocked.
2. **Closed-bar BOS logging is being mistaken for the structural break clock.** Python `Detector.accept` and native `TLBarDetector.Process` inspect closed-candle High/Low. Native `ProcessClosedBars` runs after timer draining, timestamps observations with the latest captured tick, and records the break only after its candle closes. The log is valid closed-bar evidence; it does not provide the true intrabar break time. In this M1 example it lags the observed break by **10.062 seconds**, and arrives **2.747 seconds after the first Ask return was missed**. Using that timestamp as the start of the first-return history loses real chronology and could falsely promote the 07:07 return. No new break-candle close requirement is authorized.
3. **Automatic diagnostics do not track retests.** `AutomaticRelationships` consumes closed bars and logs geometric pairs; it never observes chronological tick retest history and never promotes an automatic paper setup. `Engine.consumed_bos` is populated only for annotated active setups. Therefore the analysis's spent market opportunity is not a claim that today's automatic engine actually stored a consumed state. Pair availability must not be treated as a history reset.

The earlier generic-crossing report `work/CANDIDATE_TIMELINE_20261011.md` is superseded on **entry/consumption semantics** by this directional audit. Its tick/candle timestamps and fill evidence remain factual.

## Original audit verification (2026-10-11)

Six focused regression methods were added: four explicit `expectedFailure` reproductions of existing outbound defects, plus passing mirrored exact-return and missed-return/no-retry checks. Full Python discovery: **96 tests, 92 passing and 4 expected failures**. Expected failures are known open defects, not a claim of corrected production behavior. Entry dispatch is mocked, so no test creates a historical trade or PnL. No MQL file changed; MQL compilation was not performed for this audit.

Next implementation should preserve one per-BOS directional history from the qualified wick break, carry consumed return evidence through late FVG association, distinguish structural break occurrence from closed-bar confirmation availability, and block promotion when pending-relationship activation is unresolved. It must leave the canonical ten-following-candle confirmation intact. Updating one symmetric crossing condition alone would leave the delayed-history defect unresolved. Production fixing/fixture migration is a separate step from these audit reproductions.

## Corrected implementation — 2026-10-12

`traderlab/retests.py` retains a stable per-BOS history keyed by timeframe, side and candidate opening timestamp. Closed bars create candidates and deliver qualification; genuine subsequent ticks establish the strict wick break, outbound movement and first directional return. A break before qualification permanently blocks that lane. A closed-bar break without an observed tick break is blocked rather than assigned the later logging time. No future candle is consulted; Big Candle confirmation still requires ten following closed bars.

Outbound equality/crossing never consumes the opportunity. A return from strictly above (Buy) or below (Sell) to or across the reference consumes once. Exact observed quotes and missed crossings are distinguished; a missing quote never produces a fill. Input sequence and tick occurrence index preserve same-millisecond ordering. Terminal history survives removal from the active scan and later FVG/OB availability.

`Engine` records `BOS_INTRABAR_BREAK` and `BOS_FIRST_DIRECTIONAL_RETURN`. Unknown break quote policy produces separate Bid/Ask diagnostic lanes; these are not approved execution choices. `AutomaticRelationships` attaches retained history to blocked geometric pairs and cannot promote them while association/activation policies remain unresolved. Explicitly sourced setup annotations using the stable observed BOS ID share its existing return object. Source-only legacy annotations have an explicitly asserted validity boundary and begin unarmed at availability; they do not fabricate an earlier structural break or outbound quote. Such annotations are not automatic historical detection.

The four expected-failure reproductions now pass. Legacy synthetic execution fixtures explicitly supply an outbound departure before a return; their unit-test PnL is not historical performance. `tests/fixtures/oct07-retest-market.jsonl` retains 1,540 genuine ticks and 66 genuine closed bars in original order, with provenance hashes. It is a sparse chronology excerpt, not a complete capture or tradable setup source. Both audited candidates retain their first-return evidence through late confirmation; the 07:07 Buy Ask quote cannot rearm it.

### Native parity boundary

Python has the full chronological lifecycle. Native `TLBarDetector` still processes closed bars; `BOS_CONFIRMED`/`BOS_REJECTED` explicitly identify `confirmation_source=closed_bar_wick` and `intrabar_break_at=null`. They must not be treated as true break timestamps. Native `TLDirectionalReturn` and `StrategyChecks.mq5` cover the mirrored directional predicate, but the EA does **not** yet feed every recovered tick into a native per-BOS lifecycle or persist native consumed-return state. This remains an explicit parity limitation. Live/Demo capture logic is unchanged. No broker order execution was added.

### Full genuine replay

Using the unchanged normalized capture and an explicitly configured **Bid chart diagnostic** lane: 279,320 ticks and 1,875 closed bars produce 1,020 intrabar breaks and 1,964 first-directional-return events (Bid/Ask return lanes, not unique tradable setups). There are 303 blocked geometric relationships and **zero fully confirmed automatic setups**, positions or inferred performance. Two full replays produced byte-identical journals. The journal SHA-256 is `b06d8b94f721f43d6517415ff8bca0baf222530b7598ac4ca2fdf39a450af2f7`. Unknown executable quote selection, partial-fill permission and association/activation policies remain fail-closed.

Verification commands: `python -m unittest discover -s tests -v`; compile `mt5/TraderLab.mq5` and `mt5/StrategyChecks.mq5` with MetaEditor64. Native script assertion execution is separate from compilation and was not performed. Full Python discovery: **103 tests passed, zero expected failures**, 16.287 seconds. Actual MetaEditor compilation: **TraderLab 0 errors / 1 existing warning**, 4,752 ms; **StrategyChecks 0 errors / 0 warnings**, 2,042 ms. The existing warning 68 concerns version `0.10` not conforming to MQL5 Market `xxx.yyy` formatting. Native script assertions were not executed.
