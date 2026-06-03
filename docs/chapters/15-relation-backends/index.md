---
title: Relation Backends
description: Backend relation system implementations for Polars, Narwhals, and Ibis, including LazyFrame operations, cross-type joins, join key coalescing, backend divergences, and execution targeting.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 15: Relation Backends

## Summary

Backend relation systems (Polars LazyFrame, Narwhals, Ibis SQL), backend-specific operations, cross-type joins, join key coalescing, backend relation testing, divergences, execution target, and execute_on parameter.

## Concepts Covered

- PolarsRelationSystem
- NarwhalsRelationSystem
- IbisRelationSystem
- LazyFrame Operations
- Narwhals Portability
- Ibis SQL Compilation
- Cross-Type Joins
- Join Key Coalescing
- Backend Relation Testing
- Backend Divergences
- Execution Target
- execute_on Parameter

## Prerequisites

- [Chapter 2. Core Infrastructure](../02-core-infrastructure/)
- [Chapter 8. Expression Backends](../08-expression-backends/)
- [Chapter 10. Relation API Core Operations](../10-relation-api-core/)
- [Chapter 14. Relation AST and System Architecture](../14-relation-ast-and-system/)

---

## Introduction

Chapter 14 introduced the abstract `RelationSystem` base class and the protocol hierarchy that defines the interface every backend must implement. This chapter turns from architecture to implementation: how does the Polars backend actually execute a filter? How does the Ibis backend compile a join into SQL? What happens when the left side of a join is a Polars LazyFrame but the right side is a pandas DataFrame?

Mountainash ships three relation backends that correspond to the three expression backends from Chapter 8. Each implements the same set of relational operations but translates them into different execution models:

- **Polars**: In-memory columnar processing with lazy evaluation
- **Narwhals**: A compatibility layer that wraps pandas, PyArrow, and cuDF
- **Ibis**: SQL compilation targeting DuckDB, PostgreSQL, BigQuery, and other databases

## PolarsRelationSystem

The **PolarsRelationSystem** is the primary backend and the most mature implementation. It operates on Polars LazyFrames, building up a deferred computation graph that executes only when a terminal operation triggers collection.

The system is composed via multiple inheritance from nine mixin classes, each implementing one protocol:

```python
@register_relation_system(CONST_BACKEND.POLARS)
class PolarsRelationSystem(
    PolarsBaseRelationSystem,
    SubstraitPolarsReadRelationSystem,
    SubstraitPolarsProjectRelationSystem,
    SubstraitPolarsFilterRelationSystem,
    SubstraitPolarsSortRelationSystem,
    SubstraitPolarsFetchRelationSystem,
    SubstraitPolarsJoinRelationSystem,
    SubstraitPolarsAggregateRelationSystem,
    SubstraitPolarsSetRelationSystem,
    MountainashPolarsExtensionRelationSystem,
):
    pass
```

Each mixin lives in its own file (e.g., `relsys_pl_filter.py`, `relsys_pl_join.py`), keeping individual implementations focused and testable. The `PolarsBaseRelationSystem` mixin provides the `backend_type` property that returns `CONST_BACKEND.POLARS`.

The `@register_relation_system()` decorator registers this class in the global backend registry. When the visitor needs a Polars relation system, it calls `get_relation_system(CONST_BACKEND.POLARS)` and receives this class.

## LazyFrame Operations

The Polars backend operates on **LazyFrames** rather than eager DataFrames. A LazyFrame is a deferred computation plan -- each operation (filter, select, join) appends to the plan without executing anything. Execution occurs only when a terminal method like `.collect()` is called.

This lazy evaluation model provides two key benefits:

1. **Query optimization**: Polars can apply predicate pushdown, projection pruning, and join reordering across the entire plan before executing it
2. **Memory efficiency**: Intermediate results are never materialized, reducing peak memory usage

The `read()` method ensures all inputs are lazy:

```python
# Simplified Polars read implementation
def read(self, dataframe):
    if is_polars_lazyframe(dataframe):
        return dataframe
    if is_polars_dataframe(dataframe):
        return dataframe.lazy()
    raise TypeError(f"Cannot read {type(dataframe).__name__}")
```

All subsequent operations (`filter()`, `project_select()`, `join()`, etc.) receive and return LazyFrames. The final materialization happens outside the relation system, typically when the user calls `.to_polars()` or `.collect()` on the Relation object.

#### Diagram: LazyFrame Operation Pipeline

