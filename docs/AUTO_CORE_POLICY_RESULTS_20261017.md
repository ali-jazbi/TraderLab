# Native Core trading results — 2026-10-17

**The zero-trade loop is broken. Automatic Demo stays LOCKED.**
These are actual MT5 Strategy Tester orders/deals, not Python-generated fills.
Source: unchanged original `auto-weeks-same-02.jsonl`, 4,856,518 genuine ticks,
SHA256 `26151d557167edbcedaa822f926f0b4b8231290dd264ecf4139732d4636488e0`.

## Fixed experiments, not owner-confirmed rules

`InpExperimentalCorePolicyMask`: C=1 TOUCH_CROSSING, F=2 NON_FULL_FVG,
M=4 PER_BOS_MEMBERSHIP; 0 retains strict guards. All use the existing explicitly
experimental same-frame/earliest-qualified equal-level grouping, frozen at FVG
availability. Canonical 10/20/40 branches, extremes, C1/C3 OB and ten following
closed candles are unchanged. Consumed members stay in shared geometry and never
trade again. Multiple eligible FVG packages still block; single BE stays unresolved.

C uses the actual Bid return and Buy Ask / Sell Bid execution. Both observed Bid
displacement and executable price displacement must fit 0.5 XAUUSD price units;
configured slippage also fits that budget. Actual deal prices are checked again.
F allows PARTIAL at confirmation or before return, never FULL. Their original
states are retained separately. No future profitability influenced membership.

The full original analytical pass found 26 selected post-confirmation returns:
11 single-BE blocked, 7 FULL blocked, 8 admitted by C+F+M. Masks0–4 admit none;
mask5 admits one; mask6 admits one. See [exact quotes/rejects](reports/auto-core-policies-20261017/analytical-gates.json).

## Controlled eight-way comparison

Server period: Sep21 inclusive to Sep23 exclusive. Every tick based on real ticks,
100% quality, 567,612 Tester ticks including the excluded startup occurrence.
All eight runs used the **same compiled binary**. Counts below are .01-lot closed
positions, two per executed BOS entry; each row is an independent study.

| Mask/policies | Entries | Closed | W/L | WR | MT5 PF | Net USD | Max equity DD USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 strict | 0 | 0 | 0/0 | — | — | 0.00 | 0.00 |
| 1 C | 0 | 0 | 0/0 | — | — | 0.00 | 0.00 |
| 2 F | 0 | 0 | 0/0 | — | — | 0.00 | 0.00 |
| 3 C+F | 0 | 0 | 0/0 | — | — | 0.00 | 0.00 |
| 4 M | 0 | 0 | 0/0 | — | — | 0.00 | 0.00 |
| 5 C+M | 2 | 2 | 0/2 | 0% | 0.00 | -11.26 | 18.10 |
| 6 F+M | 2 | 2 | 2/0 | 100% | 219.90 | +21.89 | 0.68 |
| 7 C+F+M | 2 | 2 | 0/2 | 0% | 0.00 | -7.18 | 7.18 |

Mask6's PF includes negative entry-commission cash flows, despite no losing
positions. The EA incorrectly serialized null using losing-position count; this
was fixed and rerun natively with identical deals and PF219.90. Two wins do not
establish an edge or justify selecting this policy for production.

Python audited as-of membership/quote gates from original native archives; this
is not a claim of independent Python detector or PnL-engine parity. Ordered ticks
(including flags/volume/same-ms occurrences) and closed OHLC sequences matched
the original prefixes in all eleven runs; original raw SHA256 was reverified.

## Continuous execution through Sep29

Mask7, Sep21 inclusive to Sep30 exclusive: **4 setups, 8 entries, 8 closed,
2 wins / 6 losses, WR25%, PF0.75, net -$5.33, max equity DD $15.00 (1.49%)**.
2,079,789 captured ticks; 2,079,790 including startup. No end-of-test liquidation:
all exits were actual SL/TP deals. All eight analytical opportunities were reached;
four submitted and four consumed under the existing study one-new-setup/day cap.

| Server timestamp | Side / actual entry | Actual exits | Pair net USD |
|---|---|---|---:|
| Sep22 11:41:39.248 | SELL 4317.41 | SL4320.95, 11:42:53.908 | -7.18 |
| Sep23 17:53:15.283 | SELL 4294.32 | TP4288.20 at18:28:11.088; TP4284.19 at18:29:27.657 | +16.15 |
| Sep25 06:36:26.895 | BUY4275.01 | SL4271.32, 06:54:26.598 | -7.48 |
| Sep29 17:19:04.367 | SELL4171.55 | SL4174.91, 17:21:58.521 | -6.82 |

Separate Sep29 study (same complete Sep21 warm-up, earlier returns consumed but
orders disabled until Sep29) independently reproduced two SL exits, net-$6.82,
DD$12.68. It is not pooled into the continuous equity curve.
Mask6 separately proved two Ask entries4329.04, TP fills4338.05/4342.02 and actual
SL modification to shared BE4332.49; [native BE log](reports/auto-core-policies-20261017/actual-be-evidence.txt).

## Costs, checks and remaining deployment blockers

Study assumptions only: virtual deposit/risk cap$1000, cost reserve0, one new
setup/day, max exposure.04lots, pair1000ms, spread≤.22, entry slippage0points,
Tester delay0. Actual tick spreads and Tester commission$.05/entry leg were paid;
SL/TP gaps used actual deal prices. These are modeled broker costs, not verified
historical fee schedules or live latency/slippage guarantees. Nothing copies these
budgets into production defaults. Calendar remains the explicit TESTER-only
Sydney-overlap/EX_POST-news packet, not a deployable fresh news calendar.

The first probe reproduced false unknown-second-deal reconciliation and emergency
closure (net-$0.54); a range-refresh probe also failed. A third probe verified the
ticket fix (net-$7.18). All three are archived locally and excluded from the
fixed-binary comparison. Selecting and verifying each actual
terminal-history deal ticket fixed the blocker; the lifecycle receives both proven
entry tickets. Unknown/partial outcomes still fail closed. The only OrderSend site
and all Demo/Real/Contest/Reverse restrictions remain intact.

211 Python tests passed. AUTO_CORE_DEMO: compiled0errors/0warnings; TraderLab:
0errors/1 pre-existing version-format warning; StrategyChecks:0errors/0warnings.
No smoke, AutoPilot, or old native-check suite was repeated. Eleven native studies
completed, including the PF regression. Failed agent-auth launches have no results.
The port3000 conflict with a separate local Node service was avoided with the
[documented Tester Port setting](https://www.metatrader5.com/en/terminal/help/start_advanced/start).

**Demo BLOCKED:** deployment approval of experimental grouping/C/F/M is missing;
production risk/cost limits and a fresh forward calendar/account/reconciliation
safety review are also required. No canonical rule was changed to create profit.

[CSV performance](reports/auto-core-policies-20261017/performance.csv),
[actual candidate matching](reports/auto-core-policies-20261017/verified-execution.json),
[short native reports/deals](reports/auto-core-policies-20261017/native-short/results.json),
[continuous native report/deals](reports/auto-core-policies-20261017/native-continuous/results.json).
All large raw captures, journals, caches and development-probe archives remain local.
