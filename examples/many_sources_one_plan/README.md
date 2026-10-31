# Many sources, one plan

How do I combine a database table, a file and plain Python data?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/many_sources_one_plan/example.py
```

Expected output:

```text
shape: (3, 4)
┌────────┬─────────┬────────┬───────────┐
│ region ┆ revenue ┆ target ┆ on_target │
│ ---    ┆ ---     ┆ ---    ┆ ---       │
│ str    ┆ f64     ┆ f64    ┆ bool      │
╞════════╪═════════╪════════╪═══════════╡
│ east   ┆ 295.0   ┆ 250.0  ┆ true      │
│ north  ┆ 120.0   ┆ 100.0  ┆ true      │
│ south  ┆ 130.0   ┆ 150.0  ┆ false     │
└────────┴─────────┴────────┴───────────┘
transfer root/input/input/left/input/right: polars (bound) -> ibis-duckdb (bound)
transfer root/input/input/right: polars (bound) -> ibis-duckdb (bound)
```

One plan joins a DuckDB table, a CSV file read with Polars and a list of target dicts. mountainash runs every computing node in DuckDB and moves the Polars-side inputs there, and `explain()` lists those moves as `transfer` lines. The script asserts that no computing node runs anywhere else.

Book: [Operand transfer and owned copies](https://docs.mountainash.io/mountainash/chapters/09-execution-targets-and-capabilities/#operand-transfer-and-owned-copies). Next: [expressions](../expressions/).
