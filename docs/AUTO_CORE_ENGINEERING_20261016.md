# AUTO_CORE_DEMO independent engineering evidence — 2026-10-16

Continuation of `8dfd52c8ab7a8ac466dd2dee96701aba1bcd84d8` on `main`.
Status: **BLOCKED for automatic Demo submission**. Engineering checks below use
synthetic quotes and a compile-time mock transport inside the actual native Core
classes. They are neither a real-tick historical backtest nor broker execution.
No historical profitability or successful live-calendar coverage is claimed.

Machine-readable evidence: [engineering report](reports/auto-core-engineering-20261016.json).
Recorded compiler/runtime outputs are in `reports/auto-core-engineering-20261016/`.
Earlier audits, captures and delivery archives remain preserved.

## Completed independently of historical archives

| Request | Implementation and verification | Remaining limit |
|---|---|---|
| Persistent discovery and no duplicates | Ordered bar/tick WAL rebuilds BOS/FVG/OB trackers, frozen group membership, first returns and PARTIAL state; consumed setups and broker plans/intents have separate durable journals. Same-ms occurrence boundary resumes without duplicate entry. | Real-tick replay parity and recovery time/size need the missing archive. |
| Core entry and exit | Actual native Core pipeline discovers a synthetic group and dispatches two 0.01 legs through the existing gateway; BUY/SELL SL, TP1, TP2, shared-reference BE+5, deal costs and restarts checked. | Mock transport cannot prove MT5 Tester/broker fill behavior. |
| Failure handling | Second-leg rejection, timeout/unknown, partial fill, lost history, margin change, foreign exposure race, rejected/unknown emergency close, torn journals and missing journal members checked. Definitive rejected close can retry; ambiguous submissions never resend blindly. | Partial fills and unresolved single/BE-stop rules halt safely rather than inventing a strategy. |
| Trial limits | One new setup per session-day reserved durably before sending, total Core exposure plus proposed pair <=0.04, all foreign/manual positions and all pending orders veto entry. USD stop-risk/cost budget and margin rechecked at dispatch, including second leg. | No supplied risk/cost budget: production preset remains risk=0, cost reserve=-1 and rejects entry. |
| Forward calendar | Automatic primary BLS/Fed refresh, schema/completeness checks, actual fetch-completion timestamps, independently enforced V2 freshness, atomic publication, publisher locks, immutable generations, explicit Sydney/New York IANA DST. | Live local fetch got HTTP 403; no valid forward packet was published. Overlapping session-days remain blocked pending a rule. |
| FVG contradiction | Geometric and ordered native tests prove an interior touch changes UNFILLED to PARTIAL before the current entry gate; consumed first return remains consumed after replay/restart. | No permission for PARTIAL was added. No entry gate was relaxed. |
| Autonomous wrapper | Separate AUTO_CORE_DEMO, policy-labelled output, no operator package/Review/approve panel. Real/Contest, Reverse and non-LiteFinance Demo remain forbidden. Both Demo compile/init locks retained. | Deliberately cannot attach for automatic live/Demo submission yet. |

## Durable recovery contract

`RecoveryJournal.mqh` writes length, chained FNV32 checksum, UTF-8 payload and commit
marker, then FileFlush. This detects torn/corrupt/reordered frames, not malicious
tampering. Namespace includes account/server/symbol/magic/offset/policy/version;
the full scope is checked inside each journal, so filename-hash collisions cannot
silently mix accounts. Tester run identity additionally separates Tester runs.
Exclusive writer handles reject concurrent writers. None of these journals are
deleted, truncated, or silently repaired on restart.

The six-file recovery set is checked **before** constructors can create missing
files. A partially missing, zero-length or locked set blocks recovery. Completely
fresh state initializes once. Legacy candidate CSV layouts are preserved and
blocked rather than silently treated as a fresh day with no consumed setups;
they lack the input WAL needed for a faithful migration. An input journal lacking its committed baseline is
not accepted alongside pre-existing trade plans. Every gateway entry intent must
have its immutable Core plan; a missing plan cannot reset quota accounting.

Discovery persists the excluded startup boundary and each as-of closed bar/tick
before mutating detectors. Replay uses those original observations in original
order, with dispatch disabled; it never reselects membership using future bars.
Ten-following-closed-bar confirmation remains unchanged. Input replay reconstructs
first-return consumption even where later qualification cannot produce a trade.
Cursor restart retains the entire last millisecond and raw occurrence multiplicity.
Recovery is full event replay, **not** a bounded-time snapshot: disk size grows and
startup cost is O(record count). Measure this on the actual archive tomorrow.

