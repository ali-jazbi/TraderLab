# Graph Report - TraderLab  (2026-10-10)

## Corpus Check
- 61 files · ~38,067 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 586 nodes · 1233 edges · 35 communities (22 shown, 13 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Capture and Replay Pipeline
- Paper Replay Rules
- Web Application Dependencies
- Signal Detection
- Dashboard API
- Dashboard Interface
- Dashboard Product and Guides
- Broker Capability Checks
- Native Capture Integrity
- TypeScript Configuration
- Native Capture and Broker Docs
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Detection and Session Tests
- Capture and Replay Pipeline
- Native Capture and Broker Docs
- Canonical Strategy Tests
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture and Broker Docs
- Native Capture Integrity
- Native Capture and Broker Docs
- Vercel Deployment Settings
- Native Normalizer Tests
- PostgreSQL Event Storage
- Chart License Notices
- Canonical Strategy Source

## God Nodes (most connected - your core abstractions)
1. `Engine` - 45 edges
2. `ReplayChecks` - 26 edges
3. `config()` - 26 edges
4. `Dashboard()` - 25 edges
5. `tick()` - 23 edges
6. `Loss Aware Capture` - 23 edges
7. `Tester Stress Capture` - 21 edges
8. `setup_event()` - 19 edges
9. `Event Schema` - 18 edges
10. `compilerOptions` - 16 edges

## Surprising Connections (you probably didn't know these)
- `NYBias` --references--> `Regression trace: NY-01/02`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `DailyGuard` --references--> `Regression trace: DAY-01/02`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `news_block()` --references--> `Regression trace: NEWS-01`  [EXTRACTED]
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
- **History occurrence identity and scoped completeness** — docs_loss_aware_capture_ordered_full_prefix, docs_loss_aware_capture_tick_raw_fields, docs_loss_aware_capture_duplicate_overlap_skips, docs_loss_aware_capture_broker_feed_complete_unknown [EXTRACTED 1.00]
- **Normal/stress paired evidence acceptance** — docs_tester_stress_capture_common_baseline, docs_tester_stress_capture_exact_raw_comparator, docs_tester_stress_capture_positive_recovery, docs_tester_stress_capture_duplicate_occurrence_vs_overlap [EXTRACTED 1.00]
- **TraderLab Read-only Detection, Capture, and Paper Replay** — readme_traderlab, docs_strategy_spec_traderlab_strategy_spec_v01 [INFERRED 0.85]

## Communities (35 total, 13 thin omitted)

### Community 0 - "Capture and Replay Pipeline"
Cohesion: 0.06
Nodes (26): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, Regression trace: Reproducibility, BrokerCapabilityChecks, compare_captures(), main(), tester_metadata() (+18 more)

### Community 1 - "Paper Replay Rules"
Cohesion: 0.12
Nodes (15): Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: OB-01, BOS-02, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01, Regression trace: Unresolved config and execution (+7 more)

### Community 2 - "Web Application Dependencies"
Cohesion: 0.04
Nodes (40): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react, react-dom, @types/node (+32 more)

### Community 3 - "Signal Detection"
Cohesion: 0.10
Nodes (24): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Bar, big_candle(), Candidate, Detector, fvg(), instant() (+16 more)

### Community 4 - "Dashboard API"
Cohesion: 0.12
Nodes (29): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+21 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.13
Nodes (34): Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login(), logout() (+26 more)

### Community 6 - "Dashboard Product and Guides"
Cohesion: 0.07
Nodes (34): TraderLab working rules, Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL (+26 more)

### Community 7 - "Broker Capability Checks"
Cohesion: 0.17
Nodes (4): RequestGuardChecks, BrokerRequestGateway, RequestRecord, RollingRequestGuard

### Community 8 - "Native Capture Integrity"
Cohesion: 0.15
Nodes (6): duplicate_overlap_skips, Tester Stress Capture, hold_during_skips, skip_n_drain_one_after_baseline, TESTER_STRESS_CONFIG, TESTER_STRESS_SUMMARY

### Community 9 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 10 - "Native Capture and Broker Docs"
Cohesion: 0.14
Nodes (4): Closed bar availability, Event Schema, Ordered quote replay, Sourced Setup and Structure Annotations

### Community 11 - "Native Capture Integrity"
Cohesion: 0.16
Nodes (3): Loss Aware Capture, TICK_CAPTURE_RECOVERY, TICK_CAPTURE_START

### Community 13 - "Native Capture Integrity"
Cohesion: 0.22
Nodes (3): TICK_CAPTURE_START_DEFERRED, Historical Tester Capture, tester_no_first_tick

### Community 14 - "Detection and Session Tests"
Cohesion: 0.29
Nodes (4): Regression trace: NY-01/02, bar_event(), DetectionChecks, SessionChecks

### Community 15 - "Capture and Replay Pipeline"
Cohesion: 0.39
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 16 - "Native Capture and Broker Docs"
Cohesion: 0.29
Nodes (9): inspect_capture and normalize_mt5_log, TLBarDetector.Process and TLCandidateEpoch, Native Code Map, TLEventLog, traderlab/replay.py paper state machine, Native execution, full paper state machine and parity pending, StrategyChecks synthetic native checks, TLTickCapture and TLTickCursor (+1 more)

### Community 17 - "Canonical Strategy Tests"
Cohesion: 0.31
Nodes (4): Regression trace: BE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules

### Community 20 - "Native Capture and Broker Docs"
Cohesion: 0.33
Nodes (4): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0

### Community 22 - "Native Capture and Broker Docs"
Cohesion: 0.40
Nodes (4): LiteFinance Broker and Execution Profile, Read-only Detection and Paper Replay, TraderLab Strategy Specification v0.1, TraderLab README

### Community 23 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 25 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 27 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Knowledge Gaps
- **87 isolated node(s):** `Status`, `maxDuration`, `framework`, `$schema`, `traderlab_login_limits` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 177 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `next` connect `Dashboard API` to `Web Application Dependencies`, `Dashboard Interface`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `inspect_capture()` connect `Capture and Replay Pipeline` to `Native Capture Integrity`, `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **What connects `Status`, `maxDuration`, `framework` to the rest of the system?**
  _87 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Capture and Replay Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.059319482083709726 - nodes in this community are weakly interconnected._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.11864406779661017 - nodes in this community are weakly interconnected._
- **Should `Web Application Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.044444444444444446 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
