# Namespaces

How do I use string and date methods on a column?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/namespaces/example.py
```

Expected output:

```text
{'customer_id': 10, 'shout': 'AVERY', 'has_a': False}
{'customer_id': 11, 'shout': 'BLAKE', 'has_a': True}
{'customer_id': 12, 'shout': 'CASEY', 'has_a': True}
{'order_id': 1, 'year': 2026, 'renewal': '2026-02-05', 'label': '05 Jan 2026'}
{'order_id': 2, 'year': 2026, 'renewal': '2026-02-09', 'label': '09 Jan 2026'}
{'order_id': 3, 'year': 2026, 'renewal': '2026-03-02', 'label': '02 Feb 2026'}
```

`.str` and `.dt` group the string and date methods under a column, so `ma.col("name").str.to_uppercase()` and `ma.col("ordered_at").dt.add_months(1)` read the same on any backend. The script prints three customer rows and the first three orders with a year, a renewal date and a formatted label.

Book: [Strings and dates](https://docs.mountainash.io/mountainash/chapters/05-namespaces-aggregates-and-windows/#strings-and-dates). Next: [aggregates_and_windows](../aggregates_and_windows/).
