# AUTO_CORE audit v2 — 2026-10-16

Status: **BLOCKED**. Base: `202b7949717b9807da1075408563911e9305c9bc`.
This is a source audit and a locked candidate, not a fresh market backtest or a
completed autonomous Demo release. No order was submitted to a broker or Tester.

## Available evidence and limits

The local TraderLab checkout has no `work/auto-core` directory. Its `outputs/`
contains only `.gitkeep`. The installed MetaQuotes terminal has an empty
`bases/LiteFinance-MT5-Demo/ticks` tree; the searched terminal/tester folders have
no native JSONL capture. The previous report refers to another user's paths
(`C:/Users/mehdi/...`, `D:/Github/TraderLab`). Bar history is not real-tick evidence.
The current terminal process was left running and its files were not changed.
No ticks were downloaded or reconstructed and no multiweek backtest was repeated.

The following counts are **inherited assertions in `AUTO_CORE_BACKTEST.md` at
202b794**, not results independently reproduced here:

| Same-frame package result | Count | Meaning |
|---|---:|---|
| FULL | 253 | Confirmed invalid gap; cannot restore UNFILLED |
| PARTIAL | 238 | Partial permission unresolved; cannot waive it |
| Equal BOS levels | 87 | Baseline rejects ambiguous candle identities |
| No contained qualified BOS | 36 | No as-of eligible membership |
| Single BE unresolved | 23 | Canonical selection leaves one entry; no approved BE anchor |
| Consumed first return | 25 | Group activation cannot recreate the past |
| Distance >40 pips | 19 | Unapproved selection branch |
| Distance <10 pips | 5 | Unapproved selection branch |
| Total rejected | **686** | Exclusive first reasons, not all overlapping blockers |
| Accepted geometry | **2** | Not proof of an executable setup |

Inherited run: 4,856,518 ticks; Model=4 according to the old report; 0 executed
entry orders and 0 closed positions. PnL, Win Rate, Profit Factor and Drawdown
are **undefined** for the no-trade sample. Fresh Tester metrics and order count
are **unavailable**, since no new real-tick run could be performed.

## Precise chronology and the two accepted groups

Native sequence: BeforeTick delivers only closed bars → confirmed FVG availability
after ten subsequent closes → `Prices` freezes membership → `Prices` applies the
current Bid to FVG fill → BOS trackers detect the first directional return →
`ExperimentalReturn` → pending dispatch at the current drain boundary → the
original Core book, gateway, quote/history, news, daily and margin guards.
No new confirmation close or provisional pre-confirmation entry is introduced.

The prior report records no selected post-availability first return for either
accepted group. That temporal claim cannot be re-audited without its raw capture.
The existing generic `NO_ACTIVE_EXPERIMENTAL_GROUP` also hid a different case:
selected membership existed but the current tick made its gap PARTIAL/FULL.
New diagnostics distinguish these cases and record the selected identities,
frozen time, entry prices, fill before/after tick and whether the exact quote occurred.

There is a further **static geometric blocker**, provable from the published
candidate bounds without fabricating any quotes:

| SELL group (broker availability) | FVG | Lowest/highest BOS | Selected references |
|---|---|---|---|
| Sep 28 04:25:00.130 M5 | 4239.65–4249.89 | 4244.14 / 4246.82 | 4243.64 / 4246.32 |
| Sep 28 06:15:00.193 M15 | 4239.18–4249.89 | 4244.14 / 4246.44 | 4243.64 / 4245.94 |

Every selected reference lies strictly inside its FVG. Any exact SELL return to
these references necessarily has Bid > FVG.low, hence PARTIAL (or previously FULL).
Even a future return cannot enter while retaining the existing UNFILLED gate.
Checking only pre-touch UNFILLED would grant a new same-tick PARTIAL permission;
this is a strategy assumption, not a demonstrated ordering bug, and was not done.
For a dual plan with distance >20 pips, the second reference is necessarily inside
the gap or beyond its near edge; a fully UNFILLED-only policy can therefore block
the second stage even when the first stage was outside the interior.

Selection still uses the actual high/low of the entire frozen membership, the
directional five-pip offset, and the unchanged 10/20/40-pip branches. No subset is
chosen by later returns, profit, fill state or distance suitability.

## Actual programming fixes

1. Both implementations previously tested BOS qualification against finalization
   delivery time. They now use the FVG's actual confirmed availability timestamp.
   This closes a late-delivery lookahead path; it is not claimed to explain any
   specific historical rejection without the missing capture.
2. Python previously marked a future gap finalized before raising its validation
   error. Validation now precedes mutation, so retry cannot silently skip it.
3. Python promoted setups did not receive later closed-bar gap invalidations,
   unlike native `ClosedBar`. Monotonic fill propagation now preserves PARTIAL/FULL
   even if the next observed quote has recovered outside the gap.
4. Native first-return diagnostics now identify selected-but-filled groups instead
   of reporting them as absent. Zero-closed-trade native metrics use JSON null.
5. An old source-contract regression still expected the pre-202b794 account-check
   spelling. Its assertion now covers the tester branch and the mandatory Demo check.

## EXPERIMENTAL policy, explicitly not owner-confirmed

