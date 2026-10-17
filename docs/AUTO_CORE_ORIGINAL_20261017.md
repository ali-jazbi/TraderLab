# Original-history Core investigation — 2026-10-17

Base: `b4dd6d8d03ed38b33e88d14d66fc5aed3b65adc9`, fast-forwarded on the original
development computer. Status: **automatic Demo BLOCKED**. No strategy, grouping,
execution permission or price rule was changed in this work.

## Original datasets recovered and verified

All four SHA256s match their previously stored reports exactly:

| Original `work/auto-core` file | Bytes | SHA256 |
|---|---:|---|
| auto-weeks-same-02.jsonl | 3,679,331,551 | 26151d557167edbcedaa822f926f0b4b8231290dd264ecf4139732d4636488e0 |
| auto-weeks-same-01.jsonl | 3,679,330,880 | d104c0523f309e9c7fb03a280337a2a8c2075cec29793b75c9592cd88e49c4b4 |
| auto-weeks-cross-02.jsonl | 3,681,273,962 | abbe8fc85bd3f7ab07dee2a9f1d8e3a9a4b3a9737d80b3c7666eabf7a814c2a8 |
| auto-oct07-same-01.jsonl | 185,854,537 | 4c08f178d63f218e01102666797d4638d9d7644ba13cb8c9b8414c56a821f5d3 |

Same-02 is the complete configured native baseline. Same-01/Oct07 lacked calendar
transport, and cross-02 lacks its JSON configuration proof: reuse their market
records, not unsupported trade-performance claims. Original captures, manifests,
reports and archives were not replaced. Before MT5 agent synchronization, its old
Files directory plus terminal Files/config/Profiles were copied to the new local
evidence directory; live Common journals are not used by the Tester candidate.

## Full-window investigation, not another Sep21–28 comparison

The original Sep21–Oct13 capture has 4,856,518 emitted ticks and 688 frozen FVG
packages. `tools/trace_original_core.py` reads them chronologically, freezes only
the recorded qualified members, checks qualification <= FVG availability, and
compares earliest-qualified equal-price representatives without looking at later
returns. Every returned Bid is checked against the actual recorded tick; Ask is
retained separately. Same-tick confirmation is allowed in diagnostic ordering;
consumed returns are never revived. This is a diagnostic replay, not an independent
Python broker simulator or a newly approved strategy.

Across accepted **and rejected** geometry: 408 member/FVG first-return relation
records occur after confirmation; 26 concern the selected extremes. These are not
408 unique opportunities or 26 missed executable orders. Of the 26 selected records,
24 cross without the exact quote; the two exact quotes have preexisting PARTIAL
or FULL. Both originally accepted groups have no selected return in the whole window.

Among **all** members, there are 78 exact-return relation records: 31 FULL→FULL→FULL,
28 PARTIAL→PARTIAL→PARTIAL, 18 UNFILLED-at-confirmation→PARTIAL-before-touch→PARTIAL,
and one PARTIAL→FULL→FULL. None has pre-touch UNFILLED at an exact eligible return.
Consequently both strict and authorized FIRST_TOUCH gates yield zero even before
broker submission. Equal-price deduplication alone adds no accepted geometry.

Review all groups in [CSV](reports/auto-core-original-20261017/original-groups.csv),
selected actual quotes in [CSV](reports/auto-core-original-20261017/selected-returns.csv),
and [diagnostic summary](reports/auto-core-original-20261017/diagnostic-summary.json).

## Specific later prices, not hypothetical entries

- Oct1 server05:01:14.732: actual Bid4156.41/Ask4156.63, M1 BUY reference4156.41.
  This is a real unconsumed return of a nonselected member. Its FVG was UNFILLED at
  confirmation but already PARTIAL before touch; the frozen extreme package also
  has an earlier consumed member. Selecting this candle afterwards would change
  membership using an outcome; it was not promoted or traded.
- Oct7 server17:32:13.071: M1 SELL reference4103.88; Bid4103.80→4103.95. Exact quote
  absent, FVG already PARTIAL, single BE unresolved. Crossing is consumed, not filled.
