# Ternary logic vs. NULL-aware boolean reasoning

## What we built this to address

Consider a `score` column with some missing values, and a filter like:

```python
df.filter(pl.col("score") > 80)
```

The likely intent is "records with high scores". The actual result is "records with high scores that weren't missing" — records with missing scores are silently dropped, because `NULL > 80` is `NULL`, and `NULL` is falsy in a filter context.

The corrected form is more verbose:

```python
df.filter((pl.col("score") > 80) | pl.col("score").is_null())
```

…to keep the missing ones. But for the inverse — "records that did *not* meet the threshold" — there are three reasonable readings:

```python
df.filter(~(pl.col("score") > 80))                                   # drops nulls
df.filter(pl.col("score") <= 80)                                     # also drops nulls
df.filter(pl.col("score").is_null() | (pl.col("score") <= 80))       # keeps them as "didn't meet"
```

There isn't a single right answer. The right answer depends on whether "we don't know" should be lumped with "didn't meet" or treated as its own case. We think the standard libraries make the wrong default choice here: the simple form silently drops, and the explicit form is opt-in.

In SQL, the situation is famous. `WHERE score > 80` excludes NULLs; `WHERE NOT (score > 80)` also excludes NULLs; the two together cover fewer rows than the universe. Generations of analysts have rediscovered this and produced wrong answers from it.

In pandas, the situation has been messier still — NaN, `None`, `pd.NA`, and missing-by-omission have all had different semantics at different points in the library's history.

## How we approach it

Three-valued logic at the column reference, and an explicit choice of how to collapse to boolean at the decision point:

```python
import mountainash as ma

result = (
    ma.relation(df)
      .filter(ma.t_col("score").gt(80).unknown_to_false())   # missing → didn't meet
      .to_polars()
)
```

The three values — TRUE, UNKNOWN, FALSE — are encoded as sentinel integers (+1, 0, −1). NULL is not in the runtime representation, so NULL propagation traps don't fire. The booleanization step (`unknown_to_false()`, `unknown_to_true()`, or strict) is explicit and named, so a reader of the code knows which choice was made.

We don't make the choice for the caller. The library's contribution is making the choice visible.

## Side-by-side

```python
# Polars / pandas / SQL: NULL propagation
df.filter(pl.col("score") > 80)
# Silently drops NULL-score rows. A reader has to know this.

# Polars / pandas with explicit handling
df.filter((pl.col("score") > 80).fill_null(False))
# Works, but the .fill_null(False) is easy to omit, and the default is a footgun.

# mountainash, explicit ternary
ma.relation(df).filter(ma.t_col("score").gt(80).unknown_to_false())
# A reader knows: missing scores are being treated as "didn't meet".

ma.relation(df).filter(ma.t_col("score").gt(80).unknown_to_true())
# Or: missing scores are being treated as "met". Different semantics, named differently.
```

The win isn't that mountainash makes one choice; it's that the choice is in the code, named, at the point it happens.

## When combining many conditions

The pain compounds when conditions combine. A 20-clause rule with one UNKNOWN input should produce an UNKNOWN result, not silently flip to FALSE. In a standard two-valued system, the silent flip is the default behaviour.

```python
# Two-valued, default
result = (
    (pl.col("age") > 18)
    & (pl.col("income") > 50000)        # NULL income makes this NULL
    & (pl.col("region") == "valid")
)
# NULL-income records: silently dropped.
```

```python
# Ternary
result = (
    ma.t_col("age").gt(18)
    .and_(ma.t_col("income").gt(50000))   # UNKNOWN income → UNKNOWN clause
    .and_(ma.t_col("region").eq("valid"))
    .booleanize_strict()                  # raise if any UNKNOWN remains
)
# NULL-income records: surface as a runtime error, not silently dropped.
```

The strict booleanizer is the one rule-engine authors usually want. The default in the library world is the silent one. We think the defaults are wrong, and we let callers opt out of them at the type-system level.

## Where this earns its keep

- **Healthcare, finance, insurance, regulatory reporting.** Anywhere "we don't know" is a distinct, meaningful outcome.
- **Rule systems where many conditions combine.** The default-silent-flip bug is the largest source of incorrect rule evaluation we've seen.
- **Code that uses `.is_null() | ...` defensively.** The defence is the smell; ternary is the fix.

## Where ternary isn't the right tool

- **Dense data with rare or uninteresting missingness.** The two-valued world is fine.
- **A codebase that has already audited every filter and trusts how NULLs flow.** The audit is the equivalent. Ternary makes the audit a property of the code rather than a property of the developer.

## Why the runtime representation matters

Ternary expressions in mountainash compile to integer arithmetic on every backend. NULL is not involved at runtime. This is one of the few places we deliberately don't defer to the upstream library's semantics — because the upstream library's NULL semantics are the problem we set out to route around.

The implication: ternary logic works identically on Polars, pandas (via Narwhals), and Ibis. The footguns those libraries have around NULL propagation in boolean contexts simply don't apply, because the ternary path doesn't use their NULL-aware booleans.

## On pandas' `pd.NA` and Polars' explicit null handling

Both are real improvements over the historical situation. `pd.NA` propagates NULL through boolean ops correctly (NULL & False is False; NULL | True is True; NULL == NULL is NULL). Polars has explicit `.is_null()` and `.fill_null()` and treats the case more consistently than legacy pandas.

What neither gives:

- An **explicit, named** booleanization step. `.fill_null(False)` still has to be remembered at the right call site.
- A **separate sentinel** so that "UNKNOWN" can be distinguished from "value-that-happens-to-be-the-default".
- A **consistent behaviour across backends** without re-checking each library's NULL semantics.

For a single-Polars codebase whose authors have internalised the explicit-NULL discipline, ternary is a smaller win. For cross-backend work or rule-engine work, the win is large.

## What this costs

- **A different mental model.** Engineers familiar with two-valued logic need to learn the three truth tables (AND, OR, NOT) once.
- **A separate column reference type.** `ma.t_col(...)` vs. `ma.col(...)`. The distinction is the point — it's an opt-in to the more careful semantics — but two reference types coexisting in the same codebase has a small cognitive cost.

## Related

- Technical: [Ternary logic](../features-technical/ternary-logic.md)
- Comparison: [Expressions](expressions.md)
