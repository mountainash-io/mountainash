# Ternary logic

How do I keep rows whose comparison is unknown instead of dropping them silently?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/ternary_logic/example.py
```

Expected output:

```text
plain filter    [1, 4, 6]
keep unknowns   [1, 3, 4, 6]
flagged unknown [3]
```

A plain `ma.col("amount") > 90` filter drops order 3, because a null amount never passes the test. `ma.t_col` with `unknown={None}` marks the null amount as unknown, and `t_maybe_true()` turns that three-valued result into a filter that keeps unknowns. `t_is_unknown()` flags the rows that need a look. The two id sets differ by exactly order 3.

Book: [Booleanization](https://docs.mountainash.io/mountainash/chapters/06-ternary-logic/#booleanization). Next: [joins_and_set_operations](../joins_and_set_operations/).
