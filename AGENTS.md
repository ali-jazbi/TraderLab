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

2026-10-14 user changes the goal to autonomous Core discovery. Explicit EXPERIMENTAL grouping is authorized ONLY for historical backtests. MQL_TESTER may use the existing single dispatch site for simulated orders and local disposable tester journals. Live/Demo automatic submission, Real and Reverse remain forbidden; no operator confirmation is part of the automatic target. Experimental calendars/policies must not leak into live execution.

2026-10-16 user explicitly authorizes completing independent AUTO_CORE_DEMO engineering,
native synthetic integration/fault tests, durable recovery and forward calendar refresh,
with commit/push on main. Keep Demo compile/init locks closed pending real-history
and critical-control validation; do not infer missing USD risk/cost budgets or resolve
PARTIAL/day-overlap by inventing rules. Candidate journals are append-only and scoped;
never delete them on restart, including Tester reattachment. OfflineBroker.mqh is a
compile-time test transport and MUST remain outside every production EA include tree.
Only the isolated offline-native runner may launch that harness. Report its synthetic
transport calls separately from Tester orders and historical results.

2026-10-16 subsequent explicit owner authorization: compare STRICT_ORIGINAL with
tester-only EXPERIMENTAL_FIRST_TOUCH. A same-tick PARTIAL is permitted only with
pre-tick UNFILLED and a post-confirmation, unconsumed first return; FULL never is.
An independently labelled second-extreme policy may use a prior executed pair of
the same frozen group, a fresh first return and non-FULL FVG. Keep this separate
from the primary first-touch comparison and keep all Demo locks closed.