Policies 1 and 2 remain the existing same/all-frame baselines. Policy 3 is
`same_frame_earliest_qualified_equal_level_v1`: collect same-frame, same-side,
contained, as-of qualified BOS; exact equal prices form redundant identity buckets;
keep the earliest qualification, then earliest candle opening, then lexical ID.
Freeze representatives once at confirmed FVG availability. Keep all original
identities in audit events. Apply canonical extreme selection to the representatives.
A consumed representative stays consumed; a later fresh alias cannot replace it.
Return outcomes are never used to choose membership. Baseline equal-level rejection
is unchanged. This is a defensible chronology-only hypothesis, **not tested on the
missing historical data**, and no improvement in trades or profit is asserted.

The old tester calendar hypotheses remain explicitly experimental: clipping day
overlap at the next Sydney opening and ex-post preknown news. They cannot authorize
Demo. The last stored one-day session ends 2026-10-14T21:00:00Z and cannot cover
the current date or future trading days. No expired calendar is supplied in the preset.

Primary schedules were freshly rechecked at 2026-10-16T15:16:38Z:
[BLS October](https://www.bls.gov/schedule/2026/10_sched.htm),
[Fed FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm),
[Fed October calendar](https://www.federalreserve.gov/newsevents/2026-october.htm).
A separate `configs/TraderLab-core-calendar-20261019.csv` packet covers the next
Monday session, 2026-10-18T20:00Z through 2026-10-19T21:00Z, using the rechecked
[broker local hours](https://www.litefinance.org/blog/for-beginners/time-at-forex/)
and IANA conversion consistent with [NSW DST](https://www.nsw.gov.au/about-nsw/daylight-saving)
and [NIST rules](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst).
No scheduled CPI/NFP/FOMC falls in that window; this is an inference from those
primary schedules, not an assumption that news can never be rescheduled. The source
timestamp is actual forward observation, never the backtest's ex-post January date.
The packet is for review, not selected in the locked preset. It supplies neither
continuous refresh nor broker-runtime holiday approval; rollover remains blocked.

## Artifact and checks

`mt5/AUTO_CORE_DEMO.mq5` compiles separately and reuses the original engine and
single OrderSend site. It is a **tester-only locked candidate**: non-Tester init
is rejected; Real/Contest remain rejected; Reverse remains absent. Its preset sets
no operator package, no panel, no Demo request, unique magic and no calendar.
The empty calendar deliberately blocks dispatch until sourced coverage is supplied.
An EX5 compiling successfully is not evidence of order execution or restart safety.

The candidate also implements a flushed `AUTO_TRIAL_SETUP` daily reservation before
the plan/order intent, allowing the same setup's second entry but rejecting another
setup that day. It restores that reservation when reading the journal and clears it
only on a validated sourced day transition. Candidate plan/gateway journal names are
separate from the operator build. The original operator journals are never deleted.
At entry preparation and again after the intent flush at the sole send boundary,
the candidate rejects any other-magic/manual position or pending order and reserves
the pair's remaining volume against the hard 0.04-lot cap. Existing margin checks
remain in force. A required USD open-risk budget and explicit aggregate cost/slippage
reserve gate entry using broker `OrderCalcProfit`; neither value is invented in the
locked preset. Missing budgets block. This estimate does not guarantee gap fills or
actual fees. These candidate controls have compilation evidence, **no native runtime
or broker fault-injection validation**.

`tools/audit_auto_core.py` reads a supplied native capture once, keeps every selected
first return (no arbitrary 30-event sample), reports chronological fill changes,
hashes the input, rejects incomplete/configuration-missing evidence and preserves
undefined metrics. It never downloads data, annotates orders or replays the strategy.
Example against an existing archive:

```powershell
python tools/audit_auto_core.py --capture work/auto-core/auto-weeks-same-02.jsonl --out work/auto-core/audit-v2.json
```

Python regression and native compilation results are recorded in the accompanying
validation manifest. Unit tests use explicitly synthetic identities/diagnostics;
they are not a market backtest. Native check scripts were compiled, not executed.
The graph extraction executable is unavailable locally; the graph report is marked
stale for these changes instead of claiming a regenerated dependency graph.

## Activation blockers

- Restore the original raw captures/manifests/Tester reports to verify all 688
  groups and run the new same-level hypothesis on the same genuine ticks.
- Establish a genuine selected first return followed by two simulator fills,
  canonical SL/TP, TP1→BE+5 and exit through the actual Core engine. Verify spread,
  duplicate suppression, incomplete pairs, restart, news closure and emergency halt.
- Runtime-test the candidate's durable one-new-setup/day, no-other-position,
  0.04-lot, risk and margin controls before a live-capable build. Supply evidence-
  based operational risk/cost budgets; their unset values deliberately block entry.
  Establish durable autonomous membership restoration as well as the existing
  first-return/plan/deal journals; live automatic membership remains unimplemented.
- Validate forward-calendar refresh, broker holiday coverage and rollover. The new
  October19 packet is one day only; historical ex-post news hypotheses must not
  become deployment inputs.

The compile-time Demo lock remains false. No installation into a terminal, live
journal mutation, broker submission, calendar approval, profitability claim or
READY certification occurred. The locked package is for review/testing only.
