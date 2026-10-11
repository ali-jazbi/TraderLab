# Automatic historical strategy diagnostics — 2026-10-11

## Implemented scope

Owner amendment §51 is authoritative: wick-tip BOS, full candle OB, directional five-pip entry reference, single Core/Reverse SL distance=40, no mandatory H4-first. Qualification and ten-following-closed-bar confirmation are preserved. Python and native detectors log confirmed/rejected candidates. Original PDFs were not accessible in the searched project, original workspace or supplied attachments.

`AutomaticRelationships` tracks actual closed-candle FVG validity on each FVG timeframe and deduplicates same-side/same-timeframe BOS-level containment pairs. It does not choose a cross-timeframe link, nearest/newest gap, significance ranking, BOS group, expiry or first-touch history before confirmation. These geometric relationships remain diagnostic-only, with explicit blockers. No automatic relationship is promoted to a paper setup while those decisions are unapproved.

Source annotations remain a separate, explicit paper-test interface. New BOS `level` annotations derive entry from the amendment; legacy `entry` annotations explicitly supply planned prices. Confirmed SL distances are fixed, but planned/filled anchors remain null in production. No strategy owner needs to repeat the resolved bounds, offset or distances.

## Real-data evidence

Input: existing `TraderLab-tester-normal-run01.jsonl`, 167,998,790 bytes, in the local MT5 tester agent MQL5/Files directory. Raw SHA-256 before/after normalization and replay:

`655dfbace606d7f2a6f71f9565915df9f7dd357b62673c536797a7425534c316`

Normalizer integrity preflight passed. The original raw file was neither changed nor committed. Only ignored `work/` derivatives were written. Explicit `XAUUSD_o -> XAUUSD` adapter preserves source broker metadata, original market prices, timestamps, order and same-ms tick occurrences.

| Measure | Count |
|---|---:|
| Genuine ticks | 279,320 |
| Closed bars, including initial warm-up | 1,875 |
| Big Candles confirmed / rejected | 218 / 1,557 |
| FVG geometry confirmed / rejected | 30 / 188 |
| FVG state at delayed confirmation: UNFILLED / PARTIAL / FULL | 3 / 13 / 14 |
| OB full reference candle bounds | 30 |
| BOS candidates qualified before a later strict break | 1,047 |
| BOS breaks rejected (unqualified or same-bar ambiguity) | 2,439 |
| Distinct geometric BOS/FVG relationship candidates | 303 |
| Fully confirmed automatic tradable setups | **0** |
| Blocked geometric relationship candidates | **303** |

Confirmed Big Candles by timeframe: M1=170, M5=35, M15=12, H1=1, H4=0. FVG/OB geometry: M1=16, M5=9, M15=4, H1=1, H4=0. A geometry event is not proof of a valid tradable FVG: 27 gaps became FULL by the end; 1 remained PARTIAL and 2 UNFILLED. BOS qualifications without a subsequent break remain pending; qualification count is 1,295, not 1,047 executed setups.

At relationship observation: 209 pairs had invalid FULL FVGs; 93 had unresolved PARTIAL policy; 1 had UNFILLED geometry. The latter 94 also lack approved association/grouping. 162 pairs additionally predate Big Candle/FVG availability and cannot reconstruct a past first touch. Counts of reasons overlap. Geometry can connect one BOS to several gaps; 303 is not a count of strategy setups or trades.

No historical paper entries were manufactured. No win rate or PnL is reported. Both independent diagnostic runs produced identical journal hash:

`7bf1811db99d2714fe4b7c1199d9b1dd5b341e3dee174052b687a0adbebd6737`

Normalized input SHA-256: `2b6b1d99b95f3007f790bc1bf9477d7225af8d9c4986934cfe4414f3fbdd2417`.

## Actual chart inspection examples

All times below are UTC. For this verified capture, MT5 server time = UTC+3; Tehran = UTC+3:30. Candidate time is candle open; availability is later and must not be moved backwards.

