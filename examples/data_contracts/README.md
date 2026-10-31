# Data contracts

How do I declare a contract on a table and read the result for each check?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/data_contracts/example.py
```

Expected output:

```text
{'check_id': 'amount_positive', 'status': 'failed', 'pass_count': 5, 'fail_count': 1, 'unknown_count': 1}
{'check_id': 'order_id__not_null', 'status': 'passed', 'pass_count': 7, 'fail_count': 0, 'unknown_count': 0}
{'check_id': 'primary_key_unique', 'status': 'passed', 'pass_count': None, 'fail_count': 0, 'unknown_count': None}
{'check_id': 'shipped_has_amount', 'status': 'failed', 'pass_count': 6, 'fail_count': 0, 'unknown_count': 1}
{'check_id': 'shipped_has_amount_lenient', 'status': 'passed', 'pass_count': 6, 'fail_count': 0, 'unknown_count': 1}
{'check_id': 'status_enum_membership', 'status': 'failed', 'pass_count': 6, 'fail_count': 1, 'unknown_count': 0}
```

The `Orders` contract declares fields, a natural key and a status enum, and a `Validator` adds three rules. Each check gets one summary row, and the script leaves out the per-field type checks, which all pass. Order 7 fails `amount_positive` and the enum check, and the null amount on order 3 counts as unknown. `guarded` applies `shipped_has_amount` only to shipped orders; the default booleanizer treats the unknown on order 3 as a failure, and `t_maybe_true` accepts it in `shipped_has_amount_lenient`.

Book: [Rules and guarded rules](https://docs.mountainash.io/mountainash/chapters/12-data-contracts/#rules-and-guarded-rules). Next: [validation_rules](../validation_rules/).
