# Custom validation rule

How do I write a reusable check and run it on more than one backend?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/custom_validation_rule/example.py
```

Expected output:

```text
polars: [('status_at_most_2', 'failed', 1), ('status_at_most_3', 'passed', 0)]
duckdb: [('status_at_most_2', 'failed', 1), ('status_at_most_3', 'passed', 0)]
```

A reusable check is a plain function that returns a `RelationRule`, so no registration step is needed. The rule's plan uses the relation API to select the offending groups, and the runner reports a failure for each group it returns. The same rule objects run unchanged on a Polars frame and a DuckDB table, and both runs report the same summary.

Book: [Ingress handlers, units and rules](https://docs.mountainash.io/mountainash/chapters/22-extending-mountainash/#ingress-handlers-units-and-rules). Next: [examples index](../).
