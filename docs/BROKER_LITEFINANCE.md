# LiteFinance broker and execution profile

Status: broker-hardening reference for the intended MT5 XAUUSD Demo account. This document records execution facts separately from the canonical strategy. It does not enable order sending.

## Confirmed by LiteFinance support

For the user's intended account, support confirmed that Expert Advisors/automated trading and scalping are allowed, and that the account is Islamic/Swap-Free. Confirm the actual account's entity, product terms and runtime status before a Demo execution milestone. Do not infer realized swap or other costs from the account label.

## Confirmed by client agreement

The LiteFinance client agreement describes these request thresholds: more than 1,000 client requests in 300 seconds can switch the account to read-only; more than 10,000 requests in 3,600 seconds can block it. The safety policy in code is stricter at the boundary: at most 1,000 and 10,000 outbound attempts are admitted in their respective rolling windows, and the next attempt is refused. The account-specific applicable agreement and current legal entity remain to be checked before execution.

The agreement's gap handling states:

- A Stop Loss crossed by a gap executes at the first available price after the gap.
- Buy Stop/Sell Stop pending orders crossed by a gap execute at the first available price.
- Buy Limit/Sell Limit and take-profit orders normally execute at their specified price, subject to liquidity exceptions.
- When a pending-order price and its attached TP/SL are all traversed by a gap, the pending order can be cancelled.

These pending-order rules are documented for future execution only. Core entry remains a direct market entry on observed BOS touch; pending orders are not modeled or substituted.

Abnormal market conditions can delay or reject requests. Documented typical processing times are 3–5 seconds normally and 5–15 seconds under other conditions. LiteFinance may change margin requirements/leverage for new positions up to 30 minutes before and after important macroeconomic events. This is broker execution risk, not a strategy filter and does not alter NEWS-01's CPI/NFP/FOMC ±15-minute restriction.

## Confirmed by current public instrument/account information

LiteFinance's public specification currently lists XAUUSD as 100 oz per lot and minimum/step volume 0.01 lot. These published values may change and are not persisted as runtime truth. Spread, commission, tick size/value, account currency/conversion, account mode and actual execution costs must be observed from the active terminal/account.

## Time and session boundaries

The strategy session clock remains Tehran time. LiteFinance documents server time as GMT+3 from the last Sunday of March until the last Sunday of October, and GMT+2 outside that period. MT5 rows preserve server timestamp, explicit configured server offset, derived UTC timestamp, and Tehran strategy timestamp/offset when configured. No strategy window is encoded against server-clock time.

`InpServerUtcOffsetSeconds` and the Tehran offset must be explicitly supplied. Missing offsets are logged unresolved; normalization rejects them. A mismatch against the documented seasonal schedule is rejected rather than silently correcting historical data. Transition Sundays are marked unverified by the date-only diagnostic pending observed/configured offset validation.

## Runtime observations and blocking checks

At EA initialization, the native diagnostic records the exact symbol, digits, point, trade tick size and tick values, contract size, min/max/step/limit volume, stop/freeze levels, trade/order/filling modes, account currency/margin mode/leverage, account and Expert Advisor trade permissions, hedging mode, swap long/short, existing same-direction positions and pending-order volume, and configured offsets. It checks that each canonical 0.01 leg is valid and that a new two-leg 0.02 entry would fit the current directional volume limit. TICK and CLOSED_BAR rows retain the configured broker symbol including suffixes. Strategy pip remains 0.1 XAUUSD price units and is never replaced with `_Point`.

Paper replay reads the same `runtime_capabilities` shape from configuration, checks every canonical leg against min/max/step, and checks existing same-side open paper volume plus the next two-leg 0.02 entry against `volume_limit`. The production template leaves this runtime snapshot null and blocks entries until explicitly supplied. A future execution gateway must refresh actual exposure immediately before sending, including pending orders; replay configuration is not live broker state.

The diagnostic reports a broker/configuration block when the canonical 0.01 lot or a planned price level cannot be represented on runtime grids. It does not round a level. Snapshot fields that MT5 cannot provide are represented as unavailable or diagnostic-only.

## Implementation safety policy

**2026-10-12 superseding scope:** The owner authorized an isolated durable DEMO
gateway after 906f9db. [DEMO_GATEWAY](DEMO_GATEWAY.md) contains the sole guarded native
OrderSend site, default disabled with a compile-time review lock, outside the capture
EA. The following bullets describe the earlier broker-hardening milestone; durable
preparation advanced, but runtime verification and strategy integration remain blocked
as listed in [DEMO_READINESS](DEMO_READINESS.md).

- There is no OrderSend/OrderSendAsync call in this milestone. EA output is diagnostic; Python replay is paper-only; dashboard is read-only.
- Python and MQL request guards are deterministic in-memory reference implementations. They do not persist across restart, coordinate multiple EA instances, and are not connected to a trade-send path. They are not sufficient to protect an enabled Demo account.
- Future requests must use one durable gateway, count each dispatch attempt (including retry/modify/close/delete), and suppress duplicate intents. A timeout is unknown and cannot be retried until authoritative broker-state reconciliation establishes no execution; only then may an operator explicitly retry. An order/deal/position found during reconciliation consumes the intent. Restart persistence remains unresolved until the durable gateway milestone.
- A successful MT5 call is not proof a position exists. Reconcile intent → request/retcode → order → deal → position with `OnTradeTransaction` and broker state, stable linked IDs, restart recovery and margin preflight.
- Stop-gap paper exits use the first observed executable quote plus explicit adverse slippage. This cannot predict unobserved liquidity. TP fill policy remains explicit/configurable or must be based on actual broker deals; no favorable fills are fabricated.
- Islamic/Swap-Free is an account fact, not a strategy rule. Runtime swap properties are logged where observable; realized overnight costs come from account history/deals.

