# Graph Report - TraderLab  (2026-10-11)

## Corpus Check
- 67 files · ~43,620 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 665 nodes · 1540 edges · 39 communities (22 shown, 17 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Paper Replay Rules
- Capture and Replay Pipeline
- Native Capture Integrity
- Capture and Replay Pipeline
- Paper Replay Rules
- Native Capture Integrity
- Dashboard Interface
- Dashboard API
- Signal Detection
- Native Capture Integrity
- Dashboard Product and Guides
- TypeScript Configuration
- Capture and Replay Pipeline
- Native Capture Integrity
- Web Application Dependencies
- Native Capture Integrity
- Native Capture Integrity
- Web Application Dependencies
- Web Application Dependencies
- Web Application Dependencies
- Web Application Dependencies
- Vercel Deployment Settings
- Dashboard API
- Native Normalizer Tests
- PostgreSQL Event Storage
- Web Application Dependencies
- Chart License Notices
- Native Capture and Broker Docs
- Dashboard Product and Guides
- Native Capture Integrity

## God Nodes (most connected - your core abstractions)
1. `Engine` - 60 edges
2. `config()` - 31 edges
3. `tick()` - 28 edges
4. `ReplayChecks` - 27 edges
5. `Dashboard()` - 25 edges
6. `setup_event()` - 23 edges
7. `Loss Aware Capture` - 21 edges
8. `Tester Stress Capture` - 20 edges
9. `number()` - 19 edges
10. `ConfirmedAmendmentChecks` - 18 edges

## Surprising Connections (you probably didn't know these)
- `DailyGuard` --references--> `Regression trace: DAY-01/02`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `NYBias` --references--> `Regression trace: NY-01/02`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `news_block()` --references--> `Regression trace: NEWS-01`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `ob_broken()` --references--> `Regression trace: REV-01/02/03`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `reverse_plan()` --references--> `Regression trace: REV-01/02/03`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Native JSONL to checkpointed publisher, authenticated ingest and durable event storage** — tools_publish_events_module, docs_dashboard_ingest_api, docs_dashboard_postgresql_storage, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Three explicit dashboard evidence sources** — docs_dashboard_observability_console, docs_dashboard_synthetic_sample, docs_dashboard_local_jsonl_import, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Automatic setup promotion requires approved linkage and observable validity/availability** — docs_automatic_backtest_blocked_geometry_303, docs_automatic_backtest_confirmed_setups_zero, docs_open_questions_q_association, docs_open_questions_q_partial_distance_be, docs_sources_canonical_strategy_fa_availability [EXTRACTED 1.00]
- **Confirmed directional references and distances retain unresolved executable quote and stop anchor policies** — docs_sources_canonical_strategy_fa_directional_entry_reference, docs_sources_canonical_strategy_fa_single_sl_distance_40, docs_open_questions_q_touch, docs_open_questions_q_sl_anchor, docs_event_schema_exact_reference_and_sl_anchors [EXTRACTED 1.00]
- **Audit documents open defects without claiming production correction** — docs_first_retest_audit_core_direction_defect, docs_first_retest_audit_break_clock_defect, docs_first_retest_audit_automatic_history_gap, docs_first_retest_audit_regression_expected_failures, docs_first_retest_audit_next_boundary [EXTRACTED 1.00]
- **Qualified break, directional return, consumption and late FVG activation are distinct clocks** — docs_first_retest_audit_directional_return, docs_first_retest_audit_m1_break, docs_first_retest_audit_m1_ask_return, docs_first_retest_audit_m1_availability, docs_first_retest_audit_consumption, docs_first_retest_audit_activation_dependency [EXTRACTED 1.00]
- **History occurrence identity and scoped completeness** — docs_loss_aware_capture_ordered_full_prefix, docs_loss_aware_capture_tick_raw_fields, docs_loss_aware_capture_duplicate_overlap_skips, docs_loss_aware_capture_broker_feed_complete_unknown [EXTRACTED 1.00]
- **Normal/stress paired evidence acceptance** — docs_tester_stress_capture_common_baseline, docs_tester_stress_capture_exact_raw_comparator, docs_tester_stress_capture_positive_recovery, docs_tester_stress_capture_duplicate_occurrence_vs_overlap [EXTRACTED 1.00]

## Communities (39 total, 17 thin omitted)

### Community 0 - "Paper Replay Rules"
Cohesion: 0.09
Nodes (27): Regression trace: BE-01, Regression trace: TOUCH-01, SIZE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules, Bar, fvg(), instant() (+19 more)

### Community 1 - "Capture and Replay Pipeline"
Cohesion: 0.06
Nodes (18): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, CaptureInspectorChecks, event(), valid_capture(), NativeLogContractChecks, compare_captures() (+10 more)

### Community 2 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 3 - "Capture and Replay Pipeline"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Paper Replay Rules"
Cohesion: 0.15
Nodes (12): Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: OB-01, BOS-02, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: Unresolved config and execution, config() (+4 more)

### Community 5 - "Native Capture Integrity"
Cohesion: 0.07
Nodes (22): AutomaticRelationships geometric candidates, Actual historical chart inspection observations, Automatic historical strategy diagnostics 2026-10-11, Historical tester-normal-run01 input, Identical diagnostic journal hashes, AUTO_SETUP_BLOCKED schema, Confirmed/rejected and FVG validity events, Sourced setup and structure events (+14 more)

### Community 6 - "Dashboard Interface"
Cohesion: 0.12
Nodes (36): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+28 more)

