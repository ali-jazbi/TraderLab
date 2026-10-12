# Native chronological BOS / first-return diagnostics

Implementation: 2026-10-12, following Python commit b5b00f3. Detection/logging only. Directional return is the current documented reading of prior owner examples, **not a new direct owner confirmation**. Unknown executable quote selection, FVG association/activation and PARTIAL permission remain unresolved. No automatic setups or broker orders.

## Data flow and clocks

`TLTickCapture` still validates the full terminal-history batch with the ordered-prefix cursor before emitting its suffix. Startup baseline, raw quote fields, same-ms occurrence ordinals, recovery counters and stress scheduler are unchanged. An optional `TLTickObserver` runs only for each accepted suffix occurrence, never for the callback snapshot or skipped overlap. `BeforeTick` supplies closed bars; TICK is written next; `AfterTick` feeds that occurrence to all five trackers. Global log sequence remains monotonically increasing; added events naturally change its numeric values. Raw TICK payloads and occurrence identities stay intact.

`TLNativeRetestStream` observes M1/M5/M15/H1/H4. Once per timeframe bucket it fetches actual CopyRates history bounded by the recovered tick's server time, excluding the forming candle and any candle whose close lies later than that tick. Warm-up uses up to 21 actual closed bars available at the first accepted tick; these are not retroactively available at their historical openings. Subsequent queries cover all closed bars since the prior accepted opening, including a drain spanning multiple closures. Missing/API-error/invalid OHLC or dispatch-order evidence emits `BOS_TRACKER_HALTED`; detection stops without resetting its baseline, while original raw tick capture continues.

The separate `BOS_TRACKER_CLOSED_BAR` stream records this precise as-of delivery before its `before_tick_index`. Original timer-driven `CLOSED_BAR`, BOS and Big Candle/FVG/OB observations remain intact. Thus the two closed-bar streams can have different delivery timestamps. Comparing a native intrabar lifecycle against the old timer-driven bars would compare different information-availability clocks. The comparator uses **only the tracker stream** for Python lifecycle replay. Standard normalization remains the original capture stream, not a silent substitution of new bar availability.

## Per-BOS state and evidence

`TLBosTracker` retains candidate -> qualified -> intrabar break -> outbound -> first directional return -> consumed/blocked. Qualification is the existing later candle close below Buy candidate Low / above Sell candidate High **before** wick break. A tick break before qualification is permanently blocked. A closed-bar wick crossing with no previously observed tick break blocks the unobserved lane; it is not assigned a fabricated break timestamp. Duplicate closed bars cannot recreate candidates. Stable IDs are `TF:SIDE:candidate_open_UTC+00:00`, matching Python when an explicit server offset exists. With unknown offset, IDs explicitly use server epoch and UTC fields are null; those logs cannot verify Python parity.

There are separate Bid/Ask **break observation** lanes, each with separate Bid/Ask **return observation** lanes. These are diagnostic alternatives, not chosen execution policies. Buy reference = wick High+0.5, Sell = wick Low-0.5. A Buy's first downward return from strictly above, or Sell's first upward return from strictly below, consumes once. Outbound equality/crossing does not consume. A return crossing without an exact observed quote records the actual adjacent prices and missed opportunity; no fill is invented. Identical raw tick records with distinct occurrence ordinals remain legitimate. A consumed return never retries.

Terminal histories remain archived when removed from the active scan. Neither the existing FVG/OB detector nor late closed-bar BOS logging resets them. No association is inferred from keeping that history. `Read(candidate_open,side)` exposes archived state for checks/future explicit association; current EA does not promote relationships. Closed BOS diagnostics now share stable `bos_id`; their `intrabar_break_at=null` still identifies their own closed-bar-only clock. Separate `BOS_INTRABAR_BREAK` supplies actual observed time.

## New events

- `BOS_TRACKER_CLOSED_BAR`: timeframe, actual OHLC, original opening, delivery timestamp and `before_tick_index`; no `kind=bar`, so legacy normalizer remains unchanged.
- `BOS_INTRABAR_BREAK`: stable identity, qualification/break timestamps, observation lane, wick level, observed quote, tick index and millisecond ordinal.
- `BOS_FIRST_DIRECTIONAL_RETURN`: break and return lanes, entry reference, outbound/return timestamps, adjacent observed prices, exact/missed flag, consumed=true and occurrence identity; always diagnostic_only, tradable_setup=false.
- `BOS_TRACKER_HALTED`: explicit reason and detection_halted=true, tick_capture_unchanged=true. Inspector flags attention; comparator rejects detector parity evidence.
- `BOS_TRACKER_SUMMARY`: processed ticks, bars, rates calls, event counts, active/archive sizes, candidate inspections and measured processing_us. This is a known second-precision lifecycle event; market timestamp validation is still strict.

## Performance boundary

Only nonterminal candidates are scanned per tick. Terminal history stays archived, without any invented expiry rule. Arrays grow with reserved blocks; CopyRates runs on timeframe transitions rather than every quote. The existing FileFlush policy is unchanged. Summary measures real tracker CPU/wall processing work including its bar fetches and diagnostic writes, excluding original raw TICK write time. Practical runtime on the full 279,320-tick MT5 capture is **pending terminal verification**, not inferred from Python or compilation. Review processing_us, candidate_inspections, active_bos and stored_bos after the run. A longer genuinely unreturned history can increase the active scan; it must not be discarded as an optimization.

## Comparison and current verification scope