- Oct7 server21:07:05.153: M5 BUY reference4115.91; Bid4115.92→4115.90, FVG FULL.
  This cannot be restored by FIRST_TOUCH, later prices or a different fill estimate.

## Native verification

The full-window run **completed**, Model4, **100% real ticks**, 25m04.949s testing
time. [Official MT5 report](reports/auto-core-original-20261017/ORIG1710-82d48b4a5e.html),
[native audit](reports/auto-core-original-20261017/native-audit.json) and
[input fingerprints / runtime summary](reports/auto-core-original-20261017/native-report-summary.json).

| Observation | Stored strict native baseline | New FIRST_TOUCH native run |
|---|---:|---:|
| Emitted market ticks | 4,856,518 | 4,856,518 |
| Accepted experimental geometry groups | 2 | 2 |
| Opening deals / closed trades | 0 / 0 | 0 / 0 |
| Wins / losses | 0 / 0 | 0 / 0 |
| Win Rate / Profit Factor | undefined | undefined |
| Native account net change / maximum equity DD | 0 / 0 USD | 0 / 0 USD |

Zero account arithmetic is not a strategy-performance sample. Tester generated
4,856,519 ticks; exactly one accepted startup baseline occurrence is excluded.
All 4,856,518 ordered time_msc/Bid/Ask/last/volume records have the identical input
SHA256 `ca121261c6e97b55893b7dbc27725bb9e84774da16341e2f776e34c7f6e6f8ed`.
All 30,251 ordered closed-bar OHLC inputs also match, SHA256
`fe18b667f4b92fd2c4952cfc777b64b9e988a405d8846edae493a3810d9b5dc0`.
Both accepted group IDs and selected BOS IDs match the original baseline.
Controller/capture are nonhalted, cursor proof valid, ambiguities/CopyTicks errors0,
simulated dispatch enabled and actual broker dispatch locked. No entry reaches
pending dispatch, hence no broker-order rejection explains the zero-trade result.

The new run rejects686 groups: FULL253, PARTIAL238, consumed return81, single BE31,
distance>40pips42, distance<10pips5, no qualified contained BOS36. Of the original87
equal-level ambiguities,56 become consumed-return blocks,23 distance>40 blocks and8
single-BE blocks; **none becomes an additional accepted group**.

The stored strict native baseline is reused; it was not rerun. One new full-window
Model4 run uses the actual locked AUTO_CORE_DEMO, equal-level-v1 grouping and primary
FIRST_TOUCH (second-extreme permission OFF). Native completion evidence is collected
in the accompanying report. This is not a newly executed same-binary A/B: the old
baseline uses grouping1, the new candidate grouping3; the diagnostic records establish
which approved geometry is actually shared. Historical ex-post news and clipped DST
day-overlap remain explicitly experimental, with the prior test packet retained.
Risk cap1000 USD/test deposit and cost reserve0 are reused simulation inputs, never
production budgets or a claim of zero broker fees. Compile succeeded: 0 errors and
0 warnings. Four new diagnostic regression tests pass; previous infrastructure,
smoke, AutoPilot, integration and restart suites were not repeated.

All four original capture hashes were rechecked unchanged after the run. New raw,
all six journals, original Agent backup and terminal backups remain locally at
`C:/Users/mehdi/Documents/Codex/ORIG1710-82d48b4a5e/`; large raw/journal files are
not committed. The new capture SHA256 is
`de7b976f5267922c911c1407e6a67c49eb47ca8afc20bdb5d33743469afcf5da`.

## Minimum missing decisions

1. Define package membership/finalization algorithmically, including whether one
   already-consumed extreme vetoes the whole frozen group or only that BOS. No
   winner-based subset, new expiry or replacement alias was selected here.
2. Explicitly decide whether a non-FULL FVG may already be PARTIAL **before** its
   first BOS return, including prior confirmation fill versus approach-to-reference
   fill. The authorized same-tick permission answers neither case. This permission
   alone does not fix consumed membership, FULL gaps or missed exact quotes.

No single relaxed guard can truthfully guarantee a trade in these records. Automatic
Demo stays compile/init locked; Real/Contest/Reverse remain forbidden. No manual
operator-selection path, fabricated signals, fills, PnL or broker-order tests were added.