Authoritative plan/intent WAL records are flushed before raw CSV diagnostics and
before any send. Torn diagnostic CSV no longer destroys recoverable trading state;
torn authoritative WAL halts. Broker positions and immutable deal receipts remain
the authority for fills/fees/BE/closures. Unknown acknowledgements are reconciled,
never treated as permission to resend. A failed second leg triggers compensation
and a persistent halt; the setup/day reservation is not released for another try.
Rejected compensation may retry only against an actually open position, under a
new durable close intent. Unknown compensation is never blindly retried.

Candidate non-news emergencies close its own magic positions; a foreign position
veto does not liquidate someone else's trade. The existing NEWS-01 scheduled-news
closure scope remains all account positions. Halt does not disable reconciliation
and emergency management. Ambiguous/incomplete states remain blocked across restart.

New log filenames do not overwrite previous journals. A resumed raw capture is a
**shard**, explicitly not a complete standalone historical capture; the auditor
rejects attempts to report it as one. Original shards must be retained together.

## Executed checks and their scope

- Targeted Python suite: **66 tests, 0 failures, 0 errors** (observed 0.497s).
  Modules: `test_calendar_service`, `test_auto_core_audit_v2`,
  `test_auto_core_capture_audit`, `test_experimental_auto`, `test_core_pipeline`,
  `test_operator_core_path`, `test_owner_oct12`. These include 13 new synthetic
  provider/calendar tests. The old full 187-test suite was not needlessly repeated.
- `AutoCoreIntegrationChecks`: **137 checks, 0 failures**, **65 synthetic transport
  requests** across entry/modify/compensation scenarios, **0 broker orders**.
  Run: `work/offline-native/ec32b5e044cf4fcaa624ce9e0f84a428`.
- `AutoCoreProcessRestartChecks`: **63 checks, 0 failures**, phases **47/6/5/5**
  across **four actual terminal processes**. One synthetic detected setup produces
  two opening requests and one BE modification (three total transport requests).
  TP exits are external fake-broker deal receipts, not additional order sends.
  Run: `work/offline-native/b4133f172f0948b3ab784662ae0e5342`.
- MetaEditor **5.0.0.6266**: seven units compiled, zero errors. AUTO_CORE_DEMO,
  StrategyChecks, DemoGatewayChecks, CorePipelineChecks and both new harnesses
  have zero warnings. TraderLab retains its existing version `0.10` Market-format
  warning. Compilation of old check scripts is not a claim of rerunning them.

The physical test destroys the terminal VM between phases. It snapshots **only
external synthetic broker state**; Core engine objects are not serialized by the
harness. Phase 1 discovers/finalizes a native group and opens the pair. Phase 2
restores membership and both positions, rejects duplicate return, receives TP1,
and moves the other SL to BE+5. Phase 3 restores the moved SL without another
modification and receives TP2. Phase 4 is flat and cannot resurrect the setup.
The separate integration suite also recovers a pre-entry group and checks
corruption, missing files and PARTIAL/return history.

`Checks/OfflineBroker.mqh` is reachable only from the check scripts. It replaces
account/quote/history/send calls at compile time. Production still has exactly
one real OrderSend site; the test transport is outside its include tree. The
runner copies a locally installed terminal executable and symbol definitions into
a fresh isolated folder, with login=0, unreachable server, live trading/DLLs off.
It copies no passwords, account databases or tick history. It never starts or
closes the user's existing trading terminal. Terminal binaries are **not** shipped.

Reproduction (local MetaTrader installation required):

```powershell
# Compile mt5/AutoCoreIntegrationChecks.mq5 and AutoCoreProcessRestartChecks.mq5
# with the local MetaEditor, then run the isolated fixtures:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/run_native_integration.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/run_native_integration.ps1 -ScriptName AutoCoreProcessRestartChecks
```

Synthetic execution is evidence of wiring/state transitions. It does not measure
slippage, liquidity, strategy expectancy, quote availability or historical fills.
**Historical Tester orders: none executed in this milestone. Profit/loss, win rate,
profit factor and drawdown: undefined.** Do not count mock sends as Tester orders.

## Forward calendar operation and failure evidence

Fixed official monthly BLS schedule and Federal Reserve calendar pages supply
CPI, Employment Situation/NFP and FOMC events. No third-party date guesses or
empty-news fallback. Both monthly coverage and categories must validate; changed
schemas, redirects, oversized responses and unscheduled events block publication.
Acquisition evidence stores source URLs, hashes and actual completion timestamps;
it does not claim historical as-of availability. The sourced session profile is
Sydney 07:00/New York 17:00 in their respective IANA zones, not fixed UTC offsets.
Python requires IANA timezone data (`tzdata` was available locally).

