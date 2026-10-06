# Milestones

1. Preserve canonical source; map rule IDs; list missing semantics. Delivered first.
2. Closed-bar detection, no look-ahead; event schema and diagnostic MT5 EA. Build without broker orders.
3. Deterministic chronological tick replay, sourced zone annotations, paper Entry/SL/TP/BE, daily guards, news snapshots, soft NY context and linked reversal. Test canonical cases, guards, timestamps and duplicate touch consumption. Unknown paths block and log.
4. User-prioritized observability dashboard: read-only Next.js/Vercel console with chart overlays, decision journal, sourced setup timelines, paper PnL and event replay. Browser-local JSONL imports and protected PostgreSQL ingestion with a checkpointed stdlib Windows publisher. No duplicate strategy logic. Cloud/native live validation needs configured storage and actual MT5 capture. Extend beyond20,000 rows with server aggregation for long runs.
5. Compile/run native EA in MetaEditor/MT5 when the installed toolchain is provided. Validate native detector parity against offline fixtures and historical/forward real ticks using the dashboard. Resolve missing strategy definitions before autonomous execution.
6. Demo execution milestone (not enabled): durable shared broker-request gateway with restart-safe rolling counts, idempotent intents, margin preflight, retcode and OnTradeTransaction/order/deal/position reconciliation, hedging/netting policy, restart recovery and approved account config. Require successful MT5 compile and explicit milestone approval. Separate acceptance from historical replay. No real-account execution.
7. Extended analytics: historical windows, daily/session metrics, drawdown and backtest comparisons; reuse the same event evidence in the dashboard.
8. Broker hardening groundwork: record LiteFinance agreement facts and seasonal offsets, snapshot live MT5 symbol/account capabilities, add testable in-memory request safety references and model stop-gap fills. This does not send orders or resolve strategy questions.

Graphify maps supplied rules, documentation and actual source relationships. Missing implementations and annotations stay visible.
