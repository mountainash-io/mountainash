# Validation rules

How do I run row, scalar and relation rules and check a foreign key?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/validation_rules/example.py
```

Expected output:

```text
{'check_id': 'amount_non_negative', 'check_kind': 'row', 'status': 'failed', 'pass_count': 5, 'fail_count': 1, 'unknown_count': 1}
{'check_id': 'largest_order_under_500', 'check_kind': 'scalar', 'status': 'passed', 'pass_count': None, 'fail_count': None, 'unknown_count': None}
{'check_id': 'order_id_unique', 'check_kind': 'relation', 'status': 'passed', 'pass_count': None, 'fail_count': 0, 'unknown_count': None}
{'check_id': 'amount_non_negative', 'outcome': 'unknown', 'order_id': 3, 'value': None}
{'check_id': 'amount_non_negative', 'outcome': 'fail', 'order_id': 7, 'value': '-5.0'}
foreign key passes: False
{'check_id': 'orders_customer', 'outcome': 'fail', 'order_id': 7, 'customer_id': 99}
```

`ValidationRunner.validate_relation` runs a `RowRule`, a `ScalarRule` and a `RelationRule` and returns a summary row for each. The row rule reports one failure (order 7) and one unknown (order 3, null amount), and `resolve_identity` labels each failure case with its `order_id`. `validate_dag` then checks a `ForeignKeyRule` from orders to customers, and the one orphan, order 7 with customer 99, is the only failure case.

Book: [Check IR and rule kinds](https://docs.mountainash.io/mountainash/chapters/13-validation/#check-ir-and-rule-kinds) and [Foreign keys](https://docs.mountainash.io/mountainash/chapters/13-validation/#foreign-keys). Next: [datapackage_dag](../datapackage_dag/).
