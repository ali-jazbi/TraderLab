# Graph Report - TraderLab  (2026-10-21)

## Corpus Check
- 19 files · ~19,138 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 989 nodes · 2190 edges · 60 communities (34 shown, 26 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.92)
- Token cost: unavailable for host-model semantic extraction; AST extraction uses no model tokens

## Community Hubs (Navigation)
- Body80 Detection Evidence
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Web Application Dependencies
- Dashboard Interface
- Native Capture Integrity
- Native Capture Integrity
- Dashboard API
- Core Eligibility Rules
- Native Capture Integrity
- Dashboard Product and Guides
- Capture and Replay Pipeline
- TypeScript Configuration
- Body80 Detection Evidence
- Native Capture Integrity
- Native Capture Integrity
- Strategy Evidence Tools
- Native Capture Integrity
- Native Capture Integrity
- Body80 Detection Evidence
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Capture and Replay Pipeline
- Capture and Replay Pipeline
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity
- Paper Replay Rules
- Native Capture Integrity
- Capture and Replay Pipeline
- Vercel Deployment Settings
- Paper Replay Rules
- Native Normalizer Tests
- PostgreSQL Event Storage
- Chart License Notices
- Native Capture Integrity
- Native Capture Integrity
- Native Capture Integrity

## God Nodes (most connected - your core abstractions)
1. `Engine` - 48 edges
2. `tick()` - 38 edges
3. `config()` - 37 edges
4. `setup_event()` - 34 edges
5. `Bar` - 26 edges
6. `Engine` - 26 edges
7. `ReplayChecks` - 26 edges
8. `Dashboard()` - 25 edges
9. `Chronological JSONL event schema v0.2` - 22 edges
10. `Native chronological BOS first-return diagnostic stream` - 22 edges

## Surprising Connections (you probably didn't know these)
- `inspect()` --references--> `§55 Core eligibility: Body80 and contained pre-C2 BOS`  [EXTRACTED]
  tools/audit_core_eligibility.py → docs/sources/canonical-strategy.fa.md
- `core_eligibility()` --implements--> `§55 Core eligibility: Body80 and contained pre-C2 BOS`  [EXTRACTED]
  traderlab/core_eligibility.py → docs/sources/canonical-strategy.fa.md
- `ConfirmedAmendmentChecks` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `window()` --uses--> `Bar`  [INFERRED]
  tests/test_automatic_strategy.py → traderlab/detection.py
- `BatchChecks` --uses--> `Bar`  [INFERRED]
  tests/test_batch_backtest.py → traderlab/detection.py

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

## Communities (60 total, 26 thin omitted)

### Community 0 - "Body80 Detection Evidence"
Cohesion: 0.06
Nodes (34): bos(), CanonicalRules, inspect(), core_eligibility(), CoreEligibility, Bar, big_candle(), Candidate (+26 more)

### Community 1 - "Native Capture Integrity"
Cohesion: 0.05
Nodes (15): First Demo Capture, MetaEditor build 6244 compilation, StrategyChecks runtime UNVERIFIED, TraderLab native checks failures=0, Historical Tester Capture, tester_no_first_tick, Loss Aware Capture, duplicate_overlap_skips (+7 more)

### Community 2 - "Native Capture Integrity"
Cohesion: 0.14
Nodes (8): ConfirmedAmendmentChecks, BatchChecks, config(), Engine, prime_return(), ReplayChecks, setup_event(), tick()

### Community 3 - "Capture and Replay Pipeline"
Cohesion: 0.09
Nodes (12): BrokerCapabilityChecks, RequestGuardChecks, BrokerRequestGateway, capability_issues(), diagnose_server_offset(), litefinance_expected_offset_seconds(), price_grid_compatible(), RequestRecord (+4 more)

### Community 4 - "Web Application Dependencies"
Cohesion: 0.05
Nodes (38): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, @neondatabase/serverless, @phosphor-icons/react, react-dom, @types/node, @types/react, @types/react-dom (+30 more)

### Community 5 - "Dashboard Interface"
Cohesion: 0.12
Nodes (37): lightweight-charts, react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile() (+29 more)

