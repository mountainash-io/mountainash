# Migrating `is_in` / `t_is_in` — membership unification (item 60)

As of the membership-unification release (a breaking change on top of `0.2.0`,
landing **immediately with no deprecation period**), set-membership tests
(`is_in`, `is_not_in`, `t_is_in`, `t_is_not_in`) are one concept with two null
treatments, and an **ambiguous collection argument now raises at build time**
instead of ever compiling to a silently-wrong result.

## Why it changed

`col.is_in(other_col)` was ambiguous: did you mean "is this scalar one of the
values in a *set*" or "is this value a member of each row's *list* column"?
Different backends resolved that ambiguity differently — Polars raised, pandas
returned all-`False`, and Ibis silently substring-matched. There was no
schema-free way to tell the two apart, so the call is now **rejected at build**
and you state which one you mean explicitly.

`is_in` and `t_is_in` are the same membership test; they differ only in how they
treat unknowns: `is_in` returns a plain boolean (unknown → `False`), `t_is_in`
returns a three-valued result (`TRUE=1` / `UNKNOWN=0` / `FALSE=-1`) and
`is_in ≡ booleanize(t_is_in)` under `t_is_true` on every accepted shape and
backend.

## What now raises at build

A bare expression as the whole collection, a scalar column, `ma.lit([...])`, an
empty collection, a nested collection, or a raw backend-native expression as a
member each raises a typed error from
`mountainash.expressions.membership.errors` **when you build the expression** —
never at compile/collect, and never a wrong value.

| Old (now a build error) | Error | Do this instead |
|---|---|---|
| `col("x").is_in(col("tags"))` — per-row list membership | `BareExpressionCollectionError` | `col("tags").list.contains(x)` (boolean) or `col("tags").list.t_contains(x)` (null-aware ternary) |
| `col("x").t_is_in(col("tags"))` | `BareExpressionCollectionError` | `col("tags").list.t_contains(x)` |
| `col("x").is_in(scalar_col)` — "equals this column" | `BareExpressionCollectionError` | `col("x") == scalar_col` |
| `col("x").is_in(ma.lit([1, 2, 3]))` | `BareExpressionCollectionError` | pass the collection directly: `col("x").is_in([1, 2, 3])` |
| `col("x").is_in([pl.col("a"), pl.col("b")])` — native members | `NativeExprMemberError` | wrap each member: `col("x").is_in([ma.col("a"), ma.col("b")])` |
| `col("x").is_in([])` | `EmptyMembershipError` | provide at least one value |
| `col("x").is_in([[1, 2], [3, 4]])` | `NestedCollectionError` | flatten, or use a list-column op |

## Migration by intent

### "Is this scalar one of a fixed set of values" — unchanged

```python
col("x").is_in([1, 2, 3])          # boolean, unknown → False
col("x").is_in(1, 2, 3)            # variadic form, identical
col("x").t_is_in([1, 2, 3])        # ternary: TRUE / UNKNOWN / FALSE
col("x").is_in([ma.col("a"), ma.col("b")])   # members may be expressions
```

Custom unknown sentinels are honoured per member:

```python
col("x").is_in([ma.t_col("a", unknown={-999})])   # a -999 in column a → UNKNOWN
```

### "Is this value a member of each row's list column" — now explicit

```python
# OLD (ambiguous, backend-dependent, removed):
col("x").is_in(col("tags"))

# NEW — boolean per-row membership:
col("tags").list.contains(x)

# NEW — null-aware ternary per-row membership (null list row OR null/unknown
# needle → UNKNOWN(0); otherwise TRUE(1)/FALSE(-1)):
col("tags").list.t_contains(x)
```

`.list.t_contains()` is new. On Polars and Ibis it compiles directly; on
Narwhals a dynamic (expression) item is rejected at build (NW-LIST-01) and a
literal item is supported on the polars-backed path.

### "Does this column equal that column" — use `==`

```python
# OLD:  col("x").is_in(scalar_col)
# NEW:
col("x") == scalar_col
```

## Null semantics (three-valued)

For `members = ["b", None]` and `needle = "a"`:

| Op | Result | Note |
|---|---|---|
| `t_is_in` | `UNKNOWN (0)` | a `None` member makes non-matches unknown, not false |
| `t_is_not_in` | `UNKNOWN (0)` | the SQL `NOT IN (…, NULL)` trap — never a confident `TRUE` |
| `is_in` | `False` | ternary `UNKNOWN` booleanises to `False` |
| `is_not_in` | `False` | likewise — **not** `True`, matching SQL `NOT IN` with a NULL |

This is the SQL-correct behaviour: `x NOT IN ('b', NULL)` is never `TRUE`.

## See also

- Principle: `arguments-vs-options.md` — §"Set-Membership Collection Arguments"
- `col("tags").list.contains()` / `col("tags").list.t_contains()` for per-row
  list membership.
