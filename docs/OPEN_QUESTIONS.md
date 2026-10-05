# Unresolved decisions

Production configuration values remain null until explicitly supplied. Fixture values are modeling assumptions, never approvals of strategy rules.

| ID | Question / required input | Blocking scope | Canonical section |
|---|---|---|---|
| Q-OB-BOUNDS | Exact OB OHLC bounds? | Automatic setup formation; use sourced annotation only | 8 |
| Q-BOS-BOUNDS | BOS candidate identification, zone bounds and cross-timeframe FVG/OB association? | Automatic tradable BOS formation | 9–10,46 |
| Q-H1 | What mathematical H1 structure rule is required? | H1 observation only | 3 |
| Q-PARTIAL | Does any partial FVG fill retain validity? | Core after partial penetration | 7 |
| Q-SINGLE-SL | Single-entry Core SL distance? | Single Core plan | 21 |
| Q-DISTANCE | What happens at <10 and >40 pips? | These selection branches | 15 |
| Q-BE | Dual BE anchor: each entry or common reference? | New dual-entry paper positions until supplied | 22 |
| Q-RESET | Daily reset timezone and minute; stop aggregation across midnight? | Daily guards / entries | 24 |
| Q-PROFIT-BASIS | Does closed daily profit include commission/swap or deal profit only? | Profit latch uses explicitly supplied net/gross basis; swap remains unsupported | 24 / execution |
| Q-TOUCH | Which Bid/Ask observation and how to apply the 5-pip allowance? Entry level anchor planned vs filled? | Core/reverse touch and execution | 13 |
| Q-BROKER | Symbol alias, point/digits, tick size, lot step/minimum, contract/account currency conversion? | Broker integration; paper PnL needs explicit contract | 1,20 |
| Q-COSTS | Slippage, commission, TP fills and gap behavior? | Paper execution; never guessed from OHLC | execution |
| Q-NEWS | News source and coverage; reverse restriction; treatment of existing positions? | New entries if calendar unavailable; existing positions not force closed | 26 |
| Q-NY-CUTOFF | London-only scan end / NY start, range endpoint inclusivity? | Definitive NY bias; provisional observations only | 29–32 |
| Q-NY-DOUBLE | Both range sides break: what bias wins? | Bias becomes ambiguous, no hard entry gate | 32 |
| Q-IFVG | General FVG inversion and BOS break numerical semantics? | Reverse requires explicit sourced confirmations | 35,37 |
| Q-REV-SL | General reversal SL? | Reverse plan | 42 |
| Q-REV-DUAL | Which entries reverse for two-entry Core? | Dual-parent reversal | 44 |
| Q-REV-COUNT | Does reverse stop add a stopped setup or share parent's count? | Reverse with daily guards | 45 |
| Q-BE-STOP | Does a profitable BE stop count as a Daily Stop? | New entries after that event if unknown | 22–24 |
| Q-SIMULTANEOUS | Ordering when a single tick closes TP and SL and crosses $100? | Halt with unresolved reason; no fabricated chronology | execution |
| Q-LIFETIME | Setup expiry/restart restoration/duplicate setup identity and trade day policy? | Native execution milestone | execution |

No item requires an invented ICT/SMC convention. Confirmations belong in a dated spec amendment; parameterizing a rule does not make it confirmed.
