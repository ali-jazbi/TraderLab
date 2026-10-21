# Body80 checkpoint — 2026-10-21

Stopped active work at the owner's request to conserve usage. Implementation, archive census and technical validation are ready; the six-run Native comparison is NOT complete. No profitability conclusion is final.

- Base main: d4605858764508436b86679b57dad62f5f96ede2.
- Python: 278 tests passed. Offline Native: 219 checks passed. Four MQL sources compile with zero errors; TraderLab retains one existing version warning. Evidence: reports/body80-20261021/.
- Owner clarification: BOS candle precedes C2; Qualification retains the existing before-Break rule, and need not precede C2. Canonical §55 records this.
- Demo/real-order locks remain closed. Existing isolated Strategy Tester processes were left running locally; no live orders were enabled.
- Census and five chronological genuine examples: CORE_BODY80_20261021.fa.md and reports/body80-20261021/archive/. The undated M15 screenshot has no verified historical outcome.

## Local archives required to continue

These large raw archives, binaries and work files are ignored by Git and are NOT transferred by push. Copy them or use this computer to finish the study.

Baseline root:
C:/Users/mehdi/AppData/Local/TraderLabTesterArchives/POLBODY2110-738d65d0

Corrected Body80 root:
D:/Github/TraderLab/work/body80-native-archives/POLBODY2110-c4332c5d

The final driver log is work/body80-native-final-three.txt. At checkpoint, baseline training completed; baseline holdout and three new-mode runs were running, and holdout-BODY80_AGE120 was queued. Verify actual current process/status/report state before resuming. Do not launch duplicates. The driver follows replacement terminal PIDs by exact isolated executable path. Zero-byte runtime captures can remain buffered until completion.

Final protocol and exact inputs/binary hashes: reports/body80-20261021/protocol.json. Older initial-binary / launcher-restart attempts are excluded and preserved; never mix them into results. Final Native Body80 uses eight-decimal body normalization consistent with serialized OHLC; exact 8.0 price units passes.

## Remaining work

1. Finish all six fresh Native runs, with existing settings and real-tick Model 4. Do not tune parameters. Existing experimental FRESH_CONFIRMED/mask7 policy remains explicitly experimental.
2. After all six genuine reports are ready, run from the repository:

```powershell
python -m tools.report_body80_study D:/Github/TraderLab/work/body80-native-archives/POLBODY2110-c4332c5d --baseline-archive C:/Users/mehdi/AppData/Local/TraderLabTesterArchives/POLBODY2110-738d65d0 --out docs/reports/body80-20261021/native
```

The output case directories must be fresh. Investigate validation failures; never synthesize results or infer new PnL by deleting old trades. The tool checks actual deals, real ticks, input equivalence, detection/first-touch hashes and order locks.

3. Replace the pending Native section in CORE_BODY80_20261021.fa.md with actual comparison metrics and added/removed trades. No claimed outcome for the undated owner screenshot.
4. Refresh affected graph metadata if needed, validate changes and commit/push final evidence. Graph currently covers the eligibility implementation; small report-tool edits followed its last refresh.

Completed baseline training audit/performance snapshots are retained under reports/body80-20261021/checkpoint/ for reference only; they are not the finished six-run comparison.
