# What we built, compared to what's out there

The technical pages explain how mountainash works. These pages explain what we set out to change, and how the result sits next to the libraries it shares a space with: pandas, Polars, SQL embedded in Python, pandera, great_expectations, the orchestrators.

We don't claim mountainash is better at any of these tools' core competencies on their own runtime. We claim it's better at one specific thing: **keeping data logic portable across runtimes** so the choice of engine isn't a multi-month commitment.

## Where each page sits

| If the friction is… | Page | What we did about it |
|---------------------|------|----------------------|
| Writing the same logic twice — once in pandas/Polars, once in SQL for the warehouse | [Cross-backend execution](cross-backend.md) | Authored once. Compiled to whichever engine the call site needs. |
| Picking a DataFrame library and accepting the lock-in that comes with it | [Expressions](expressions.md) | A Polars-shaped API that lowers to Polars / pandas / Ibis — no rewrite when scale or destination changes. |
| Per-library DataFrame pipelines, often re-implementing the same chain in two engines | [Relations](relations.md) | One pipeline definition; the runtime is the terminal call. |
| Hand-writing cast/rename/null-fill blocks at every data-ingest boundary | [TypeSpec and conformance](typespec-conform.md) | A schema *is* the transformation. One definition; conform applies it. |
| Maintaining pandera schemas for dev, SQL `CHECK`s for prod, and Pydantic for the API — all describing the same fields | [Data contracts](datacontracts.md) | One contract, validated on any backend the relation API supports. |
| Reaching for Airflow/Prefect/Dagster for a five-step in-process pipeline | [Pipelines](pipelines.md) | A library-level pipeline framework that composes into relation code, with caching but no daemon. |
| Treating NULL as FALSE in filters because that's what SQL/pandas does, and chasing the resulting bugs | [Ternary logic](ternary-logic.md) | First-class TRUE/UNKNOWN/FALSE with explicit booleanization, not silent NULL propagation. |

## What this isn't

These pages aren't a takedown of pandas, Polars, Ibis, pandera, great_expectations, dbt, or any of the orchestrators. Every one of those tools is well-engineered, and most of them are better than mountainash at their core competency on the runtime they target. We're not trying to win on any single one of those axes.

What we're trying to win on is **portability of intent**. The cost of "we picked the wrong library three years ago" is what we set out to retire. Projects that don't pay that cost don't need this library.

## The trade-offs we made

Three honest costs come with the design:

1. **A small per-call overhead.** Compilation walks an AST. For interactive analysis on million-row frames it's invisible; for tight inner loops dispatching per record it isn't, and the right answer there is to drop into the backend directly.

2. **Alpha churn.** The package is not yet 1.0. Renames happen between minor versions. We catalog every intentional cross-backend divergence (≈ 94 entries today) so behavioural drift can't be silent, but API surface churn is still real.

3. **Coverage gaps.** Some operations aren't yet on every backend (Narwhals has the largest gap). The contract is: a clear error at the call site pointing at the catalog entry, never a silent wrong answer.

## Migration distance

The API shape is close to Polars on purpose. We picked Polars conventions because we think it has the cleanest expression model in Python, and adopting a familiar shape costs us nothing while reducing the migration distance for anyone already using it:

```python
# Before (Polars)
df.filter(pl.col("age") > 30).group_by("region").agg(pl.col("score").mean())

# After (mountainash)
ma.relation(df).filter(ma.col("age").gt(30)).group_by("region").agg(ma.col("score").mean()).to_polars()
```

The shape is nearly identical. The dividend isn't in any one line; it's in being able to swap `.to_polars()` for `.to_pandas()` (or `.execute()` on an Ibis backend) without re-authoring the rest.

---

Continue to a specific comparison:

- [Cross-backend execution vs. picking one library](cross-backend.md)
- [Expressions vs. per-library DSLs and embedded SQL](expressions.md)
- [Relations vs. per-library DataFrame pipelines](relations.md)
- [TypeSpec and conformance vs. hand-written schema code](typespec-conform.md)
- [Data contracts vs. pandera and great_expectations](datacontracts.md)
- [Pipelines vs. orchestrators for in-process work](pipelines.md)
- [Ternary logic vs. NULL-aware boolean reasoning](ternary-logic.md)
