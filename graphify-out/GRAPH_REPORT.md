# Graph Report - TraderLab  (2026-10-07)

## Corpus Check
- 55 files · ~31,679 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 474 nodes · 1037 edges · 24 communities (16 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Paper Replay Rules
- Broker Capability Checks
- Detection and Session Tests
- Canonical Strategy Tests
- Native Normalizer Tests
- Signal Detection
- Dashboard Interface
- Capture Validation
- Replay and Live Publishing
- Web UI Dependencies
- Dashboard API
- TypeScript Configuration
- Vercel Deployment Settings
- PostgreSQL Event Storage
- Chart License Notices
- Canonical Strategy Source
- Dashboard Product and Guides
- Native Capture and Broker Docs

## God Nodes (most connected - your core abstractions)
1. `Engine` - 45 edges
2. `ReplayChecks` - 26 edges
3. `config()` - 26 edges
4. `Dashboard()` - 25 edges
5. `tick()` - 23 edges
6. `setup_event()` - 19 edges
7. `compilerOptions` - 16 edges
8. `TraderLab observability console` - 13 edges
9. `BrokerRequestGateway` - 12 edges
10. `authenticated()` - 12 edges

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
- **TraderLab Read-only Detection, Capture, and Paper Replay** — readme_traderlab, docs_first_demo_capture_first_litefinance_demo_capture, docs_event_schema_event_schema_v01, docs_strategy_spec_traderlab_strategy_spec_v01 [INFERRED 0.85]

## Communities (24 total, 8 thin omitted)

### Community 0 - "Paper Replay Rules"
Cohesion: 0.12
Nodes (14): ReplayChecks, Engine, Setup, config(), setup_event(), tick(), Regression trace: DAY-01/02, Regression trace: FVG-03 (+6 more)

### Community 1 - "Broker Capability Checks"
Cohesion: 0.09
Nodes (13): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, RequestRecord, RollingRequestGuard, main(), capability_issues(), diagnose_server_offset() (+5 more)

### Community 11 - "Detection and Session Tests"
Cohesion: 0.29
Nodes (4): DetectionChecks, SessionChecks, bar_event(), Regression trace: NY-01/02

### Community 12 - "Canonical Strategy Tests"
Cohesion: 0.31
Nodes (4): CanonicalRules, bos(), Regression trace: BE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01

### Community 3 - "Signal Detection"
Cohesion: 0.10
Nodes (24): Bar, Candidate, Detector, NYBias, Bos, DailyGuard, Plan, Unresolved (+16 more)

### Community 4 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): Status, Bar, Dataset, EventRow, RunInfo, Page(), Analytics(), clock() (+28 more)

### Community 7 - "Capture Validation"
Cohesion: 0.11
Nodes (7): CaptureInspectorChecks, NativeLogContractChecks, event(), valid_capture(), decimal(), inspect_capture(), main()

### Community 8 - "Replay and Live Publishing"
Cohesion: 0.11
Nodes (9): Position, main(), publish(), main(), digest(), encode(), json_line(), run() (+1 more)

### Community 2 - "Web UI Dependencies"
Cohesion: 0.05
Nodes (39): metadata, dependencies, @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, next, @phosphor-icons/react (+31 more)

### Community 5 - "Dashboard API"
Cohesion: 0.12
Nodes (28): GET(), POST(), GET(), DELETE(), POST(), GET(), authenticated(), issueSession() (+20 more)

### Community 10 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 13 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 15 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 17 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): TradingView Lightweight Charts v5.2.1, Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice

### Community 6 - "Dashboard Product and Guides"
Cohesion: 0.07
Nodes (34): tools/publish_events.py: checkpointed stdlib local publisher, web/db/schema.sql: documented database schema, Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, Browser-local JSONL import, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+26 more)

### Community 9 - "Native Capture and Broker Docs"
Cohesion: 0.14
Nodes (19): Execution Unresolved Event, Read-only Detection and Paper Replay, Sourced Setup and Structure Annotations, LiteFinance Broker and Execution Profile, Event Schema v0.1, TraderLab Strategy Specification v0.1, TraderLab README, StrategyChecks.mq5 (+11 more)

## Knowledge Gaps
- **81 isolated node(s):** `Status`, `allowJs`, `esModuleInterop`, `incremental`, `isolatedModules` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 138 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Native source map` connect `Native Capture and Broker Docs` to `Replay and Live Publishing`, `Broker Capability Checks`, `Dashboard Product and Guides`, `Capture Validation`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `Native MT5 validation milestone` connect `Dashboard Product and Guides` to `Native Capture and Broker Docs`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `Engine` connect `Paper Replay Rules` to `Replay and Live Publishing`, `Capture Validation`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **What connects `Status`, `allowJs`, `esModuleInterop` to the rest of the system?**
  _81 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.11981297486849796 - nodes in this community are weakly interconnected._
- **Should `Broker Capability Checks` be split into smaller, more focused modules?**
  _Cohesion score 0.08928571428571429 - nodes in this community are weakly interconnected._
- **Should `Signal Detection` be split into smaller, more focused modules?**
  _Cohesion score 0.10253699788583509 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
Graph health: no dangling/missing endpoints or collapsed edges; two pre-existing self-loops remain (encode recursion and super().__init__ extraction).
