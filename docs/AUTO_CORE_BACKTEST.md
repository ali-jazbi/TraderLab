# Automatic Core: actual local tester evidence, 2026-10-14

Target: autonomous original Core; no operator-selected BOS/FVG packages. Demo auto
submission remains locked. Real/Contest and Reverse remain prohibited.

## Scope and assumptions

Actual LiteFinance XAUUSD_o, MT5 build 6244, Model=4 (Every tick based on real
ticks), 2026-09-21 through 2026-10-13 inclusive, USD1000, hedging, leverage1:200.
The accepted startup history baseline is excluded, then every occurrence is kept.
Local raw archives and reports are in `work/auto-core/`; large captures are not committed.

Original detectors and ten-following-closed-bar confirmation are retained. Automatic
package membership is **EXPERIMENTAL, tester only**: freeze qualified contained
BOS members at confirmed FVG availability, either same timeframe (1) or all frames
(2). There is no invented expiry, ranking, partial permission or rearming.
Single BE ambiguity, equal levels, invalid distances and consumed returns block.
Candidate groups are not canonical approved setups or evidence of executable entry.

The existing sole gateway send site and CoreLifecycle are reused for virtual tester
orders: two .01 legs per selected BOS, actual simulator fills, canonical shared
SL/TP/BE, journals, margin/FOK/quote checks, daily/news/emergency guards. Tester
journals are disposable local agent files; live account journals are untouched.
Experimental calendars are rejected outside MQL_TESTER. No auto Demo variant is
approved by this evidence.

Operational modeling: zero execution delay, pair1000ms, spread cap .22, deviation0,
news closure lead120 seconds before the canonical E−3min deadline. These trial
limits are not broker guarantees. No historical live-cost or latency parity is claimed.
Sydney07:00/NewYork17:00 are the existing sourced broker profile converted through
IANA DST. Overlapping days are **experimentally clipped** at the next Sydney open.
News is an explicit **ex-post preknown schedule hypothesis**, not historical as-of
publication proof. Sources: existing `configs/core-calendar.sources-20261013.json`,
[September BLS](https://www.bls.gov/schedule/2026/09_sched.htm) and
[Fed calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm).
September NFP/CPI and FOMC meeting precede this September21 start. Calendar builder
rejects requests outside the reviewed date range instead of claiming unknown coverage.

## Results

Final same-frame run `auto-weeks-same-02` completed with **JOURNAL OK, PAIR LIMITS
OK, CALENDAR_OK**, simulated_orders_enabled=true and broker_orders_enabled=false.

| Result | Same-frame experiment | All-frame experiment |
|---|---:|---:|
| Canonical approved setups | 0 | 0 |
| Experimental geometry groups | 2 | 0 |
| Rejected FVG packages | 686 | 688 |
| Executed .01 legs / closed trades | 0 / 0 | 0 / 0 |
| Wins / losses | 0 / 0 | 0 / 0 |
| Net PnL / max equity drawdown USD | 0 / 0 | 0 / 0 |
| Win rate / Profit Factor | undefined / undefined | undefined / undefined |

Zero PnL/drawdown only means no trades; it is not performance validation.
Same-frame rejection reasons: FULL253, PARTIAL238, equal BOS levels87, no contained
qualified BOS36, single BE23, prior consumed return25, distance>40pips19,
distance<10pips5. The two geometry groups have no selected post-availability first
return during the recorded window. They do not provide any executable trade sample.
Capture/controller are nonhalted; ambiguity/CopyTicks/snapshot/timer errors are all0.

Multiweek detected market evidence: 4,856,518 recorded ticks, 30,251 delivered closed
candles, 3,932 confirmed Big Candles, 21,197 qualified BOS, 688 FVG/OB pairs and
175,559 BOS/FVG relationships. Actual market history comparison has identical
ordered SHA256 `ca121261c6e97b55893b7dbc27725bb9e84774da16341e2f776e34c7f6e6f8ed`
for time_msc/Bid/Ask/last/volume, including repeated same-ms occurrences. API REAL
flag stripping in the tester is excluded from this quote comparison.

All-frame experiment: 0 geometry groups, 688 rejected, 0 trades, wins0/losses0,
net0 USD, maximum equity drawdown0 USD. Win rate and Profit Factor are undefined.
Rejections: FULL263, PARTIAL246, equal BOS levels153, no contained qualified BOS10,
single BE10, prior consumed return3, distance>40pips1, distance<10pips2.
This earlier binary logged JOURNAL OK/CALENDAR_OK in its actual agent journal but
has no JSON configuration event; the parser conservatively labels configuration
not verified. Its results are secondary to the later fully instrumented same-frame run.

First same-frame attempt had missing tester calendar transport and is detection-only.
`#property tester_file` fixes transport; it was rerun with explicit status evidence.
October7 attempt also lacked calendar: use its Python/native agreement for detections
and retest diagnostics only, not validated trade performance.

## Genuine candidate examples, not trades

September28 broker04:25:00.130, M5 SELL FVG4239.65–4249.89,
OB4249.89–4254.32. Contained qualified BOS members are September24 broker13:30,
18:10,18:15,18:30,18:35. Canonical extremes4244.14/4246.82 imply references
4243.64/4246.32. No selected first directional return was recorded after package
availability through the end of this capture. Both references are inside the FVG;
a later observed return into its interior would additionally require unresolved
PARTIAL permission. No execution or profitability is inferred from geometry.

September28 broker06:15:00.193, M15 SELL FVG4239.18–4249.89,
OB4249.89–4257.28. Members September24 broker13:30,18:00,18:30;
extremes4244.14/4246.44 imply references4243.64/4245.94. Same absence of a selected
post-availability directional return; no fabricated fill or trade sample.

## Verification and blockers

Python/native October7: 279,320 identical input ticks, 30 FVG each, zero groups/trades,
identical group reasons (PARTIAL11, FULL12, no contained BOS6, single BE1).
Full-window Python/native closed-candle detection counts agree: qualified BOS21,197
and FVG688. Full-window tick-driven Python replay was stopped after slow processing;
**full trade-lifecycle parity is not verified**. Python atomic paired fills and its
quote-based stop model also differ from MT5's sequential virtual orders.

New targeted regression checks: 7 PASS. EA compiled: 0 errors, 1 existing version
warning; StrategyChecks compiled: 0 errors, 0 warnings. Prior142/7 native broker
checks and smoke/AutoPilot trades were not repeated. Zero actual strategy trades
means the full automatic entry→two orders→TP/BE/exit path is unproven on market data.

Automatic Demo **BLOCKED**: package membership/finalization is still a hypothesis;
PARTIAL permission/single BE/day overlap remain unresolved; no executable strategy
round trip supports activation. Retaining UNFILLED and ten-bar availability produced
no trades. This does not establish profitability or justify relaxing these guards.

Archive incident: MT5 cleared the previous tester-agent sandbox on a new run before
its old raw October7 capture was archived. The original normalized October7 files
remain available; the old raw is unavailable. Live Demo raw captures were untouched.
Every new multiweek raw was archived outside the agent before another run.
Computer Use was stopped by user Escape; subsequent compilation/testing used CLI
only. No further terminal UI automation was issued.
