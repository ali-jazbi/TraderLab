# Loss-aware native tick capture

Read-only terminal-history capture; no strategy change or broker execution. The user's run03 report confirms valid JSON and Demo/hedging permissions on XAUUSD_o, not complete tick delivery. Run04 is the first live validation of this implementation.

## Architecture

`TickCapture.mqh` owns a single TLTickCursor and TLTickCapture. OnTick increments the callback count and drains history; it contains no CopyRates/detector loop. A **one-second OnTimer** calls the same drain, then processes the five closed-bar timeframes once using the latest emitted source tick's timestamp. No five-timeframe scan runs per recovered tick. Deinit kills the timer, drains once more, processes pending closed-bar observations, writes the summary and then EA_DEINIT. MT5 serializes an EA's handlers; there is one cursor and one emitter.

Startup samples the configured symbol's latest MqlTick and requests its complete millisecond group with `CopyTicksRange(COPY_TICKS_ALL, head.time_msc, head.time_msc)`. The group must contain the sampled head. The accepted database snapshot is the explicit capture boundary: the entire baseline group and all earlier ticks are excluded. Capture begins after that snapshot, not at a guessed wall-clock millisecond or with arbitrary historical replay. Later appended occurrences in the startup millisecond are captured. Initialization fails if the baseline cannot be established.

Each drain samples a head and requests the inclusive range `[cursor.time_msc, head.time_msc]` in a dynamic array. It validates the whole result before consuming any suffix: API success with no error (even positive partial timeout results are rejected), raw seconds/time_msc agreement, chronological order and the sampled head's presence. No default 2000-tick CopyTicks limit or silent count cap is used. On API failure, no ticks are emitted and the cursor remains unchanged; later drains can retry, but the recorded error still makes the run unacceptable. Synchronization can block the handler; large backlogs can time out or exhaust memory, which must be reported rather than skipped.

The cursor retains **all raw records of the last millisecond in order**, comparing time, time_msc, bid, ask, last, volume, flags and volume_real. The next range must reproduce that exact full prefix. Only previously consumed occurrences are skipped. Distinct and repeated identical same-ms records appended after it are emitted individually. A missing, shortened, reordered or mutated prefix, missing head, invalid raw time or regression emits TICK_CAPTURE_AMBIGUITY and permanently halts tick emission/detectors for that run. Failed validation leaves the cursor unchanged. No price-only hash, blanket same-ms discard, fallback quote or fabricated tick exists.

MT5 provides no global broker tick ID. Evidence relies on an unchanged ordered terminal-history prefix; identical records cannot prove identity beyond occurrence/order, and changes leaving an identical observed prefix cannot be distinguished. Upstream broker/network omissions outside this evidence are not detectable from our sequence alone. **broker_feed_complete remains null**, even on a valid run; zero tick_index gaps prove only our emitted stream's continuity.

