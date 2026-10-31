---
title: Ternary logic and unknown values
---

# Ternary logic and unknown values

Ternary expressions evaluate conditions to one of three values: TRUE, UNKNOWN or FALSE, stored as the integers 1, 0 and -1. A ternary condition built with the `t_` methods (`t_gt`, `t_eq`, `t_is_in`, `t_and`, ...) returns UNKNOWN when a value is null or matches a sentinel such as `-99999` that the data uses for "missing". A booleanizer then turns the three-valued result into an ordinary boolean, under a policy chosen at the point of use: strict, lenient, or "find the uncertain rows".

Assumes: [Three-valued logic](../01-what-mountainash-does/index.md#three-valued-logic) and [Building expressions](../04-building-expressions/index.md), in particular [Operators](../04-building-expressions/index.md#operators).

## Ternary columns and sentinels

<!-- concept:350 -->
`ma.t_col(name)` is a column reference for ternary work. With no further arguments it behaves like `ma.col(name)`: in a ternary comparison a null value gives UNKNOWN (0). Any expression can start a ternary chain; use `t_col` when a column has sentinels to declare.

<!-- concept:351 -->
`ma.t_col(name, unknown={...})` names the values that mean "unknown" in this column. A value in the set gives UNKNOWN in every ternary comparison on that column. The set replaces the default: once `unknown=` is given, null is UNKNOWN only if `None` is in the set, and otherwise a null makes the comparison FALSE.

```python
import polars as pl
import mountainash as ma

scores = pl.DataFrame({
    "score": [80, -99999, 60, None],
    "status": ["active", "N/A", "closed", None],
})

print(ma.relation(scores).with_columns(
    ma.col("score").t_gt(70).alias("col"),
    ma.t_col("score").t_gt(70).alias("t_col"),
    ma.t_col("score", unknown={-99999}).t_gt(70).alias("sentinel"),
    ma.t_col("score", unknown={-99999, None}).t_gt(70).alias("sentinel_null"),
).to_polars())
```

```text
shape: (4, 6)
┌────────┬────────┬─────┬───────┬──────────┬───────────────┐
│ score  ┆ status ┆ col ┆ t_col ┆ sentinel ┆ sentinel_null │
│ ---    ┆ ---    ┆ --- ┆ ---   ┆ ---      ┆ ---           │
│ i64    ┆ str    ┆ i32 ┆ i32   ┆ i32      ┆ i32           │
╞════════╪════════╪═════╪═══════╪══════════╪═══════════════╡
│ 80     ┆ active ┆ 1   ┆ 1     ┆ 1        ┆ 1             │
│ -99999 ┆ N/A    ┆ -1  ┆ -1    ┆ 0        ┆ 0             │
│ 60     ┆ closed ┆ -1  ┆ -1    ┆ -1       ┆ -1            │
│ null   ┆ null   ┆ 0   ┆ 0     ┆ -1       ┆ 0             │
└────────┴────────┴─────┴───────┴──────────┴───────────────┘
```

On a plain column, `-99999 > 70` is FALSE. Include `None` in the set (`unknown={-99999, None}`) whenever nulls should stay UNKNOWN. Relation methods return ternary results as raw integers (see [Booleanization](#booleanization)); their integer width depends on the backend (32-bit on Polars, 8-bit on Ibis).

<!-- concept:357 -->
`ma.always_true()`, `ma.always_unknown()` and `ma.always_false()` are constant ternary expressions, 1, 0 and -1 on every row. They are useful as defaults in a `when(...).then(...).otherwise(...)` chain and as neutral starting points when combining a variable number of conditions. They take part in booleanization like any other ternary expression.

```python
print(scores.select(
    true=ma.always_true().compile(scores, booleanizer=None),
    unknown=ma.always_unknown().compile(scores, booleanizer=None),
    false=ma.always_false().compile(scores, booleanizer=None),
).head(1))
```

```text
shape: (1, 3)
┌──────┬─────────┬───────┐
│ true ┆ unknown ┆ false │
│ ---  ┆ ---     ┆ ---   │
│ i32  ┆ i32     ┆ i32   │
╞══════╪═════════╪═══════╡
│ 1    ┆ 0       ┆ -1    │
└──────┴─────────┴───────┘
```

## Ternary comparisons and logic

<!-- concept:352 -->
Every comparison operator has a ternary form: `t_eq`, `t_ne`, `t_gt`, `t_ge`, `t_lt` and `t_le`, plus the membership tests `t_is_in` and `t_is_not_in` (see [Membership](../05-namespaces-aggregates-and-windows/index.md#membership)) and `list.t_contains` for list columns. Each returns 1 where the comparison holds, -1 where it does not, and 0 where either side is null or a declared sentinel. For membership, a null member also makes every non-match UNKNOWN, since the missing member might have matched. A null list row in `list.t_contains` is UNKNOWN as well.

<!-- concept:353 -->
`t_and`, `t_or` and `t_not` combine ternary values. With the encoding TRUE=1, UNKNOWN=0, FALSE=-1, AND is the minimum of its inputs, OR is the maximum, and NOT flips the sign. `t_xor` is TRUE when exactly one input is TRUE and UNKNOWN when any input is UNKNOWN; `t_xor_parity` tests for an odd number of TRUE inputs. `t_and`, `t_or` and `t_xor` accept several operands at once.

AND (`a.t_and(b)`):

| a \ b | TRUE (1) | UNKNOWN (0) | FALSE (-1) |
|---|---|---|---|
| TRUE (1) | TRUE | UNKNOWN | FALSE |
| UNKNOWN (0) | UNKNOWN | UNKNOWN | FALSE |
| FALSE (-1) | FALSE | FALSE | FALSE |

OR (`a.t_or(b)`):

| a \ b | TRUE (1) | UNKNOWN (0) | FALSE (-1) |
|---|---|---|---|
| TRUE (1) | TRUE | TRUE | TRUE |
| UNKNOWN (0) | TRUE | UNKNOWN | UNKNOWN |
| FALSE (-1) | TRUE | UNKNOWN | FALSE |

NOT (`a.t_not()`):

| a | TRUE (1) | UNKNOWN (0) | FALSE (-1) |
|---|---|---|---|
| result | FALSE | UNKNOWN | TRUE |

FALSE AND UNKNOWN is FALSE and TRUE OR UNKNOWN is TRUE: the known input already fixes the outcome, so the result is definite. Evaluating every pair of the `always_*` constants confirms these tables.

```python
score = ma.t_col("score", unknown={-99999, None})
status = ma.t_col("status", unknown={"N/A", None})

print(ma.relation(scores).with_columns(
    score.t_ge(70).alias("passed"),
    status.t_is_in(["active", "pending"]).alias("open"),
    score.t_ge(70).t_and(status.t_eq("active")).alias("both"),
    score.t_ge(70).t_or(status.t_eq("active")).alias("either"),
    score.t_ge(70).t_not().alias("failed"),
).to_polars())
```

```text
shape: (4, 7)
┌────────┬────────┬────────┬──────┬──────┬────────┬────────┐
│ score  ┆ status ┆ passed ┆ open ┆ both ┆ either ┆ failed │
│ ---    ┆ ---    ┆ ---    ┆ ---  ┆ ---  ┆ ---    ┆ ---    │
│ i64    ┆ str    ┆ i32    ┆ i32  ┆ i32  ┆ i32    ┆ i32    │
╞════════╪════════╪════════╪══════╪══════╪════════╪════════╡
│ 80     ┆ active ┆ 1      ┆ 1    ┆ 1    ┆ 1      ┆ -1     │
│ -99999 ┆ N/A    ┆ 0      ┆ 0    ┆ 0    ┆ 0      ┆ 0      │
│ 60     ┆ closed ┆ -1     ┆ -1   ┆ -1   ┆ -1     ┆ 1      │
│ null   ┆ null   ┆ 0      ┆ 0    ┆ 0    ┆ 0      ┆ 0      │
└────────┴────────┴────────┴──────┴──────┴────────┴────────┘
```

## Booleanization

<!-- concept:354 -->
Filters and most downstream code expect booleans in place of -1/0/1. A booleanizer maps a ternary result to `true` or `false`. `expr.compile(df)` applies one automatically to a ternary expression, using `"t_is_true"` by default: only definite TRUE becomes `true`. Pass `booleanizer=` to choose another, a callable that takes and returns an expression for a custom rule, or `None` to keep the raw integers. An expression that already ends in a booleanizer compiles as it is.

```python
passed = score.t_ge(70)
print(scores.select(
    raw=passed.compile(scores, booleanizer=None),
    default=passed.compile(scores),
    maybe_true=passed.compile(scores, booleanizer="t_maybe_true"),
    is_unknown=passed.compile(scores, booleanizer="t_is_unknown"),
))
```

```text
shape: (4, 4)
┌─────┬─────────┬────────────┬────────────┐
│ raw ┆ default ┆ maybe_true ┆ is_unknown │
│ --- ┆ ---     ┆ ---        ┆ ---        │
│ i32 ┆ bool    ┆ bool       ┆ bool       │
╞═════╪═════════╪════════════╪════════════╡
│ 1   ┆ true    ┆ true       ┆ false      │
│ 0   ┆ false   ┆ true       ┆ true       │
│ -1  ┆ false   ┆ false      ┆ false      │
│ 0   ┆ false   ┆ true       ┆ true       │
└─────┴─────────┴────────────┴────────────┘
```

!!! warning "Relations do not booleanize ternary results"
    `expr.compile(df)` is the one place that booleanizes automatically. Relation methods compile their expressions as they are, so a ternary expression passed straight to `relation.filter(...)` reaches the engine as an integer column, which the engine rejects. In `with_columns` and `select` the result stays as raw -1/0/1. In relation code, call a booleanizer method explicitly.

```python
try:
    ma.relation(scores).filter(passed).to_polars()
except Exception as exc:
    print(type(exc).__name__, exc)
```

```text
ComputeError filter predicate must be of type `Boolean`, got `i32`
```

The working pattern names the policy in the plan:

```python
print(ma.relation(scores).filter(passed.t_maybe_true()).to_polars())
```

```text
shape: (3, 2)
┌────────┬────────┐
│ score  ┆ status │
│ ---    ┆ ---    │
│ i64    ┆ str    │
╞════════╪════════╡
│ 80     ┆ active │
│ -99999 ┆ N/A    │
│ null   ┆ null   │
└────────┴────────┘
```

The same filter on a DuckDB table through Ibis keeps the same three rows:

```python
import ibis

con = ibis.duckdb.connect()
scores_db = con.create_table("scores", scores)
print(ma.relation(scores_db).filter(passed.t_maybe_true()).to_polars())
```

```text
shape: (3, 2)
┌────────┬────────┐
│ score  ┆ status │
│ ---    ┆ ---    │
│ i64    ┆ str    │
╞════════╪════════╡
│ 80     ┆ active │
│ -99999 ┆ N/A    │
│ null   ┆ null   │
└────────┴────────┘
```

<!-- concept:355 -->
There are six built-in booleanizers. Each is a method on a ternary expression and also a string accepted by `compile(..., booleanizer=...)`.

| Booleanizer | TRUE (1) | UNKNOWN (0) | FALSE (-1) | Selects |
|---|---|---|---|---|
| `t_is_true` (default) | `true` | `false` | `false` | Definite matches |
| `t_maybe_true` | `true` | `true` | `false` | Anything not ruled out |
| `t_is_false` | `false` | `false` | `true` | Definite non-matches |
| `t_maybe_false` | `false` | `true` | `true` | Anything not confirmed |
| `t_is_unknown` | `false` | `true` | `false` | Undecidable rows |
| `t_is_known` | `true` | `false` | `true` | Rows with a definite answer |

The choice decides where uncertain rows go. A strict data-quality rule that should pass only rows that clearly satisfy it uses `t_is_true`; a rule that should fail only rows that clearly break it uses `t_maybe_true`; `t_is_unknown` collects the rows to investigate.

<!-- concept:356 -->
Boolean and ternary expressions convert into each other automatically when they meet. A boolean expression passed to a ternary operator (`t_and`, `t_or`, `t_not`, `t_xor`) is wrapped with `to_ternary()`, which maps `true` to 1, `false` to -1 and null to 0. A ternary expression passed to a boolean operator (`&`, `|`, `and_`, `or_`) is wrapped with `t_is_true()`. The conversion happens while the expression is built, so every operator in the compiled plan receives operands in its own encoding.

```python
flags = pl.DataFrame({"active": [True, False, None, True], "score": [80, 90, 75, None]})

print(ma.relation(flags).with_columns(
    ma.col("active").eq(True).t_and(ma.col("score").t_gt(70)).alias("ternary_and"),
    ma.col("active").to_ternary().alias("active_t"),
    (ma.col("score").t_gt(70) & ma.col("active")).alias("boolean_and"),
).to_polars())
```

```text
shape: (4, 5)
┌────────┬───────┬─────────────┬──────────┬─────────────┐
│ active ┆ score ┆ ternary_and ┆ active_t ┆ boolean_and │
│ ---    ┆ ---   ┆ ---         ┆ ---      ┆ ---         │
│ bool   ┆ i64   ┆ i32         ┆ i32      ┆ bool        │
╞════════╪═══════╪═════════════╪══════════╪═════════════╡
│ true   ┆ 80    ┆ 1           ┆ 1        ┆ true        │
│ false  ┆ 90    ┆ -1          ┆ -1       ┆ false       │
│ null   ┆ 75    ┆ 0           ┆ 0        ┆ null        │
│ true   ┆ null  ┆ 0           ┆ 1        ┆ false       │
└────────┴───────┴─────────────┴──────────┴─────────────┘
```

In the last row, `score > 70` is UNKNOWN, so the boolean `&` sees it as `false` after `t_is_true`.

!!! warning "Bare boolean columns are not converted"
    Automatic conversion applies to operation results. Plain column references and literals pass through as they are. A boolean column used directly as a ternary operand is read as its storage value, so `false` behaves like UNKNOWN (0) and the results are wrong. Wrap the column with `.to_ternary()`, or compare it (`ma.col("active").eq(True)`), before using it in ternary logic.

```python
print(ma.relation(flags).with_columns(
    ma.col("active").t_and(ma.col("score").t_gt(70)).alias("bare"),
    ma.col("active").to_ternary().t_and(ma.col("score").t_gt(70)).alias("wrapped"),
).to_polars())
```

```text
shape: (4, 4)
┌────────┬───────┬──────┬─────────┐
│ active ┆ score ┆ bare ┆ wrapped │
│ ---    ┆ ---   ┆ ---  ┆ ---     │
│ bool   ┆ i64   ┆ i32  ┆ i32     │
╞════════╪═══════╪══════╪═════════╡
│ true   ┆ 80    ┆ 1    ┆ 1       │
│ false  ┆ 90    ┆ 0    ┆ -1      │
│ null   ┆ 75    ┆ 1    ┆ 0       │
│ true   ┆ null  ┆ 0    ┆ 0       │
└────────┴───────┴──────┴─────────┘
```

### Where the semantics are enforced

The ternary operations are ordinary function keys in the Mountainash extension namespace, so they pass through the same build, visit and backend layers as every other operation (see [How expressions compile](../18-expression-compilation/index.md)). Each ternary function key is classified as terminal (the six booleanizers, which return booleans) or non-terminal (comparisons, logical operators, `to_ternary`, `list.t_contains` and the `always_*` constants, which return -1/0/1). Two frozensets in the function-key enums module, `MOUNTAINASH_TERNARY_TERMINAL` and `MOUNTAINASH_TERNARY_NON_TERMINAL`, record that split; `compile()` uses it to decide whether to booleanize, and the API builders use it to decide when to convert between encodings. Sentinel sets travel as options on the comparison node, and each backend's ternary expression system (`expsys_pl_ext_ma_scalar_ternary.py`, `expsys_nw_ext_ma_scalar_ternary.py`, `expsys_ib_ext_ma_scalar_ternary.py`) turns them into a "null or sentinel gives 0" condition in native code. A new ternary operation belongs in one of the two sets, because booleanization and coercion recognise only the operations listed there.

[Validation](../13-validation/index.md) builds its rule outcomes on the same ternary expressions and booleanizers.
