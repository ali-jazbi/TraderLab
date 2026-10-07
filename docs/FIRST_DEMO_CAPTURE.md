# First LiteFinance Demo capture

This is a read-only pipeline check. `TraderLab.mq5` records diagnostics and market data; it has no order-placement or position-management calls. No trade should be placed during this procedure.

For the current milestone and requested **run05**, follow [LOSS_AWARE_CAPTURE](LOSS_AWARE_CAPTURE.md): CopyTicksRange cursor, one-second timer, final recovery summary and exact inputs. Earlier callback-only captures are legacy evidence; tick_index continuity does not prove complete delivery.

## Compile on Windows

At initial preparation MetaEditor was unavailable. On 2026-10-07, both sources were actually compiled with MetaEditor build 6244: TraderLab had 0 errors and one pre-existing Market version-format warning; StrategyChecks had 0 errors and 0 warnings. Native script execution remains **UNVERIFIED**. See the [first capture review](DEMO_CAPTURE_REVIEW_20261007.md) for the current evidence and required fresh capture after the serialization fix.

After installing/opening the LiteFinance MT5 terminal, use **File → Open Data Folder** to identify its installation and data folders. Compile the two repository sources with the terminal's `MetaEditor64.exe` (replace the executable path if installed elsewhere):

```powershell
$metaEditor = 'C:\Program Files\MetaTrader 5\MetaEditor64.exe'
& $metaEditor '/compile:D:\Github\TraderLab\mt5\TraderLab.mq5' '/log:D:\Github\TraderLab\TraderLab.compile.log'
& $metaEditor '/compile:D:\Github\TraderLab\mt5\StrategyChecks.mq5' '/log:D:\Github\TraderLab\StrategyChecks.compile.log'
```

Review both logs individually. Require **0 errors** and review every warning. The sources include their dependencies under `mt5\Include\TraderLab`; keep that relative layout intact. Successful compilation does not mean `StrategyChecks` ran.

To run the native checks, copy `StrategyChecks.ex5` into the terminal data folder's `MQL5\Scripts`, refresh **Navigator → Scripts**, and run `StrategyChecks`. Confirm the Experts/Journal output ends with:

```text
TraderLab native checks failures=0
```

To attach the EA, copy `TraderLab.ex5` into the terminal data folder's `MQL5\Experts`, refresh **Navigator → Expert Advisors**, and attach it to the target chart.

## Verify the server offset

Before accepting or normalizing a capture, verify a fresh broker quote's displayed server time against a synchronized UTC clock on the same computer. Check several live quote updates, not a stale chart bar. On 2026-10-06, LiteFinance GMT+3 / `10800` seconds is only the expected value; confirm it from the connected Demo terminal. If the observed difference is not +03:00, stop and leave the capture unaccepted. Never edit timestamps to make them fit. Use a new capture after confirming the active server offset. Tehran strategy time is separately configured as `12600` seconds (+03:30).

## Capture checklist

1. Log in to the LiteFinance **Demo** account and show the broker's gold instrument in Market Watch.
2. Open its chart and copy the exact symbol text, including any suffix. Enter that value as `InpBrokerSymbol`; the EA refuses attachment to a chart with a different symbol.
3. Verify the server offset as above. For this October 6, 2026 run, set `InpServerUtcOffsetSeconds=10800` only if the live observation confirms it. Set `InpTehranUtcOffsetSeconds=12600`.
4. Set a unique `InpLogFile`, for example `TraderLab-litefinance-demo-20261006-run01.jsonl`. Existing files are intentionally never overwritten.
5. Attach `TraderLab` to that exact symbol chart. Keep Algo Trading disabled if MT5 still runs the diagnostic EA and logs ticks; enable it only if required for EA operation. This EA has no order execution code.
6. Confirm the Experts/Journal says `TraderLab detection capture active` and that `EA_INIT` reports `broker_orders_enabled:false`. Let live ticks arrive for 5–10 minutes.
7. Remove the EA cleanly. Find the JSONL under the terminal data folder's `MQL5\Files`.
8. Normalize to a new output file (do not overwrite an earlier result):

   ```powershell
   python D:\Github\TraderLab\tools\normalize_mt5_log.py `
     'C:\path\to\terminal\MQL5\Files\TraderLab-litefinance-demo-20261006-run01.jsonl' `
     'D:\Github\TraderLab\work\native-events-demo-20261006-run01.jsonl'
   ```

9. Run the read-only capture checks. Resolve every `ERROR`; review reported `CONFIG_UNRESOLVED` and `BROKER_CONFIG_BLOCKED` events before accepting the capture:

   ```powershell
   python D:\Github\TraderLab\tools\inspect_capture.py `
     'C:\path\to\terminal\MQL5\Files\TraderLab-litefinance-demo-20261006-run01.jsonl'
   ```

## Review the capture

The raw JSONL must contain `EA_INIT` with `broker_orders_enabled:false`, a `BROKER_CAPABILITY_SNAPSHOT` with the exact symbol and runtime instrument/account properties, ticks with increasing `seq` and `tick_index`, Bid/Ask and non-negative spread, closed-bar events, and explicit UTC/server/Tehran timestamps. Tehran time must carry `+03:30`; UTC must end in `Z`. Normalization checks server wall time plus the configured offset against canonical UTC exactly, including milliseconds, and rejects offset mismatches rather than rewriting history.

Review any `BROKER_CONFIG_BLOCKED` or `CONFIG_UNRESOLVED` event before treating the pipeline as valid. Preserve the raw capture unchanged. Dynamic symbol/account values are observations, not pass/fail comparisons to assumed broker values. No real capture is present in the repository yet, so these runtime checks remain pending the first Demo run.
