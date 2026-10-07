# Native source map (documentation, not AST extraction)

This map records direct includes and calls visible in the source. Graphify0.9.74 does not classify the MQL5 file extensions. Graph consumers must not infer native AST coverage from these references.

| Source | Explicit relationship |
|---|---|
| mt5/TraderLab.mq5 | includes Include/TraderLab/Detection.mqh |
| mt5/TraderLab.mq5 OnInit | calls TLEventLog.Open/Write; records broker/account capability snapshot, margin-news observation window and configured offsets; no broker orders |
| mt5/TraderLab.mq5 OnTick | CopyRates start_pos1 closed bars; calls TLBarDetector.Process; logs MqlTick bid/ask and tick_index |
| mt5/TraderLab.mq5 OnDeinit | calls TLEventLog.Write/Close |
| mt5/Include/TraderLab/Detection.mqh | includes Rules.mqh and EventLog.mqh |
| TLBarDetector.Process | implements BIG-01 delayed21-bar window, FVG-01/02 geometry and BOS-01 diagnostic candidates; calls TLEventLog.Write and TLCandidateEpoch for numeric candidate_server_epoch fields |
| TLCandidateEpoch | converts datetime through long before string serialization; shared by BOS candidate and Big Candle/FVG event payloads |
| TLEventLog | implements JSONL escaping and optional explicit server-to-UTC plus Tehran strategy-time conversion; records timestamp_precision as seconds for default lifecycle observations or milliseconds for explicit market fractions; refuses log overwrite |
| mt5/Include/TraderLab/RequestGuard.mqh | isolated in-memory request-rate/idempotency reference; no dispatch method and not connected to TraderLab.mq5 |
| mt5/Include/TraderLab/Rules.mqh | TLCorePlan implements SELECT-02, SL-01 and TP-01; TLBreakEven implements BE-01; TLOBroken implements OB10-pip rule; TLDailyGuard implements DAY-01/02 |
| mt5/StrategyChecks.mq5 | includes Rules.mqh, RequestGuard.mqh, EventLog.mqh and Detection.mqh; checks canonical plans/boundaries, OB penetration, BE mirror, daily guards, request guards and exact generated numeric candidate JSON |
| tools/inspect_capture.py | validates native JSONL read-only; treats known TimeCurrent lifecycle/diagnostic observations as one-second intervals, including legacy .000 events; keeps market capture chronology exact and never lowers the prior ordering floor |
| tools/normalize_mt5_log.py | extracts kind=bar/tick from native JSONL, rejects unknown UTC times, preserves ordering |
| traderlab/replay.py | consumes normalized bars/ticks plus sourced setup/structure annotations; owns paper state machine |

Native broker execution, native full paper state machine and Python/MQL5 execution parity remain pending. Both sources compiled with MetaEditor build 6244 on 2026-10-07; native check script execution is still unverified. See [the first capture review](DEMO_CAPTURE_REVIEW_20261007.md).
