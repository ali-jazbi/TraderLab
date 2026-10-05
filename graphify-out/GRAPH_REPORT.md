# Graph Report - TraderLab  (2026-10-05)

## Corpus Check
- Corpus is ~24,881 words - fits in a single context window. You may not need a graph.

## Summary
- 414 nodes · 1046 edges · 24 communities (17 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.93)
- Token cost: unavailable (host runtime exposes no measured semantic usage)

## Community Hubs (Navigation)
- Strategy rules and helpers
- Canonical evidence and boundaries
- Interactive dashboard and replay
- Paper regression checks
- Private APIs and authentication
- Cloud observability pipeline
- Capture and publishing tools
- Detection and session checks
- TypeScript configuration
- Package metadata
- Application dependencies
- Self-hosted fonts and layout
- Database schema installation
- Application commands
- Vercel deployment configuration
- Operator guide and framework
- Transactional event storage
- Development dependencies
- Strategy scope limits
- Unresolved execution details

## God Nodes (most connected - your core abstractions)
1. `Engine` - 47 edges
2. `tests/test_strategy.py: explicit rule-linked Python regressions` - 33 edges
3. `Dashboard()` - 25 edges
4. `ReplayChecks` - 23 edges
5. `config()` - 22 edges
6. `traderlab/replay.py: documented chronological paper state machine` - 21 edges
7. `tick()` - 19 edges
8. `number()` - 19 edges
9. `TraderLab observability console` - 18 edges
10. `compilerOptions` - 16 edges

## Surprising Connections (you probably didn't know these)
- `news_block()` --references--> `Regression trace: NEWS-01`  [EXTRACTED]
  traderlab/session.py → docs/STRATEGY_SPEC.md
- `reverse_plan()` --references--> `Regression trace: REV-01/02/03`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `ob_broken()` --references--> `Regression trace: REV-01/02/03`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `DailyGuard` --references--> `Regression trace: DAY-01/02`  [EXTRACTED]
  traderlab/strategy.py → docs/STRATEGY_SPEC.md
- `tick()` --references--> `Regression trace: Unresolved config and execution`  [EXTRACTED]
  tests/test_strategy.py → docs/STRATEGY_SPEC.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Native JSONL to checkpointed publisher, authenticated ingest and durable event storage** — mt5_traderlab_ea, tools_publish_events_module, docs_dashboard_ingest_api, docs_dashboard_postgresql_storage, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Three explicit dashboard evidence sources** — docs_dashboard_observability_console, docs_dashboard_synthetic_sample, docs_dashboard_local_jsonl_import, docs_dashboard_protected_cloud_runs [EXTRACTED 1.00]
- **Documented MQL5 helper coverage with unverified compilation and unsupported AST extraction** — docs_native_code_map_documented_native_relationships, mt5_traderlab_ea, mt5_include_traderlab_detection_tlbardetector_process, mt5_include_traderlab_eventlog_tleventlog, mt5_include_traderlab_rules_tlcoreplan, mt5_include_traderlab_rules_tlbreakeven, mt5_include_traderlab_rules_tlobroken, mt5_include_traderlab_rules_tldailyguard, mt5_strategychecks_script [EXTRACTED 1.00]
- **Explicit unresolved policy register and blocked dependent behavior** — docs_open_questions_unresolved_decisions, docs_open_questions_zone_and_structure_decisions, docs_open_questions_entry_and_position_decisions, docs_open_questions_execution_and_lifecycle_decisions, docs_open_questions_daily_and_news_decisions, docs_open_questions_ny_decisions [EXTRACTED 1.00]
- **Canonical rule IDs and numbered source sections** — docs_strategy_spec_strategy_specification, docs_sources_canonical_strategy_fa_canonical_strategy, docs_strategy_spec_unit_01, docs_strategy_spec_tf_01, docs_strategy_spec_big_01, docs_strategy_spec_big_02, docs_strategy_spec_fvg_01, docs_strategy_spec_fvg_02, docs_strategy_spec_fvg_03, docs_strategy_spec_ob_01, docs_strategy_spec_bos_01, docs_strategy_spec_bos_02, docs_strategy_spec_touch_01, docs_strategy_spec_select_01, docs_strategy_spec_select_02, docs_strategy_spec_select_03, docs_strategy_spec_size_01, docs_strategy_spec_tp_01, docs_strategy_spec_sl_01, docs_strategy_spec_sl_02, docs_strategy_spec_be_01, docs_strategy_spec_day_01, docs_strategy_spec_day_02, docs_strategy_spec_trend_01, docs_strategy_spec_news_01, docs_strategy_spec_ny_01, docs_strategy_spec_ny_02, docs_strategy_spec_rev_01, docs_strategy_spec_rev_02, docs_strategy_spec_rev_03, docs_strategy_spec_rev_04, docs_strategy_spec_scope_01, docs_strategy_spec_claim_01 [EXTRACTED 1.00]