<iframe src="../../sims/lazyframe-pipeline/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>LazyFrame Operation Pipeline</summary>
Type: Flow Diagram | **sim-id:** lazyframe-pipeline<br/> | **Library:** vis-network<br/> | **Status:** Specified
Shows a chain of LazyFrame operations: Read (DataFrame to LazyFrame), Filter (predicate appended), Project (column selection), Sort (ordering), and finally Collect (materialization). Each stage shows the logical plan growing. A "Query Optimizer" box sits between the plan and execution. Learning objective: Understand lazy evaluation in the Polars backend. Bloom level: Understand. Interactions: Click each stage to see the internal plan state, toggle optimizer on/off to compare plans.
</details>

## NarwhalsRelationSystem

The **NarwhalsRelationSystem** wraps pandas, PyArrow, and cuDF DataFrames through the Narwhals compatibility layer. Narwhals provides a DataFrame-agnostic API that translates operations to the underlying library's native calls.

```python
@register_relation_system(CONST_BACKEND.NARWHALS)
class NarwhalsRelationSystem(
    NarwhalsBaseRelationSystem,
    SubstraitNarwhalsReadRelationSystem,
    SubstraitNarwhalsProjectRelationSystem,
    SubstraitNarwhalsFilterRelationSystem,
    SubstraitNarwhalsSortRelationSystem,
    SubstraitNarwhalsFetchRelationSystem,
    SubstraitNarwhalsJoinRelationSystem,
    SubstraitNarwhalsAggregateRelationSystem,
    SubstraitNarwhalsSetRelationSystem,
    MountainashNarwhalsExtensionRelationSystem,
):
    pass
```

The composition follows the identical mixin pattern as Polars, with each mixin translating mountainash's relational operations to Narwhals API calls.

## Narwhals Portability

The primary value of the Narwhals backend is **portability**. Code written against the mountainash Relation API works identically regardless of whether the underlying data is a pandas DataFrame, a PyArrow table, or a cuDF GPU DataFrame. The Narwhals layer handles the translation transparently.

This portability has practical applications:

- **Migration**: Move from pandas to PyArrow without rewriting transformation logic
- **GPU acceleration**: Switch from pandas to cuDF for GPU-accelerated processing without code changes
- **Interoperability**: Accept data from any library that Narwhals supports and process it uniformly

The Narwhals backend auto-detects the input type when `read()` is called, wrapping it in a Narwhals DataFrame via `nw.from_native()`. Output is returned in the same native format, preserving the caller's library choice.

However, the Narwhals backend operates eagerly (no lazy evaluation), which means intermediate results are materialized at each step. For large datasets where memory pressure is a concern, the Polars backend is preferred.

| Characteristic | Polars | Narwhals | Ibis |
|---------------|--------|----------|------|
| Evaluation | Lazy | Eager | Lazy (SQL) |
| Optimization | Polars query optimizer | None (pass-through) | Database query planner |
| Primary use case | In-memory analytics | Library portability | Database-backed queries |
| Memory model | Deferred materialization | Per-step materialization | Server-side execution |

## IbisRelationSystem

The **IbisRelationSystem** compiles mountainash relations into SQL via the Ibis expression framework. Ibis supports multiple SQL backends including DuckDB, PostgreSQL, BigQuery, Snowflake, and SQLite.

```python
@register_relation_system(CONST_BACKEND.IBIS)
class IbisRelationSystem(
    IbisBaseRelationSystem,
    SubstraitIbisReadRelationSystem,
    SubstraitIbisProjectRelationSystem,
    SubstraitIbisFilterRelationSystem,
    SubstraitIbisSortRelationSystem,
    SubstraitIbisFetchRelationSystem,
    SubstraitIbisJoinRelationSystem,
    SubstraitIbisAggregateRelationSystem,
    SubstraitIbisSetRelationSystem,
    MountainashIbisExtensionRelationSystem,
):
    pass
```

## Ibis SQL Compilation

The Ibis backend transforms each relational operation into an Ibis table expression, which Ibis then compiles to SQL for the target database. This means the same mountainash pipeline can run against DuckDB during development and PostgreSQL in production without code changes.

The compilation chain works as follows:

1. Mountainash relation operations create AST nodes
2. The visitor calls `IbisRelationSystem` methods
3. Each method translates to Ibis table expression API calls
4. Ibis compiles the expression tree to SQL for the connected backend
5. The database executes the SQL and returns results

The key distinction from the Polars backend is that execution happens server-side. Filters, joins, and aggregations are pushed to the database engine, which can leverage indexes, partitioning, and distributed execution that are unavailable in client-side processing.

The Ibis backend handles the translation of mountainash join types, sort specifications, and set operations to their SQL equivalents. Some operations that are natural in DataFrame APIs (like `with_row_index`) require SQL-specific implementations using window functions.

