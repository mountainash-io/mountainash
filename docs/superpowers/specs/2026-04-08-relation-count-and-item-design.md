# Relation `count_rows()` and `item()` — Design

**Date:** 2026-04-08
**Status:** Design / approved for planning
**Scope:** Two new terminal operations on `mountainash.relations.Relation`. No new node types, no new visitor methods, no protocol changes.

## Motivation

A downstream rules-engine rewrite needs to express three patterns concisely:

```python
# How many rows does this filtered result have?
count = relation(df).filter(...).count_rows()

# Pull a single cell out of a one-row result
value = relation(df).filter(...).head(1).item("__t_specificity")

# Existence check
if relation(df).filter(...).count_rows() == 0:
    raise KeyError(...)
```

Both terminals are standard in every DataFrame library — Polars, Pandas, Ibis, Narwhals all expose row-count and scalar-extraction operations natively. Mountainash currently has neither on `Relation`. The closest existing terminals are `to_polars()` / `to_dicts()` (full materialisation, then count or index manually) and `head(n)` (limit, then materialise). Neither is a clean fit for "give me a row count" or "give me one cell".

The audit confirmed: **`pydata.egress` does not provide either operation either** — egress only handles "convert the materialised result to a Python collection". This is a genuine new addition, not a discoverability gap.

The downstream consumer (`RuleResult` in the rules engine) becomes backend-agnostic with these two methods landed:

```python
class RuleResult:
    @property
    def count(self) -> int:
        return relation(self._df).count_rows()

    def explain(self, rule_name: str) -> dict[str, int]:
        rel = relation(self._df).filter(ma.col("rule_name").eq(ma.lit(rule_name))).head(1)
        if rel.count_rows() == 0:
            raise KeyError(f"Rule '{rule_name}' not found")
        return {dim: rel.item(f"__t_{dim}") for dim in self._active_dimensions}
```

Zero backend-specific code in `RuleResult`. Every method goes through `mountainash.relations`.

## What already exists

| Concept | Lives in | Notes |
|---|---|---|
| Terminal operations | `relation_api/relation.py` — `collect`, `to_polars`, `to_pandas`, `to_dict`, `to_dicts`, `to_tuples` | All compile via `_compile_and_execute()` |
| `head(n)` | `relation_api/relation.py:170` | Builds a `FetchRelNode` |
| Aggregate function `count` | Wired through six layers per the wiring matrix | All 3 backends already implement it |
| `AggregateRelNode` | `relation_nodes/substrait/` | Handles single-column aggregates and group-by aggregates |
| `_compile_and_execute()` | `relation_api/relation_base.py` | Detects backend, walks the tree via the visitor |

The new methods reuse all of this. No new wiring matrix entries.

## Design

### `count_rows() -> int`

A terminal operation that returns the number of rows the relation would produce, executed via a count-pushdown rewrite.

**Algorithm:**

1. Wrap `self._node` in an `AggregateRelNode` projecting a single `count(*)` measure (no group-by). Reuses the existing aggregate pipeline — no new node type.
2. Compile the wrapped tree through the existing `_compile_and_execute()` path.
3. Extract the single integer from the result via the backend's native scalar accessor (Polars `.item()`, Pandas `.iloc[0,0]`, Ibis `.execute()` already returns a scalar for `.count()`).
4. Coerce to `int` and return.

**Per-backend rewrite:**

| Backend | Wrapped tree compiles to | Native call to extract scalar |
|---|---|---|
| Polars | `lf.select(pl.len())` | `.collect().item()` |
| Narwhals | `nw_frame.select(nw.len())` | `.item()` (Narwhals exposes `Series.item()`) |
| Ibis | `expr.count()` | `.execute()` (returns a Python int directly) |

The variance is absorbed by the existing aggregate wiring. The Polars path produces a single-row, single-column LazyFrame; the helper that does the final scalar extraction is the only count-specific code.

### `item(column: str, row: int = 0) -> Any`

A terminal operation that returns a single Python scalar from a materialised result, with **strict** semantics.

**Algorithm:**

1. Compile the relation through the existing `to_polars()` terminal path → `pl.DataFrame`.
2. Validate `column in df.columns`; raise `KeyError(column)` if missing.
3. Validate `0 <= row < len(df)`; raise `IndexError` with a clear message otherwise.
4. Return `df[column][row]` — Polars Series scalar accessor handles native → Python conversion (datetime, decimal, etc.).

**Strict semantics rationale:**

- Empty result → `IndexError("no row 0 in empty relation")`. Callers wanting a safe variant must `count_rows()` first or wrap their own try/except. The downstream `explain()` example does exactly this.
- `row=5` on a 3-row result → `IndexError`. No silent truncation.
- Missing column → `KeyError(column)`. No silent `None`.
- Negative indexing (`row=-1`) — **out of scope**. Defer until a real use case lands.
- `default=` kwarg — **out of scope**. Permissive APIs encourage swallowing real errors (e.g. `explain("MissingRule")` returning `None` would mask rules-engine bugs).

This matches Polars `Series.item()` exactly.

### Behaviour matrix

