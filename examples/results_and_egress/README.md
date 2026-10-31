# Results and egress

How do I get rows out of a relation as dicts, dataclasses or Pydantic models?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/results_and_egress/example.py
```

Expected output:

```text
dicts: {'order_id': 1, 'amount': 120.0}
tuples: (1, 120.0)
columns: {'order_id': [1, 2, 3], 'amount': [120.0, 80.0, 50.0]}
dataclass: Order(order_id=1, amount=120.0, note=None)
dataclass with defaults: Order(order_id=1, amount=120.0, note='none')
pydantic: order_id='1' amount=120.0
```

`to_dicts()`, `to_tuples()` and `to_dict()` return plain Python rows or columns. `to_dataclasses` and `to_pydantic` build one object per row, matching columns to fields by name and dropping `customer_id`, which the plan already left out. A field with no column receives `None` (`note` in the first dataclass line) unless `apply_defaults=True` fills in the dataclass default, and Pydantic coerces `order_id` to the model's `str`.

Book: [Egress formats](https://docs.mountainash.io/mountainash/chapters/08-collecting-results/#egress-formats). Next: [python_data_in](../python_data_in/).
