# Graph Report - TraderLab  (2026-10-12)

## Corpus Check
- 80 files · ~54,338 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 845 nodes · 1929 edges · 67 communities (28 shown, 39 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Paper Replay Rules
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Web Application Dependencies
- Dashboard Interface
- Native Capture Integrity
- Dashboard API
- Native Capture Integrity
- Dashboard Product and Guides
- Capture and Replay Pipeline
- Native Capture Integrity
- Capture and Replay Pipeline
- TypeScript Configuration
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Paper Replay Rules
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Paper Replay Rules
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Vercel Deployment Settings
- Native Normalizer Tests
- PostgreSQL Event Storage
- Chart License Notices
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity

## God Nodes (most connected - your core abstractions)
1. `Engine` - 61 edges
2. `config()` - 45 edges
3. `tick()` - 43 edges
4. `setup_event()` - 41 edges
5. `Engine` - 26 edges
6. `ReplayChecks` - 26 edges
7. `Dashboard()` - 25 edges
8. `Bar` - 23 edges
9. `OwnerOct12Checks` - 23 edges
10. `Native chronological BOS first-return diagnostic stream` - 22 edges

## Surprising Connections (you probably didn't know these)
- `FirstRetestAudit` --uses--> `Engine`  [INFERRED]
  tests/test_first_retest_audit.py → traderlab/replay.py
- `window()` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `ConfirmedAmendmentChecks` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `ConfirmedAmendmentChecks` --uses--> `Engine`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/replay.py
- `ConfirmedAmendmentChecks` --uses--> `Bos`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/strategy.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Native JSONL to checkpointed publisher, authenticated ingest and durable event storage** — tools_publish_events_module, docs_dashboard_ingest_api, docs_dashboard_postgresql_storage, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Three explicit dashboard evidence sources** — docs_dashboard_observability_console, docs_dashboard_synthetic_sample, docs_dashboard_local_jsonl_import, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Prepared locked gateway, native compilation only and blocked execution readiness** — docs_demo_gateway_isolated_demo_gateway, docs_demo_gateway_verification_boundary, docs_demo_readiness_demo_readiness [EXTRACTED 1.00]
- **Qualified tick break, terminal directional return and retained blocked-pair history** — docs_event_schema_bos_intrabar_break, docs_event_schema_first_directional_return, docs_event_schema_blocked_pair_history [EXTRACTED 1.00]
- **Automatic setup promotion requires approved linkage and observable validity/availability** — docs_automatic_backtest_blocked_geometry_303, docs_automatic_backtest_confirmed_setups_zero, docs_sources_canonical_strategy_fa_availability [EXTRACTED 1.00]
- **History occurrence identity and scoped completeness** — docs_loss_aware_capture_ordered_full_prefix, docs_loss_aware_capture_tick_raw_fields, docs_loss_aware_capture_duplicate_overlap_skips, docs_loss_aware_capture_broker_feed_complete_unknown [EXTRACTED 1.00]
- **Accepted suffix tick, as-of closed bars and archived directional lifecycle** — docs_native_retests_accepted_suffix_observer, docs_native_retests_as_of_stream, docs_native_retests_tracker_delivery_clock, docs_native_retests_per_bos_lifecycle, docs_native_retests_diagnostic_lanes, docs_native_retests_archived_history [EXTRACTED 1.00]
- **New compiled checks, fresh normal/stress captures and observed metrics remain required** — docs_native_retests_new_assertions, docs_native_retests_fresh_normal_steps, docs_native_retests_audited_expectations, docs_native_retests_fresh_stress_steps, docs_native_retests_verification_scope, docs_native_retests_performance_boundary [EXTRACTED 1.00]
- **Tracker delivery stream, tick identity and reconciled diagnostics required for genuine parity** — docs_native_retests_comparator, docs_native_retests_bar_event, docs_native_retests_break_event, docs_native_retests_return_event, docs_native_retests_summary_event, docs_native_retests_halted_detection [EXTRACTED 1.00]
- **Normal/stress paired evidence acceptance** — docs_tester_stress_capture_common_baseline, docs_tester_stress_capture_exact_raw_comparator, docs_tester_stress_capture_positive_recovery, docs_tester_stress_capture_duplicate_occurrence_vs_overlap [EXTRACTED 1.00]

## Communities (67 total, 39 thin omitted)

### Community 0 - "Paper Replay Rules"
Cohesion: 0.08
Nodes (30): bos(), CanonicalRules, Bar, big_candle(), Candidate, fvg(), instant(), Engine (+22 more)

### Community 1 - "Native Capture Integrity"
Cohesion: 0.10
Nodes (9): BatchChecks, at(), OwnerOct12Checks, config(), Engine, prime_return(), ReplayChecks, setup_event() (+1 more)

### Community 2 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 3 - "Capture and Replay Pipeline"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Web Application Dependencies"
Cohesion: 0.05
Nodes (39): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react (+31 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 6 - "Native Capture Integrity"
Cohesion: 0.09
Nodes (28): First-return audit and 2026-10-12 correction, Reviewed canonical authority and unavailable original PDFs, Full genuine diagnostic replay without setups or performance, M1 BUY qualification and actual structural break, M1 first Ask downward return: missed and consumed, M1 first Bid downward return: exact and spent, M1 FVG formation, availability and later full invalidity, M5 SELL mirrored first returns both miss reference (+20 more)

### Community 7 - "Dashboard API"
Cohesion: 0.12
Nodes (28): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+20 more)

### Community 8 - "Native Capture Integrity"
Cohesion: 0.18
Nodes (7): ConfirmedAmendmentChecks, window(), bar_event(), DetectionChecks, SessionChecks, AutomaticRelationships, Detector

### Community 9 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 10 - "Capture and Replay Pipeline"
Cohesion: 0.15
Nodes (12): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, compare_captures(), main(), tester_metadata(), capture_integer(), decimal() (+4 more)

### Community 13 - "Capture and Replay Pipeline"
Cohesion: 0.20
Nodes (10): main(), batch(), Equity, reports_results(), results(), main(), digest(), encode() (+2 more)

### Community 14 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 15 - "Native Capture Integrity"
Cohesion: 0.16
Nodes (6): comparator_fixture(), NativeRetestChecks, compare_capture(), compare_rows(), main(), signature()

### Community 17 - "Capture and Replay Pipeline"
Cohesion: 0.35
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 18 - "Native Capture Integrity"
Cohesion: 0.20
Nodes (6): NEWS_FORCE_CLOSE / NEWS_CLOSE_DEADLINE_MISSED, REVERSAL_MOMENTUM_CLOSE_DIAGNOSTIC does not enable Reverse, Sydney_open_to_New_York_close sourced UTC calendar contract, §§25–32 trend/news and Tehran NY context, §§17–20 split0.02 volume and fixed60/100 targets, NET daily guards/news deadline/soft NY context

### Community 19 - "Native Capture Integrity"
Cohesion: 0.24
Nodes (3): DEMO readiness owner§52: automatic approval/execution blocked, Batch paper evidence and simulated entry/exit quote contract, §52 direct owner-relayed final answers after906f9db

### Community 21 - "Native Capture Integrity"
Cohesion: 0.20
Nodes (6): Actual historical chart inspection observations, Historical tester-normal-run01 input, Identical diagnostic journal hashes, §4 Big Candle equals Momentum Candle, Owner chart numerical example, Confirmed Big/FVG/OB/BOS geometry with unresolved package

### Community 26 - "Paper Replay Rules"
Cohesion: 0.24
Nodes (3): FirstReturn, HistoricalRetests, History

### Community 27 - "Native Capture Integrity"
Cohesion: 0.22
Nodes (3): LiteFinance Broker and Execution Profile, Isolated DEMO gateway prepared, DISABLED and unconnected, Explicit unresolved configuration register

### Community 28 - "Native Capture Integrity"
Cohesion: 0.25
Nodes (5): Chronological JSONL event schema v0.2, Explicit sourced setup and structure annotations, TLCorePlan, §§39–45 exact original planned Core reverse retest, §§51.3,52.3 single Core/Reverse SL40 from actual fill

### Community 30 - "Native Capture Integrity"
Cohesion: 0.29
Nodes (4): TLBarDetector.Process, TLBosLevel, TLOrderBlockBounds, 2026-10-11 owner-resolved rules must not be re-asked

### Community 31 - "Paper Replay Rules"
Cohesion: 0.38
Nodes (6): TraderLab working rules, Automatic historical strategy diagnostics 2026-10-11, Native source relationships documented without MQL5 AST, Preserved Persian canonical strategy, sections1–52, TraderLab strategy specification v0.2, canonical1–52, TraderLab overview

### Community 32 - "Native Capture Integrity"
Cohesion: 0.29
Nodes (4): LiteFinance1000/300s and10000/3600s request thresholds, CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED preserves own FVG OB, BOS_FIRST_DIRECTIONAL_RETURN retained terminal evidence, FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION selected lane

### Community 34 - "Native Capture Integrity"
Cohesion: 0.33
Nodes (3): AutomaticRelationships geometric candidates, BOS_FVG_GEOMETRY_CONFIRMED necessary wick containment, §§5–7 three-candle wick-to-wick FVG

### Community 35 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 37 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 39 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Knowledge Gaps
- **107 isolated node(s):** `Status`, `allowJs`, `esModuleInterop`, `incremental`, `isolatedModules` (+102 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 265 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Engine` connect `Paper Replay Rules` to `Native Capture Integrity`, `Native Capture Integrity`, `Capture and Replay Pipeline`, `Capture and Replay Pipeline`, `Native Capture Integrity`, `Capture and Replay Pipeline`, `Native Capture Integrity`, `Native Capture Integrity`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `config()` connect `Native Capture Integrity` to `Paper Replay Rules`, `Native Capture Integrity`, `Capture and Replay Pipeline`, `Native Capture Integrity`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `DemoLedger` connect `Native Capture Integrity` to `Paper Replay Rules`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `FirstRetestAudit`) actually correct?**
  _`Engine` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `allowJs`, `esModuleInterop` to the rest of the system?**
  _107 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.07681970884658455 - nodes in this community are weakly interconnected._
- **Should `Native Capture Integrity` be split into smaller, more focused modules?**
  _Cohesion score 0.09724106739032112 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