| Scenario | `count_rows()` | `item("c", 0)` |
|---|---|---|
| Empty relation | returns `0` | raises `IndexError` |
| Missing column | (column irrelevant) | raises `KeyError` |
| `row` out of range | (row irrelevant) | raises `IndexError` |
| Relation contains `RefRelNode` standalone | raises `RelationDAGRequired` | raises `RelationDAGRequired` |
| Relation inside `RelationDAG.collect()` | works via `ref_resolver` | works via `ref_resolver` |
| Lazy backend (Polars `LazyFrame`) | only computes the count, not the full result | materialises then extracts |
| Already-aggregated relation (`group_by().agg()`) | counts the result rows, not the input rows | works on the aggregated columns |

## Implementation locations

| File | Change |
|---|---|
| `src/mountainash/relations/core/relation_api/relation.py` | Add `count_rows()` and `item()` methods alongside existing `collect()` / `to_polars()` / `to_dict()` / etc. |
| `src/mountainash/relations/core/relation_api/relation_base.py` | If the count rewrite needs a helper (`_compile_count`), add it next to `_compile_and_execute()`. Otherwise inline. |
| `tests/relations/test_terminals.py` *(new or extend existing terminal-test file)* | Cross-backend parametrized tests for both methods |

**No** new node types. **No** new visitor methods. **No** changes to protocols, backend systems, or function-key enums. The aggregate-rewrite for `count_rows()` reuses the existing `AggregateRelNode` and the `count` aggregate function, both of which the wiring matrix already covers across all 3 backends.

## API surface

```python
import mountainash as ma
from mountainash.relations import relation

r = relation(df).filter(ma.col("status").eq("active"))

# Row count via count-pushdown rewrite
n: int = r.count_rows()                    # 0 if empty

# Single scalar from a one-row result
top = r.head(1)
value = top.item("amount")                  # raises IndexError on empty
score = top.item("score", row=0)            # explicit row index also accepted
```

**API surface note:** the feature request used `relation(df).head(1).execute()` — `.execute()` is **not** a current method on `Relation`. The convention is `.collect()` (returns native) or `.to_polars()` / `.to_pandas()` (returns specific type). Calling code adopting `count_rows()` should use `.collect()` for "execute and return native".

## Tests (per `testing-philosophy.md`)

Cross-backend parametrized tests covering, for each of Polars / Narwhals / Ibis:

**`count_rows()` cases:**
- Fresh relation built from a DataFrame: count matches `len(df)`
- Relation after `head(n)`: count matches `min(n, len(df))`
- Relation after `filter(...)` matching nothing: count is `0`
- Relation after `group_by(...).agg(...)`: count matches the number of groups
- Relation containing a `RefRelNode` standalone: raises `RelationDAGRequired`
- Relation containing a `RefRelNode` inside `RelationDAG.collect()`: works correctly

**`item()` cases:**
- One-row relation, valid column: returns the scalar
- Empty relation: raises `IndexError`
- Missing column: raises `KeyError`
- `row=5` on a 3-row result: raises `IndexError`
- Datetime / decimal column (verifies native → Python coercion)
- Inside `RelationDAG.collect()`: works via the visitor's `ref_resolver`

## Out of scope

- Negative row indexing (`item("c", row=-1)`)
- `default=` kwarg on `item()`
- Aggregate fast paths beyond `count(*)` (e.g. `Relation.sum(col)`, `Relation.first(col)`, `Relation.min(col)`) — natural follow-up if a "scalar terminals" batch is wanted
- Reorganising `pydata.egress` for discoverability — the audit confirmed neither method exists in egress, and no reorganisation is warranted

## Risks

### Aggregate rewrite + `RefRelNode`

Wrapping a relation that contains a `RefRelNode` in an `AggregateRelNode` should work (the visitor walks the wrapped subtree and resolves refs through the resolver), but this combination is new. **Mitigation:** explicit test in the cross-backend matrix verifying `count_rows()` works inside `RelationDAG.collect()` on a relation containing `dag.ref(...)`.

### Narwhals scalar extraction

Narwhals' `Series.item()` exists in the public API but the project's existing relation backends may not currently exercise it. **Mitigation:** smoke test the Narwhals `count_rows()` path against a real Narwhals frame before relying on the API; if `Series.item()` proves unreliable, fall back to `len(narwhals_frame.select(nw.col("__count")).to_native())` or convert to Polars first.

### Ibis count execution

`expr.count()` on Ibis returns an `IntegerScalar` expression, not an int. The actual execution happens at `.execute()`. Verify that `.execute()` on an Ibis count scalar returns a plain Python int (it does in current Ibis versions, but worth a sanity test in the cross-backend matrix).

### Lazy `pl.DataFrame.item(row, col)` vs `Series.item(row)`

Polars exposes both `df.item(row, col)` and `series.item(idx)`. The implementation should pick one consistently and stick with it. The plan picks `df[column][row]` for clarity at the call site (column-then-row, not row-then-column). Verify against current Polars version.

## Dependencies

- Existing `Relation` fluent API
- Existing `_compile_and_execute()` pipeline
- Existing `AggregateRelNode` and the `count` aggregate function (already wired across all 3 backends per the wiring matrix)
- Existing `UnifiedRelationVisitor` with `ref_resolver` support (for `RelationDAG.collect()` integration)
- Polars `Series.item()` / Narwhals `Series.item()` / Ibis scalar `.execute()` for the final scalar extraction

No new external dependencies. No new internal protocols.
