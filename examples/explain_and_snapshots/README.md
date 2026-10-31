# Explain and snapshots

How do I inspect a plan, compare data across engines and freeze a result?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/explain_and_snapshots/example.py
```

Expected output:

```text
polars plan:
  FILTER col("amount") > 90.0
  FROM
    DF ["order_id", "customer_id", "amount"]; PROJECT["order_id", "amount"] 2/3 COLUMNS
sql plan:
  SELECT
    "t0"."order_id",
    "t0"."amount"
  FROM "memory"."main"."orders" AS "t0"
  WHERE
    "t0"."amount" > 90
same content, different engines: True
changed amounts: False
rows, snapshot vs live: 3 4
```

`explain()` shows Polars' optimised plan for a Polars source and the SQL for a DuckDB source, without running either. `fingerprint()` hashes the content, so the Polars and DuckDB copies of the orders compare equal and a copy with changed amounts does not. `snapshot()` evaluates the plan once: after a new order is inserted, the snapshot still counts 3 rows while the live relation counts 4.

Book: [Explain, fingerprint and snapshots](https://docs.mountainash.io/mountainash/chapters/08-collecting-results/#explain-fingerprint-and-snapshots). Next: [execution_targets_and_limits](../execution_targets_and_limits/).