Primary references: [CopyTicksRange bounds/errors](https://www.mql5.com/en/docs/series/copyticksrange), [CopyTicks synchronization and batching](https://www.mql5.com/en/docs/series/copyticks), [OnTick coalescing](https://www.mql5.com/en/docs/event_handlers/ontick), [OnTimer](https://www.mql5.com/en/docs/event_handlers/ontimer).

## Tick schema and diagnostics

Existing TICK time/server_time/timestamp_precision/symbol/tick_index/bid/ask/spread fields remain. New fields: native integer `time_msc`, native datetime cast through long as `broker_time_seconds`, one-based full-database-group `millisecond_ordinal`, integer `flags`/`volume`, and decimal-string `last`/`volume_real` with 16 fractional places. Bid/ask/spread retain eight-place serialization; dedupe compares original native values before formatting. One strategy pip remains 0.1 XAUUSD price units.

TICK_CAPTURE_START records capture_version=loss_aware_v1, cursor, excluded baseline count, policies and timer_interval_ms=1000. TICK_CAPTURE_RECOVERY records drain source (ontick/timer/deinit), first/last emitted index and recovered count when positive. Error/ambiguity timestamps use the latest emitted tick if available, otherwise explicitly second-precision TimeCurrent; retries do not fabricate a future market timestamp. Final summary uses second-precision TimeCurrent.

| Summary counter/field | Meaning |
|---|---|
| ontick_callbacks | Handler invocations, including after a halt |
| drain_calls | Runtime drain calls, including halted/no-op calls; excludes baseline |
| copyticks_calls | Actual CopyTicksRange calls, including baseline |
| emitted_ticks | TICK writes attempted; equals final tick_index; reconciled against stored rows |
| callback_snapshot_matches | At most one newly emitted occurrence matching an OnTick head snapshot; last matching occurrence chosen deterministically |
| recovered_ticks | Emitted minus callback_snapshot_matches; timer/deinit emissions all count here. Not a count of provably dropped NewTick events |
| duplicate_overlap_skips | Sum of validated consumed prefix occurrences across drains; repeated reads count repeatedly |
| cursor_ambiguities | Fatal cursor/history-proof failures |
| copyticks_errors / snapshot_errors / timer_errors | History API, head snapshot and timer setup failures |
| capture_halted | Permanent stop, including failed initialization |
| terminal_cursor_evidence_valid | No halt or recorded error/ambiguity; scoped to terminal cursor evidence |
| broker_feed_complete | Always null: upstream completeness unknown |
| cursor_time_msc / cursor_boundary_count | Final full millisecond group; checked against final tick/ordinal |

`emitted_ticks = callback_snapshot_matches + recovered_ticks`. Callbacks can exceed emitted ticks when timers already drained notified ticks; emitted ticks can exceed callbacks when history contains additional occurrences. Recovery counters do not claim every broker tick arrived.

## Durability and acceptance

Existing **FileWriteString + FileFlush for every event is retained**. No buffering or delayed flush is introduced. Clean deinit flushes final ticks/summary/EA_DEINIT, then closes. A crash can leave an in-progress row incomplete and no final summary; there is no restart restoration or silent reuse of a file. FileFlush does not guarantee immunity to OS/device failure. Native write-error telemetry is outside this change; JSON integrity, stored-row/count reconciliation and the final envelope are required for acceptance, so an in-memory counter alone cannot certify successful storage.

Inspector validates start/summary/deinit, raw milliseconds/ordinals, chronological ticks/bars, contiguous emitted indexes and recovery totals. It prominently rejects error/ambiguity events, including errors followed by successful retry. Normalizer preflights new loss-aware captures through that inspector, refusing incomplete/error/ambiguous evidence before writing output. Legacy captures retain prior normalization rules and explicitly have no CopyTicks completeness evidence. Raw captures are not repaired or edited.

## Checks and verification

StrategyChecks calls TickCursorChecks with synthetic MqlTick arrays and no live API: normal tick, multi-tick delayed batch, overlap, distinct/identical same-ms occurrences, flags/real-volume identity, whole-batch chronology, exact milliseconds/UTC formatting, startup exclusion, missing/truncated/mutated/reordered/empty boundary, unchanged cursor on failure and raw seconds mismatch. These native assertions do not themselves test the live CopyTicks API or timer.

Python tests use synthetic recorded evidence: summary/ordinal/counter checks, strict timestamps, error prominence, raw preservation and end-to-end normalizer acceptance/refusal. Source guards check one native history path, separate detectors and retained flushing. **Python source tests do not execute MQL5.**

Verification on 2026-10-07: 67 Python tests passed. Actual MetaEditor 5.0.0.6244 compilation: TraderLab 0 errors/1 pre-existing Market version-format warning (`0.10`); StrategyChecks 0 errors/0 warnings. Native script runtime and run04 remain UNVERIFIED until performed. Development did not modify prior captures or install binaries into the terminal.

## Exact run04 procedure

1. Compile repository TraderLab.mq5 and StrategyChecks.mq5 with their Include layout intact; use [FIRST_DEMO_CAPTURE](FIRST_DEMO_CAPTURE.md) commands and review both logs separately.
2. Copy the newly compiled StrategyChecks.ex5 to terminal Data Folder/MQL5/Scripts, refresh Navigator and run it. Require `TraderLab native checks failures=0` in Experts/Journal. Compilation alone is not this result.
3. Detach TraderLab before replacing its binary. Copy the new TraderLab.ex5 to Data Folder/MQL5/Experts, refresh Navigator, use **LiteFinance Demo / hedging** and the exact XAUUSD_o chart. Code remains read-only regardless of Algo Trading state.
4. Verify the connected server UTC offset independently as in FIRST_DEMO_CAPTURE. For this October 7 run, use these requested values only if live observation still confirms GMT+3:

   ```ini
   InpBrokerSymbol=XAUUSD_o
   InpLogFile=TraderLab-demo-20261007-run04.jsonl
   InpServerUtcOffsetSeconds=10800
   InpTehranUtcOffsetSeconds=12600
   ```

   If the filename already exists, choose another unique run. A contradictory offset prevents acceptance; never rewrite old timestamps.
5. Attach the EA, confirm detection capture active, broker_orders_enabled=false, and TICK_CAPTURE_START with the baseline/policies and 1000 ms timer. Receive live ticks for 5–10 minutes, then remove the EA cleanly. Preserve raw JSONL in MQL5/Files.
6. Inspect first, then normalize to a fresh output. Use the actual connected terminal Data Folder if different:

   ```powershell
   $rawCapture = 'C:\Users\mehdi\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\TraderLab-demo-20261007-run04.jsonl'
   python D:\Github\TraderLab\tools\inspect_capture.py $rawCapture
   python D:\Github\TraderLab\tools\normalize_mt5_log.py $rawCapture 'D:\Github\TraderLab\work\native-events-demo-20261007-run04.jsonl'
   ```

7. Require successful exits; valid JSON, exact symbol/capabilities, UTC/server/Tehran milliseconds, tick_index/ordinal continuity, start/final summary/deinit and no chronology errors. Require zero TICK_CAPTURE_ERROR/TICK_CAPTURE_AMBIGUITY and zero CONFIG_UNRESOLVED/BROKER_CONFIG_BLOCKED. Compare summary callbacks, emitted/recovered ticks, snapshot matches, overlap skips, drain/copy calls and all errors; reconcile recovery totals. Recovery can be zero in a quiet run. Do not treat index continuity as proof of broker-feed completeness.

Implementation changed: TraderLab.mq5, new TickCapture.mqh, StrategyChecks.mq5, inspect_capture.py, normalize_mt5_log.py, test_native_log_contract.py and new test_tick_capture_evidence.py; related documentation and Graphify outputs. Canonical strategy code and OPEN_QUESTIONS unchanged.
