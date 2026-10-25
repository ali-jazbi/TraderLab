# TraderLab

Latest execution fix: [Market closed no longer permanently halts unrelated opportunities](docs/MARKET_CLOSED_RECOVERY_20261025.fa.md).
The limited Native regression through May15 retained all prior fills and executed
four fresh positions after the rejection; Demo/Real locks remain closed.

Latest profitability evidence: [stopped long-history assessment: INSUFFICIENT_EVIDENCE](docs/LONG_PROFITABILITY_20261025.fa.md).
Twelve closed positions in five setup IDs yielded USD +30.93 from actual fill
prices before unrecovered commission/swap/fees. Execution halted May7 after
Market closed; tick ingestion through August is not active multi-month validation.
The [earlier frozen profitability assessment](docs/FINAL_PROFITABILITY_20261023.fa.md) remains separate.
Body80+M1 AGE120 was frozen and tested on October19–20 and21–22 with genuine
real ticks and full warm-up. No parameter was tuned from these outcomes.
The [earlier Body80 comparison](docs/CORE_BODY80_20261021.fa.md) retains its numbers,
but all three earlier Holdout data-quality claims were corrected: Agent logs
showed192 missing real-tick minutes despite the HTML label. Real remains forbidden;
Demo is restricted to forward evaluation and dispatch remains locked.

Current AUTO_CORE engineering status: [recovery, integrated native fault checks and
forward calendar service](docs/AUTO_CORE_ENGINEERING_20261016.md). The separate
automatic candidate has no operator selection/approval UI. Demo remains locked;
synthetic native integration is not a historical backtest or broker certification.

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

The fixture deliberately chooses values for unresolved policies to exercise the code. These are **synthetic modeling choices, not strategy approvals**. For example, its planned SL anchor, own-entry BE, empty news calendar, UTC day reset and London scan end are not production defaults. The 2026-10-11 amendment now confirms single Core/Reverse SL distance40 and directional Core reference+5/-5; it does not approve Bid/Ask or SL anchors. `configs/production.template.json` leaves these null, blocks dependent entries, and emits reasons.

Replay writes `events.jsonl` and `manifest.json`: input/config/code/spec hashes, event hash, open legs and closed daily USD result. Identical input/config/code yields identical bytes. The canonical-A fixture produces +38USD, the stopped version -18USD under the explicitly supplied synthetic100 contract and zero costs. These are regressions, not historical performance evidence.

## Native MT5 capture

See [First LiteFinance Demo capture](docs/FIRST_DEMO_CAPTURE.md) for the read-only attach checklist, time-offset verification, unique filenames, and capture validation steps. The EA records symbol/account capabilities and cannot place or manage orders.

```powershell
python tools/normalize_mt5_log.py work/TraderLab-run01.jsonl work/native-events.jsonl
python -m traderlab --events work/native-events.jsonl --config configs/production.template.json --out outputs/native-detection
```

MT5 captures now include wick-tip BOS and full reference-candle OB diagnostics. Automatic geometric relationships remain blocked by unapproved association/grouping; see [real historical diagnostic backtest](docs/AUTOMATIC_BACKTEST.md). Add sourced `setup`/`structure` annotations to an explicitly chronological input when exercising paper trading. Do not sort future confirmations backward or retroactively label first touches.

The EA implements native diagnostic detectors; selection/BE/daily helper rules and an isolated request guard reference have a native check script. The paper Entry/SL/TP/BE/news/session/reversal state machine lives in Python at this milestone. Broker request guards are in-memory reference infrastructure, not restart-safe and not wired to any send site. Native trade execution and execution parity are pending. On 2026-10-11 both MQL sources were actually compiled: TraderLab 0 errors/1 existing version warning, StrategyChecks 0 errors/0 warnings. Native script execution remains separately unverified.

## Graphify

`graphify-out/graph.html`, `graph.json`, `GRAPH_REPORT.md` map source rules, implementation and checks. This installed graphify version does not classify `.mq5/.mqh` as supported source; [native map](docs/NATIVE_CODE_MAP.md) documents their explicit relationships. Native internal calls are not represented as a verified language AST. Rebuild/update using graphify when the code/spec changes.

## Official platform references

Native history ordering and closed-bar access follow [CopyRates](https://www.mql5.com/en/docs/series/copyrates); quotes use the [MqlTick structure](https://www.mql5.com/en/docs/constants/structures/mqltick). Capture storage follows [FileOpen's file sandbox](https://www.mql5.com/en/docs/files/fileopen). See [MetaEditor compilation](https://www.metatrader5.com/en/metaeditor/help/development/compile) and [Strategy Tester behavior](https://www.mql5.com/en/docs/runtime/testing) for the next native validation milestone. Platform documentation does not supply missing strategy rules.