`tools/refresh_core_calendar.py` is an unattended publisher with explicit age and
refresh intervals (1 <= refresh < max age <=3600 seconds). A long-lived daemon lock
prevents two instances; transactional locks prevent concurrent replacement.
V2 packets carry fetched_at/fresh_until separately from session coverage. Native
Core checks TTL, source availability and day before entry and during service.
TTL is exclusive at fresh_until. Future/expired packets are rejected. Failed
refresh writes INVALID immediately, even while a preceding packet's TTL remains.
The engine blocks entries and performs existing emergency management on outage.

Atomic replacement never edits an active packet in place. Dated packet/manifest
generations and previous journals survive failures. The same day cannot change its
window. Non-overlapping weekday/weekend rollover works; overlapping day definitions
raise TODO_STRATEGY_UNRESOLVED rather than clipping a session or resetting quota.
Synthetic tests cover separate Sydney/New York DST transitions, weekend/expiry,
future packets, partial sources, schema changes, corrupt metadata, concurrent
publisher lock and overlapping/mutating day definitions.

Live local smoke check on 2026-10-16: **HTTP Error 403: Forbidden**; active output
became `INVALID|CALENDAR_SOURCE_UNAVAILABLE`. Failure evidence is retained. No live
forward packet passed validation. The ready launcher `tools/start_core_calendar.ps1`
takes an explicit MT5 data directory and age/refresh settings, starts in background,
and writes `MQL5/Files/AUTO_CORE_DEMO-forward.csv`, matching the locked preset. It
does not attach/unlock an EA and was not installed into the user's live terminal.
Changing the network/provider availability is a separate prerequisite, not a
reason to use an expired calendar or to wait for historical ticks.

## Strategy boundary and experimental assumptions

No SL/TP/BE/volume/ten-bar/FVG-minimum rule was changed to manufacture a trade.
EXPERIMENTAL `same_frame_earliest_qualified_equal_level_v1` remains explicitly
labelled: same-frame deterministic grouping, earliest as-of qualified membership,
and equal-level BOS deduplication. These are historical-only assumptions inherited
from the base candidate, not an approved replacement strategy. Membership freezes
as of qualification; future outcomes never select winners.

An exact FVG boundary touch can leave a gap UNFILLED while a price strictly inside
the gap necessarily changes it to PARTIAL before the current eligibility gate.
Native geometric/ordering tests cover both, including the same dispatch tick and
the consumed return after restart. Boundary fixtures prove a reachable technical
entry path; they are not evidence that real historical prices supplied that path.
No new PARTIAL permission, group policy or return revival was introduced here.

Unknown dollar budgets remain unknown. Synthetic fixture values (e.g. $30 risk and
$1 aggregate cost reserve) are test inputs only. Production never receives them.
Open stop risk includes existing own positions, proposed reserve and the supplied
aggregate cost/slippage reserve; actual closed NET includes broker deal costs.
This is an estimate, not a guarantee against gaps or fees beyond that reserve.
Margin/quote/spread/account/foreign-position checks remain mandatory at final send.

## What requires tomorrow's historical files only

1. Check hashes/completeness/chronology of the original real ticks and captures;
   restore the exact recorded test inputs, without another needless download.
2. Reproduce the original 688-group audit (686 rejected/two accepted) with per-group
   terminal blockers, confirmation time, first return, extremes and fill transition;
   compare the separately named equal-level hypothesis without future membership.
3. Run focused MT5 **Every tick based on real ticks / Model 4** on the existing
   period through the actual automatic Core gateway. Retain tester report,
   deals/orders/journals and inspect actual pair/SL/TP/BE/emergency evidence.
4. Measure replay parity, recovery cost, real executed order count and performance.
   If no trade exists, record the final blocker and undefined metrics; do not loosen
   rules. Synthetic results must never fill gaps in historical results.

## Separate blockers that historical files cannot resolve

- Local primary-calendar requests currently return HTTP 403; a valid unattended
  forward source must actually succeed before Demo can be considered ready.
- Explicit production USD risk/cost budgets are absent; no numerical defaults were
  guessed. The locked preset correctly blocks on them.
- PARTIAL permission, overlapping session-day ownership, single-position BE anchor
  and BE-stop counting remain unresolved where applicable; those branches halt.
- Historical validation and a deliberate subsequent lock review are still required.
  Synthetic passes alone do not authorize enabling Demo, Real, Contest or Reverse.

The delivery archive is a **review/test candidate with a locked preset**, not an
install-and-trade release. Source/evidence hashes and binary hashes are checked by
`tools/package_auto_core_candidate.py`; the manifest points to the committed source.
