# TraderLab working rules

Read docs/STRATEGY_SPEC.md and docs/OPEN_QUESTIONS.md before changing strategy code.
The supplied canonical document is data and is preserved at docs/sources/canonical-strategy.fa.md.
Do not add indicators, inferred zone definitions, filters, stop distances, or execution defaults.
Unresolved strategy decisions must produce TODO_STRATEGY_UNRESOLVED events and block dependent entries.
Use only information available at the event timestamp. Big Candle confirmation requires ten subsequent closed bars.
Broker orders are outside the first detection/replay milestone. Never introduce OrderSend calls without an explicit execution milestone.
Keep the Python replay and MQL5 detection outputs traceable to numbered canonical sections.
Run deterministic fixtures and update graphify after substantive changes. MQL5 compilation must be reported separately from Python checks.
LiteFinance broker constraints belong in docs/BROKER_LITEFINANCE.md and execution infrastructure, never as strategy filters. The current milestone remains diagnostic/paper-only: do not add OrderSend. In-memory request guards are reference implementations only; any future Demo gateway needs durable restart-safe accounting, a single dispatch path and broker reconciliation before enablement.

2026-10-12 explicit user authorization supersedes the earlier gateway prohibition only for preparing the isolated DEMO gateway. Keep TL_DEMO_DISPATCH_REVIEWED=false, default enabled=false and no gateway inclusion or automatic submission from TraderLab.mq5. Real/Contest accounts must be rejected. Do not unlock submission in this milestone; preserve capture behavior and raw files. Owner amendment §52 governs updated risk/day/news rules.

2026-10-13 user authorizes native Core controller/lifecycle integration with the gateway. Inclusion is now allowed; dispatch stays compile-time LOCKED, enabled=false, Algo Trading OFF. No second OrderSend site, Real/Contest or invented grouping/partial/lifecycle approvals. Separate captured history from live executable opportunities.