## Communities (24 total, 7 thin omitted)

### Community 0 - "Strategy rules and helpers"
Cohesion: 0.09
Nodes (23): Regression trace: BE-01, Regression trace: TOUCH-01, SIZE-01, Regression trace: UNIT-01, SELECT-01/02, SL-01, TP-01, bos(), CanonicalRules, instant(), Position, Setup (+15 more)

### Community 1 - "Canonical evidence and boundaries"
Cohesion: 0.08
Nodes (54): TraderLab working rules, Persian RTL event inspection, chart overlays and replay UI, Public canonical synthetic paper sample, Q-RESET, Q-NEWS, Q-REV-COUNT, Q-BE-STOP, Q-PROFIT-BASIS, Q-SINGLE-SL, Q-DISTANCE, Q-BE, Q-TOUCH, Q-REV-SL, Q-REV-DUAL, Q-NY-CUTOFF, Q-NY-DOUBLE, Unresolved strategy decisions, Q-OB-BOUNDS, Q-BOS-BOUNDS, Q-H1, Q-PARTIAL, Q-IFVG (+46 more)

### Community 2 - "Interactive dashboard and replay"
Cohesion: 0.12
Nodes (37): react, Page(), Analytics(), clock(), Dashboard(), changeSource(), importFile(), login() (+29 more)

### Community 3 - "Paper regression checks"
Cohesion: 0.18
Nodes (11): Regression trace: DAY-01/02, Regression trace: FVG-03, Regression trace: NEWS-01, Regression trace: REV-01/02/03, Regression trace: REV-04, Regression trace: Unresolved config and execution, config(), ReplayChecks (+3 more)

### Community 4 - "Private APIs and authentication"
Cohesion: 0.16
Nodes (25): dynamic, GET(), dynamic, POST(), dynamic, GET(), DELETE(), dynamic (+17 more)

### Community 5 - "Cloud observability pipeline"
Cohesion: 0.11
Nodes (26): Short-run browser dataset limits, POST /api/ingest, TradingView Lightweight Charts attribution and API, Browser-local JSONL import, Neon serverless driver, Neon PostgreSQL provisioning and DATABASE_URL, Next.js16.3.8 / React19.3.0 TypeScript application in web/, Next.js installation and application routing (+18 more)

### Community 6 - "Capture and publishing tools"
Cohesion: 0.11
Nodes (10): Chronological JSONL event schema v0.1, Regression trace: Reproducibility, tools/normalize_mt5_log.py: native bar/tick normalization, main(), publish(), main(), digest(), encode() (+2 more)

### Community 7 - "Detection and session checks"
Cohesion: 0.18
Nodes (12): Regression trace: BIG-01/02, FVG-01/02, Regression trace: BOS-01, Regression trace: NY-01/02, bar_event(), DetectionChecks, SessionChecks, Bar, big_candle() (+4 more)

### Community 8 - "TypeScript configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 9 - "Package metadata"
Cohesion: 0.15
Nodes (12): lightweight-charts, @phosphor-icons/react, react-dom, @types/node, @types/react, @types/react-dom, typescript, engines (+4 more)

### Community 10 - "Application dependencies"
Cohesion: 0.22
Nodes (9): dependencies, @fontsource/ibm-plex-mono, @fontsource/vazirmatn, lightweight-charts, @neondatabase/serverless, next, @phosphor-icons/react, react (+1 more)

### Community 11 - "Self-hosted fonts and layout"
Cohesion: 0.33
Nodes (3): @fontsource/ibm-plex-mono, @fontsource/vazirmatn, metadata

### Community 12 - "Database schema installation"
Cohesion: 0.33
Nodes (4): @neondatabase/serverless, divider, sql, statements

### Community 13 - "Application commands"
Cohesion: 0.33
Nodes (6): scripts, build, db:setup, dev, start, typecheck

### Community 14 - "Vercel deployment configuration"
Cohesion: 0.33
Nodes (5): maxDuration, framework, functions, app/api/**/route.ts, $schema

