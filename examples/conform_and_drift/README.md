# Conform and drift

How do I conform messy input to a schema and see what changed?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/conform_and_drift/example.py
```

Expected output:

```text
shape: (3, 4)
┌──────────┬────────┬─────────┬────────────┐
│ order_id ┆ amount ┆ status  ┆ ordered_at │
│ ---      ┆ ---    ┆ ---     ┆ ---        │
│ i64      ┆ f64    ┆ str     ┆ date       │
╞══════════╪════════╪═════════╪════════════╡
│ 1        ┆ 120.0  ┆ shipped ┆ null       │
│ 2        ┆ null   ┆ pending ┆ null       │
│ 3        ┆ 50.0   ┆ shipped ┆ null       │
└──────────┴────────┴─────────┴────────────┘
note discard
ordered_at null_fill
order_id MountainashDtype.I64 MountainashDtype.STRING discard_value
amount MountainashDtype.FP64 MountainashDtype.STRING discard_value
compatible: False
```

`conform()` casts the string columns to the declared types, discards the undeclared `note` column and adds the missing `ordered_at` column as nulls, as the contract dictionary says. The value `n/a` in `amount` fails conversion and becomes null. `collect_with_drift()` returns the typed frame and a drift report that lists the extra and missing columns and the columns whose source type differs from the declared type. The report works from schemas, so it lists `order_id` as a type mismatch even though every value converts.

Book: [ConformContract dimensions and presets](https://docs.mountainash.io/mountainash/chapters/11-conforming-data/#conformcontract-dimensions-and-presets) and [Drift reporting](https://docs.mountainash.io/mountainash/chapters/11-conforming-data/#drift-reporting). Next: [data_contracts](../data_contracts/).
