# Graph Report - TraderLab  (2026-10-10)

## Corpus Check
- 58 files · ~36,104 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 556 nodes · 1169 edges · 29 communities (18 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Native Capture and Broker Docs
- Paper Replay Rules
- Capture and Replay Pipeline
- Broker Capability Checks
- Dashboard Interface
- Web Application Dependencies
- Signal Detection
- Dashboard Product and Guides
- Dashboard API
- TypeScript Configuration
- Detection and Session Tests
- Capture and Replay Pipeline
- Native Capture Integrity
- Canonical Strategy Tests
- Native Capture and Broker Docs
- Native Capture Integrity
- Native Capture and Broker Docs
- Vercel Deployment Settings
- Native Normalizer Tests
- PostgreSQL Event Storage
- Chart License Notices
- Canonical Strategy Source
- Native Capture and Broker Docs

## God Nodes (most connected - your core abstractions)
1. `Engine` - 45 edges
2. `ReplayChecks` - 26 edges
3. `config()` - 26 edges
4. `Dashboard()` - 25 edges
5. `tick()` - 23 edges
6. `Loss-aware native tick capture` - 23 edges
7. `Historical Strategy Tester capture startup` - 21 edges
8. `setup_event()` - 19 edges
9. `compilerOptions` - 16 edges
10. `TraderLab observability console` - 13 edges

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
- **Capture acceptance requires retained evidence, strict validation and explicit limits** — docs_historical_tester_capture_historical_acceptance, docs_loss_aware_capture_inspector_normalizer, docs_event_schema_native_tick_metadata [INFERRED 0.85]
- **TraderLab Read-only Detection, Capture, and Paper Replay** — readme_traderlab, docs_strategy_spec_traderlab_strategy_spec_v01 [INFERRED 0.85]

## Communities (29 total, 11 thin omitted)

### Community 0 - "Native Capture and Broker Docs"
Cohesion: 0.05
Nodes (47): TICK_CAPTURE_START_DEFERRED: second precision, environment=strategy_tester, until=first_ontick, first_callback_history_is_baseline=true; does not replace START or certify capture, Event schema v0.1, REQUEST lifecycle reserved for future gateway; timeout stays unknown until authoritative reconciliation; current diagnostic EA has no order-send site, Native TICK exact broker alias and precision; loss-aware ms/raw fields preserve distinct and identical occurrences through tick_index and ordinal, Output seq/time/event/rule/spec_version; confirmation availability, attributed annotations, core/BOS plans/fills, exits, reverse anchors, guards, broker diagnostics and NY context, JSONL replay input: explicit UTC chronological time, decimal strings, unique event_id, canonical XAUUSD for authored replay metadata, Valid prices/times, advancing nonoverlapping bars, globally unique BOS IDs and preserved input ordering; OHLC does not fabricate ticks, bar/tick/setup/structure input types: closed-bar availability, actual quotes and tie index, sourced confirmed setup zones/linkages and sourced structure confirmation (+39 more)

### Community 1 - "Paper Replay Rules"
Cohesion: 0.11
Nodes (16): Regression trace: BE-01, Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: OB-01, BOS-02, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: TOUCH-01, SIZE-01 (+8 more)

### Community 2 - "Capture and Replay Pipeline"
Cohesion: 0.07
Nodes (14): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, CaptureInspectorChecks, event(), valid_capture(), capture_integer(), decimal() (+6 more)

### Community 3 - "Broker Capability Checks"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Dashboard Interface"
Cohesion: 0.11
Nodes (39): react, dynamic, POST(), Page(), Analytics(), clock(), Dashboard(), changeSource() (+31 more)

### Community 5 - "Web Application Dependencies"
Cohesion: 0.05
Nodes (39): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react (+31 more)

### Community 6 - "Signal Detection"
Cohesion: 0.11
Nodes (23): Regression trace: BIG-01/02, FVG-01/02, Bar, big_candle(), Candidate, Detector, fvg(), instant(), news_block() (+15 more)

### Community 7 - "Dashboard Product and Guides"
Cohesion: 0.07
Nodes (34): TraderLab working rules, Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL (+26 more)

### Community 8 - "Dashboard API"
Cohesion: 0.13
Nodes (25): next, dynamic, GET(), dynamic, GET(), DELETE(), dynamic, POST() (+17 more)

### Community 9 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 10 - "Detection and Session Tests"
Cohesion: 0.26
Nodes (5): Regression trace: BOS-01, Regression trace: NY-01/02, bar_event(), DetectionChecks, SessionChecks

### Community 11 - "Capture and Replay Pipeline"
Cohesion: 0.27
Nodes (6): Regression trace: Reproducibility, main(), digest(), encode(), json_line(), run()

### Community 13 - "Canonical Strategy Tests"
Cohesion: 0.36
Nodes (3): Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules

### Community 14 - "Native Capture and Broker Docs"
Cohesion: 0.33
Nodes (4): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0

### Community 16 - "Native Capture and Broker Docs"
Cohesion: 0.40
Nodes (4): LiteFinance Broker and Execution Profile, Read-only Detection and Paper Replay, TraderLab Strategy Specification v0.1, TraderLab README

### Community 17 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 19 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 21 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Underlying tester allocation/readiness mechanism remains unproven` → `Strategy Tester agent-local tick cache/database`  [AMBIGUOUS]
  docs/HISTORICAL_TESTER_CAPTURE.md · relation: conceptually_related_to

## Knowledge Gaps
- **92 isolated node(s):** `Status`, `node`, `name`, `private`, `version` (+87 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 163 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Underlying tester allocation/readiness mechanism remains unproven` and `Strategy Tester agent-local tick cache/database`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Engine` connect `Paper Replay Rules` to `Capture and Replay Pipeline`, `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `next` connect `Dashboard API` to `Dashboard Interface`, `Web Application Dependencies`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `Status`, `node`, `name` to the rest of the system?**
  _92 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Native Capture and Broker Docs` be split into smaller, more focused modules?**
  _Cohesion score 0.05222734254992319 - nodes in this community are weakly interconnected._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.11420765027322405 - nodes in this community are weakly interconnected._
- **Should `Capture and Replay Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.06836055656382335 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
