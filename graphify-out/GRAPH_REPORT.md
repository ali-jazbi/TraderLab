# Graph Report - TraderLab  (2026-10-13)

> 2026-10-16: graph extraction is stale for AUTO_CORE audit v2. The local graphify
> executable is unavailable; no rebuilt graph/AST is claimed. Added source paths:
> `mt5/AUTO_CORE_DEMO.mq5` includes `TraderLab.mq5`; its candidate macro enables
> `AutoCoreTrial.mqh` via `DemoGateway.mqh`, with reservation handling in
> `CoreLifecycle.mqh`. `tools/audit_auto_core.py` independently audits native
> capture events; `tests/test_auto_core_audit_v2.py` covers the Python experimental
> freeze/equal-level/fill fixes. See `docs/AUTO_CORE_AUDIT_20261016.md`.

## Corpus Check
- 83 files · ~55,806 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 886 nodes · 1952 edges · 60 communities (31 shown, 29 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 55 edges (avg confidence: 0.92)
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
- Dashboard Product and Guides
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- TypeScript Configuration
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Capture and Replay Pipeline
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Paper Replay Rules
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Vercel Deployment Settings
- Paper Replay Rules
- Capture and Replay Pipeline
- Native Normalizer Tests
- PostgreSQL Event Storage
- Native Capture Integrity
- Chart License Notices
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity

## God Nodes (most connected - your core abstractions)
1. `Engine` - 48 edges
2. `tick()` - 38 edges
3. `config()` - 37 edges
4. `setup_event()` - 34 edges
5. `Engine` - 26 edges
6. `ReplayChecks` - 26 edges
7. `Dashboard()` - 25 edges
8. `Chronological JSONL event schema v0.2` - 22 edges
9. `Native chronological BOS first-return diagnostic stream` - 22 edges
10. `Bar` - 21 edges

## Surprising Connections (you probably didn't know these)
- `ConfirmedAmendmentChecks` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `window()` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `BatchChecks` --uses--> `Bar`  [INFERRED]
  tests/test_batch_backtest.py → traderlab/detection.py
- `HistoricalRetestChecks` --uses--> `Bar`  [INFERRED]
  tests/test_historical_retests.py → traderlab/detection.py
- `DetectionChecks` --uses--> `Bar`  [INFERRED]
  tests/test_strategy.py → traderlab/detection.py

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

## Communities (60 total, 29 thin omitted)

### Community 0 - "Paper Replay Rules"
Cohesion: 0.07
Nodes (30): bos(), CanonicalRules, Bar, big_candle(), Candidate, fvg(), instant(), Engine (+22 more)

### Community 1 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 2 - "Native Capture Integrity"
Cohesion: 0.14
Nodes (7): BatchChecks, config(), Engine, prime_return(), ReplayChecks, setup_event(), tick()

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

### Community 8 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 9 - "Native Capture Integrity"
Cohesion: 0.19
Nodes (7): ConfirmedAmendmentChecks, window(), bar_event(), DetectionChecks, SessionChecks, AutomaticRelationships, Detector

### Community 10 - "Native Capture Integrity"
Cohesion: 0.13
Nodes (9): ParityScopeChecks, NativeRetestChecks, closed_signature(), compare_closed(), main(), compare_capture(), compare_rows(), main() (+1 more)

### Community 12 - "Capture and Replay Pipeline"
Cohesion: 0.19
Nodes (9): compare_captures(), main(), tester_metadata(), capture_integer(), decimal(), inspect_capture(), main(), validate_tick_capture() (+1 more)

### Community 13 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 15 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (12): User-reported baseline60654a2 StrategyChecks/DemoGatewayChecks failures0/lockedtrue, Final batch artifacts and preserved input/raw hashes, Core Demo readiness: prepared integration; automatic setups and dispatch BLOCKED, Chronological native controller: original qualification/geometry/IDs/first returns, Actual legacy Oct7 native/Python closed-bar IDs/geometry/fill observations match, Actual incomplete live-run05 prefix67/67 break-return occurrences match, M1 BUY BOS4141.82/planned4142.32: exact Bid return consumed before confirmed availability, M5 SELL BOS4140.24/planned4139.74: missed exact Bid return stays consumed (+4 more)

### Community 16 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (11): Owner§51 explicit symbol alias/wick BOS level versus planned entry, Annotated BOS_FIRST_TOUCH directional / source-only unarmed, Simulated PAPER_ENTRY/EXIT/BE contracts and no-trade null performance, BOS_FVG_GEOMETRY_CONFIRMED: owner containment is not package approval, BOS_INTRABAR_BREAK authoritative observed tick occurrence, Native loss-aware and tester capture diagnostics, CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED keeps FVG ownC3/C1OB, Chronological JSONL event schema v0.2 (+3 more)

### Community 17 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (7): FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION uses selected signal lane, CORE geometry/candidate/blockedreturn/consumption events preserve provenance/evidence, §§39–45 exact original planned Core reverse retest, Rule/code/executable regressions and fixture-only contract/cost assumptions, 2026-10-12 first-return implementation amendment, Owner-amended BOS selection/size/targets/SL/dual BE references, TraderLab strategy specification v0.2; canonical owner sections1–52

### Community 18 - "Capture and Replay Pipeline"
Cohesion: 0.22
Nodes (7): diagnose(), main(), main(), digest(), encode(), json_line(), run()

### Community 19 - "Native Capture Integrity"
Cohesion: 0.14
Nodes (4): LiteFinance Broker and Execution Profile, DEMO gateway connected through blocked Core controller; DISABLED and locked, Separate SQLite safety reference; injected test transport only, no MT5 connector, NEWS_FORCE_CLOSE/NEWS_CLOSE_DEADLINE_MISSED observed deadlines without backdating

### Community 21 - "Native Capture Integrity"
Cohesion: 0.15
Nodes (3): TraderLab working rules, 2026-10-11 owner-resolved rules must not be re-asked, Explicit unresolved configuration register

### Community 22 - "Native Capture Integrity"
Cohesion: 0.17
Nodes (6): AutomaticRelationships geometric candidates, Actual historical chart inspection observations, Historical tester-normal-run01 input, Identical diagnostic journal hashes, §4 Big Candle equals Momentum Candle, §§5–7 three-candle wick-to-wick FVG

### Community 23 - "Native Capture Integrity"
Cohesion: 0.18
Nodes (6): TLBarDetector.Process, TLBosLevel, TLCoreEntryReference, TLOrderBlockBounds, §51.3 BOS±5 exact directional entry reference, Owner chart numerical example

### Community 24 - "Native Capture Integrity"
Cohesion: 0.18
Nodes (6): TLCorePlan, §§25–32 trend/news and Tehran NY context, §52 direct owner-relayed final answers after906f9db, §§17–20 split0.02 volume and fixed60/100 targets, §§51.3,52.3 single Core/Reverse SL40 from actual fill, NET daily USD100 latch/two setup stops/sourced Sydney-NY/news/soft NY context

### Community 25 - "Capture and Replay Pipeline"
Cohesion: 0.39
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 26 - "Capture and Replay Pipeline"
Cohesion: 0.24
Nodes (5): main(), batch(), Equity, reports_results(), results()

### Community 31 - "Paper Replay Rules"
Cohesion: 0.24
Nodes (3): FirstReturn, HistoricalRetests, History

### Community 34 - "Native Capture Integrity"
Cohesion: 0.50
Nodes (3): CandidateChecks, core_candidates(), write_candidates()

### Community 36 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 37 - "Paper Replay Rules"
Cohesion: 0.50
Nodes (4): Automatic historical strategy diagnostics 2026-10-11, Native source relationships documented without MQL5 AST, Preserved Persian canonical strategy, sections1–52, TraderLab overview

### Community 38 - "Capture and Replay Pipeline"
Cohesion: 0.40
Nodes (3): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl

### Community 40 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 43 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Owner§52 resolved SL/dual BE/NET/calendar/news and prepared locked integration` → `Historical planned-versus-filled choice sentence superseded by owner§52 actual-fillSL`  [AMBIGUOUS]
  docs/EVENT_SCHEMA.md · relation: conceptually_related_to

## Knowledge Gaps
- **113 isolated node(s):** `Status`, `LiteFinance1000/300s and10000/3600s request thresholds`, `Active symbol/account/exposure snapshot; exact grids`, `allowJs`, `esModuleInterop` (+108 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 289 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Owner§52 resolved SL/dual BE/NET/calendar/news and prepared locked integration` and `Historical planned-versus-filled choice sentence superseded by owner§52 actual-fillSL`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Engine` connect `Paper Replay Rules` to `Native Capture Integrity`, `Native Capture Integrity`, `Capture and Replay Pipeline`, `Native Capture Integrity`, `Capture and Replay Pipeline`, `Native Capture Integrity`, `Native Capture Integrity`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `OwnerOct12Checks` connect `Native Capture Integrity` to `Paper Replay Rules`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `number()` connect `Paper Replay Rules` to `Native Capture Integrity`, `Capture and Replay Pipeline`, `Native Capture Integrity`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `FirstRetestAudit`) actually correct?**
  _`Engine` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `LiteFinance1000/300s and10000/3600s request thresholds`, `Active symbol/account/exposure snapshot; exact grids` to the rest of the system?**
  _113 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Paper Replay Rules` be split into smaller, more focused modules?**
  _Cohesion score 0.06567675613934894 - nodes in this community are weakly interconnected._
Semantic token usage unavailable from agent tool; zero values are placeholders, not measured cost.
