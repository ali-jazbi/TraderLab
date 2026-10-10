# Tester-only loss-aware recovery stress comparison

## Implementation and evidence scope

InpTesterStress defaults to false. Only the MQL_TESTER branch configures TLTesterStress; a Live/Demo instance ignores both stress inputs, including invalid skip counts. Existing live startup, timer, history queries, ticks, detectors and FileFlush remain unchanged. No sleep or synthetic market tick is used.

The first tester callback always establishes/drains the existing accepted baseline. Thereafter, when enabled with InpTesterStressSkipCallbacks=N (positive integer), skip N OnTick drains, perform one drain, and repeat. All actual callbacks still increment ontick_callbacks; drain_calls counts only calls made to Drain. The pure scheduler never owns/advances a tick cursor. While a skip window is pending, timer drains AND closed-bar scans are held so the timer cannot undo the intended backlog. The next selected callback uses the existing CopyTicksRange history/prefix recovery. Deinit always performs the existing final drain, including a run ending inside a skip window.

TICK_CAPTURE_START records the deliberately excluded startup snapshot and full same-ms multiplicity as before. Stress never changes or shifts this baseline. History alone supplies every emitted MqlTick; raw timestamps/values/ordered same-ms multiplicity and fatal prefix mutation/truncation/reordering checks remain intact. The first-callback snapshot is excluded explicitly, so this is not full-period replay including the first snapshot.

Tester-only TESTER_STRESS_CONFIG records environment, enabled, skip_callbacks, policy=skip_n_drain_one_after_baseline and timer_policy=hold_during_skips. TESTER_STRESS_SUMMARY before the final capture summary records callbacks_seen, skipped_callbacks and deferred_timer_calls. Both are known second-precision lifecycle events; there are no per-skipped-callback timestamps that would move the chronology floor ahead of the delayed ticks. Failure to initialize history/timer still stops the tester; errors remain invalid evidence.

## Exact MT5 procedure: normal then stress

1. Compile repository TraderLab.mq5 and StrategyChecks.mq5, including TickCapture.mqh and new TesterStress.mqh. Run the newly compiled StrategyChecks script and require `TraderLab native checks failures=0`. Its synthetic scheduler/cursor assertions do not test actual CopyTicks API availability.
2. Detach any old EA before replacing its binary; install the new TraderLab.ex5 in the terminal Experts folder and refresh Navigator. In Strategy Tester choose **single local test**, optimization off, exact **XAUUSD_o**, **M1**, **Every tick based on real ticks**, From **2026-10-07** to **2026-10-08**. Dates refer to broker/server calendar. Preserve the same terminal/agent build, history, settings and date range for both passes. Preserve previous failed captures.
3. Run the normal pass with:

   ```ini
   InpBrokerSymbol=XAUUSD_o
   InpLogFile=TraderLab-tester-normal-20261007-20261008-run01.jsonl
   InpServerUtcOffsetSeconds=10800
   InpTehranUtcOffsetSeconds=12600
   InpTesterStress=false
   InpTesterStressSkipCallbacks=8
   ```

   Independently verify the historical October 7 server offset before using10800 as accepted metadata. A prior configured value is not independent verification. Use unique filenames if these exist; no overwrites.
4. Run the stress pass with **identical settings/data**; change only:

   ```ini
   InpLogFile=TraderLab-tester-stress-20261007-20261008-run01.jsonl
   InpTesterStress=true
   ```

   Keep skip_callbacks=8. Let each pass finish cleanly. Expect deferred startup, capture start, tester config/summary, TICK/recovery/closed-bar observations and final capture summary/deinit. If a short period produces no skipped callbacks or no recovery, the comparison must fail; use a fresh pair covering more callbacks, never relax acceptance or fabricate ticks.
5. Locate both raw JSONL files in the **tester agent** MQL5/Files sandbox (not live terminal Files). Example using the observed local agent:

   ```powershell
   $testerFiles = 'C:\Users\mehdi\AppData\Roaming\MetaQuotes\Tester\D0E8209F77C8CF37AD8BF550E51FF075\Agent-127.0.0.1-3000\MQL5\Files'
   $normalCapture = Join-Path $testerFiles 'TraderLab-tester-normal-20261007-20261008-run01.jsonl'
   $stressCapture = Join-Path $testerFiles 'TraderLab-tester-stress-20261007-20261008-run01.jsonl'
   python D:\Github\TraderLab\tools\inspect_capture.py $normalCapture
   python D:\Github\TraderLab\tools\inspect_capture.py $stressCapture
   python D:\Github\TraderLab\tools\compare_stress_capture.py $normalCapture $stressCapture
   ```

   Use the actual local agent folder if different. Comparison reads raw files and writes only its JSON report to stdout; it never normalizes/repairs/alters inputs.
6. Require exit0/status=PASS. The comparison requires both inspectors clean; no unresolved/blocked diagnostics; matching baseline millisecond/count/policy/version; normal=false and stress=true tester metadata; identical callback totals and reconciled skip schedule; positive skipped_callbacks and stress recovered_ticks. Entire ordered TICK rows are exactly equal except global event seq, which can differ with recovery diagnostics. This includes tick_index, raw fields, UTC/server/Tehran timestamps, time_msc and same-ms ordinals. No intersection, trimming, rounding or baseline alignment is attempted.
7. Require zero ambiguities and API/timer errors and zero duplicate emitted occurrences. Occurrence identity is (time_msc,millisecond_ordinal); identical raw records with distinct ordinals are legitimate. duplicate_overlap_skips measures successful re-reading of the retained prefix and should not be required to equal0. The comparison reports emitted count and a common sequence SHA256, skipped/deferred counters and recovery totals. recovered_ticks must exceed0 but is diagnostic classification, not proof that a broker lost NewTick notifications. Save both raw files, comparison output and Tester Reports/Journals. Tester real-tick mode can substitute generated ticks for inconsistent/absent minute history; this code creates none and validates the supplied tester-history stream, not complete original broker feed.

## Verification and limitations

2026-10-10: **80 Python tests passed**. Actual MetaEditor compilation: TraderLab 0 errors/1 existing version-format warning; StrategyChecks 0 errors/0 warnings. New Python tests cover exact comparator CLI acceptance/refusal, unchanged raw inputs, legitimate identical same-ms records, altered raw fields/ordinals, missing ticks, baseline mismatch, zero recovery, schedule/counter mismatch and capture errors. Native TesterStressChecks cover tester gating, ignored live requests, deterministic skips, held timers, common baseline, exact normal vs delayed fixture sequence and zero overlap duplicates. Python source guards do not execute these MQL assertions.

**Native script runtime and the real normal/stress MT5 pair are UNVERIFIED until run.** Passing synthetic tests or compiling is not a claim that historical API availability or real sequence parity passed. All previous failed raw captures remain unchanged and invalid. No broker execution API or strategy rule was added.
