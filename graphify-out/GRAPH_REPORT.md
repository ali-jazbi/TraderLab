# Graph Report - TraderLab  (2026-10-12)

## Corpus Check
- 77 files · ~50,786 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 757 nodes · 1654 edges · 38 communities (21 shown, 17 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Paper Replay Rules
- Web Application Dependencies
- Paper Replay Rules
- Dashboard Interface
- Dashboard API
- Paper Replay Rules
- Capture and Replay Pipeline
- Dashboard Product and Guides
- Native Capture Integrity
- Native Capture Integrity
- Paper Replay Rules
- TypeScript Configuration
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Paper Replay Rules
- Capture and Replay Pipeline
- Vercel Deployment Settings
- Native Normalizer Tests
- PostgreSQL Event Storage
- Chart License Notices
- Dashboard Product and Guides

## God Nodes (most connected - your core abstractions)
1. `Engine` - 40 edges
2. `config()` - 31 edges
3. `tick()` - 27 edges
4. `Engine` - 26 edges
5. `ReplayChecks` - 25 edges
6. `Dashboard()` - 25 edges
7. `Native chronological BOS first-return diagnostic stream` - 25 edges
8. `setup_event()` - 23 edges
9. `Loss Aware Capture` - 21 edges
10. `Tester Stress Capture` - 20 edges

## Surprising Connections (you probably didn't know these)
- `NYBias` --implements--> `Daily/news/New York context rules`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `HistoricalRetestChecks` --uses--> `Bar`  [INFERRED]
  tests/test_historical_retests.py → traderlab/detection.py
- `HistoricalRetestChecks` --uses--> `Engine`  [INFERRED]
  tests/test_historical_retests.py → traderlab/replay.py
- `DailyGuard` --implements--> `Daily/news/New York context rules`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `FirstRetestAudit` --uses--> `Engine`  [INFERRED]
  tests/test_first_retest_audit.py → traderlab/replay.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Native JSONL to checkpointed publisher, authenticated ingest and durable event storage** — tools_publish_events_module, docs_dashboard_ingest_api, docs_dashboard_postgresql_storage, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Three explicit dashboard evidence sources** — docs_dashboard_observability_console, docs_dashboard_synthetic_sample, docs_dashboard_local_jsonl_import, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Automatic setup promotion requires approved linkage and observable validity/availability** — docs_automatic_backtest_blocked_geometry_303, docs_automatic_backtest_confirmed_setups_zero, docs_sources_canonical_strategy_fa_availability [EXTRACTED 1.00]
- **Qualified break, directional return and retained blocked-pair history** — docs_event_schema_bos_intrabar_break, docs_event_schema_first_directional_return, docs_event_schema_blocked_pair_history [EXTRACTED 1.00]
- **History occurrence identity and scoped completeness** — docs_loss_aware_capture_ordered_full_prefix, docs_loss_aware_capture_tick_raw_fields, docs_loss_aware_capture_duplicate_overlap_skips, docs_loss_aware_capture_broker_feed_complete_unknown [EXTRACTED 1.00]
- **Accepted suffix tick, as-of closed bars and archived directional lifecycle** — docs_native_retests_accepted_suffix_observer, docs_native_retests_as_of_stream, docs_native_retests_tracker_delivery_clock, docs_native_retests_per_bos_lifecycle, docs_native_retests_diagnostic_lanes, docs_native_retests_archived_history [EXTRACTED 1.00]
- **New compiled checks, fresh normal/stress captures and observed metrics remain required** — docs_native_retests_new_assertions, docs_native_retests_fresh_normal_steps, docs_native_retests_audited_expectations, docs_native_retests_fresh_stress_steps, docs_native_retests_verification_scope, docs_native_retests_performance_boundary [EXTRACTED 1.00]
- **Tracker delivery stream, tick identity and reconciled diagnostics required for genuine parity** — docs_native_retests_comparator, docs_native_retests_bar_event, docs_native_retests_break_event, docs_native_retests_return_event, docs_native_retests_summary_event, docs_native_retests_halted_detection [EXTRACTED 1.00]
- **Normal/stress paired evidence acceptance** — docs_tester_stress_capture_common_baseline, docs_tester_stress_capture_exact_raw_comparator, docs_tester_stress_capture_positive_recovery, docs_tester_stress_capture_duplicate_occurrence_vs_overlap [EXTRACTED 1.00]

## Communities (38 total, 17 thin omitted)

### Community 0 - "Capture and Replay Pipeline"
Cohesion: 0.05
Nodes (28): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, diagnose(), main(), main(), compare_capture(), main() (+20 more)

### Community 1 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 2 - "Native Capture Integrity"
Cohesion: 0.08
Nodes (33): LiteFinance Broker and Execution Profile, Batch paper replay invocation and annotation boundary, DEMO readiness — 2026-10-12, Implemented multi-timeframe geometry and first-return diagnostics, Native source audit and unverified fresh runtime parity, StrategyChecks and fresh normal/stress MT5 capture verification, Real October 7 replay with no automatic setups or trades, Existing paper engine and explicit execution evidence (+25 more)

### Community 3 - "Capture and Replay Pipeline"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Paper Replay Rules"
Cohesion: 0.09
Nodes (27): Automatic historical strategy diagnostics 2026-10-11, Native source relationships documented without MQL5 AST, Preserved Persian canonical strategy, current section 51, Daily/news/New York context rules, 2026-10-12 first-return implementation amendment, Reverse original planned entry and prerequisites, Confirmed selection and Core risk references, TraderLab strategy specification v0.2 (+19 more)

### Community 5 - "Web Application Dependencies"
Cohesion: 0.05
Nodes (39): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react (+31 more)

### Community 6 - "Paper Replay Rules"
Cohesion: 0.11
Nodes (5): BatchChecks, AutomaticRelationships, Engine, Position, Setup

### Community 7 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 8 - "Dashboard API"
Cohesion: 0.12
Nodes (28): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+20 more)

