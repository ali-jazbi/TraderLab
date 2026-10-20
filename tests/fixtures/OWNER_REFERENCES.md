# Owner reference cases

Append a case to `owner-reference-cases.json`; the data-driven tests discover it.
For a BOS supply `kind=bos`, stable `id`, `side`, actual closed `bar`, broker
`tick_size`, `owner_expected`, `rule_expected` and provenance. A matched label
uses `alignment=MATCHED`; unresolved feed/OHLC contradictions stay explicit as
`OHLC_LABEL_CONFLICT`, never a candle-specific implementation override.
`owner_expected` is human feedback; `rule_expected` is the testable directional
shadow predicate. They must not be silently substituted for each other.
For FVG supply the three actual `candles`, `owner_expected` and exact `zone`.
Keep genuine timing/context/tick evidence when available; synthetic edge tests
are separately labelled in the test code. Approximate OB/SL feedback is metadata,
not execution configuration. Never derive new expected labels from profit/loss.