| TF / side | BOS candle open UTC | BOS level | Entry reference | FVG | OB | Relationship observed UTC | Status |
|---|---|---:|---:|---|---|---|---|
| M1 / BUY | 2026-10-07T03:10:00Z | 4141.82000000 | 4142.32000000 | 4139.60000000–4142.19000000 | 4142.19000000–4143.85000000 | 2026-10-07T03:36:00.045000Z | PARTIAL; diagnostic only |
| M5 / SELL | 2026-10-07T02:20:00Z | 4142.58000000 | 4142.08000000 | 4142.48000000–4145.22000000 | 4145.22000000–4147.05000000 | 2026-10-07T03:50:00.890000Z | FULL; diagnostic only |
| M5 / SELL | 2026-10-07T02:05:00Z | 4140.24000000 | 4139.74000000 | 4139.67000000–4141.76000000 | 4141.76000000–4143.04000000 | 2026-10-07T05:25:01.010000Z | UNFILLED; diagnostic only |

The owner's separate 4114 / [4111,4116] / [4104,4111] example is preserved in canonical §51.4, not inserted into this history. Its reference candle/timeframes are unavailable; it cannot prove a same-triple Buy C3 association.

## Remaining paper-entry blockers

1. Approved association and group membership/finalization, including timing/expiry and cross-timeframe linkage. Geometry alone is insufficient.
2. Bid/Ask trigger and invalidation quote side; planned versus filled SL anchors. Distance=40 and offset=5 are already resolved.
3. Partial FVG policy; <10/>40 distance branches; dual BE anchor.
4. Daily reset/profit/BE-stop accounting, historical news source and coverage, actual fees/slippage/TP-fill model and runtime capability configuration. Captured capabilities are facts, not policy approvals.
5. Reversal iFVG/BOS invalidation semantics, dual-parent reversal and stop counting; H1 and NY timing remain context-only.

## Reproduce offline

Use fresh output names; files/directories are intentionally not overwritten:

```powershell
Set-Location D:\Github\TraderLab
python tools/normalize_mt5_log.py '<tester-agent Files path>/TraderLab-tester-normal-run01.jsonl' work/new-normalized.jsonl
python tools/automatic_backtest.py --events work/new-normalized.jsonl --config configs/production.template.json --out work/new-automatic-diagnostics
python -m unittest discover -s tests -v
```

`summary.json` contains hashes, counts, timeframe breakdown and example observations; `events.jsonl` contains every candidate, rejection and blocked relationship with candle/availability timestamps and levels. Market-only diagnostics reject setup/structure annotations and omit profit metrics. Native versus Python full execution parity is not claimed.

## Exact next MT5 step

1. Copy the newly compiled `mt5/StrategyChecks.ex5` into the terminal Data Folder `MQL5/Scripts`, refresh Navigator and run it. Require `TraderLab native checks failures=0`. Compilation does not execute assertions.
2. Inspect the existing historical chart first: `XAUUSD_o`, M1, **2026-10-07 06:10 server time** (03:10 UTC), BOS high **4141.82**; qualification precedes break at **06:26:00.798** server time. FVG impulse is **06:25**, C3 **06:26**; FVG **4139.60–4142.19**, C3 OB **4142.19–4143.85**. Big Candle/FVG became available only at **06:36:00.045**, and the gap was PARTIAL. Annotate the intended associated candle/group on this actual chart; do not repeat the already resolved boundary/SL questions.
3. If visual historical playback is needed, detach the old EA before replacing its binary, install newly compiled `TraderLab.ex5` in `MQL5/Experts`, refresh Navigator. Ctrl+R: single local test, optimization off, XAUUSD_o, M1, Every tick based on real ticks, 2026-10-07 to 2026-10-08, Visual mode on. Inputs: `InpBrokerSymbol=XAUUSD_o`, `InpServerUtcOffsetSeconds=10800`, `InpTehranUtcOffsetSeconds=12600`, `InpTesterStress=false`, **fresh** `InpLogFile=TraderLab-strategy-diagnostic-20261007-run01.jsonl` (choose a different name if present). These offsets apply to the reviewed historical capture, not arbitrary dates.
4. Pause at the server times above and compare wick level, reference candle and availability. This EA remains detection/logging only; the visual run cannot produce strategy trades or a meaningful Tester profitability report. Further tick stress development is not required for this milestone.

## Verification

90 Python tests passed. Actual MetaEditor compilation: TraderLab 0 errors / 1 pre-existing Market version-format warning; StrategyChecks 0 errors / 0 warnings. Native script execution and new visual playback remain UNVERIFIED until performed in MT5. No tick-capture code, terminal binary or broker execution path was changed.
