# Aggregates and windows

How do I total per group and attach the group total to every row?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/aggregates_and_windows/example.py
```

Expected output:

```text
group_by
{'customer_id': 10, 'total': 120.0, 'amounts_seen': 1, 'orders': 2}
{'customer_id': 11, 'total': 130.0, 'amounts_seen': 2, 'orders': 2}
{'customer_id': 12, 'total': 295.0, 'amounts_seen': 2, 'orders': 2}
over
{'order_id': 1, 'customer_id': 10, 'customer_total': 120.0}
{'order_id': 2, 'customer_id': 11, 'customer_total': 130.0}
{'order_id': 3, 'customer_id': 10, 'customer_total': 120.0}
{'order_id': 4, 'customer_id': 12, 'customer_total': 295.0}
{'order_id': 5, 'customer_id': 11, 'customer_total': 130.0}
{'order_id': 6, 'customer_id': 12, 'customer_total': 295.0}
```

`group_by(...).agg(...)` collapses the orders to one row per customer, and `sum().over("customer_id")` keeps every row and adds the group total beside it. Sums skip the null amount, and `count` counts only present values while `count_records` counts rows. The script runs both plans on Polars and on an Ibis DuckDB table and asserts the results match.

Book: [Aggregates](https://docs.mountainash.io/mountainash/chapters/05-namespaces-aggregates-and-windows/#aggregates) and [Windows with over](https://docs.mountainash.io/mountainash/chapters/05-namespaces-aggregates-and-windows/#windows-with-over). Next: [ternary_logic](../ternary_logic/).
