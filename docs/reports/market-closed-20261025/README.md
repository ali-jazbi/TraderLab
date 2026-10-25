# Limited Market closed regression

Engineering result: the definitive first-leg Market closed rejection no longer
permanently stops unrelated fresh opportunities. This is not a profitability
acceptance study or Demo activation.

- `limited-native-result.json`: actual closed positions/deals, costs, original
  fill-prefix comparison, rejection/no-retry proof and final controller state.
- `POLMCFIX2510-0669ccf6.html`: original completed MT5 report and adjacent PNGs.
- `native-audit.json`: strict completed-real-tick reconciliation, raw SHA256,
  actual deal timestamps and original dispatch/group evidence.
- `native-regression-log-extract.txt`: actual 10018 responses, no-retry recovery,
  initial deposit and Native completion evidence.
- `synthetic-native-result.json`: 198 isolated native fault/restart checks. Its
  85 injected transport calls are separate from the historical Tester deals.
- `frozen-parameter-and-source-audit.json`: unchanged strategy/preset evidence,
  with only log filename differing from the stopped historical run.

Measured April24–May15; warm-up April7. All 16 positions (including every prior
loss) and all 32 actual deals remain in the result. Net USD +60.41 includes
commission -0.80 and swap -1.78. Four positions entered after the rejection netted
+31.86. The first such entry was May8 03:10:41.860 broker server time. Both
rejected first touches belonged to different BOS IDs; neither was retried.

Final controller: not halted; simulated orders enabled; broker orders disabled;
compile dispatch lock closed. No end-of-test forced liquidations. Historical
broker fee/latency realism is not independently certified by this engineering
test. The earlier profitability verdict remains separate.

`reproduction/audit_limited.py` reads the preserved local archive identified in
`native-run-protocol.json`. From the repository root, reproduce with:

```
python -c "import runpy; runpy.run_path('docs/reports/market-closed-20261025/reproduction/audit_limited.py')"
```

It verifies the completed Native report and reconstructs all positions without
counting rejected plans as trades. The archive is required; its 7.27GB raw is not
stored in Git. Runner/storage scripts are session-specific provenance, depend on
the sealed existing local caches and compiled EA, and are not standalone setup
instructions. The superseded pre-measurement warm-up and all journals remain
preserved. `ntfs-storage-control.json` proves the stable raw prefix was unchanged
when transparent NTFS compression was removed from this run's output only.

Graphify was updated with scoped manually reviewed MQL/evidence pointers;
no full Graphify extraction or MQL AST verification is claimed.
