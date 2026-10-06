# TraderLab

Canonical XAUUSD strategy: native MetaTrader5 detection capture, deterministic Python paper replay and a read-only observability dashboard. No broker orders are sent.

The intended broker profile is LiteFinance MT5/XAUUSD. Broker permissions, published request/gap limits, seasonal server offset, runtime capability snapshot and execution safety boundaries are tracked in [LiteFinance broker notes](docs/BROKER_LITEFINANCE.md). These execution facts do not change the canonical strategy. Order sending remains disabled.

## Observability dashboard

The user prioritized the dashboard before native execution. [Dashboard and live setup](docs/DASHBOARD.md) describes the Next.js app in `web/`, Vercel/Neon provisioning and the checkpointed local publisher. Run `npm ci` then `npm run dev` inside `web`. Sample fixtures are explicitly synthetic; native data needs a running EA, the publisher and configured cloud storage. Live data is private; the sample is public. The `/guide` page includes operator setup instructions.

Start with [Strategy Spec](docs/STRATEGY_SPEC.md), [open questions](docs/OPEN_QUESTIONS.md), and the preserved [Persian source](docs/sources/canonical-strategy.fa.md). The supplied summary is authoritative for this project; the original PDFs/RAR/images have not been independently inspected.

## Run locally

Requires Python3.10+; no third-party libraries for the replay/checks. UTC resets work without timezone packages. Named reset zones such as Asia/Tehran need an installed IANA timezone database; a missing database is an explicit error, not an inferred offset.

```powershell
Set-Location D:\Github\TraderLab
python -m unittest discover -s tests -v
python -m traderlab --events tests/canonical-buy.jsonl --config configs/fixture.example.json --out outputs/canonical-A
```

The fixture deliberately chooses values for unresolved policies to exercise the code. These are **synthetic modeling choices, not strategy approvals**. For example, its single/reverse SL40, own-entry BE, expanded touch zone, empty news calendar, UTC day reset and London scan end are not production defaults. `configs/production.template.json` leaves these null, blocks dependent entries, and emits reasons.

Replay writes `events.jsonl` and `manifest.json`: input/config/code/spec hashes, event hash, open legs and closed daily USD result. Identical input/config/code yields identical bytes. The canonical-A fixture produces +38USD, the stopped version -18USD under the explicitly supplied synthetic100 contract and zero costs. These are regressions, not historical performance evidence.

## Native MT5 capture

1. Copy the `mt5` folder contents together to a dedicated `MQL5/Experts/TraderLab` folder in your terminal data directory. Preserve the relative `Include/TraderLab` layout.
2. Compile `TraderLab.mq5` and `StrategyChecks.mq5` using MetaEditor. Attach the EA to the exact configured broker symbol chart. Run the checks separately as a script.
3. Set `InpBrokerSymbol` explicitly for broker suffixes. Strategy pip is always0.1, independent of reported point/digits.
4. Choose a fresh `InpLogFile` each run. Existing logs are never overwritten. Logs are inside the terminal/tester `MQL5/Files` sandbox.
5. Provide `InpServerUtcOffsetSeconds` for the captured interval and the explicit Tehran UTC offset used for strategy-time logging. Unset offsets still permit diagnostic capture, but emit null UTC timestamps and are rejected by the replay importer. Split captures at broker offset changes. Daily reset and Tehran calendar interpretation remain separate configuration. EA startup records symbol/account capabilities and blocks diagnostically when canonical lot or strategy price levels cannot be represented.
6. Capture from Demo or Strategy Tester. Use observed tick data when validating touches; OHLC alone does not supply their order. The first bootstrap exports the available21 closed bars per timeframe at their actual capture availability, not fabricated earlier timestamps.

```powershell
python tools/normalize_mt5_log.py work/TraderLab-run01.jsonl work/native-events.jsonl
python -m traderlab --events work/native-events.jsonl --config configs/production.template.json --out outputs/native-detection
```

MT5 captures contain no automatically inferred tradable zones. Add sourced `setup`/`structure` annotations to an explicitly chronological input when exercising paper trading. Do not sort future confirmations backward or retroactively label first touches.

The EA implements native diagnostic detectors; selection/BE/daily helper rules and an isolated request guard reference have a native check script. The paper Entry/SL/TP/BE/news/session/reversal state machine lives in Python at this milestone. Broker request guards are in-memory reference infrastructure, not restart-safe and not wired to any send site. Native trade execution and execution parity are pending. No MetaEditor installation was found in the usual installed locations, so `.mq5/.mqh` compilation is unverified; Python checks do not establish MQL5 compilation.

## Graphify

`graphify-out/graph.html`, `graph.json`, `GRAPH_REPORT.md` map source rules, implementation and checks. This installed graphify version does not classify `.mq5/.mqh` as supported source; [native map](docs/NATIVE_CODE_MAP.md) documents their explicit relationships. Native internal calls are not represented as a verified language AST. Rebuild/update using graphify when the code/spec changes.

## Official platform references

Native history ordering and closed-bar access follow [CopyRates](https://www.mql5.com/en/docs/series/copyrates); quotes use the [MqlTick structure](https://www.mql5.com/en/docs/constants/structures/mqltick). Capture storage follows [FileOpen's file sandbox](https://www.mql5.com/en/docs/files/fileopen). See [MetaEditor compilation](https://www.metatrader5.com/en/metaeditor/help/development/compile) and [Strategy Tester behavior](https://www.mql5.com/en/docs/runtime/testing) for the next native validation milestone. Platform documentation does not supply missing strategy rules.
