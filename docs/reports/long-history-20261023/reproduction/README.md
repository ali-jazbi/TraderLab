# Measurement sources, not production EAs

These files preserve the read-only Native coverage/calendar helpers and the
isolated run controls used for this study. They are outside the production EA
include tree. The frozen strategy EA was not rebuilt or modified.

- `NativeCoverageAudit.mq5`: no-order year request and monthly callback inventory.
  Native Agent logs establish the first real-tick date; callbacks in the earlier
  generated prefix are rejected. Callback counts alone cannot certify real ticks.
- `ReadOnlyNewsCalendarV2.mq5`: read-only USD calendar metadata export. Dated
  primary-source evidence in the parent directory establishes pre-event knowledge.
- `ServerHistoryMetadata.mq5`: bar-series metadata, which cannot establish Tick age.
- `prepare_six_month.py`: dated source reconciliation and unchanged session-calendar
  preparation before any long-study strategy outcomes. Do not run over sealed
  evidence; use a new workspace and fresh output directory for another study.
- `run_native_coverage.ps1` and `run_six_month.ps1`: original isolated launch
  configurations. Paths, account identifiers, cache provenance and hashes are
  specific to the preserved local experiment. Encrypted account config is omitted.
- `adopt_native_watch.ps1`: supervision-only handover to avoid the original
  six-hour timeout. It suspends only the verified original PowerShell watcher,
  never the Native terminal/agent, and preserves the same uninterrupted run.
  Process IDs are session-specific; this is an archival record, not a reusable
  command to run blindly. The Native EA, account and parameters stay unchanged.
- `uncompress_current_raw.py`: removes transparent NTFS compression only from the
  current growing raw file to reduce measured kernel overhead. It checks a fixed,
  already-written prefix hash before/after, never suspends/restarts Native and
  does not rewrite journal contents. The archive records the exact operation,
  Microsoft documentation, matching hashes and a conservative dispatch check.

The `*.compile.txt` results apply only to data helpers. They are neither a new
strategy compile nor evidence of profitability. Existing attempts and raw logs
are retained locally, including failed/timed-out read-only probes.

After the Native terminal completes and `native-files` is collected, use the
repository tool `python -m tools.report_long_profitability <archive> --out <fresh>`
for strict data quality, frozen inputs, deal costs, setup/month accounting and
calendar checks. Large raw JSONL and broker caches stay in the local archive.
