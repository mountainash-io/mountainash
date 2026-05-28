# Ternary logic

Most boolean systems have two values: TRUE and FALSE. Real data has three: TRUE, FALSE, and "we don't know". Treating "we don't know" as either of the other two produces wrong answers — silently, and only on the records that matter most.

mountainash has first-class three-valued logic.

## What it is

A ternary expression takes one of three values:

| Value | Encoded as | Means |
|-------|-----------|-------|
| TRUE | `+1` | The condition is known to hold |
| UNKNOWN | `0` | We can't tell — typically because of missing input |
| FALSE | `-1` | The condition is known not to hold |

Encoding is a sentinel integer, not Python `None`. This is deliberate: NULL propagation in pandas, Polars, and SQL all have well-known footguns where `NULL == NULL` is `NULL`, not `True`, and where `NOT NULL` is `NULL`, not `True`. The sentinel encoding sidesteps the trap.

## Why this matters

Suppose you have a `score` column with some missing values, and you want to find records where the score is above 80.

In two-valued boolean systems with NULL propagation:

```python
df.filter(pl.col("score") > 80)
```

Records with NULL score are silently dropped. That's a particular semantics — it might be what you want. But if you ask "how many records did NOT have score > 80?", the answer excludes both the genuinely low scores and the missing scores, lumping them together.

In ternary logic, that condition produces UNKNOWN for the missing records. You can then choose what to do with them — explicitly:

```python
ma.t_col("score").gt(80).booleanize_unknown_as_true()    # treat unknowns as passing
ma.t_col("score").gt(80).booleanize_unknown_as_false()   # treat unknowns as failing
ma.t_col("score").gt(80).booleanize_strict()             # error on unknowns
```

The choice is at the point of decision, not absorbed into the operator.

## When to reach for it

Ternary logic earns its keep when:

- **Missing data is meaningful.** Healthcare, finance, insurance, regulatory reporting — anywhere "we don't know" is a different outcome from "no".
- **Rule systems combine many conditions.** A 20-clause rule with one UNKNOWN input should produce an UNKNOWN result, not silently flip to FALSE.
- **You need to distinguish "rule doesn't apply" from "rule fails".** A common bug class: treating "applicable: false" and "result: false" the same.

If your data is dense and missingness is rare or uninteresting, the two-valued world is fine. Don't reach for ternary as the default — reach for it when you need it.

## API

```python
import mountainash as ma

t = ma.t_col("score")                    # ternary column reference
t.gt(80)                                  # ternary comparison
t.and_(ma.t_col("age").lt(40))            # ternary AND
t.or_(ma.always_true())                   # ternary OR with always-TRUE
t.not_()                                  # ternary NOT
t.unknown_to_false()                      # coerce to bool, UNKNOWN → FALSE
t.unknown_to_true()                       # coerce to bool, UNKNOWN → TRUE
```

Special expressions:

- `ma.always_true()`, `ma.always_false()`, `ma.always_unknown()`
- `ma.t_col(name, unknown={value1, value2, ...})` — treats specified values as UNKNOWN on read

## Truth tables

### AND

| AND | TRUE | UNKNOWN | FALSE |
|-----|------|---------|-------|
| TRUE | TRUE | UNKNOWN | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN | FALSE |
| FALSE | FALSE | FALSE | FALSE |

### OR

| OR | TRUE | UNKNOWN | FALSE |
|----|------|---------|-------|
| TRUE | TRUE | TRUE | TRUE |
| UNKNOWN | TRUE | UNKNOWN | UNKNOWN |
| FALSE | TRUE | UNKNOWN | FALSE |

### NOT

| NOT | result |
|-----|--------|
| TRUE | FALSE |
| UNKNOWN | UNKNOWN |
| FALSE | TRUE |

These match Kleene's strong three-valued logic, the standard semantics used in SQL `NULL`-aware boolean reasoning — without the NULL-propagation footguns.

## Booleanization

Ternary expressions can be used directly where a boolean is expected (e.g. inside `.filter()`). When that happens, mountainash automatically inserts a booleanization step. By default, UNKNOWN is treated as FALSE. You can override with one of the explicit booleanizers above.

This is intentional: it should never be a quiet conversion. The default exists so common cases work without ceremony, but the explicit form is preferred in code that anyone else will read.

## Bidirectional coercion

A plain boolean can be lifted to a ternary expression for AND/OR composition:

```python
ma.t_col("a").and_(ma.col("b").gt(5))    # mixed; the boolean side is coerced to ternary
```

The coercion happens at the API builder layer, so the AST stays clean.

## Sentinel customisation

You can declare values that should be read as UNKNOWN:

```python
ma.t_col("status", unknown={"unknown", "n/a", "pending"})
```

This is the cleanest entry point for legacy data where "UNKNOWN" is encoded as a string sentinel rather than a missing value.

## Cross-backend

Ternary logic compiles to integer arithmetic on every backend. There is no NULL involvement in the runtime representation, so backend-specific NULL semantics don't apply. This is one of the few places mountainash deliberately *doesn't* lean on the upstream library's built-in semantics — because the built-in semantics are the problem.

## Related

- [Expressions](expressions.md) — ternary is one operation category among many
- Architecture principle: `d.ternary-logic/three-valued-semantics.md` (in the principles tree)
