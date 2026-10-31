# Execution targets and limits

How do I choose where a join runs, and what happens when a backend refuses an operation?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/execution_targets_and_limits/example.py
```

Expected output:

```text
default placement:
root: JoinRelNode on ibis-duckdb (bound)
root/left: ReadRelNode on ibis-duckdb (bound)
root/right: ReadRelNode on polars (bound)
transfer root/right: polars (bound) -> ibis-duckdb (bound)
execute_on='right':
root: JoinRelNode on polars (bound)
root/left: ReadRelNode on ibis-duckdb (bound)
root/right: ReadRelNode on polars (bound)
transfer root/left: ibis-duckdb (bound) -> polars (bound)
result types: ibis polars
refused: [ibis] Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported.
dialect and parameter: ibis-duckdb seed
rows per draw under a narrower policy: {5}
seed honoured (draws identical): False
```

A join runs at its left input by default, so the DuckDB table stays in DuckDB and the Polars customers move there. `execute_on="right"` flips the placement, and `explain()` prints the node locations and the transfer. Exact-count sampling with a seed is refused on Ibis, and the script prints the `BackendCapabilityError` message. The refusal gate is classed as unclassified, so a `ma.capability_policy` that protects only the availability class does not cover it and the call runs. The cost is that the seed is no longer honoured: twenty runs give different rows, so use a narrower policy only when you accept what the refusal protected.

Book: [Execution targets and locations](https://docs.mountainash.io/mountainash/chapters/09-execution-targets-and-capabilities/#execution-targets-and-locations) and [Capability errors and capability_policy](https://docs.mountainash.io/mountainash/chapters/09-execution-targets-and-capabilities/#capability-errors-and-capability_policy). Next: [table_schemas](../table_schemas/).
