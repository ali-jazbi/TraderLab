# Graph Report - TraderLab  (2026-10-06)

## Corpus Check
- 15 files · ~30,342 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 454 nodes · 982 edges · 22 communities (15 shown, 7 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Capture Validation
- Paper Replay Rules
- Web UI Dependencies
- Signal Detection
- Dashboard Product and Guides
- Dashboard Interface
- Dashboard API
- Broker Request Safety
- TypeScript Configuration
- Strategy and Normalizer Tests
- Detection and Session Tests
- Strategy and Broker Docs
- Vercel Deployment Settings
- PostgreSQL Event Storage
- Chart License Notices
- Canonical Strategy Source

## God Nodes (most connected - your core abstractions)
1. `Engine` - 45 edges
2. `config()` - 26 edges
3. `ReplayChecks` - 26 edges
4. `Dashboard()` - 25 edges
5. `tick()` - 23 edges
6. `setup_event()` - 19 edges
7. `compilerOptions` - 16 edges
8. `TraderLab observability console` - 13 edges
9. `authenticated()` - 12 edges
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

## Communities (22 total, 7 thin omitted)

### Community 0 - "Capture Validation"
Cohesion: 0.06
Nodes (23): Regression trace: Reproducibility, BrokerCapabilityChecks, CaptureInspectorChecks, event(), valid_capture(), decimal(), inspect_capture(), main() (+15 more)

### Community 1 - "Paper Replay Rules"
Cohesion: 0.12
Nodes (15): Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: OB-01, BOS-02, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01, Regression trace: Unresolved config and execution (+7 more)

### Community 2 - "Web UI Dependencies"
Cohesion: 0.05
Nodes (39): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react (+31 more)

### Community 3 - "Signal Detection"
Cohesion: 0.10
Nodes (24): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Bar, big_candle(), Candidate, Detector, fvg(), instant() (+16 more)

### Community 4 - "Dashboard Product and Guides"
Cohesion: 0.06
Nodes (40): TraderLab working rules, Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL (+32 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 6 - "Dashboard API"
Cohesion: 0.12
Nodes (28): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+20 more)

### Community 7 - "Broker Request Safety"
Cohesion: 0.17
Nodes (4): RequestGuardChecks, BrokerRequestGateway, RequestRecord, RollingRequestGuard

### Community 8 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 9 - "Strategy and Normalizer Tests"
Cohesion: 0.21
Nodes (5): Regression trace: BE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, NormalizeNativeLogChecks, bos(), CanonicalRules

### Community 10 - "Detection and Session Tests"
Cohesion: 0.29
Nodes (4): Regression trace: NY-01/02, bar_event(), DetectionChecks, SessionChecks

### Community 11 - "Strategy and Broker Docs"
Cohesion: 0.22
Nodes (8): LiteFinance Broker and Execution Profile, Event Schema v0.1, Execution Unresolved Event, First LiteFinance Demo Capture, Read-only Detection and Paper Replay, Sourced Setup and Structure Annotations, TraderLab Strategy Specification v0.1, TraderLab README

### Community 12 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 13 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 15 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Knowledge Gaps
- **86 isolated node(s):** `Status`, `maxDuration`, `framework`, `$schema`, `traderlab_login_limits` (+81 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 140 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Engine` connect `Paper Replay Rules` to `Capture Validation`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `next` connect `Dashboard API` to `Web UI Dependencies`, `Dashboard Interface`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `BrokerRequestGateway` connect `Broker Request Safety` to `Capture Validation`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `Status`, `maxDuration`, `framework` to the rest of the system?**
  _86 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Capture Validation` be split into smaller, more focused modules?**
  _Cohesion score 0.05824561403508772 - nodes in this community are weakly interconnected._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.11694915254237288 - nodes in this community are weakly interconnected._
- **Should `Web UI Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._