### Community 6 - "Native Capture Integrity"
Cohesion: 0.10
Nodes (8): window(), at(), OwnerOct12Checks, bar_event(), DetectionChecks, SessionChecks, AutomaticRelationships, Detector

### Community 7 - "Native Capture Integrity"
Cohesion: 0.09
Nodes (28): First-return audit and 2026-10-12 correction, Reviewed canonical authority and unavailable original PDFs, Full genuine diagnostic replay without setups or performance, M1 BUY qualification and actual structural break, M1 first Ask downward return: missed and consumed, M1 first Bid downward return: exact and spent, M1 FVG formation, availability and later full invalidity, M5 SELL mirrored first returns both miss reference (+20 more)

### Community 8 - "Dashboard API"
Cohesion: 0.12
Nodes (28): next, dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE() (+20 more)

### Community 9 - "Core Eligibility Rules"
Cohesion: 0.09
Nodes (15): 2026-10-21 Core restriction; fixed native comparisons and locked Demo, Core setup/package eligibility events independent of detection and remaining guards, C2 body >=80 strategy pips =8.0 price units on every frame, Only BOS candle precedes C2; qualification follows existing before-Break rule, §55 Core eligibility: Body80 and contained pre-C2 BOS, Detection history remains separate from Core eligibility, M15 owner example approximate; no exact date/feed/OHLC or historical result, Owner M15 Gold chart: hand-marked BOS near4148 and body roughly4146–4154 (+7 more)

### Community 10 - "Native Capture Integrity"
Cohesion: 0.11
Nodes (10): ParityScopeChecks, comparator_fixture(), NativeRetestChecks, closed_signature(), compare_closed(), main(), compare_capture(), compare_rows() (+2 more)

### Community 12 - "Dashboard Product and Guides"
Cohesion: 0.11
Nodes (24): Short-run browser dataset limits, Persian RTL event inspection, chart overlays and replay UI, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/ (+16 more)

### Community 13 - "Capture and Replay Pipeline"
Cohesion: 0.14
Nodes (12): First LiteFinance Demo capture review — 2026-10-07, MetaEditor build 6244 compilation evidence, TraderLab-demo-20261007-run01.jsonl, compare_captures(), main(), tester_metadata(), capture_integer(), decimal() (+4 more)

### Community 14 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 15 - "Body80 Detection Evidence"
Cohesion: 0.18
Nodes (3): ExperimentalChecks, utc(), ExperimentalEngine

### Community 16 - "Native Capture Integrity"
Cohesion: 0.20
Nodes (4): CandidateChecks, NativeIntegrationContracts, core_candidates(), write_candidates()

### Community 17 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (12): User-reported baseline60654a2 StrategyChecks/DemoGatewayChecks failures0/lockedtrue, Final batch artifacts and preserved input/raw hashes, Core Demo readiness: prepared integration; automatic setups and dispatch BLOCKED, Chronological native controller: original qualification/geometry/IDs/first returns, Actual legacy Oct7 native/Python closed-bar IDs/geometry/fill observations match, Actual incomplete live-run05 prefix67/67 break-return occurrences match, M1 BUY BOS4141.82/planned4142.32: exact Bid return consumed before confirmed availability, M5 SELL BOS4140.24/planned4139.74: missed exact Bid return stays consumed (+4 more)

### Community 18 - "Strategy Evidence Tools"
Cohesion: 0.26
Nodes (5): OperatorPackagesChecks, first_return_issue(), Package, read_packages(), resolve()

### Community 19 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (11): Owner§51 explicit symbol alias/wick BOS level versus planned entry, Annotated BOS_FIRST_TOUCH directional / source-only unarmed, Simulated PAPER_ENTRY/EXIT/BE contracts and no-trade null performance, BOS_FVG_GEOMETRY_CONFIRMED: owner containment is not package approval, BOS_INTRABAR_BREAK authoritative observed tick occurrence, Native loss-aware and tester capture diagnostics, CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED keeps FVG ownC3/C1OB, Chronological JSONL event schema v0.2 (+3 more)