### Community 9 - "Paper Replay Rules"
Cohesion: 0.18
Nodes (7): ConfirmedAmendmentChecks, config(), Engine, prime_return(), ReplayChecks, setup_event(), tick()

### Community 10 - "Capture and Replay Pipeline"
Cohesion: 0.15
Nodes (11): Confirmed Big Candle/FVG/OB/BOS geometry, window(), bar_event(), DetectionChecks, SessionChecks, Bar, big_candle(), Candidate (+3 more)

### Community 11 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 12 - "Native Capture Integrity"
Cohesion: 0.11
Nodes (17): First-return audit and 2026-10-12 correction, Reviewed canonical authority and unavailable original PDFs, Full genuine diagnostic replay without setups or performance, M1 BUY qualification and actual structural break, M1 first Ask downward return: missed and consumed, M1 first Bid downward return: exact and spent, M1 FVG formation, availability and later full invalidity, M5 SELL mirrored first returns both miss reference (+9 more)

### Community 13 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (10): AutomaticRelationships geometric candidates, Actual historical chart inspection observations, Historical tester-normal-run01 input, Identical diagnostic journal hashes, TLBarDetector.Process, TLBosLevel, TLCoreEntryReference, TLCorePlan (+2 more)

### Community 14 - "Paper Replay Rules"
Cohesion: 0.14
Nodes (4): HistoricalRetestChecks, FirstReturn, HistoricalRetests, History

### Community 15 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 16 - "Native Capture Integrity"
Cohesion: 0.19
Nodes (4): comparator_fixture(), NativeRetestChecks, compare_rows(), signature()

### Community 18 - "Capture and Replay Pipeline"
Cohesion: 0.35
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 23 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 25 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 27 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Owner chart numerical example` → `Order Block full reference candle`  [AMBIGUOUS]
  docs/sources/canonical-strategy.fa.md · relation: conceptually_related_to

## Knowledge Gaps
- **94 isolated node(s):** `Status`, `allowJs`, `esModuleInterop`, `incremental`, `isolatedModules` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 212 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Owner chart numerical example` and `Order Block full reference candle`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Automatic geometric pairs diagnostic-only; annotations explicit` connect `Paper Replay Rules` to `Capture and Replay Pipeline`, `Native Capture Integrity`, `Paper Replay Rules`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `2026-10-12 first-return implementation amendment` connect `Paper Replay Rules` to `Native Capture Integrity`, `Capture and Replay Pipeline`, `Native Capture Integrity`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`, `Paper Replay Rules`, `Native Capture Integrity`, `Paper Replay Rules`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `FirstRetestAudit`) actually correct?**
  _`Engine` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `allowJs`, `esModuleInterop` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Capture and Replay Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.05153576582148011 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