The translation from mountainash operations to SQL concepts follows predictable patterns:

| Mountainash Operation | SQL Equivalent |
|----------------------|---------------|
| `filter(predicate)` | `WHERE clause` |
| `select(cols)` | `SELECT col1, col2, ...` |
| `join(other, on=...)` | `JOIN ... ON ...` or `JOIN ... USING (...)` |
| `group_by().agg()` | `GROUP BY ... SELECT agg(...)` |
| `sort(col)` | `ORDER BY col` |
| `head(n)` | `LIMIT n` |
| `union(other)` | `UNION ALL` |
| `with_row_index()` | `ROW_NUMBER() OVER ()` |

Because Ibis itself supports multiple SQL dialects, the mountainash Ibis backend does not generate raw SQL strings. Instead, it constructs Ibis expression objects and lets Ibis handle the dialect-specific SQL generation. This means the same mountainash code correctly generates PostgreSQL syntax (`LIMIT` / `OFFSET`), BigQuery syntax (`LIMIT` with different offset semantics), and DuckDB syntax automatically.

#### Diagram: Three Backend Execution Models

<iframe src="../../sims/backend-execution-models/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Three Backend Execution Models</summary>
Type: Comparison Diagram | **sim-id:** backend-execution-models<br/> | **Library:** vis-network<br/> | **Status:** Specified
Three parallel columns showing the same mountainash query compiled through each backend. Polars shows a LazyFrame plan; Narwhals shows eager pandas operations; Ibis shows generated SQL. All three produce the same logical result. Learning objective: Compare how the same query executes across backends. Bloom level: Analyze. Interactions: Select a backend to highlight its column, hover over operations to see backend-specific translations.
</details>

## Cross-Type Joins

A **cross-type join** occurs when the left and right sides of a join come from different DataFrame libraries. For example, the left side might be a Polars LazyFrame while the right side is a pandas DataFrame passed in by the user.

The `UnifiedRelationVisitor` handles this transparently through its `_visit_and_coerce_right()` method. When the right side produces a different backend type from the left, the visitor coerces the right to match:

```python
def _visit_and_coerce_right(self, right_node, left_result):
    try:
        return self.visit(right_node)
    except TypeError:
        if isinstance(right_node, ReadRelNode):
            return self._coerce_to_match(left_result, right_node.dataframe)
        raise
```

The coercion logic supports the following conversions when the target is a Polars LazyFrame:

- Polars DataFrame \(\rightarrow\) `.lazy()` promotion
- pandas DataFrame \(\rightarrow\) `pl.from_pandas()` followed by `.lazy()`
- PyArrow Table \(\rightarrow\) `pl.from_arrow()` followed by `.lazy()`
- Python dict \(\rightarrow\) `pl.DataFrame(dict).lazy()`
- Narwhals DataFrame \(\rightarrow\) via pandas intermediary to Polars

This means users can write `relation(polars_df).join(pandas_df, on="id")` without manually converting the pandas DataFrame. The coercion happens at compilation time, not at API call time, so the AST remains backend-neutral.

## Join Key Coalescing

**Join key coalescing** is the process of deduplicating and reconciling join key columns after a join operation. In standard SQL, an inner join on `A.id = B.id` produces two `id` columns that contain identical values. Polars handles this differently -- shared join keys appear only once in the output.

The mountainash relation system handles coalescing at the backend level rather than at the AST level. Each backend's join implementation is responsible for producing the correct output columns:

- **Polars**: Native join key coalescing (shared keys appear once automatically)
- **Narwhals**: Follows the behavior of the underlying library (pandas produces duplicates that need manual dedup)
- **Ibis**: SQL `USING` clauses coalesce naturally; `ON` clauses may need explicit column selection

When `left_on` and `right_on` differ, the key columns from both sides are preserved. The `suffix` parameter (default `"_right"`) disambiguates any other columns that share names.

Consider a concrete example where the difference matters:

```python
# Same-name join keys (coalesced)
result = orders.join(customers, on=["customer_id"], how="inner")
# Result has ONE customer_id column

# Different-name join keys (both preserved)
result = orders.join(
    customers,
    left_on=["cust_id"],
    right_on=["customer_id"],
    how="inner",
)
# Result has BOTH cust_id and customer_id columns
```

The coalescing behavior is particularly important for multi-key joins. If a join uses `on=["region", "date"]`, both columns appear exactly once in the output, preventing the common pitfall of accidentally selecting the wrong copy of a duplicated key column.

## Backend Relation Testing