## Definitive first-leg rejection and reconciliation — 2026-10-25

The stopped Native study returned `TRADE_RETCODE_MARKET_CLOSED` (10018) with
zero order/deal IDs on May7. The response classifier previously omitted this
definitive rejection and both gateway/Core layers then latched emergency stops.
This is execution infrastructure, not a strategy/session filter.

Market-closed responses with zero IDs are now persisted as `REJECTED`. Known
first-leg OrderCheck rejections before submission also retain a durable rejected
identity, including the final check immediately before Claim/OrderSend. A failed
first leg permits unrelated new opportunities only after fresh broker history,
positions, active orders, deals and historical orders reconcile with no evidence
for that rejected intent. The attempted return, plan and identity remain consumed;
no retry is scheduled. Unknown/timeouts, nonzero response IDs, unavailable or
contradictory evidence and incomplete pairs retain their protective blocks.
Existing UNKNOWN/emergency journals are not rewritten or automatically cleared.
No trading session hours or alternative TP/SL/volume settings were introduced.
The Demo compile/init locks and Real/Contest rejection remain unchanged.

MetaQuotes defines [trade-server return codes](https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes).

## Still unresolved before Demo execution

2026-10-25: the connected account was freshly verified Demo/USD/Hedging in an
isolated read-only terminal, with Algo Trading OFF and zero open positions/orders.
Disconnect now revokes cached reconciliation; no fresh-entry preflight can rely
on an offline broker snapshot. Live calendars require the forward V2 provider and
matching observation timestamps. Actual owned-position exit receipts are tracked
by original position ID even when their deal magic differs. These controls do not
approve missing risk/cost inputs, resolve session overlap or activate Demo.

Verify the applicable entity/agreement and limits for this account; capture symbol alias and every dynamic capability at runtime; measure spread, commission, slippage, TP/limit liquidity outcomes and realized financing; configure server/Tehran offsets for each capture including transition times; implement durable request counting, rate guard, margin preflight, retcode/transaction reconciliation, restart recovery and hedging/netting behavior. Existing strategy questions remain listed in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md); broker research does not resolve them.

## Sources

### Measured Demo evidence — 2026-10-13

The complete October7 Core capture has279320 ticks: spread median/p95=0.22,
p99=0.52,maximum=1.08 XAU price units. The October13 live prefix reviewed through
10:46:13.716 UTC has11736 ticks,all with0.22 spread. It is an in-progress prefix,
not a completed capture. Three preexisting open requests took99.038–100.884ms;
three closes97.280–98.422ms. Three entry prices match broker deals with zero
observed slippage. No actual paired Core execution was measured. These samples
do not determine safe pair/slippage/news-closure tail limits; production values
remain unset. See configs/core-demo-measurements-20261013.json for counts/hashes.
Prior Smoke/AutoPilot results were read only, not rerun.

Calendar packets use this broker's published Sydney07:00 and New York17:00
local session clocks with IANA Australia/Sydney and America/New_York conversion.
These are a sourced execution profile, not new owner clock-hour confirmation.
The article's fixed UTC tables are internally inconsistent across seasons.
Each packet contains one DAY; adjacent25-hour windows overlap in October and
cannot be silently combined or allocated to a guessed reset policy. Original
Sydney-to-New-York rule is unchanged. BLS and Fed calendar snapshots cover the
restricted event families; CPI October14 is12:30 UTC. Packets expire, require
source re-verification before activation and are not an automatic news feed.

- [LiteFinance local session clocks](https://www.litefinance.org/blog/for-beginners/time-at-forex/)
- [BLS October2026 calendar](https://www.bls.gov/schedule/2026/10_sched.htm)
- [Federal Reserve October2026 calendar](https://www.federalreserve.gov/newsevents/2026-october.htm)

- [LiteFinance client agreement (Persian PDF)](https://www.litefinance.org/uploads/documents/pdf-litefinance/litefinance-client-agreement-fa.pdf?v=5e48f9eb)
- [LiteFinance agreement on quoting and transaction procedure (English PDF)](https://www.litefinance.org/agreement-on-quoting-system-and-transactions-procedure-en.pdf)
- [LiteFinance public XAUUSD trading specifications](https://my.litefinance.org/trading/info?language_save=true&rtkcid=6a49d8ec92d85c976f5dad2c&symbol=XAUUSD)
- [LiteFinance Islamic/Swap-Free account information](https://www.litefinance.org/trading/account-types/islamic-no-swap/)
- [LiteFinance margin requirement change schedule](https://www.litefinance.org/markets/list-of-changes-in-margin-requirements/)
- [MetaTrader symbol properties](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants), [account information](https://www.mql5.com/en/docs/constants/environment_state/accountinformation), [OrderCheck](https://www.mql5.com/en/docs/trading/ordercheck), [OrderCalcMargin](https://www.mql5.com/en/docs/trading/ordercalcmargin), [OnTradeTransaction](https://www.mql5.com/en/docs/event_handlers/ontradetransaction)