### Community 20 - "Native Capture Integrity"
Cohesion: 0.12
Nodes (7): FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION uses selected signal lane, CORE geometry/candidate/blockedreturn/consumption events preserve provenance/evidence, §§39–45 exact original planned Core reverse retest, Rule/code/executable regressions and fixture-only contract/cost assumptions, 2026-10-12 first-return implementation amendment, Owner-amended BOS selection/size/targets/SL/dual BE references, TraderLab strategy specification v0.2; canonical owner sections1–52

### Community 21 - "Body80 Detection Evidence"
Cohesion: 0.17
Nodes (6): EligibilityReportChecks, summarize(), compare(), entry_identity(), report(), structural_proof()

### Community 22 - "Capture and Replay Pipeline"
Cohesion: 0.24
Nodes (7): diagnose(), main(), main(), digest(), encode(), json_line(), run()

### Community 23 - "Native Capture Integrity"
Cohesion: 0.14
Nodes (4): LiteFinance Broker and Execution Profile, DEMO gateway connected through blocked Core controller; DISABLED and locked, Separate SQLite safety reference; injected test transport only, no MT5 connector, NEWS_FORCE_CLOSE/NEWS_CLOSE_DEADLINE_MISSED observed deadlines without backdating

### Community 25 - "Native Capture Integrity"
Cohesion: 0.15
Nodes (3): TraderLab working rules, 2026-10-11 owner-resolved rules must not be re-asked, Explicit unresolved configuration register

### Community 26 - "Capture and Replay Pipeline"
Cohesion: 0.22
Nodes (5): main(), batch(), Equity, reports_results(), results()

### Community 27 - "Native Capture Integrity"
Cohesion: 0.17
Nodes (6): AutomaticRelationships geometric candidates, Actual historical chart inspection observations, Historical tester-normal-run01 input, Identical diagnostic journal hashes, §4 Big Candle equals Momentum Candle, §§5–7 three-candle wick-to-wick FVG

### Community 28 - "Native Capture Integrity"
Cohesion: 0.18
Nodes (6): TLBarDetector.Process, TLBosLevel, TLCoreEntryReference, TLOrderBlockBounds, §51.3 BOS±5 exact directional entry reference, Owner chart numerical example

### Community 29 - "Native Capture Integrity"
Cohesion: 0.18
Nodes (6): TLCorePlan, §§25–32 trend/news and Tehran NY context, §52 direct owner-relayed final answers after906f9db, §§17–20 split0.02 volume and fixed60/100 targets, §§51.3,52.3 single Core/Reverse SL40 from actual fill, NET daily USD100 latch/two setup stops/sourced Sydney-NY/news/soft NY context

### Community 31 - "Capture and Replay Pipeline"
Cohesion: 0.39
Nodes (3): CaptureInspectorChecks, event(), valid_capture()

### Community 36 - "Paper Replay Rules"
Cohesion: 0.24
Nodes (3): FirstReturn, HistoricalRetests, History

### Community 39 - "Vercel Deployment Settings"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 40 - "Paper Replay Rules"
Cohesion: 0.50
Nodes (4): Automatic historical strategy diagnostics 2026-10-11, Native source relationships documented without MQL5 AST, Preserved Persian canonical strategy, sections1–52, TraderLab overview

### Community 42 - "PostgreSQL Event Storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 44 - "Chart License Notices"
Cohesion: 0.50
Nodes (4): Apache License 2.0, Lightweight Charts Apache License 2.0, Lightweight Charts attribution notice, TradingView Lightweight Charts v5.2.1

## Ambiguous Edges - Review These
- `Historical planned-versus-filled choice sentence superseded by owner§52 actual-fillSL` → `Owner§52 resolved SL/dual BE/NET/calendar/news and prepared locked integration`  [AMBIGUOUS]
  docs/EVENT_SCHEMA.md · relation: conceptually_related_to

