# Ternary logic

How do I keep rows whose comparison is unknown instead of dropping them silently?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/ternary_logic/example.py
```

Expected output:

```text
plain filter    [1, 4, 6]
keep unknowns   [1, 3, 4, 6, 7]
flagged unknown [3, 7]
```

A plain `ma.col("amount") > 90` filter drops order 3, because a null amount never passes the test. Order 7 is a synthetic row whose amount `-1.0` is a sentinel code for "not recorded". `ma.t_col("amount", unknown={-1.0, None})` marks both values as unknown, and `t_maybe_true()` turns that three-valued result into a filter that keeps unknowns. The set replaces the default of `{None}`, so `None` stays in it to keep the null handled. `t_is_unknown()` flags orders 3 and 7 for a look.

Book: [Booleanization](https://docs.mountainash.io/mountainash/chapters/06-ternary-logic/#booleanization). Next: [joins_and_set_operations](../joins_and_set_operations/).
