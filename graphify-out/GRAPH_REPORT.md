# Graph Report - TraderLab  (2026-10-07)

## Corpus Check
- 57 files · ~34,968 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 538 nodes · 1148 edges · 33 communities (22 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Paper Replay Rules
- Capture and Replay Pipeline
- Native Capture and Broker Docs
- Broker Capability Checks
- Signal Detection
- Dashboard Interface
- Dashboard Product and Guides
- Dashboard API
- TypeScript Configuration
- Capture and Replay Pipeline
- Detection and Session Tests
- Web Application Dependencies
- Native Capture Integrity
- Canonical Strategy Tests
- Runtime Packages
- Native Capture and Broker Docs
- Typography and Root Layout
- Database Setup Script
- Native Capture Integrity
- Build and Development Scripts
- Vercel Deployment Settings
- Guides and Next Configuration
- Native Normalizer Tests
- PostgreSQL Event Storage
- TypeScript Development Dependencies
- Chart License Notices
- Canonical Strategy Source

## God Nodes (most connected - your core abstractions)
1. `Engine` - 45 edges
2. `Loss Aware Capture` - 30 edges
3. `ReplayChecks` - 26 edges
4. `config()` - 26 edges
5. `Dashboard()` - 25 edges
6. `tick()` - 23 edges
7. `setup_event()` - 19 edges
8. `compilerOptions` - 16 edges
9. `TraderLab observability console` - 13 edges
10. `inspect_capture()` - 13 edges

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
- **Fresh run05 acceptance evidence** — docs_loss_aware_capture_run05_acceptance, docs_loss_aware_capture_inspector_normalizer, docs_loss_aware_capture_v2_counters, docs_loss_aware_capture_clean_deinit, docs_loss_aware_capture_terminal_evidence [EXTRACTED 1.00]
- **History-authoritative startup, drain and retained occurrence prefix** — docs_loss_aware_capture_history_startup, docs_loss_aware_capture_history_drain, docs_loss_aware_capture_full_prefix_cursor, docs_loss_aware_capture_batch_validation [EXTRACTED 1.00]
- **TraderLab Read-only Detection, Capture, and Paper Replay** — readme_traderlab, docs_strategy_spec_traderlab_strategy_spec_v01 [INFERRED 0.85]

## Communities (33 total, 11 thin omitted)

### Community 0 - "Paper Replay Rules"
Cohesion: 0.12
Nodes (15): Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: OB-01, BOS-02, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01, Regression trace: Unresolved config and execution (+7 more)

### Community 1 - "Capture and Replay Pipeline"
Cohesion: 0.07
Nodes (14): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, CaptureInspectorChecks, event(), valid_capture(), capture_integer(), decimal() (+6 more)

### Community 2 - "Native Capture and Broker Docs"
Cohesion: 0.06
Nodes (34): Reserved request lifecycle vocabulary, Event Schema, EXECUTION_UNRESOLVED, Native server, UTC and Tehran timestamps, First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0 (+26 more)

### Community 3 - "Broker Capability Checks"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Signal Detection"
Cohesion: 0.10
Nodes (24): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Bar, big_candle(), Candidate, Detector, fvg(), instant() (+16 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 6 - "Dashboard Product and Guides"
Cohesion: 0.07
Nodes (34): TraderLab working rules, Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL (+26 more)

### Community 7 - "Dashboard API"
Cohesion: 0.15
Nodes (26): dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE(), dynamic (+18 more)

### Community 8 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 9 - "Capture and Replay Pipeline"
Cohesion: 0.27
Nodes (6): Regression trace: Reproducibility, main(), digest(), encode(), json_line(), run()

### Community 10 - "Detection and Session Tests"
Cohesion: 0.29
Nodes (4): Regression trace: NY-01/02, bar_event(), DetectionChecks, SessionChecks

### Community 11 - "Web Application Dependencies"
Cohesion: 0.15
Nodes (12): lightweight-charts, @phosphor-icons/react, react-dom, @types/node, @types/react, @types/react-dom, typescript, engines (+4 more)

### Community 13 - "Canonical Strategy Tests"
Cohesion: 0.31
Nodes (4): Regression trace: BE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules

### Community 14 - "Runtime Packages"
Cohesion: 0.22
Nodes (9): dependencies, @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, next, @phosphor-icons/react, react (+1 more)

### Community 15 - "Native Capture and Broker Docs"
Cohesion: 0.40
Nodes (4): LiteFinance Broker and Execution Profile, Read-only Detection and Paper Replay, TraderLab Strategy Specification v0.1, TraderLab README

### Community 16 - "Typography and Root Layout"
Cohesion: 0.33
Nodes (3): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, metadata

### Community 17 - "Database Setup Script"
Cohesion: 0.33
Nodes (4): @neondatabase/serverless, divider, sql, statements

### Community 19 - "Build and Development Scripts"
Cohesion: 0.33
Nodes (6): scripts, build, db:setup, dev, start, typecheck

### Community 20 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 23 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 24 - "TypeScript Development Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, @types/react, @types/react-dom, typescript

### Community 26 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Knowledge Gaps
- **87 isolated node(s):** `Status`, `node`, `name`, `private`, `version` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 156 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`, `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `next` connect `Guides and Next Configuration` to `Typography and Root Layout`, `Web Application Dependencies`, `Dashboard Interface`, `Dashboard API`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `Status`, `node`, `name` to the rest of the system?**
  _87 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.11694915254237288 - nodes in this community are weakly interconnected._
- **Should `Capture and Replay Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.07017543859649122 - nodes in this community are weakly interconnected._
- **Should `Native Capture and Broker Docs` be split into smaller, more focused modules?**
  _Cohesion score 0.06233766233766234 - nodes in this community are weakly interconnected._
- **Should `Broker Capability Checks` be split into smaller, more focused modules?**
  _Cohesion score 0.09158186864014801 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
