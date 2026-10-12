# Graph Report - TraderLab  (2026-10-12)

## Corpus Check
- 73 files · ~48,553 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 729 nodes · 1586 edges · 42 communities (23 shown, 19 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Native Capture Integrity
- Paper Replay Rules
- Paper Replay Rules
- Capture and Replay Pipeline
- Web Application Dependencies
- Dashboard Interface
- Paper Replay Rules
- Capture and Replay Pipeline
- Dashboard API
- Native Capture Integrity
- Native Capture Integrity
- Dashboard Product and Guides
- Capture and Replay Pipeline
- Native Capture Integrity
- TypeScript Configuration
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Capture and Replay Pipeline
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
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
5. `ReplayChecks` - 25 edges
6. `Dashboard()` - 25 edges
7. `Native chronological BOS first-return diagnostic stream` - 25 edges
8. `setup_event()` - 23 edges
9. `Loss Aware Capture` - 21 edges
10. `Tester Stress Capture` - 20 edges

## Surprising Connections (you probably didn't know these)
- `DailyGuard` --references--> `Regression trace: DAY-01/02`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `news_block()` --references--> `Regression trace: NEWS-01`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `ConfirmedAmendmentChecks` --uses--> `AutomaticRelationships`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/automatic.py
- `ConfirmedAmendmentChecks` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `ConfirmedAmendmentChecks` --uses--> `Detector`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Native JSONL to checkpointed publisher, authenticated ingest and durable event storage** — tools_publish_events_module, docs_dashboard_ingest_api, docs_dashboard_postgresql_storage, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Three explicit dashboard evidence sources** — docs_dashboard_observability_console, docs_dashboard_synthetic_sample, docs_dashboard_local_jsonl_import, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Automatic setup promotion requires approved linkage and observable validity/availability** — docs_automatic_backtest_blocked_geometry_303, docs_automatic_backtest_confirmed_setups_zero, docs_sources_canonical_strategy_fa_availability [EXTRACTED 1.00]
- **History occurrence identity and scoped completeness** — docs_loss_aware_capture_ordered_full_prefix, docs_loss_aware_capture_tick_raw_fields, docs_loss_aware_capture_duplicate_overlap_skips, docs_loss_aware_capture_broker_feed_complete_unknown [EXTRACTED 1.00]
- **Accepted suffix tick, as-of closed bars and archived directional lifecycle** — docs_native_retests_accepted_suffix_observer, docs_native_retests_as_of_stream, docs_native_retests_tracker_delivery_clock, docs_native_retests_per_bos_lifecycle, docs_native_retests_diagnostic_lanes, docs_native_retests_archived_history [EXTRACTED 1.00]
- **New compiled checks, fresh normal/stress captures and observed metrics remain required** — docs_native_retests_new_assertions, docs_native_retests_fresh_normal_steps, docs_native_retests_audited_expectations, docs_native_retests_fresh_stress_steps, docs_native_retests_verification_scope, docs_native_retests_performance_boundary [EXTRACTED 1.00]
- **Tracker delivery stream, tick identity and reconciled diagnostics required for genuine parity** — docs_native_retests_comparator, docs_native_retests_bar_event, docs_native_retests_break_event, docs_native_retests_return_event, docs_native_retests_summary_event, docs_native_retests_halted_detection [EXTRACTED 1.00]
- **Normal/stress paired evidence acceptance** — docs_tester_stress_capture_common_baseline, docs_tester_stress_capture_exact_raw_comparator, docs_tester_stress_capture_positive_recovery, docs_tester_stress_capture_duplicate_occurrence_vs_overlap [EXTRACTED 1.00]

## Communities (42 total, 19 thin omitted)

### Community 0 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 1 - "Paper Replay Rules"
Cohesion: 0.10
Nodes (10): Regression trace: DAY-01/02, Regression trace: OB-01, BOS-02, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01, HistoricalRetestChecks, Engine, Position, Setup (+2 more)

### Community 2 - "Paper Replay Rules"
Cohesion: 0.09
Nodes (23): Regression trace: BE-01, Regression trace: REV-01/02/03, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules, instant(), History, news_block() (+15 more)

### Community 3 - "Capture and Replay Pipeline"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Web Application Dependencies"
Cohesion: 0.04
Nodes (40): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react, react-dom, @types/node (+32 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.12
Nodes (37): dynamic, POST(), Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile() (+29 more)

### Community 6 - "Paper Replay Rules"
Cohesion: 0.16
Nodes (10): Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: Unresolved config and execution, ConfirmedAmendmentChecks, config(), Engine, prime_return(), ReplayChecks (+2 more)

### Community 7 - "Capture and Replay Pipeline"
Cohesion: 0.12
Nodes (14): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Regression trace: NY-01/02, window(), bar_event(), DetectionChecks, SessionChecks, AutomaticRelationships (+6 more)

### Community 8 - "Dashboard API"
Cohesion: 0.13
Nodes (26): next, dynamic, GET(), dynamic, GET(), DELETE(), dynamic, POST() (+18 more)

### Community 9 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (23): Explicit symbol adapter and BOS versus entry annotation, Annotated BOS_FIRST_TOUCH directional / source-only unarmed, BOS_INTRABAR_BREAK authoritative observed tick occurrence, Native loss-aware and tester capture diagnostics, Chronological JSONL event schema v0.2, BOS_FIRST_DIRECTIONAL_RETURN retained terminal evidence, Explicit sourced setup and structure annotations, TLTickObserver accepted terminal-history suffix only (+15 more)

### Community 10 - "Native Capture Integrity"
Cohesion: 0.08
Nodes (24): First-return audit and 2026-10-12 correction, Reviewed canonical authority and unavailable original PDFs, Full genuine diagnostic replay without setups or performance, M1 BUY qualification and actual structural break, M1 first Ask downward return: missed and consumed, M1 first Bid downward return: exact and spent, M1 FVG formation, availability and later full invalidity, M5 SELL mirrored first returns both miss reference (+16 more)

### Community 11 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 13 - "Capture and Replay Pipeline"
Cohesion: 0.16
Nodes (8): Regression trace: Reproducibility, diagnose(), main(), main(), digest(), encode(), json_line(), run()

### Community 14 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (10): AutomaticRelationships geometric candidates, Actual historical chart inspection observations, Historical tester-normal-run01 input, Identical diagnostic journal hashes, TLBarDetector.Process, TLBosLevel, TLCoreEntryReference, TLCorePlan (+2 more)

### Community 15 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 16 - "Native Capture Integrity"
Cohesion: 0.16
Nodes (6): comparator_fixture(), NativeRetestChecks, compare_capture(), compare_rows(), main(), signature()

### Community 18 - "Capture and Replay Pipeline"
Cohesion: 0.22
Nodes (9): compare_captures(), main(), tester_metadata(), capture_integer(), decimal(), inspect_capture(), main(), validate_tick_capture() (+1 more)

### Community 19 - "Capture and Replay Pipeline"
Cohesion: 0.35
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 24 - "Capture and Replay Pipeline"
Cohesion: 0.33
Nodes (3): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl

### Community 25 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 27 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 28 - "Native Capture Integrity"
Cohesion: 0.67
Nodes (4): Automatic historical strategy diagnostics 2026-10-11, Native source relationships documented without MQL5 AST, Preserved Persian canonical strategy, current section 51, TraderLab overview

### Community 30 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Owner chart numerical example` → `Order Block full reference candle`  [AMBIGUOUS]
  docs/sources/canonical-strategy.fa.md · relation: conceptually_related_to

## Knowledge Gaps
- **98 isolated node(s):** `Status`, `allowJs`, `esModuleInterop`, `incremental`, `isolatedModules` (+93 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 211 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Owner chart numerical example` and `Order Block full reference candle`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Engine` connect `Paper Replay Rules` to `Paper Replay Rules`, `Capture and Replay Pipeline`, `Capture and Replay Pipeline`, `Capture and Replay Pipeline`, `Native Capture Integrity`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `inspect_capture()` connect `Capture and Replay Pipeline` to `Capture and Replay Pipeline`, `Capture and Replay Pipeline`, `Native Capture Integrity`, `Native Capture Integrity`, `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `FirstRetestAudit`) actually correct?**
  _`Engine` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `allowJs`, `esModuleInterop` to the rest of the system?**
  _98 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Native Capture Integrity` be split into smaller, more focused modules?**
  _Cohesion score 0.05263157894736842 - nodes in this community are weakly interconnected._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.09620721554116558 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
