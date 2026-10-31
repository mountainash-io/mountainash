# Python data in

How do I start a relation from Python records?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/python_data_in/example.py
```

Expected output:

```text
dicts [1, 2]
dataclasses [1, 2]
pydantic [1, 2]
{'order_id': 1, 'customer_id': 10, 'amount': 120.0, 'ordered_at': datetime.date(2026, 1, 5)}
```

`ma.relation` accepts a list of dicts, a list of dataclass instances or a list of Pydantic models and converts each to a Polars frame when the plan runs. The same filter and sort give identical rows from all three, which the script asserts. A dict of lists works too.

Book: [Relations from Python data](https://docs.mountainash.io/mountainash/chapters/07-relations/#relations-from-python-data). Next: [explain_and_snapshots](../explain_and_snapshots/).
