# Explain and snapshots

How do I inspect a plan, compare data across engines and freeze a result?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/explain_and_snapshots/example.py
```

Expected output:

```text
polars explain names the columns: True
sql explain is a SELECT on orders: True
root: JoinRelNode on ibis-duckdb (bound)
root/left: ReadRelNode on ibis-duckdb (bound)
root/right: ReadRelNode on polars (bound)
transfer root/right: polars (bound) -> ibis-duckdb (bound)
same content, different engines: True
changed amounts: False
rows, snapshot vs live: 3 4
```

`explain()` describes a plan without running it. The recipe checks the shape of the engine text (Polars' plan and DuckDB's SQL), which varies between versions, and prints only the placement tree that mountainash itself writes when a join crosses engines. `fingerprint()` hashes the content, so the Polars and DuckDB copies of the orders compare equal and a copy with changed amounts does not. `snapshot()` evaluates the plan once: after a new order is inserted, the snapshot still counts 3 rows while the live relation counts 4.

Book: [Explain, fingerprint and snapshots](https://docs.mountainash.io/mountainash/chapters/08-collecting-results/#explain-fingerprint-and-snapshots). Next: [execution_targets_and_limits](../execution_targets_and_limits/).