The mountainash test suite validates that all three backends produce identical results for the same logical operations. This is achieved through **cross-backend parametrize** -- pytest fixtures that run each test against Polars, Narwhals, and Ibis.

The testing strategy follows the same pattern as expression backend testing (Chapter 8):

```python
@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_filter_gt(backend, sample_data):
    rel = relation(sample_data[backend])
    result = rel.filter(col("age").gt(lit(30))).to_polars()
    assert result.shape == (expected_rows, expected_cols)
```

Each test case provides the same logical data in all three formats (Polars DataFrame, pandas DataFrame, Ibis table), applies the same operations, and asserts identical outcomes. This ensures that backend divergences are caught immediately.

The test infrastructure handles the necessary setup for each backend:

- **Polars**: Direct DataFrame construction
- **Narwhals**: pandas DataFrame wrapped in `nw.from_native()`
- **Ibis**: DuckDB in-memory table created from the same data

## Backend Divergences

Despite the goal of identical behavior across backends, some **divergences** exist due to fundamental differences in how each library handles edge cases. These are documented and tracked as known limitations:

**Null handling in comparisons**: Polars propagates nulls through comparisons (\(\text{null} > 5\) returns null), while some SQL databases return false. The mountainash test suite marks these cases with `xfail` annotations that specify which backends diverge.

**Sort stability**: Polars provides stable sorts (equal elements maintain their original order), but SQL databases do not guarantee sort stability. When test assertions depend on row order within tied groups, the test must explicitly add a tiebreaker column.

**Float precision**: Aggregations involving floating-point arithmetic may produce slightly different results across backends. Tests use approximate comparison (`assert_frame_equal` with tolerance) for numeric aggregations.

**Type coercion on empty results**: When a filter produces zero rows, the resulting empty DataFrame's column types may differ. Polars preserves the original schema, while pandas may lose type information on empty frames.

These divergences are not bugs -- they reflect real differences in the underlying execution engines. The `xfail` mechanism ensures that known divergences do not cause spurious test failures while remaining visible for tracking.

#### Diagram: Backend Divergence Map

<iframe src="../../sims/backend-divergence-map/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Backend Divergence Map</summary>
Type: Matrix Diagram | **sim-id:** backend-divergence-map<br/> | **Library:** vis-network<br/> | **Status:** Specified
Heatmap-style matrix showing operation categories (filter, join, aggregate, sort, null handling) across backends (Polars, Narwhals, Ibis). Cells are green (identical behavior), yellow (minor divergence), or red (known incompatibility with xfail). Learning objective: Identify where backends diverge. Bloom level: Evaluate. Interactions: Click cells for detailed divergence descriptions, filter by severity level.
</details>

## Execution Target

The **ExecutionTarget** concept determines which side of a join controls execution placement. In most cases, execution happens wherever the left side of the join resides. But when the right side is a large table in a remote database and the left side is small local data, it may be more efficient to push execution to the right side.

The `ExecutionTarget` enum provides the options:

- **LEFT** (default): Execute the join on the left side's backend
- **RIGHT**: Execute the join on the right side's backend

This is primarily relevant for the Ibis backend, where one side might be a local DataFrame and the other a remote database table. Choosing the correct execution target avoids pulling a large remote table to the client just to perform a join.

## execute_on Parameter

The `execute_on` parameter on the `.join()` method exposes the `ExecutionTarget` concept to user code. It accepts an `ExecutionTarget` enum value (or None for the default left-side execution).

```python
import mountainash as ma
from mountainash.core.constants import ExecutionTarget

# Small local data
local_lookup = ma.relation(small_df)

# Large remote table (via Ibis)
remote_orders = ma.relation(ibis_table)

# Execute on the right (remote) side to avoid pulling data locally
result = local_lookup.join(
    remote_orders,
    on=["customer_id"],
    how="inner",
    execute_on=ExecutionTarget.RIGHT,
)
```

The JoinRelNode carries the `execute_on` value, and the backend's join implementation uses it to decide the execution strategy. When `execute_on=RIGHT`, the visitor may upload the small left-side data to the remote backend (e.g., as a temporary table) and execute the join server-side.

The `execute_on` parameter is optional. When omitted, the default behavior executes on the left side, which is correct for the common case where both sides are the same backend type.

## Backend Selection and Auto-Detection

When a relation is compiled (via `.to_polars()`, `.collect()`, or `dag.collect()`), the system needs to determine which backend to use. The auto-detection logic walks the AST tree to find a `ReadRelNode` and identifies the backend from its dataframe type:

1. If the user explicitly provides a backend (e.g., `dag.collect("x", backend="polars")`), use that
2. Otherwise, find the first `ReadRelNode` in the dependency tree
3. Call `identify_backend()` on its dataframe to determine `CONST_BACKEND`
4. If no ReadRelNode exists (e.g., pure SourceRelNode trees), fall back to Polars

This auto-detection means users almost never need to specify a backend manually. The system infers the correct backend from the data being processed.

#### Diagram: Backend Auto-Detection Flow

<iframe src="../../sims/backend-auto-detection/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Backend Auto-Detection Flow</summary>
Type: Decision Flowchart | **sim-id:** backend-auto-detection<br/> | **Library:** vis-network<br/> | **Status:** Specified
Decision tree showing the backend auto-detection algorithm: check for explicit backend parameter, walk AST for ReadRelNode, call identify_backend() on the dataframe, fall back to Polars. Each decision node shows the condition and outcome. Learning objective: Trace the backend selection logic. Bloom level: Apply. Interactions: Click decision nodes to see example scenarios, highlight the path taken for different input types.
</details>

## Mixin Architecture in Practice

Each backend's relation system is composed from separate mixin classes, one per relational operation category. This architecture keeps individual files small (typically 30-80 lines) and makes it straightforward to compare how different backends implement the same operation.

For example, the filter operation has three parallel implementations:

- `SubstraitPolarsFilterRelationSystem` -- calls `lazyframe.filter(predicate)`
- `SubstraitNarwhalsFilterRelationSystem` -- calls `nw_frame.filter(predicate)`
- `SubstraitIbisFilterRelationSystem` -- calls `ibis_table.filter(predicate)`

The naming convention is consistent: `Substrait{Backend}{Operation}RelationSystem` for Substrait-aligned operations and `Mountainash{Backend}ExtensionRelationSystem` for extension operations. This naming makes it easy to find the implementation for any specific backend-operation combination.

The mixin approach also means that a new operation can be added to one backend without touching the others. If a Polars-specific optimization is needed for aggregation, only `relsys_pl_aggregate.py` changes. The other backends continue to use their existing implementations.

## The Complete Backend Architecture

The relation backend architecture connects the abstract system from Chapter 14 to the concrete implementations in this chapter. The full flow from user code to execution is:

1. User calls `relation(df).filter(pred).select(cols).to_polars()`
2. The Relation API builds an AST: `ProjectRelNode -> FilterRelNode -> ReadRelNode`
3. `to_polars()` triggers compilation -- auto-detects Polars from the DataFrame type
4. `get_relation_system(CONST_BACKEND.POLARS)` returns `PolarsRelationSystem`
5. `UnifiedRelationVisitor` is constructed with the Polars system and expression system
6. The visitor walks the AST recursively, calling backend methods at each node
7. The result is a Polars LazyFrame that `.collect()` materializes into a DataFrame

For DAG-based execution, the same flow applies but with the addition of topological ordering and the ref_resolver cache from Chapter 13.

#### Diagram: End-to-End Backend Architecture

<iframe src="../../sims/backend-architecture-e2e/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>End-to-End Backend Architecture</summary>
Type: Architecture Diagram | **sim-id:** backend-architecture-e2e<br/> | **Library:** vis-network<br/> | **Status:** Specified
Full architecture view: User API layer creates AST nodes; backend auto-detection selects the relation system and expression system; the visitor compiles through the system; the result flows back to the user. Shows all three backends as alternatives at the system layer. Learning objective: Trace the complete path from API call to backend execution. Bloom level: Evaluate. Interactions: Click backend labels to highlight their specific path through the architecture, step through the compilation stages.
</details>

## Key Takeaways

- **PolarsRelationSystem** operates on LazyFrames, deferring execution until collection and enabling Polars query optimization.
- **NarwhalsRelationSystem** provides portability across pandas, PyArrow, and cuDF through the Narwhals adapter, but operates eagerly without cross-operation optimization.
- **IbisRelationSystem** compiles relations to SQL, pushing execution to database engines that can leverage indexes and distributed processing.
- **Cross-type joins** are handled transparently by the visitor's coercion logic, converting the right side to match the left side's backend type.
- **Backend divergences** in null handling, sort stability, and float precision are documented and tracked with xfail annotations in the cross-backend test suite.
- The **execute_on parameter** controls join execution placement, enabling efficient remote joins where a small local dataset joins against a large database table.
- **Backend auto-detection** walks the AST to find ReadRelNode leaf data types, defaulting to Polars when no DataFrame is present.
- All three backends implement the same protocol interfaces via mixin composition, ensuring that adding operations or backends requires minimal changes.