`tools/compare_native_retests.py` validates the raw loss-aware capture, requires a nonhalted tracker summary reconciled against every TICK and diagnostic event, and replays the recorded tracker bars/ticks with unknown execution policies. It verifies each native event follows its genuine matching tick index, ordinal, timestamp and observed quote. For the two audited stable IDs it compares both observation lanes, true breaks, qualification times, outbound/return times, adjacent prices, exact flags, consumption and occurrence indexes. Duplicate diagnostics, missing candidates, mismatches and incomplete/legacy streams fail. It never modifies raw files or claims whole-system parity.

The existing Visual October 7 capture was read and correctly rejected as legacy evidence: it has no native tracker stream. Regression harness tests use genuine excerpt quotes with explicitly delayed bar delivery and Python-shaped native diagnostics solely to test the comparator. They are **not native execution or parity evidence**. Original normalized/raw hashes remain preserved.

New StrategyChecks assertions cover qualification, actual break, outbound exact touch, missed Buy/Sell return, exact mirrored returns, same-ms occurrence order, duplicate event/bar prevention, delayed confirmation, stable IDs and blocked-before-qualification preservation. Prior user-reported failures=0 applies to the previous script; the newly added checks require execution of the newly compiled binary. Compilation does not execute these assertions.

## Exact next MT5 verification

1. Detach any old EA before replacing its binary. Install the newly compiled repository `mt5/TraderLab.ex5` in the terminal Experts location and `mt5/StrategyChecks.ex5` in Scripts; refresh Navigator. Run the **new StrategyChecks** script and save Journal showing `TraderLab native checks failures=0`.
2. Strategy Tester: **single local test**, optimization off, symbol **XAUUSD_o**, period **M1**, mode **Every tick based on real ticks**, broker dates **2026-10-07 to 2026-10-08**. Keep the same agent/build/history as the successful capture. Independently verify the configured historical UTC offsets.
3. Inputs for a fresh normal run:

   ```ini
   InpBrokerSymbol=XAUUSD_o
   InpLogFile=TraderLab-native-retests-normal-20261007-run01.jsonl
   InpServerUtcOffsetSeconds=10800
   InpTehranUtcOffsetSeconds=12600
   InpTesterStress=false
   InpTesterStressSkipCallbacks=8
   ```

   Use a new suffix if the filename exists; preserve every previous capture. No new executable quote policy input is needed or approved.
4. After clean completion, use the actual tester agent Files folder:

   ```powershell
   $nativeRun = 'C:\Users\mehdi\AppData\Roaming\MetaQuotes\Tester\D0E8209F77C8CF37AD8BF550E51FF075\Agent-127.0.0.1-3000\MQL5\Files\TraderLab-native-retests-normal-20261007-run01.jsonl'
   python D:\Github\TraderLab\tools\inspect_capture.py $nativeRun
   python D:\Github\TraderLab\tools\compare_native_retests.py $nativeRun
   ```

   Require inspector integrity clean, no BOS_TRACKER_HALTED, summary processed_ticks matching all emitted ticks, and comparator exit0 / matches=true. Save runtime metrics and test Journal. Capture startup still excludes its accepted baseline; do not claim coverage of those pre-start ticks.
5. Inspect server-time quote evidence (Bid break lane, while both alternatives remain diagnostic):

   | Candidate | Actual break | First Ask return | First Bid return |
   |---|---|---|---|
   | M1 BUY 4141.82 / reference 4142.32 | 06:25:50.736 | 06:25:58.051, 4142.33 -> 4142.30, missed | 06:28:51.731, 4142.33 -> 4142.32, exact |
   | M5 SELL 4140.24 / reference 4139.74 | 06:06:25.538 | 06:12:47.038, 4139.73 -> 4139.79, missed | 06:12:53.153, 4139.71 -> 4139.84, missed |

   All times are October 7 server UTC+03:00. The Buy Ask 07:07:18.392 exact quote must never replace its already consumed first return. These are previously verified Python expectations, **not newly observed native results**. Qualification delivery can differ from the prior timer-driven capture; compare Python using the new tracker stream.
6. Repeat with a fresh `TraderLab-native-retests-stress-20261007-run01.jsonl`, changing only InpTesterStress=true and filename. Run the native/Python comparator on it too, then `tools/compare_stress_capture.py normal_path stress_path`. Require identical complete TICK sequences/baselines, zero cursor/API errors or duplicate emitted occurrences, and positive recovered_ticks. Recovery overlap skips are expected, not duplicated emissions. Because bar scheduling is tied to each recovered tick, batching must not change audited lifecycle events. No claim of complete native/Python parity until genuine fresh runs are inspected; these two candidates alone do not certify all strategy features.

## Verification performed in this commit

- Full Python discovery: **110 passed**, zero expected failures, 21.518 seconds. Seven new comparator/source-contract checks do not execute MQL5.
- Actual MetaEditor64 compilation: TraderLab **0 errors / 1 existing warning**, 2,730 ms; StrategyChecks **0 errors / 0 warnings**, 3,229 ms. Existing warning 68 is version `0.10` versus MQL5 Market `xxx.yyy` format.
- New native script execution, full historical tracker runtime and genuine native/Python event comparison: **UNVERIFIED, require the fresh MT5 steps above**.
- Existing normalized capture SHA-256 remains `2b6b1d99b95f3007f790bc1bf9477d7225af8d9c4986934cfe4414f3fbdd2417`; Visual raw remains `0f105703e67b4ce619cbd61dc675776ffac81fac7f64f8fcfdf116018969642f`. No raw capture or terminal binary was replaced.
