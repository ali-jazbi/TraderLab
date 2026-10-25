# Long-history evidence: stopped, not a completed six-month test

The final assessment is [INSUFFICIENT_EVIDENCE](../../LONG_PROFITABILITY_20261025.fa.md).
`partial-price-performance.json` reconstructs 12 closed positions in five frozen
setup IDs from actual Native fill prices. USD +30.93 excludes unrecovered
commission, swap and fees. It is not net profitability or a Native final report.
Execution halted May 7 after Market closed; later tick ingestion through August
must not be represented as months of active trading.

`python tools/report_stopped_native_prices.py` reproduces the price accounting
from the committed trade extract, gateway journal and runtime broker capability.
`user-stopped-partial.json` records the interrupted run and local preserved raw
location. The large raw and journals remain local and are not deleted.

The broker coverage audit completed separately. It establishes observed real
ticks from January 2 through October 23, 2026, and rejects generated 2025 ticks.
Calendar, frozen-input and reproduction files document the attempted study;
their presence does not establish completion or PASS. The full-run reporter
remains completion-gated and was not used to certify this interrupted run.
