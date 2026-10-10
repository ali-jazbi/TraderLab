# Historical Strategy Tester capture startup

## Failed evidence and investigation

Reviewed read-only on 2026-10-10: `TraderLab-backtest-20261007.jsonl` in the local tester agent MQL5/Files folder has six valid JSON events, no TICK/CLOSED_BAR, CopyTicks(COPY_TICKS_ALL,0,1)=-1/error4004 in startup, callbacks=0, emitted=0, copyticks_errors=1, halted=true and evidence=false. EA_DEINIT reason=8 confirms initialization failure. Inspector still rejects it. SHA256 before/after inspection: BB5C09E4DC68BBF35FA986389B66252A8A3559E6DC112E6E1DE3DE727B34FCFB. Do not edit, overwrite or repair this capture.

[Official runtime errors](https://www.mql5.com/en/docs/constants/errorswarnings/errorcodes) define 4004 as ERR_NOT_ENOUGH_MEMORY, not a dedicated history-not-ready status. The evidence locates the failure before the first callback; it cannot prove the underlying tester allocation/readiness mechanism. [CopyTicks](https://www.mql5.com/en/docs/series/copyticks) synchronizes tick history. [Tester documentation](https://www.mql5.com/en/docs/runtime/testing) describes an agent-local tick cache/database; it does not guarantee successful CopyTicks in OnInit on every agent/build. Deferral is a scoped compatibility correction whose live historical success requires a fresh test, not a claim that every 4004 is transient.

## Startup policy

Only MQL_TESTER enables deferral. OnInit retains chart/config/log/capability checks, writes TICK_CAPTURE_START_DEFERRED, and returns INIT_SUCCEEDED without querying tick history or starting the timer. Live Demo still calls Start and StartTimer synchronously in OnInit with the original error returns; TickCapture.mqh is unchanged.

The first OnTick clears the pending flag before one startup attempt using the existing history-authoritative Start. Success starts the one-second timer and enters the existing shared drain. Failure retains the original error/ambiguity diagnostics, counts the callback with no halted emission, then ExpertRemove stops the tester pass. There is no sleep, retry loop or later baseline reset that could erase the failed interval. If the test ends without any tick, deinit records TICK_CAPTURE_ERROR(reason=tester_no_first_tick); the absent start/zero ticks/halted summary remain invalid.

**The first callback history snapshot is explicitly excluded as baseline**, including its complete same-millisecond multiplicity and all earlier records. This is the existing capture policy, not full-period replay from the very first tester tick. TICK_CAPTURE_START_DEFERRED records first_callback_history_is_baseline=true; TICK_CAPTURE_START records the retained baseline millisecond/count. Later appended occurrences in that millisecond are emitted individually. If full-period coverage including that first snapshot is required, this capture is insufficient; do not relabel the excluded baseline as emitted evidence. No SymbolInfoTick quote is serialized as a replacement tick.

The same ordered-prefix validation, actual raw tick timestamps/fields, counters, FileFlush, strict market chronology and inspector/normalizer rejection apply. CopyTicks calls still include two startup history queries. The deferred lifecycle event is explicitly second precision; this does not relax tick or closed-bar ordering.

## Fresh historical test procedure

1. Compile repository mt5/TraderLab.mq5 and mt5/StrategyChecks.mq5 with their includes. Review both compilation logs. Run the compiled StrategyChecks script separately and require `TraderLab native checks failures=0`; compilation alone does not run assertions.
2. Install the newly compiled TraderLab.ex5 into the terminal Experts folder while the old EA is detached; refresh Navigator. Use a **single local test**, optimization off, no cloud/remote agent. Existing failed capture stays untouched.
3. Select TraderLab, exact symbol **XAUUSD_o**, timeframe **M1**, mode **Every tick based on real ticks**, From **2026-10-07**, To **2026-10-08**. Record these settings and terminal/agent build in the report. Dates refer to the tester's broker/server calendar; do not replace them with Tehran or UTC calendar dates.
4. Set inputs below. Independently verify the historical server offset for October 7 before accepting timestamps; the old configured value is not proof. Tehran is explicitly UTC+03:30:

   ```ini
   InpBrokerSymbol=XAUUSD_o
   InpLogFile=TraderLab-backtest-20261007-20261008-retest01.jsonl
   InpServerUtcOffsetSeconds=10800
   InpTehranUtcOffsetSeconds=12600
   ```

   Use a new unique filename if retest01 exists. No capture overwrite is permitted.
5. Start the test. Expect EA_INIT and TICK_CAPTURE_START_DEFERRED before the first callback; then TICK_CAPTURE_START followed by real history TICK records, CLOSED_BAR observations and a final summary/EA_DEINIT. A deferred event alone is not successful capture. If startup still returns4004 (or any API/prefix error), preserve log and agent Journal, reject the run and investigate resources/history; do not retry within the EA or enable trading.
6. Locate the output in the **tester agent** MQL5/Files sandbox, not the live terminal Files folder. Example for the observed local agent:

   ```powershell
   $historicalCapture = 'C:\Users\mehdi\AppData\Roaming\MetaQuotes\Tester\D0E8209F77C8CF37AD8BF550E51FF075\Agent-127.0.0.1-3000\MQL5\Files\TraderLab-backtest-20261007-20261008-retest01.jsonl'
   python D:\Github\TraderLab\tools\inspect_capture.py $historicalCapture
   python D:\Github\TraderLab\tools\normalize_mt5_log.py $historicalCapture 'D:\Github\TraderLab\work\native-events-historical-retest01.jsonl'
   ```

   Use the actual agent folder if different; normalized output must also be fresh.
7. Require valid JSON, exact milliseconds/symbol, no configuration/API/ambiguity errors, strict chronology, baseline/ordinal/index continuity, final summary/deinit and reconciled emitted=recovered+snapshot_matches. Save tester Report and Journal (including tick history quality/coverage warnings). The tester may generate replacement ticks where minute/tick history disagrees or is absent even in real-tick mode; official tester documentation explains this. Capture validates the provided tester history, not independent proof of original broker-feed completeness or the complete simulated callback stream. No trade results are expected from this detection-only EA.

## Verification

2026-10-10: 73 Python tests passed. Actual MetaEditor compilation: TraderLab 0 errors/1 existing version-format warning, StrategyChecks 0 errors/0 warnings. Python tests include tester source flow guards, synthetic deferred evidence normalization, failed startup/no-first-tick rejection and existing millisecond/cursor tests. Native TesterBaselineChecks additionally cover explicit first-callback exclusion, identical baseline records, later same-ms emission and boundary mutation. **Native script execution and fresh historical test execution are UNVERIFIED.** No tester or live capture was modified, no terminal binary was replaced, and no broker execution API was added.
