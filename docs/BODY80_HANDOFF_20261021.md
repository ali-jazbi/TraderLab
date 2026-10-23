# Body80 checkpoint — 2026-10-21

Quality correction, 2026-10-23: mechanical reconciliation below does not establish
real-tick-only data. The Agent logs of all three Holdout runs explicitly record
192 missing real-tick minutes and fallback generation. Their outcomes are retained
diagnostically. `reports/final-profitability-20261023/prior-data-quality-audit.json`
supersedes the previous quality claim; the current strict audit rejects fallback.

The original October 21 checkpoint is retained below. Completion on October 23 supersedes its pending status: all six fresh Native runs and their strict reconciliation passed. See CORE_BODY80_20261021.fa.md and reports/body80-20261021/native/comparison.json. Demo remains locked.

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

## Resume on the home computer — 2026-10-23

Local and remote main both resolve to `91497ad9e19cd11748f6488bfce39daa920ce41f`.
The old Body80 raw archives are unavailable here. September/October XAUUSD_o tick
caches and the LiteFinance terminal configuration exist under the current user's
MetaQuotes data directory. All six cases must be rerun together in a fresh batch;
do not combine fresh runs with the old training checkpoint.

Fresh verification: 278 Python tests passed; baseline d460585 AUTO_CORE_DEMO,
current AUTO_CORE_DEMO, CoreEligibilityChecks and StrategyChecks compiled with
zero errors and zero warnings. Current TraderLab compiled with zero errors and
its one existing version warning. The isolated offline CoreEligibilityChecks
script passed 219 checks, exactly matching the committed numerical evidence.
Compile logs and numerical runtime evidence are in
`reports/body80-20261021/resume-20261023/`. These checks are neither simulated
Tester orders nor historical performance. Demo locks remain closed.

The launcher now accepts TerminalData, TerminalInstall and CalendarFile overrides;
its default history follows TerminalData. The default calendar is the committed
holdout-calendar.csv (SHA256
`537c38d7a502c882d94277ef2e16947445ba2597eb18e2c75a1c24d62e724985`).
This retains the existing explicitly experimental calendar; it is not new live
calendar approval. No strategy or execution parameter was changed.

The first local attempt, `D:/TraderLabTesterArchives/POLBODY2110-4c3fdb0a`, stopped
during history copying because the main terminal held XAUUSD_o/2026.hcc exclusively.
No isolated Tester case started and no result is available. The partial archive
is preserved; the next attempt must use a fresh batch. The main terminal was left
running. Close it before copying history, then run from the repository:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/run_body80_study.ps1 -ArchiveParent D:/TraderLabTesterArchives -TimeoutSeconds 7200 -Parallel 3 -FirstPort 3400
```

The current and baseline binaries have already been compiled locally. Baseline
source is an exact git archive of d460585's mt5 tree in work/body80-baseline.
Monitor the driver until all six cases finish, then audit the new batch with
tools.report_body80_study; preserve original protocol.json and store new binary,
input and archive provenance separately. No final profitability result exists yet.

After the owner closed the main terminal, fresh batch
`D:/TraderLabTesterArchives/POLBODY2110-86b0dd17` started successfully. Driver log:
`work/body80-resume-20261023/driver-fresh.txt`. Three training cases are running;
the three holdout cases are queued. A complete six-case input/binary/calendar
protocol is retained in `reports/body80-20261021/resume-20261023/protocol.json`.
Every non-log input matches the original committed protocol. Verify current
processes and reports before any restart; this paragraph records launch state,
not final outcomes.

## Completed fresh comparison — 2026-10-23

All six runs in POLBODY2110-86b0dd17 completed and passed reconciliation. The raw archive remains at D:/TraderLabTesterArchives/POLBODY2110-86b0dd17; it is outside Git. Published reports, plans-derived performance, tick/closed-bar fingerprints, detection proofs, runtime lock evidence and actual trade differences are under reports/body80-20261021/native/. All six binaries match the fresh protocol. Training BASELINE includes two end-of-test liquidations totaling +4.70 USD within its +32.11 USD net; these are finite-horizon Tester exits, not TP/SL. All other cases have zero end-of-test liquidations. Current work is complete; earlier running/queued paragraphs are launch history. Original unavailable archives and the first partial local copying attempt were not reused or deleted.
