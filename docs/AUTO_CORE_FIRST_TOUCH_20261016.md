# Actual MT5 FIRST_TOUCH comparison — 2026-10-16

**BLOCKED for automatic Demo.** Actual native Strategy Tester runs completed;
none executed an entry. No synthetic test results are used in this report.

| Run | Native real ticks | Qualified groups | Executed setups / opening deals | Closed / wins / losses | Win rate / PF |
|---|---:|---:|---:|---:|---|
| A: STRICT_ORIGINAL | 1,785,371 | 2 | 0 / 0 | 0 / 0 / 0 | undefined / undefined |
| B: EXPERIMENTAL_FIRST_TOUCH | 1,785,371 | 2 | 0 / 0 | 0 / 0 / 0 | undefined / undefined |
| Separate B second-extreme hypothesis | 1,785,371 | 2 | 0 / 0 | 0 / 0 / 0 | undefined / undefined |

Period: server 2026-09-21 00:00 through 2026-09-29 00:00 exclusive, including
September 28; LiteFinance-MT5-Demo / XAUUSD_o / M1 / Model=4. Each official HTML
report says **100% real ticks**. Native account arithmetic: gross profit, gross
loss, net profit and maximum equity drawdown all zero; there are no closed-trade
performance observations. Order, execution-price, exit, SL/TP and BE lists are
empty, not estimated. Deposit USD1000/leverage1:200 are simulation inputs.

[A native report](reports/auto-core-first-touch-20261016/AB-dae327f274-WARM_A.html),
[B native report](reports/auto-core-first-touch-20261016/AB-dae327f274-WARM_B.html),
[separate second-extreme native report](reports/auto-core-first-touch-20261016/AB-dae327f274-WARM_B_SECOND.html).
Per-run summary JSON, group decision CSV, selected native JSONL evidence, report
images and actual Tester journals are in that directory. Full raw captures and
recovery journals are preserved under `work/auto-core/AB-dae327f274/`.

## Exact final blocker

The initial September-28-only A/B pilot each processed 347,894 native ticks and
rejected all 50 groups. The six-session runs restore the earlier BOS context and
reproduce the two September-28 groups, with membership frozen without future data:

| Confirmed group, server time | Sell entries | Highest Bid after confirmation through test end | Entry observations |
|---|---|---:|---:|
| M5, Sep28 04:25:00.130 | 4243.64 / 4246.32 | 4223.66 | 0 |
| M15, Sep28 06:15:00.193 | 4243.64 / 4245.94 | 4201.18 | 0 |

Neither group had any subsequent price at or above even its lowest Sell entry.
There is **no selected first return**, so no pending entry reaches the gateway.
FIRST_TOUCH permission cannot produce a trade without that physical return.
All runs reject 277 other groups: already PARTIAL at confirmation96, FULL91,
consumed first return29, no qualified contained BOS25, single BE unresolved17,
distance>40pips15, distance<10pips4. These are group rejections, **not** rejected
broker order requests: entry attempts/order rejections both equal zero.
The 6,690 NO_ACTIVE_EXPERIMENTAL_GROUP returns concern other BOS, not executable
returns of the two accepted groups. No multiweek expansion was triggered because
the requested prerequisite of a valid executed trade was absent.

## Policy scope

Both A and B retain the existing EXPERIMENTAL same-frame earliest-qualified
equal-level-v1 grouping. STRICT_ORIGINAL names the FVG entry gate, not an assertion
that this grouping is the approved original strategy.

B records the FVG state before the current tick and carries a distinct native
permission through Core guards/book/gateway. Only an unconsumed post-confirmation
first return with pre-tick UNFILLED may tolerate a same-tick PARTIAL. FULL is always
invalid, including quotes between the two 0.01 network legs. Nothing revives an
earlier return. SL/TP/BE, exact quote, spread, margin and trial limits remain.

Primary B keeps the second extreme strict. The separately selected mode requires
an already executed pair of the same frozen group, the other extreme's own fresh
first return, a non-FULL FVG and the existing compatibility/daily/risk/.04 checks.
It cannot arm a second group or resend a consumed return. This mode also executed
zero trades; it does **not** establish a valid second-entry or BE lifecycle.

## Calendar, controls and limits

Historical schedules were rechecked against the official
[BLS September calendar](https://www.bls.gov/schedule/2026/09_sched.htm) and
[Fed September calendar](https://www.federalreserve.gov/newsevents/2026-september.htm).
Their scheduled CPI/NFP/FOMC events fall outside Sep21–28. Historical packets are
explicit EX_POST tester-only calendar inputs, not verified historical publication
timestamps. Sydney07:00/NewYork17:00 use the existing sourced IANA profile; these
September windows do not overlap, so no clipping/reset hypothesis is needed.
Forward HTTP403 did not block any historical run.

Simulation-only risk cap=$1000 (the test deposit) and extra cost reserve=$0 were
explicit study inputs, **not supplied production budgets or evidence of zero
broker fees**. Native Tester modeled costs remain distinct from historical broker
fee proof. Production preset risk0/cost-1 and the compile/init Demo locks remain
unchanged. The connected account is read-only/investor mode; it can supply Tester
history but is not demonstrated to permit Demo orders. No historical pair/TP1/
BE+5/exit cycle was formed, so critical execution controls remain unverified by
this dataset. Real/Contest/Reverse and automatic Demo submission remain disabled.
