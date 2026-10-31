# Develop locally, run in production

How do I test a plan on a small extract and run it on the full table?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/dev_to_prod/example.py
```

Expected output:

```text
dev:  [{'customer_id': 10, 'revenue': 120.0}, {'customer_id': 11, 'revenue': 80.0}, {'customer_id': 12, 'revenue': 200.0}]
prod: [{'customer_id': 10, 'revenue': 120.0}, {'customer_id': 11, 'revenue': 130.0}, {'customer_id': 12, 'revenue': 295.0}]
```

`customer_revenue` runs on a Parquet extract of the first four orders with Polars, then on the full `orders` table in a DuckDB file. DuckDB stands in for the production database here; the [support matrix](https://docs.mountainash.io/mountainash/chapters/16-backend-support-and-limits/#support-matrix) lists which SQL engines mountainash supports and their known limits. The dev result equals the prod result restricted to orders 1 to 4, so the logic you tested is the logic that runs.

Book: [Support matrix](https://docs.mountainash.io/mountainash/chapters/16-backend-support-and-limits/#support-matrix). Next: [many_sources_one_plan](../many_sources_one_plan/).
