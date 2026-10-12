# Graph Report - TraderLab  (2026-10-12)

## Corpus Check
- 70 files · ~45,847 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 686 nodes · 1479 edges · 36 communities (19 shown, 17 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Capture and Replay Pipeline
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Web Application Dependencies
- Dashboard Interface
- Paper Replay Rules
- Dashboard API
- Paper Replay Rules
- Paper Replay Rules
- Dashboard Product and Guides
- Capture and Replay Pipeline
- Native Capture Integrity
- TypeScript Configuration
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Vercel Deployment Settings
- Native Normalizer Tests
- PostgreSQL Event Storage
- Native Capture Integrity
- Chart License Notices
- Native Capture and Broker Docs
- Dashboard Product and Guides

## God Nodes (most connected - your core abstractions)
1. `Engine` - 42 edges
2. `config()` - 31 edges
3. `tick()` - 28 edges
4. `Engine` - 26 edges
5. `Dashboard()` - 25 edges
6. `ReplayChecks` - 25 edges
7. `setup_event()` - 23 edges
8. `Loss Aware Capture` - 21 edges
9. `Tester Stress Capture` - 20 edges
10. `Bar` - 19 edges

## Surprising Connections (you probably didn't know these)
- `DailyGuard` --references--> `Regression trace: DAY-01/02`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `news_block()` --references--> `Regression trace: NEWS-01`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `NYBias` --references--> `Regression trace: NY-01/02`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `breakeven()` --references--> `Regression trace: BE-01`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `core_plan()` --references--> `Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Native JSONL to checkpointed publisher, authenticated ingest and durable event storage** — tools_publish_events_module, docs_dashboard_ingest_api, docs_dashboard_postgresql_storage, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Three explicit dashboard evidence sources** — docs_dashboard_observability_console, docs_dashboard_synthetic_sample, docs_dashboard_local_jsonl_import, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Automatic setup promotion requires approved linkage and observable validity/availability** — docs_automatic_backtest_blocked_geometry_303, docs_automatic_backtest_confirmed_setups_zero, docs_sources_canonical_strategy_fa_availability [EXTRACTED 1.00]
- **Tick break and consumed return evidence flow into blocked geometric pairs and stable annotations** — docs_event_schema_bos_intrabar_break, docs_event_schema_first_directional_return, docs_event_schema_closed_bar_boundary, docs_event_schema_blocked_pair_history, docs_event_schema_annotated_return [EXTRACTED 1.00]
- **Observed wick break, outbound departure, terminal first return and late association retained independently** — docs_first_retest_audit_python_lifecycle, docs_first_retest_audit_return_state, docs_first_retest_audit_activation_boundary, docs_first_retest_audit_annotation_boundary [EXTRACTED 1.00]
- **Both genuine candidates retain early consumed returns without historical fill inference** — docs_first_retest_audit_market_provenance, docs_first_retest_audit_m1_first_ask_return, docs_first_retest_audit_m1_first_bid_return, docs_first_retest_audit_m5_first_returns, docs_first_retest_audit_regression_evidence [EXTRACTED 1.00]
- **History occurrence identity and scoped completeness** — docs_loss_aware_capture_ordered_full_prefix, docs_loss_aware_capture_tick_raw_fields, docs_loss_aware_capture_duplicate_overlap_skips, docs_loss_aware_capture_broker_feed_complete_unknown [EXTRACTED 1.00]
- **Normal/stress paired evidence acceptance** — docs_tester_stress_capture_common_baseline, docs_tester_stress_capture_exact_raw_comparator, docs_tester_stress_capture_positive_recovery, docs_tester_stress_capture_duplicate_occurrence_vs_overlap [EXTRACTED 1.00]

## Communities (36 total, 17 thin omitted)

### Community 0 - "Capture and Replay Pipeline"
Cohesion: 0.05
Nodes (27): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Regression trace: NY-01/02, ConfirmedAmendmentChecks, window(), BrokerCapabilityChecks, bar_event(), DetectionChecks (+19 more)

### Community 1 - "Capture and Replay Pipeline"
Cohesion: 0.06
Nodes (22): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, Regression trace: Reproducibility, diagnose(), main(), compare_captures(), main() (+14 more)

### Community 2 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 3 - "Native Capture Integrity"
Cohesion: 0.06
Nodes (31): Explicit symbol adapter and BOS versus entry annotation, Annotated BOS_FIRST_TOUCH directional / source-only unarmed, BOS_INTRABAR_BREAK authoritative observed tick occurrence, Native loss-aware and tester capture diagnostics, Chronological JSONL event schema v0.2, BOS_FIRST_DIRECTIONAL_RETURN retained terminal evidence, Explicit sourced setup and structure annotations, First-return audit and 2026-10-12 correction (+23 more)

### Community 4 - "Web Application Dependencies"
Cohesion: 0.05
Nodes (39): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react (+31 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 6 - "Paper Replay Rules"
Cohesion: 0.18
Nodes (9): Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: Unresolved config and execution, config(), Engine, prime_return(), ReplayChecks, setup_event() (+1 more)

### Community 7 - "Dashboard API"
Cohesion: 0.12
Nodes (28): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+20 more)

### Community 8 - "Paper Replay Rules"
Cohesion: 0.11
Nodes (21): Regression trace: BE-01, Regression trace: REV-01/02/03, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules, news_block(), Bos, breakeven() (+13 more)

### Community 9 - "Paper Replay Rules"
Cohesion: 0.13
Nodes (8): Regression trace: DAY-01/02, Regression trace: OB-01, BOS-02, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01, HistoricalRetestChecks, Engine, Position, Setup

### Community 10 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 11 - "Capture and Replay Pipeline"
Cohesion: 0.17
Nodes (4): RequestGuardChecks, BrokerRequestGateway, RequestRecord, RollingRequestGuard

### Community 12 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (10): AutomaticRelationships geometric candidates, Actual historical chart inspection observations, Historical tester-normal-run01 input, Identical diagnostic journal hashes, TLBarDetector.Process, TLBosLevel, TLCoreEntryReference, TLCorePlan (+2 more)

### Community 13 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 15 - "Capture and Replay Pipeline"
Cohesion: 0.35
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 19 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 21 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 22 - "Native Capture Integrity"
Cohesion: 0.67
Nodes (4): Automatic historical strategy diagnostics 2026-10-11, Native source relationships documented without MQL5 AST, Preserved Persian canonical strategy, current section 51, TraderLab overview

### Community 24 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Owner chart numerical example` → `Order Block full reference candle`  [AMBIGUOUS]
  docs/sources/canonical-strategy.fa.md · relation: conceptually_related_to

## Knowledge Gaps
- **97 isolated node(s):** `Status`, `allowJs`, `esModuleInterop`, `incremental`, `isolatedModules` (+92 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 205 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Owner chart numerical example` and `Order Block full reference candle`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`, `Capture and Replay Pipeline`, `Paper Replay Rules`, `Native Capture Integrity`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`, `Paper Replay Rules`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `BrokerRequestGateway` connect `Capture and Replay Pipeline` to `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `FirstRetestAudit`) actually correct?**
  _`Engine` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `allowJs`, `esModuleInterop` to the rest of the system?**
  _97 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Capture and Replay Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.05175438596491228 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
