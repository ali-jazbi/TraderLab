# First strategy-driven Demo trade

Automatic discovery: **BLOCKED**. The single missing association decision is:
**For this confirmed FVG/C3-or-C1 OB, which exact qualified BOS IDs form the complete
package, and when is that membership final?** Canonical §51.2 and §52.1 explicitly
leave this unresolved; wick containment alone supplies no selection/grouping rule.
The §51.4 chart gives prices without candle/timeframe identities and its lower Buy
OB cannot establish the preserved C3 mapping. No same-timeframe shortcut is approved.

Interim mode is **OPERATOR_APPROVED_CORE**, not automatic discovery. The operator
selects actual logged IDs and supplies their complete membership; detection, prices,
ten-following-bar availability, C3/C1 identity and exact first return remain mandatory.
Approval files cannot supply prices, fabricate signals, allow PARTIAL/FULL, revive a
consumed return or override broker/news/session/day/restart/review guards.

## Interface

Copy configs/core-operator-packages.example.csv into the active MQL5/Files directory.
Its header contains the exact broker symbol. Add rows in this format:

    PACKAGE|id|operator|approval_evidence|approved_UTC_epoch_seconds|FVG_ID|OB_ID|BOS_ID;BOS_ID

Use logged full IDs including their timeframe and UTC candle timestamp. OB_ID must
equal the selected FVG_ID plus :C3 for Buy or :C1 for Sell. Package ID is immutable,
alphanumeric, at most12 characters (broker comment identities). Approval must follow
all members' observed qualification and FVG confirmation. File receipt is recorded
with second precision; same-second eligibility is conservatively blocked. Missing,
malformed, changed or overlapping approvals block entry. The file reloads while the
existing EA runs, avoiding a restart/warmup reset.

Shortest supported execution branch: approved dual BOS package, distance >20 and
<=40 strategy pips, distinct levels, UNFILLED FVG and the genuine exact first return.
Shared dual BE is owner-confirmed. Single plans are reportable but submission remains
blocked on their unanswered BE anchor; this interface does not let an operator invent it.
Only a return at the current live drain tail with unchanged observed Bid/Ask can reach
the existing gateway. Older recovered returns and timer-only recovery are consumed.
Each selected BOS submits two0.01 legs through the existing sole send site, if enabled.

## Existing evidence and next actions

User-reported: CorePipelineChecks58/58 and native capture279320 ticks/nonhalted;
successful0.01 Demo smoke/AutoPilot opens/closes with10009. Local scripts and terminal
Journal confirm their existence and order confirmations. They are transport evidence,
not strategy signals and not imported or rerun.

Actual Core capture SHA2566dc73e240c26cc0969f4abaf78c3a0efaa69d44157deab40ef079fdacd22dd0f:
1172 pairs,909 consumed-return observations;885 PARTIAL/FULL,16 startup-history,
7 missed exact quotes,1 before confirmation. **Zero eligible UNFILLED exact returns
after confirmation; zero approved packages/trades.** No estimated trades or
profit are reported. Full local evidence:work/operator-original-core-review.json.

1. Install the updated existing EA/includes. Keep execution requested=false and lock
   false. Run the added package checks in CorePipelineChecks; no repeat smoke tests.
   This change adds13 native checks to the verified58; they are compiled, not yet
   executed in the terminal. Locally13 targeted Python package/safety tests passed.
2. On live Demo, approve one fresh dual UNFILLED package using real IDs before its
   first return. Set InpCoreOperatorPackages to that file. Require
   CORE_OPERATOR_PLAN_READY; inspect CORE_OPERATOR_FIRST_RETURN/dispatch reasons.
3. Supply the sourced calendar already required by CoreLifecycle, explicit magic,
   UTC offsets and positive news closure lead. Verify native reject/unknown/partial,
   TP1/BE and restart behavior for this Core route before activation. Both legs
   require the original observed return Quote; a changed second-leg Quote triggers
   incomplete-pair handling rather than a later-price substitution. Existing
   transport success does not certify this new strategy integration.
4. Separately review mt5/activation/CoreDemo.activation.patch (NOT applied). Only after
   that review, compile the Demo build, request execution explicitly and enable Algo
   Trading on verified Demo. Real/Contest/tester rejection remains unconditional.
   A new genuine eligible first return drives the trade; do not rearm old candidates.

The activation patch uses zero context; its dry-run was checked with
git apply --unidiff-zero --check. Applying it requires the same --unidiff-zero option.
