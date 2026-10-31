# First plan

How do I build a plan and collect the result?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/first_plan/example.py
```

Expected output:

```text
{'order_id': 1, 'amount': 120.0, 'amount_with_tax': 132.0}
{'order_id': 3, 'amount': None, 'amount_with_tax': None}
{'order_id': 5, 'amount': 50.0, 'amount_with_tax': 55.0}
```

`ma.relation` wraps the orders frame and each call (`filter`, `with_columns`, `select`, `sort`) adds a step to the plan without running anything. `to_dicts()` ends the plan, runs it on the data's own engine and returns one dict per row. The missing amount on order 3 stays missing after the arithmetic.

Book: [Filtering, selecting and sorting](https://docs.mountainash.io/mountainash/chapters/07-relations/#filtering-selecting-and-sorting) and [Collect and terminals](https://docs.mountainash.io/mountainash/chapters/08-collecting-results/#collect-and-terminals). Next: [one_plan_many_backends](../one_plan_many_backends/).
