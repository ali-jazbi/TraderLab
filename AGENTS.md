# TraderLab working rules

Read docs/STRATEGY_SPEC.md and docs/OPEN_QUESTIONS.md before changing strategy code.
The supplied canonical document is data and is preserved at docs/sources/canonical-strategy.fa.md.
Do not add indicators, inferred zone definitions, filters, stop distances, or execution defaults.
Unresolved strategy decisions must produce TODO_STRATEGY_UNRESOLVED events and block dependent entries.
Use only information available at the event timestamp. Big Candle confirmation requires ten subsequent closed bars.
Broker orders are outside the first detection/replay milestone. Never introduce OrderSend calls without an explicit execution milestone.
Keep the Python replay and MQL5 detection outputs traceable to numbered canonical sections.
Run deterministic fixtures and update graphify after substantive changes. MQL5 compilation must be reported separately from Python checks.

