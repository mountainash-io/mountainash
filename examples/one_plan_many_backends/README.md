# One plan, many backends

How do I run the same plan on Polars, pandas and a SQL engine?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/one_plan_many_backends/example.py
```

Expected output:

```text
polars: [{'region': 'east', 'revenue': 295.0}, {'region': 'north', 'revenue': 120.0}, {'region': 'south', 'revenue': 130.0}]
pandas: [{'region': 'east', 'revenue': 295.0}, {'region': 'north', 'revenue': 120.0}, {'region': 'south', 'revenue': 130.0}]
ibis-duckdb: [{'region': 'east', 'revenue': 295.0}, {'region': 'north', 'revenue': 120.0}, {'region': 'south', 'revenue': 130.0}]
```

`revenue_by_region` takes any source and builds the same plan each time. mountainash compiles it for the engine that holds the data: Polars, pandas through Narwhals, and DuckDB through Ibis. The three results are equal, and the script asserts it.

Book: [One logic, many engines](https://docs.mountainash.io/mountainash/chapters/01-what-mountainash-does/#one-logic-many-engines). Next: [dev_to_prod](../dev_to_prod/).
