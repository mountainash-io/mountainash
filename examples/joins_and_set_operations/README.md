# Joins and set operations

How do I join two relations, find unmatched rows and stack relations?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/joins_and_set_operations/example.py
```

Expected output:

```text
inner [1, 2, 3, 4, 5, 6]
left  [1, 2, 3, 4, 5, 6, 7]
semi  [1, 2, 3, 4, 5, 6]
anti  [7]
left, order 7 name: [None]
semi columns: ['order_id', 'customer_id', 'amount', 'status', 'ordered_at']
concat rows: 9
concat order ids: [1, 2, 3, 4, 5, 6, 7, 101, 102]
```

The inner join keeps the six orders whose customer exists, and the left join keeps all seven, with a missing name on order 7 because customer 99 is not in the customers table. The semi join returns the orders that have a match and keeps only the order columns, while the anti join returns the order that has none. `ma.concat` stacks two relations with the same columns into one plan, here the seven orders plus re-numbered copies of the first two.

Book: [Joins](https://docs.mountainash.io/mountainash/chapters/07-relations/#joins) and [Combining relations](https://docs.mountainash.io/mountainash/chapters/07-relations/#combining-relations). Next: [results_and_egress](../results_and_egress/).
