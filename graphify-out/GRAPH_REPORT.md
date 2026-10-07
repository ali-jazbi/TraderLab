# Graph Report - TraderLab  (2026-10-07)

## Corpus Check
- 57 files · ~34,470 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 506 nodes · 1110 edges · 30 communities (20 shown, 10 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Capture and Replay Pipeline
- Paper Replay Rules
- Canonical Strategy Tests
- Tick Capture Evidence
- Native Normalizer Tests
- Broker Capability Checks
- Signal Detection
- Dashboard Interface
- Detection and Session Tests
- Typography and Root Layout
- Guides and Next Configuration
- Dashboard API
- Web Application Dependencies
- Runtime Packages
- Database Setup Script
- Build and Development Scripts
- Vercel Deployment Settings
- PostgreSQL Event Storage
- TypeScript Development Dependencies
- TypeScript Configuration
- Chart License Notices
- Canonical Strategy Source
- Native Capture and Broker Docs
- Dashboard Product and Guides

## God Nodes (most connected - your core abstractions)
1. `Engine` - 45 edges
2. `ReplayChecks` - 26 edges
3. `config()` - 26 edges
4. `Dashboard()` - 25 edges
5. `tick()` - 23 edges
6. `setup_event()` - 19 edges
7. `compilerOptions` - 16 edges
8. `inspect_capture()` - 13 edges
9. `TraderLab observability console` - 13 edges
10. `BrokerRequestGateway` - 12 edges

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

## Communities (30 total, 10 thin omitted)

### Community 0 - "Capture and Replay Pipeline"
Cohesion: 0.06
Nodes (18): CaptureInspectorChecks, NativeLogContractChecks, event(), valid_capture(), capture_integer(), decimal(), inspect_capture(), main() (+10 more)

### Community 1 - "Paper Replay Rules"
Cohesion: 0.12
Nodes (15): ReplayChecks, Engine, Position, Setup, config(), setup_event(), tick(), Regression trace: DAY-01/02 (+7 more)

### Community 11 - "Canonical Strategy Tests"
Cohesion: 0.31
Nodes (4): CanonicalRules, bos(), Regression trace: BE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01

### Community 2 - "Broker Capability Checks"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, RequestRecord, RollingRequestGuard, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds() (+4 more)

### Community 3 - "Signal Detection"
Cohesion: 0.10
Nodes (24): Bar, Candidate, Detector, NYBias, Bos, DailyGuard, Plan, Unresolved (+16 more)

### Community 4 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): Status, Bar, Dataset, EventRow, RunInfo, Page(), Analytics(), clock() (+28 more)

### Community 9 - "Detection and Session Tests"
Cohesion: 0.29
Nodes (4): DetectionChecks, SessionChecks, bar_event(), Regression trace: NY-01/02

### Community 14 - "Typography and Root Layout"
Cohesion: 0.33
Nodes (3): metadata, @fontsource/ibm-plex-mono, @fontsource/vazirmatn

### Community 7 - "Dashboard API"
Cohesion: 0.15
Nodes (26): GET(), POST(), GET(), DELETE(), POST(), GET(), authenticated(), issueSession() (+18 more)

### Community 10 - "Web Application Dependencies"
Cohesion: 0.15
Nodes (12): engines, node, name, private, version, lightweight-charts, @phosphor-icons/react, react-dom (+4 more)

### Community 13 - "Runtime Packages"
Cohesion: 0.22
Nodes (9): dependencies, @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, next, @phosphor-icons/react, react (+1 more)

### Community 15 - "Database Setup Script"
Cohesion: 0.33
Nodes (4): divider, sql, statements, @neondatabase/serverless

### Community 16 - "Build and Development Scripts"
Cohesion: 0.33
Nodes (6): scripts, build, db:setup, dev, start, typecheck

### Community 17 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 20 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 21 - "TypeScript Development Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, @types/react, @types/react-dom, typescript

### Community 8 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 23 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): TradingView Lightweight Charts v5.2.1, Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice

### Community 5 - "Native Capture and Broker Docs"
Cohesion: 0.09
Nodes (28): MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, Read-only Detection and Paper Replay, Sourced Setup and Structure Annotations, LiteFinance Broker and Execution Profile, First LiteFinance Demo capture review — 2026-10-07, TraderLab Strategy Specification v0.1, TraderLab README (+20 more)

### Community 6 - "Dashboard Product and Guides"
Cohesion: 0.07
Nodes (34): tools/publish_events.py: checkpointed stdlib local publisher, web/db/schema.sql: documented database schema, Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, Browser-local JSONL import, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+26 more)

## Knowledge Gaps
- **81 isolated node(s):** `Status`, `node`, `name`, `private`, `version` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 141 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Native source map` connect `Native Capture and Broker Docs` to `Dashboard Product and Guides`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `Native MT5 validation milestone` connect `Dashboard Product and Guides` to `Native Capture and Broker Docs`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **What connects `Status`, `node`, `name` to the rest of the system?**
  _81 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Capture and Replay Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.0579476861167002 - nodes in this community are weakly interconnected._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.11694915254237288 - nodes in this community are weakly interconnected._
- **Should `Broker Capability Checks` be split into smaller, more focused modules?**
  _Cohesion score 0.09468599033816426 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
Graph health: no dangling/missing endpoints or collapsed edges; two pre-existing self-loops remain (encode recursion and super().__init__ extraction).
