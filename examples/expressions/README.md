# Expressions

How do I compute, branch, cast and handle nulls in a column expression?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/expressions/example.py
```

Expected output:

```text
{'order_id': 1, 'with_tax': 132.0, 'size': 'large', 'whole': 120, 'mid_open': True}
{'order_id': 2, 'with_tax': 88.0, 'size': 'small', 'whole': 80, 'mid_open': True}
{'order_id': 3, 'with_tax': None, 'size': 'small', 'whole': 0, 'mid_open': None}
{'order_id': 4, 'with_tax': 220.0, 'size': 'large', 'whole': 200, 'mid_open': False}
{'order_id': 5, 'with_tax': 55.0, 'size': 'small', 'whole': 50, 'mid_open': False}
{'order_id': 6, 'with_tax': 104.5, 'size': 'small', 'whole': 95, 'mid_open': True}
```

Operators, `ma.when(...).then(...).otherwise(...)`, `is_between`, `fill_null` and `cast` build expressions that `select` evaluates on every row. The missing amount on order 3 stays missing through the tax arithmetic and the range test, falls to `small` in the condition, and becomes 0 after `fill_null` and the cast. `alias` names each output column.

Book: [Operators](https://docs.mountainash.io/mountainash/chapters/04-building-expressions/#operators) and [Casting, cast safety and nulls](https://docs.mountainash.io/mountainash/chapters/04-building-expressions/#casting-cast-safety-and-nulls). Next: [namespaces](../namespaces/).
