# Graph Report - TraderLab  (2026-10-06)

## Corpus Check
- 17 files · ~27,817 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 435 nodes · 933 edges · 20 communities (15 shown, 5 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.88)
- Token cost: unavailable (host-agent usage not exposed)

## Community Hubs (Navigation)
- Paper Replay Rules
- Broker Safety Checks
- Dashboard Dependencies
- Signal Detection and Sessions
- Dashboard Interface
- Strategy and Broker Docs
- Dashboard API and Auth
- Replay and Event Publisher
- Dashboard Architecture Docs
- TypeScript Configuration
- Detection and Session Tests
- Strategy Rule Tests
- Vercel Deployment Config
- Neon Event Storage
- Chart License
- Persian Canonical Source

## God Nodes (most connected - your core abstractions)
1. `Engine` - 42 edges
2. `Dashboard()` - 25 edges
3. `config()` - 24 edges
4. `ReplayChecks` - 24 edges
5. `tick()` - 21 edges
6. `setup_event()` - 17 edges
7. `compilerOptions` - 16 edges
8. `TraderLab observability console` - 13 edges
9. `Unresolved strategy and execution questions` - 13 edges
10. `authenticated()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `DailyGuard` --references--> `Regression trace: DAY-01/02`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `NYBias` --references--> `Regression trace: NY-01/02`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
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

## Communities (20 total, 5 thin omitted)

### Community 0 - "Paper Replay Rules"
Cohesion: 0.12
Nodes (15): Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: OB-01, BOS-02, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01, Regression trace: Unresolved config and execution (+7 more)

### Community 1 - "Broker Safety Checks"
Cohesion: 0.10
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, main(), BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible() (+4 more)

### Community 2 - "Dashboard Dependencies"
Cohesion: 0.05
Nodes (39): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react (+31 more)

### Community 3 - "Signal Detection and Sessions"
Cohesion: 0.10
Nodes (24): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Bar, big_candle(), Candidate, Detector, fvg(), instant() (+16 more)

### Community 4 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 5 - "Strategy and Broker Docs"
Cohesion: 0.07
Nodes (39): TraderLab working rules, Future durable broker request gateway, Broker gap handling rules, LiteFinance broker and execution profile, LiteFinance rolling request limits, Runtime broker capability snapshot, Seasonal server time offsets, Event availability and chronology (+31 more)

### Community 6 - "Dashboard API and Auth"
Cohesion: 0.12
Nodes (28): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+20 more)

### Community 7 - "Replay and Event Publisher"
Cohesion: 0.10
Nodes (8): Regression trace: Reproducibility, main(), publish(), main(), digest(), encode(), json_line(), run()

### Community 8 - "Dashboard Architecture Docs"
Cohesion: 0.13
Nodes (21): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+13 more)

### Community 9 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 10 - "Detection and Session Tests"
Cohesion: 0.29
Nodes (4): Regression trace: NY-01/02, bar_event(), DetectionChecks, SessionChecks

### Community 11 - "Strategy Rule Tests"
Cohesion: 0.31
Nodes (4): Regression trace: BE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules

### Community 12 - "Vercel Deployment Config"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 13 - "Neon Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 15 - "Chart License"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Knowledge Gaps
- **74 isolated node(s):** `Status`, `@fontsource/ibm-plex-mono`, `@fontsource/vazirmatn`, `lightweight-charts`, `@neondatabase/serverless` (+69 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 124 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Engine` connect `Paper Replay Rules` to `Replay and Event Publisher`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `next` connect `Dashboard API and Auth` to `Dashboard Dependencies`, `Dashboard Interface`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `Status`, `@fontsource/ibm-plex-mono`, `@fontsource/vazirmatn` to the rest of the system?**
  _74 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.12092731829573934 - nodes in this community are weakly interconnected._
- **Should `Broker Safety Checks` be split into smaller, more focused modules?**
  _Cohesion score 0.09595959595959595 - nodes in this community are weakly interconnected._
- **Should `Dashboard Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
- **Should `Signal Detection and Sessions` be split into smaller, more focused modules?**
  _Cohesion score 0.10253699788583509 - nodes in this community are weakly interconnected._