### Community 16 - "Transactional event storage"
Cohesion: 0.70
Nodes (4): traderlab_events, traderlab_ingest(), traderlab_login_limits, traderlab_runs

### Community 17 - "Development dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, @types/react, @types/react-dom, typescript

## Ambiguous Edges - Review These
- `traderlab/replay.py: documented chronological paper state machine` → `mt5/TraderLab.mq5: native diagnostic capture EA`  [AMBIGUOUS]
  docs/NATIVE_CODE_MAP.md · relation: conceptually_related_to

## Knowledge Gaps
- **71 isolated node(s):** `dynamic`, `dynamic`, `dynamic`, `dynamic`, `dynamic` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 111 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `traderlab/replay.py: documented chronological paper state machine` and `mt5/TraderLab.mq5: native diagnostic capture EA`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `traderlab/replay.py: documented chronological paper state machine` connect `Canonical evidence and boundaries` to `Strategy rules and helpers`, `Cloud observability pipeline`, `Capture and publishing tools`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `Engine` connect `Paper regression checks` to `Strategy rules and helpers`, `Capture and publishing tools`, `Detection and session checks`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Engine` (e.g. with `ReplayChecks` and `Bar`) actually correct?**
  _`Engine` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ReplayChecks` (e.g. with `Engine` and `Unresolved`) actually correct?**
  _`ReplayChecks` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dynamic`, `dynamic`, `dynamic` to the rest of the system?**
  _71 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Strategy rules and helpers` be split into smaller, more focused modules?**
  _Cohesion score 0.09463869463869463 - nodes in this community are weakly interconnected._
## Coverage limits

MQL5 files are unsupported by this graphify AST classifier. Native nodes represent documented source relationships, not verified AST coverage or compilation. Original PDFs/RAR/images are absent. Native trading and execution parity remain pending.

Normalized 89 byte-equivalent edge duplicates from cached traceability links before graph construction. Relation/context variants are retained in extraction and counted below. Cloud ingestion and actual MT5-to-dashboard validation remain unverified until configured.

Graph integrity diagnostic:

```text
[graphify] MultiDiGraph edge-collapse diagnostic
input: <in-memory>
input_stage: provided JSON (normal graph.json is post-build)
effective_directed: <direct-call>
nodes: 392
unverified_code_nodes: 0
raw_edges: 1062
valid_candidate_edges: 1023
missing_endpoint_edges: 0
dangling_endpoint_edges: 36
external_reference_edges: 3
self_loop_edges: 2
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 1009
directed_same_endpoint_collapsed_edges: 14
undirected_unique_endpoint_pairs: 1009
undirected_same_endpoint_collapsed_edges: 14
same_endpoint_group_count: 13
relation_variant_groups: 11
source_file_variant_groups: 0
source_location_variant_groups: 1
context_variant_groups: 1
post_build_graph_type: Graph
post_build_edges: 1046
producer_suppression_sites: 12
producer_suppression_examples:
  - L1676 seen_ids arity=unknown
  - L2209 seen_ids arity=unknown
  - L2211 seen_doc_refs arity=unknown
  - L2628 seen_ids arity=unknown
  - L2775 seen_ids arity=unknown
  - L3501 seen_keys arity=unknown
  - L3670 seen_keys arity=unknown
  - L5777 seen_ids arity=unknown
examples:
  - web_app_layout -> ref_fontsource_vazirmatn edges=3 relations=['imports_from'] locations=['L2', 'L3', 'L4'] contexts=['import']
  - traderlab_strategy_core_plan -> traderlab_strategy_plan edges=2 relations=['calls', 'references'] locations=['L103', 'L114'] contexts=['call', 'return_type']
  - traderlab_strategy_reverse_plan -> traderlab_strategy_plan edges=2 relations=['calls', 'references'] locations=['L118', 'L124'] contexts=['call', 'return_type']
  - traderlab_strategy_breakeven -> traderlab_strategy_py_decimal edges=2 relations=['references'] locations=['L129'] contexts=['parameter_type', 'return_type']
  - web_components_dashboard_dashboard -> web_components_dashboard_dashboard_poll edges=2 relations=['calls', 'contains'] locations=['L118', 'L92'] contexts=['', 'call']
note: normal graph.json is post-build; raw producer loss must be measured earlier.
```

Coverage note: public vendor LICENSE/NOTICE documents are excluded from the architecture corpus; they are retained in web/public for distribution. Native .mqh relationships are documented separately in docs/NATIVE_CODE_MAP.md.