### Community 7 - "Dashboard API"
Cohesion: 0.15
Nodes (26): dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE(), dynamic (+18 more)

### Community 8 - "Signal Detection"
Cohesion: 0.14
Nodes (12): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Regression trace: NY-01/02, ConfirmedAmendmentChecks, window(), bar_event(), DetectionChecks, SessionChecks (+4 more)

### Community 9 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (20): First return semantics audit 2026-10-11, Canonical sections 9, 11-12 and 51, Current direct user clarification: Core FIRST RETURN, M1 Ask initial outbound touch is not retest, M1 first Ask downward return lacks exact quote, M1 geometry versus confirmed availability, M1 first Bid downward return has exact quote, M1 qualified intrabar structural break (+12 more)

### Community 10 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 11 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 12 - "Capture and Replay Pipeline"
Cohesion: 0.25
Nodes (8): Regression trace: Reproducibility, diagnose(), main(), main(), digest(), encode(), json_line(), run()

### Community 14 - "Web Application Dependencies"
Cohesion: 0.15
Nodes (12): lightweight-charts, @phosphor-icons/react, react-dom, @types/node, @types/react, @types/react-dom, typescript, engines (+4 more)

### Community 17 - "Web Application Dependencies"
Cohesion: 0.22
Nodes (9): dependencies, @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, next, @phosphor-icons/react, react (+1 more)

### Community 18 - "Web Application Dependencies"
Cohesion: 0.33
Nodes (3): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, metadata

### Community 19 - "Web Application Dependencies"
Cohesion: 0.33
Nodes (4): @neondatabase/serverless, divider, sql, statements

### Community 20 - "Web Application Dependencies"
Cohesion: 0.33
Nodes (6): scripts, build, db:setup, dev, start, typecheck

### Community 21 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 24 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 25 - "Web Application Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, @types/react, @types/react-dom, typescript

### Community 27 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Owner chart numerical example` → `Order Block full reference candle`  [AMBIGUOUS]
  docs/sources/canonical-strategy.fa.md · relation: conceptually_related_to

## Knowledge Gaps
- **89 isolated node(s):** `Status`, `allowJs`, `esModuleInterop`, `incremental`, `isolatedModules` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 188 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Owner chart numerical example` and `Order Block full reference candle`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Engine` connect `Paper Replay Rules` to `Paper Replay Rules`, `Signal Detection`, `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `FirstRetestAudit` connect `Native Capture Integrity` to `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `next` connect `Dashboard API` to `Web Application Dependencies`, `Web Application Dependencies`, `Dashboard Interface`, `Dashboard API`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `ReplayChecks`) actually correct?**
  _`Engine` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ReplayChecks` (e.g. with `Engine` and `Unresolved`) actually correct?**
  _`ReplayChecks` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `allowJs`, `esModuleInterop` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