## Knowledge Gaps
- **123 isolated node(s):** `Status`, `Final batch artifacts and preserved input/raw hashes`, `Chronological native controller: original qualification/geometry/IDs/first returns`, `Actual legacy Oct7 native/Python closed-bar IDs/geometry/fill observations match`, `Actual incomplete live-run05 prefix67/67 break-return occurrences match` (+118 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 324 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Historical planned-versus-filled choice sentence superseded by owner§52 actual-fillSL` and `Owner§52 resolved SL/dual BE/NET/calendar/news and prepared locked integration`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Engine` connect `Body80 Detection Evidence` to `Native Capture Integrity`, `Native Capture Integrity`, `Native Capture Integrity`, `Native Capture Integrity`, `Native Capture Integrity`, `Body80 Detection Evidence`, `Capture and Replay Pipeline`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `CoreEligibilityChecks` connect `Core Eligibility Rules` to `Body80 Detection Evidence`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `Bar` connect `Body80 Detection Evidence` to `Native Capture Integrity`, `Body80 Detection Evidence`, `Native Capture Integrity`, `Native Capture Integrity`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Engine` (e.g. with `ConfirmedAmendmentChecks` and `FirstRetestAudit`) actually correct?**
  _`Engine` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Status`, `Final batch artifacts and preserved input/raw hashes`, `Chronological native controller: original qualification/geometry/IDs/first returns` to the rest of the system?**
  _123 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Body80 Detection Evidence` be split into smaller, more focused modules?**
  _Cohesion score 0.058428680396643784 - nodes in this community are weakly interconnected._

## Scoped owner55 update — 2026-10-21

This is a partial update of the existing graph, not a full corpus refresh. Earlier
legacy sources and prior graph assertions remain; unrelated stale sources, archives,
PDFs, reports, work directories and Native historical outcomes were not re-extracted.

Python AST re-extracted from these latest source files:
- `traderlab/core_eligibility.py`
- `traderlab/detection.py`
- `traderlab/automatic.py`
- `traderlab/core_packages.py`
- `traderlab/experimental.py`
- `tests/test_core_eligibility.py`
- `tests/test_core_packages.py`
- `tests/test_experimental_auto.py`
- `tests/test_core_eligibility_reports.py`
- `tests/test_owner_oct12.py`
- `tools/audit_core_eligibility.py`
- `tools/report_body80_study.py`

Semantic review covers only canonical §55 (including its prerequisite references),
the CORE-ELIGIBILITY-01 spec row, AGENTS owner55 amendment, and EVENT_SCHEMA's new
owner55 subsection. Existing semantic nodes from those files are retained; their
whole-file semantic hashes are deliberately cleared to avoid asserting a complete
refresh. The new owner M15 image was visually reviewed as an educational screenshot;
no exact historic date/feed/OHLC, entry or future outcome is established.

Native CoreEligibility.mqh and the controller's Eligibility helper/call sites are
manually source-reviewed evidence, explicitly not language AST extraction or proof
of runtime/compilation results. No strategy or execution source was changed by this
graph update. MQL compile/history results belong in the task's independent report.

Token accounting: semantic extraction performed by the delegated host model; exact
input/output token usage and monetary cost are unavailable. Generated numeric zero
fields are structural-pass placeholders, not a claim of zero model usage.

Graph health warning: the merged graph has six self-loop call edges (three
retained legacy edges and three from the updated experimental engine AST). No
missing or dangling endpoints were found in the merged graph. These extractor
artifacts are retained as emitted; graph calls are navigation evidence and need
source verification. Raw scoped Python extraction diagnostics are preserved in
`health.json` separately from post-merge diagnostics.

Raw scoped Python AST diagnostics reported 56 endpoints outside that scoped
fragment and four same-endpoint edge collisions under the retained undirected
graph model. All scoped endpoints resolve after merging with retained corpus
nodes, but the four raw edge variants collapse in graph.json; consult source/AST
for those relation details. This is a graph limitation, not a strategy test result.

Boundary follow-up: re-extracted latest `tests/test_core_eligibility.py` AST after
the 219-vector parity test update. Manually reviewed Native CoreEligibility body
subtraction normalization to eight decimal places, matching existing OHLC evidence
precision; this is a boundary correction, not a tolerance admitting 7.99999999.
The helper semantic manifest hash now matches that corrected source. This graph
does not assert the new binary compile/runtime result or historic-run outcomes.
