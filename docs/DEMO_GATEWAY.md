# Locked DEMO gateway — owner §52, integration 2026-10-13

**Prepared, DISABLED, connected through the blocked Core controller.** The native review lock
`TL_DEMO_DISPATCH_REVIEWED=false` and constructor `enabled=false` both prevent
submission. Production replay retains `broker_execution_enabled=false`.
No input can override the review lock. Reverse is unsupported. Capture behavior
and original market files are unchanged.

## Quote and fill contract

The observation policy verifies `SYMBOL_CHART_MODE_BID` and observes the exact
Bid-chart entry reference. Buy execution uses observed Ask; Sell execution uses Bid.
LAST charts are blocked. Ask return diagnostics remain separate from Bid signals.
This is explicit engineering policy, not new owner terminology.
[MT5 chart modes](https://www.mql5.com/en/book/automation/symbols/symbols_chart_mode),
[Bid/Ask execution](https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation).

A crossed reference without an observed exact signal quote consumes the opportunity
without a fill. A historical quote is not a live execution opportunity. Changed
prepared quotes are rejected instead of replaced. Requested prices and successful
responses are not executed prices: broker deals/positions must reconcile the intent.
Single SL40 is repaired to actual position fill; dual SL/TP retain canonical shared
references. [OrderSend contract](https://www.mql5.com/en/docs/trading/ordersend).

## Native safety boundary

Source: `mt5/Include/TraderLab/DemoGateway.mqh`.

- Every dispatch rechecks DEMO type, login/server, connection and trade permissions.
  REAL/CONTEST are rejected. Core supports USD hedging only.
  [Account properties](https://www.mql5.com/en/docs/constants/environment_state/accountinformation).
- Canonical 0.01-lot legs, exact price/volume grids, exposure including pending orders,
  stops/freeze geometry, margin and OrderCheck must pass. FOK only; unsupported partial
  fills persist an emergency halt. Preflight is not execution proof.
  [OrderCalcMargin](https://www.mql5.com/en/docs/trading/ordercalcmargin),
  [OrderCheck](https://www.mql5.com/en/docs/trading/ordercheck).
  Its documented successful check retcode 0 is accepted separately from send retcodes;
  neither a successful check nor send ACK proves an actual fill.
- Core prepares two legs with distinct durable IDs. UNFILLED FVG, explicit strategy,
  session/news guards and exact first-touch evidence are required. Market legs are
  not atomic; incomplete/unknown outcomes halt and attempt account-wide Demo closure.
  Core leaves grouping/finalization unapproved and live execution proof unset;
  no EA input enables dispatch.
- Canonical account/server FILE_COMMON journal has an exclusive local file handle,
  scoped header and immutable intent payloads. Intent is flushed before the sole send
  site; stable IDs/opportunities suppress duplicates, including rejected intents.
  Corruption, changed scope or unknown outcomes block entries. Existing broker rate
  guards persist. No automatic timeout retry; no multi-host coordination is provided.
- Restart reconciles linked broker deals/orders/positions. Missing history does not
  establish rejection. Unlinked/mixed/partial exposure and incomplete pairs fail
  closed. Actual-fill SL has a durable marker to avoid resetting a later reviewed BE.
- Emergency halt persists. Account-wide closure uses authoritative current Demo
  tickets, observed exit quotes and full position volume. Failed/unknown closes are
  reported; no closure is inferred from ACK alone.
- Core persists an account/server/symbol/magic-scoped plan before submission and
  BOS consumption before considering a request. Absent/unrestored plans halt.
  Callbacks read actual deals, position identifiers and costs. TP1 requires broker
  TP evidence; shared-reference BE resolves the current position ticket from its
  identifier. Confirmed BE is checked without retrying an unknown modification.
  Out-of-order/conflicting/partial deals fail closed. Actual native transport and
  restart behavior require terminal verification before activation.
  Transaction arrival order is not guaranteed by
  [MetaQuotes](https://www.mql5.com/en/docs/event_handlers/ontradetransaction).
- Tester history never initializes production Core journals or a broker trade book,
  even with nonzero magic. Gateway account checks reject tester transport.
  Calendar test scripts use local synthetic fixtures; terminal history still feeds
  the diagnostic controller. Tester TimeGMT equals simulated server time according
  to [MetaQuotes](https://www.mql5.com/en/docs/dateandtime/timegmt), so it must not be
  mistaken for an independently verified UTC execution clock.
- News coverage, CPI/NFP/FOMC times, announcement availability and broker UTC offset
  must be supplied. Caller supplies positive operational closure lead; no calendar
  hours or safety buffer is guessed. Close ahead of event minus3 minutes. Late calls,
  unknown closes or coarse deadline-second observations cannot certify compliance
  and halt entries, including gaps spanning the news window. Missing coverage triggers
  emergency best-effort closure. Late-opened positions inside the news window are also
  targeted; an unverified position clock triggers closure without claiming compliance.

`traderlab/demo_gateway.py` is a separate SQLite safety reference with injected
**test transport only**, no MT5 connector. Tests cover durable duplicates, crash/restart
UNKNOWN state, conflicting payloads, competing instances, rejection, identity/margin
checks and persistent halt. These are not native broker tests.

## Verification and exact manual next steps

Executed locally for the original §52 milestone: **141 Python tests passed**. MetaEditor compiled TraderLab.mq5
(0 errors, 1 existing warning), StrategyChecks.mq5 and DemoGatewayChecks.mq5
(both 0 errors, 0 warnings). No broker submission occurred. Native script execution,
journal recovery/retcodes/SL repair/close deadlines and fresh detector parity remain
**UNVERIFIED**.

1. MT5: **File → Open Data Folder**. Copy compiled
   `D:\Github\TraderLab\mt5\StrategyChecks.ex5` and `DemoGatewayChecks.ex5`
   into that terminal's `MQL5\Scripts`. Refresh Navigator.
2. Verify **LiteFinance DEMO**, open **XAUUSD_o**, run each script once.
   DemoGatewayChecks is read-only: no journal initialization or order check/send.
   Save Experts/Journal: require `failures=0`, `dispatch_locked=true`; inspect chart
   mode, margin mode, currency, volume/tick grids and filling mode. Keep review false.
3. Fresh October7 normal/stress captures with the existing read-only EA; preserve both
   raw files. Follow [NATIVE_RETESTS](NATIVE_RETESTS.md) for exact parameters,
   inspection and comparison of both audited BOS candidates.
4. Supply sourced session/news calendars and account/cost inputs, resolve minimum
   decisions in [DEMO_READINESS](DEMO_READINESS.md), then separately review native
   fault/restart/duplicate tests before installing a strategy controller or unlocking.

The procedure above records the historical §52 state. The 2026-10-13 Core integration
supersedes its pending-controller statement. Current script set, verification scope,
candidate results and activation checklist are in [DEMO_READINESS](DEMO_READINESS.md).
Broker fault/restart execution remains unverified; this is not an approved Demo trader.
