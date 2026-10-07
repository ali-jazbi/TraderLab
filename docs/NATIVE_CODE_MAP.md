# Native source map (documentation, not AST extraction)

This map records direct includes and calls visible in the source. Graphify0.9.74 does not classify the MQL5 file extensions. Graph consumers must not infer native AST coverage from these references.

| Source | Explicit relationship |
|---|---|
| mt5/TraderLab.mq5 | includes Include/TraderLab/Detection.mqh and TickCapture.mqh |
| mt5/TraderLab.mq5 OnInit | calls TLEventLog.Open/Write; records broker/account capability snapshot, margin-news observation window and configured offsets; no broker orders |
| mt5/TraderLab.mq5 OnTick | calls TLTickCapture.OnCallback; no CopyRates/detector loop |
| mt5/TraderLab.mq5 OnTimer | same TLTickCapture.Drain each second; ProcessClosedBars scans five CopyRates start_pos1 frames with latest emitted source timestamp |
| mt5/TraderLab.mq5 OnDeinit | kills timer; final Drain/ProcessClosedBars; TLTickCapture.Summary; TLEventLog.Write/Close |
| TLTickCursor | pure full-boundary-millisecond ordered-prefix comparison; retains raw multiplicity; validates the whole batch before consuming a suffix |
| TLTickCapture | includes EventLog.mqh; CopyTicksRange COPY_TICKS_ALL inclusive overlap; raw TICK metadata and start/recovery/error/ambiguity/summary; excludes baseline; no order API |
| mt5/Include/TraderLab/Detection.mqh | includes Rules.mqh and EventLog.mqh |
| TLBarDetector.Process | implements BIG-01 delayed21-bar window, FVG-01/02 geometry and BOS-01 diagnostic candidates; calls TLEventLog.Write and TLCandidateEpoch for numeric candidate_server_epoch fields |
| TLCandidateEpoch | converts datetime through long before string serialization; shared by BOS candidate and Big Candle/FVG event payloads |
| TLEventLog | implements JSONL escaping and optional explicit server-to-UTC plus Tehran strategy-time conversion; records timestamp_precision as seconds for default lifecycle observations or milliseconds for explicit market fractions; refuses log overwrite |
| mt5/Include/TraderLab/RequestGuard.mqh | isolated in-memory request-rate/idempotency reference; no dispatch method and not connected to TraderLab.mq5 |
| mt5/Include/TraderLab/Rules.mqh | TLCorePlan implements SELECT-02, SL-01 and TP-01; TLBreakEven implements BE-01; TLOBroken implements OB10-pip rule; TLDailyGuard implements DAY-01/02 |
| mt5/StrategyChecks.mq5 | includes Rules/RequestGuard/EventLog/Detection/TickCapture; synthetic cursor checks plus canonical plans/boundaries, OB/BE/daily/request guards and numeric candidate JSON |
| tools/inspect_capture.py | read-only JSONL; explicit lifecycle second intervals; precise market chronology; validates loss-aware raw metadata/counters/start/summary/deinit; rejects errors/ambiguities |
| tools/normalize_mt5_log.py | preflights loss-aware captures through inspect_capture; extracts kind=bar/tick, rejects unknown UTC, preserves ordering |
| traderlab/replay.py | consumes normalized bars/ticks plus sourced setup/structure annotations; owns paper state machine |

Native broker execution, native full paper state machine and Python/MQL5 execution parity remain pending. Both sources compiled with MetaEditor build 6244 on 2026-10-07; native check script execution is still unverified. See [the first capture review](DEMO_CAPTURE_REVIEW_20261007.md) and [loss-aware capture/run04](LOSS_AWARE_CAPTURE.md).
