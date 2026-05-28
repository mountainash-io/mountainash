# Cross-backend execution

mountainash compiles a single expression tree or query plan to whichever backend you are using, without you choosing the backend at authoring time.

## The backends

| Backend | What it executes on | Why you'd pick it |
|---------|---------------------|-------------------|
| **Polars** | `pl.LazyFrame` (native Polars expressions, lazy by default) | Speed; most complete operation coverage; the reference backend |
| **Narwhals** | pandas DataFrames or PyArrow tables under a Narwhals wrapper | You already have pandas/PyArrow data and you don't want to convert |
| **Ibis** | Any Ibis-supported SQL engine: DuckDB, SQLite, Postgres, BigQuery, Snowflake, … | Push the compute into a real database; reuse warehouse infrastructure |

You do not choose at authoring time. You write:

```python
import mountainash as ma

result = (
    ma.relation(df)
      .filter(ma.col("amount").gt(100))
      .group_by("region")
      .agg(ma.col("amount").sum().alias("total"))
      .to_polars()
)
```

If `df` is a `pl.DataFrame`, this runs on Polars. If it's a pandas DataFrame, it routes through Narwhals. If it's an Ibis table, it builds SQL and pushes it to whichever engine that table is connected to. The expression is identical in all three cases.

## How dispatch works

When you call a terminal operation (`.to_polars()`, `.to_pandas()`, `.collect()`, `.execute()`), the visitor:

1. Detects the backend from the input frame's type.
2. Walks the expression / relation tree.
3. For each node, looks up its function key and calls the corresponding method on the backend's implementation class.
4. The backend method returns a native expression. The visitor composes them.

There is no eval loop, no interpretation, no shadow execution. The output of compilation is whatever the native library would have produced if you'd written it yourself. The CPU cost of the abstraction is the tree walk — typically a few hundred microseconds for a non-trivial expression — and nothing else.

## Cross-type joins

You can join across backend boundaries:

```python
polars_left  = pl.DataFrame({"id": [1, 2], "x": [10, 20]})
pandas_right = pd.DataFrame({"id": [1, 2], "y": [100, 200]})

ma.relation(polars_left).join(pandas_right, on="id", how="inner").to_polars()
```

One side is coerced. By default, the coercion target is the backend that produced the left input; you can force a target with `execute_on=`.

## What's the same across backends

The intent. Operations have the same logical semantics on every backend:

- A `filter` keeps rows for which the predicate is `TRUE`.
- A `sum` aggregates non-null values.
- A `cast("integer")` produces the same integer for the same input.
- A `join("inner", on=…)` produces the same rows.

This is the contract. It is enforced by ~3,000 cross-backend tests that check, for the same input, all backends return the same output.

## What can differ

Some operations cannot be made identical without paying unacceptable cost. We track and document every such case rather than silently allowing it.

### Known divergences

The full catalog lives in [`docs/known-divergences.md`](https://github.com/mountainash-io/mountainash/blob/develop/docs/known-divergences.md). It has ≈ 94 entries across categories: string ops, datetime, math, type system, relational ops, aggregates, window, lists, casting, intervals.

Each entry has:

- **ID**: stable identifier (`IB-STR-04`, `NW-DT-12`, etc.).
- **Backends affected**: specific list, not "Narwhals" but `narwhals-pandas` vs `narwhals-polars`.
- **Root cause**: one of `upstream_bug`, `upstream_feature_gap`, `parameter_width`, `by_design`.
- **Workaround**: usually a clear error message or a strict `xfail`.
- **Status**: open, investigating, by design, or closed (when the upstream fix landed).

The discipline is: if your code hits an unsupported case on a specific backend, you get a friendly error pointing at the limitation — not a silently incorrect answer.

### Parameter-width restrictions

A common class of divergence is that some upstream libraries accept literals where mountainash accepts expressions. For example, Polars' `str.replace` requires a literal substring on the pattern argument — you can't pass a column reference. mountainash will let you write it, but the call site will fail with an error that names the specific limitation and links to the divergence entry.

This is intentional: we'd rather you discover the limit at the call site than have us silently re-implement what the upstream library is missing.

## Adding a new backend

Backends are composed from a set of `Protocol` implementations. Adding a backend means implementing the protocol surface — typically a dozen mixins covering scalar / aggregate / window / relational categories. The wiring-verification test suite ensures you can't ship a backend with a missing method.

The architecture is laid out so that adding **DataFusion** or **Spark** (via Substrait or Ibis) is structurally a matter of writing the implementation, not modifying the AST. See the [vision](../vision.md) for where this is going.

## Tests prove it

Every operation has cross-backend tests:

```python
@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_sum(backend):
    df = _fixture_for(backend)
    out = (
        ma.relation(df)
          .group_by("k")
          .agg(ma.col("v").sum().alias("s"))
          .to_polars()
    )
    assert _values(out, "s") == [10, 20, 30]
```

If we add a new operation without cross-backend coverage, CI fails. If a backend silently starts diverging, CI fails. If an upstream library lands the fix for an `xfail`'d operation, CI fails (and we get to close a divergence entry).

This is the closest we know how to come to "the same code, the same answer, on any of these engines" while still being honest about the cases where the engines disagree.

## Related

- [Expressions](expressions.md) — column-level operations
- [Relations](relations.md) — DataFrame-level operations
- [Vision](../vision.md) — long-term backend roadmap
