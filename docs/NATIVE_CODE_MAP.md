# Native source map (documentation, not AST extraction)

2026-10-16 engineering update: the older dated observations below are historical.
Current candidate relationships and runtime evidence are documented in
[AUTO_CORE_ENGINEERING_20261016.md](AUTO_CORE_ENGINEERING_20261016.md).
`AUTO_CORE_DEMO.mq5 -> TraderLab.mq5 -> NativeRetestStream/CoreController ->
CoreLifecycle -> DemoGateway` retains a single production OrderSend site.
The candidate additionally includes `RecoveryJournal.mqh`; its input WAL rebuilds
trackers and group membership before enabling new discovery. Candidate lifecycle
and gateway WALs reconcile plans/intents against broker positions/history.
Only `AutoCoreIntegrationChecks.mq5` and `AutoCoreProcessRestartChecks.mq5` include
`Checks/OfflineBroker.mqh`: their compile-time transport cannot send broker orders.
`calendar_service.py -> refresh_core_calendar.py -> MQL5/Files` publishes the V2
forward packet; CoreLifecycle validates freshness independently on every entry.

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

Native broker execution, native full paper state machine and Python/MQL5 execution parity remain pending. Both sources compiled with MetaEditor build 6244 on 2026-10-07; native check script execution is still unverified. See [the first capture review](DEMO_CAPTURE_REVIEW_20261007.md) and [loss-aware capture/run05](LOSS_AWARE_CAPTURE.md).


## Owner amendment 2026-10-11

TLBarDetector.Process now emits wick-tip BOS_CONFIRMED/BOS_REJECTED, BIG_CANDLE_REJECTED and FVG_REJECTED. OB_CONFIRMED uses TLOrderBlockBounds to extract the entire Buy C3 / Sell C1 candle on every observed timeframe, with no mandatory H4-first. Rules.mqh exposes TLBosLevel and TLCoreEntryReference (+0.5 Buy / -0.5 Sell); TLCorePlan single stop is a 40-pip planned-anchor preview, not approval of an execution anchor. StrategyChecks includes synthetic wick/OB/directional-reference assertions. Python AutomaticRelationships handles same-timeframe geometric containment and closed-candle validity; native relationship association and broker execution remain absent. Compilation on 2026-10-11 succeeded for both sources; script runtime is separately unverified.
