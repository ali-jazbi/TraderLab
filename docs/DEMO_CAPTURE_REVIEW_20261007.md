# First LiteFinance Demo capture review — 2026-10-07

Source: `TraderLab-demo-20261007-run01.jsonl`, provided from the terminal's `MQL5/Files` directory. The raw capture was read only, was not copied into Git, and was not repaired or filtered. SHA-256 before and after review:

`50d0f76e5c0849fa2794df8e72028276feab058bedf81ecedcfe4a2dac8db4ed`

## Observed results

| Observation | Result |
|---|---|
| Exact runtime symbol | `XAUUSD_o` |
| Total lines / raw event sequence | 1,911; contiguous seq 1–1911 |
| TICK / CLOSED_BAR | 1,537 / 118; tick indexes have no gaps |
| First UTC / last precise market UTC | `2026-10-07T05:44:45.000Z` / `2026-10-07T05:54:41.864Z` |
| Tehran observed range | `09:14:45.000+03:30` through `09:24:41.864+03:30` |
| Configured server / Tehran offset | 10800 / 12600 seconds; all parseable rows reproduce UTC/Tehran exactly |
| Bid/Ask/spread | Parseable ticks consistent; spread min/avg/max all 0.22 price units (2.2 strategy pips) |
| Initialization / capability snapshot | Present; `broker_orders_enabled:false` |
| Runtime instrument properties | digits 2; point/tick size 0.01; contract size 100; volume min/step 0.01, max 100, limit 0; stops/freeze 0; trade/order/filling modes 4/127/1 |
| Runtime account properties | Demo (`account_trade_mode:0`); margin mode 2; USD; leverage 200; hedge allowed true; trade allowed false; trade expert true |
| CONFIG_UNRESOLVED / BROKER_CONFIG_BLOCKED | Neither present |

Time agreement demonstrates internal capture consistency, not an independent measurement of the configured server offset against a UTC clock.

## Defects and focused fixes

All 252 malformed rows contain an unquoted formatted datetime in `candidate_server_epoch`: 179 BOS_CANDIDATE_BREAK, 71 BOS_CANDIDATE_QUALIFIED and 2 BIG_CANDLE_CONFIRMED. Detection now shares a serializer that casts `datetime` through `long`, emitting a JSON integer. The Big Candle payload reused by FVG events receives the same fix. Strategy rules and event availability timestamps are unchanged.

The final tick was `05:54:41.864Z`; EA_DEINIT was `05:54:41.000Z`, from second-resolution `TimeCurrent()`. The logger now records `timestamp_precision`, using `seconds` for default observations and `milliseconds` for an explicitly supplied market fraction, including zero. The inspector treats only known lifecycle/initialization diagnostic events at a whole second as the interval `[second, second+1s)`. Legacy captures without the marker use this same explicit event allowlist. No timestamp is rewritten. A previous-second shutdown still fails; tick/bar and other precise events retain strict chronology, including 1 ms regressions across lifecycle events. A market event cannot claim second precision to bypass validation.

The original capture still **FAILS** with exactly 252 invalid-JSON errors. The shutdown produces no chronology error after the inspector fix. Apparent parsed-event seq gaps of 252 correspond to those rejected rows; the raw seq is contiguous. The normalizer correctly refuses this malformed capture and writes no normalized output. No historical repair was attempted; a fresh capture from the recompiled EA is required for complete pipeline acceptance.

## Verification

- Full Python suite: 58 tests passed, including the exact reported shutdown timestamps, strict market regression, raw-file preservation and native serialization source guards.
- Native generated-JSON assertions added to StrategyChecks for `1791361380` and zero epoch values. Python source guards verify both BOS and Big Candle payloads use the shared serializer; these guards do not execute MQL5.
- Actual compiler: `C:\Program Files\MetaTrader 5\metaeditor64.exe`, version `5.0.0.6244`.
- `mt5/TraderLab.mq5`: 0 errors, 1 warning. Warning 68 is the pre-existing `#property version "0.10"` MQL5 Market format warning (`xxx.yyy` required for Market publication); left unchanged because publication is outside this fix.
- `mt5/StrategyChecks.mq5`: 0 errors, 0 warnings. Compilation does not prove native assertions ran; script execution remains **UNVERIFIED**.
- No OrderSend, OrderSendAsync, CTrade Buy/Sell or position/order mutation path introduced. The EA remains detection/logging only. Compiled binaries were not installed into the running terminal.

Next validation: run the compiled StrategyChecks script manually, then capture a new 5–10 minute run with `InpBrokerSymbol=XAUUSD_o`, a fresh filename, the independently verified server offset and Tehran offset 12600. Preserve run01 as evidence; validate and normalize the new file using the [capture procedure](FIRST_DEMO_CAPTURE.md).
