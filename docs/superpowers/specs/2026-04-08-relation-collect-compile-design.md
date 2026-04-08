# Relation `collect()` / `compile()` Contract

**Date:** 2026-04-08
**Status:** Approved
**Related principles:**
- `c.api-design/build-then-collect.md`
- `c.api-design/build-then-compile.md` (expressions-side counterpart)

## Problem

`Relation.collect()` currently returns whatever `_compile_and_execute()` hands back. For a Polars `LazyFrame` source that is a `LazyFrame` — **not** a materialized result. Users must call `rel.collect().collect()` to actually get data, which breaks the "one syntax for all backends" promise.

`Relation.to_polars()` already guards against this:

```python
if is_polars_lazyframe(result):
    return result.collect()
```

So the author knew the hazard existed but fixed it only in `to_polars()`. Every other terminal (`to_dicts`, `item`, `count_rows`, the scalar aggregates) happens to route through `to_polars()` / `item()` and therefore sidesteps the bug. `collect()` itself is the only leaky path.

### Why tests missed it

No test asserts what `rel.collect()` returns when the source is a `pl.LazyFrame`. All existing relation terminal tests use `to_polars()`, `to_dicts()`, `item()`, `count_rows()`, or the scalar aggregates — every one of which materializes internally. `.collect()` on a lazy input is effectively untested.

## Design

### Semantics

| Method | Returns | Purpose |
|---|---|---|
| `rel.compile()` | Native backend **plan** (lazy where the backend is lazy) | Escape hatch — interleave native ops before materializing. Symmetric with `expr.compile(df)`. |
| `rel.collect()` | Native backend **materialized** result (always eager) | Default "give me the data" terminal. One syntax, all backends. |
| `rel.to_polars()` | `pl.DataFrame` | Unchanged externally. Becomes a thin wrapper over `collect()` + Polars coercion. |
| `rel.to_pandas()` / `to_dict()` / `to_dicts()` / `item()` / scalar aggregates | Unchanged | Already materialize via `to_polars()`; no behavior change. |

`compile()` and `collect()` form a symmetric pair with the expressions-side API:

- Expressions: `expr.compile(df)` → native expression, `df.with_columns(expr.compile(df))` executes.
- Relations: `rel.compile()` → native plan, `rel.collect()` → materialized result.

### Implementation

In `src/mountainash/relations/core/relation_api/relation.py`:

```python
def compile(self) -> Any:
    """Compile to a native backend plan without materializing.

    For lazy backends (Polars LazyFrame, Ibis) this returns the unexecuted
    plan — use it as an escape hatch to interleave native ops before
    calling collect(). For eager backends the result is already
    materialized and collect() is a no-op over it.
    """
    return self._compile_and_execute()

def collect(self) -> Any:
    """Execute the plan and return a fully materialized native result.

    Always eager: a Polars LazyFrame source returns a DataFrame, an
    Ibis expression returns an executed result, and so on. One syntax
    for all backends.
    """
    from mountainash.core.types import is_polars_lazyframe
    result = self.compile()
    if is_polars_lazyframe(result):
        return result.collect()
    return result
```

`to_polars()` simplifies to route through `collect()`:

```python
def to_polars(self) -> Any:
    from mountainash.core.types import is_polars_dataframe
    result = self.collect()
    if is_polars_dataframe(result):
        return result
    import polars as pl
    return pl.from_pandas(result.to_pandas())
```

No changes to other terminals, to `_compile_and_execute()`, to the visitor, or to `RelationDAG`. The fix is local to the `Relation` public terminal methods.

### Test coverage

Add `tests/relations/test_terminal_collect_compile.py` — a single home for the `collect()`/`compile()` contract across all backends.

Required assertions, parametrized across every backend source (Polars eager, Polars lazy, narwhals-pandas, narwhals-polars, Ibis DuckDB):

1. **`collect()` always returns a materialized type.** For every backend source, `type(rel.collect())` is the backend's eager type — never a `LazyFrame`, never an unexecuted `ibis.Table`.
2. **`compile()` returns the native plan type.** For Polars lazy source, `compile()` returns a `LazyFrame`. For Polars eager source, `compile()` returns a `DataFrame` (the backend had nothing to defer). For Ibis, `compile()` returns an unexecuted `ibis.Table`. For narwhals, `compile()` returns the underlying native frame.
3. **Round-trip equivalence.** `rel.collect()` and manually materializing `rel.compile()` produce equal results (frame-equal for DataFrames, value-equal for scalars).
4. **No double-collect required.** Specifically assert `rel.collect()` on a `pl.LazyFrame` source is a `pl.DataFrame`, not a `pl.LazyFrame`. This is the regression guard for the reported bug.

### Documentation updates

- `c.api-design/build-then-collect.md` — add one paragraph clarifying the `compile()` / `collect()` split and pairing it explicitly with `build-then-compile.md`.
- `src/mountainash/relations/core/relation_api/relation.py` module docstring — one-line statement of the contract.

### Scope / non-goals

- **Not** renaming `_compile_and_execute` — low-value churn.
- **Not** changing any terminal other than `collect()` (and `to_polars()` to route through it).
- **Not** touching `RelationDAG.collect()` — it uses the visitor directly and is unaffected.
- **Not** adding a `.lazy()` toggle or execution-mode flag.

## Risk

Low. The only user-visible behavior change is `rel.collect()` on a Polars `LazyFrame` source now returns a `DataFrame` instead of a `LazyFrame`. Any existing code doing `rel.collect().collect()` will break with a clear `AttributeError: 'DataFrame' object has no attribute 'collect'` — which is the correct surface, since that code was already relying on undefined, backend-inconsistent behavior.

No public API removals. `compile()` is additive.
