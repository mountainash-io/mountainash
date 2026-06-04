---
title: Relation API Core Operations
description: The relation() factory, Relation class, and core relational operations including filter, sort, select, join, group_by, set operations, and concat.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 10: Relation API Core Operations

## Summary

The relation() factory, Relation class, RelationBase protocol, and core relational operations: filter, sort, head/fetch, select/project, join, group_by, GroupedRelation, aggregation on groups, set operations, and concat.

## Concepts Covered

- relation Factory
- Relation Class
- RelationBase
- Filter Operation
- Sort Operation
- Head Fetch Operation
- Select Project Operation
- Join Operation
- Group By Operation
- GroupedRelation
- Aggregation on Groups
- Set Operations
- concat Function

## Prerequisites

- [Chapter 1. Foundation Concepts](../01-foundations/)
- [Chapter 2. Core Infrastructure](../02-core-infrastructure/)
- [Chapter 3. Expression API Basics](../03-expression-api-basics/)
- [Chapter 5. Expression Operations](../05-expression-operations/)

---

## Introduction

While expressions describe column-level computations, relations describe table-level transformations. The relation API provides the primary interface for building data pipelines in mountainash. You start with a `relation()` call that wraps a DataFrame, then chain operations to filter, sort, project, join, aggregate, and combine data. Each operation produces a new `Relation` object wrapping a new AST node, and no execution occurs until a terminal operation is called.

<!-- concept:95 -->
## relation Factory

The `relation()` factory function is the entry point for creating relation objects from existing data. It accepts any supported DataFrame type (Polars, pandas, PyArrow, Ibis, Narwhals) and wraps it in a `Relation` object backed by a `ReadRelNode`.

```python
import mountainash as ma
import polars as pl

df = pl.DataFrame({
    "name": ["Alice", "Bob", "Carol"],
    "age": [30, 25, 35],
    "dept": ["eng", "sales", "eng"],
})

# Create a relation from a Polars DataFrame
rel = ma.relation(df)
```

The factory performs backend detection on the input data using the string-inspection system described in Chapter 2. The detected backend determines which expression system and relation system will be used during compilation. The returned `Relation` object is backend-agnostic; all backend-specific behavior is deferred to compilation.

The `relation()` function also accepts method chaining directly after construction, enabling compact pipeline expressions.

<!-- concept:96 -->
## Relation Class

The `Relation` class is the user-facing fluent API for relational operations. Every chainable method returns a new `Relation` instance wrapping a new AST node. The class inherits from `RelationBase` (which provides compilation machinery) and adds the relational operation methods.

```python
class Relation(RelationBase):
    """Fluent builder for relational query plans."""

    def filter(self, *predicates) -> Relation: ...
    def sort(self, *by, descending=False) -> Relation: ...
    def head(self, n=5) -> Relation: ...
    def join(self, other, *, on=None, how="inner") -> Relation: ...
    def group_by(self, *keys) -> GroupedRelation: ...
    # ... more operations
```

The `Relation` class maintains a single `_node` attribute (inherited from `RelationBase`) that holds the root of the AST tree built so far. Each method creates a new node type with `input=self._node`, producing a chain of nodes that represents the pipeline.

<!-- concept:97 -->
## RelationBase

`RelationBase` is the base class that provides the compilation and execution machinery. It is separate from `Relation` so that the fluent API methods and the compilation logic do not mix.

The key method is `_compile_and_execute()`, which performs the full compilation pipeline. It detects the backend from the AST tree, retrieves the appropriate relation and expression systems, creates visitors, and walks the AST to produce backend-native output.

```python
class RelationBase:
    __slots__ = ("_node",)

    def __init__(self, node: RelationNode):
        self._node = node

    def _compile_and_execute(self):
        node = self._apply_optimisations(self._node)
        backend = self._detect_backend_from(node)
        relation_system = get_relation_system(backend)()
        expression_system = get_expression_system(backend)()
        expr_visitor = UnifiedExpressionVisitor(expression_system)
        visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
        return visitor.visit(node)
```

The method applies any registered optimization passes before compilation, potentially rewriting the AST for better performance.

<!-- concept:98 -->
## Filter Operation

The `filter` method creates a `FilterRelNode` that selects rows matching a boolean predicate expression. Multiple predicates can be passed as separate arguments, producing chained filter nodes.

```python
import mountainash as ma

# Single predicate
adults = ma.relation(df).filter(ma.col("age") >= 18)

# Multiple predicates (AND logic)
senior_engineers = ma.relation(df).filter(
    ma.col("age") >= 65,
    ma.col("dept") == "eng"
)

# Compound predicate
complex_filter = ma.relation(df).filter(
    (ma.col("age") >= 18) & (ma.col("score") > 80) | ma.col("exempt")
)
```

When multiple predicates are passed, each produces a separate `FilterRelNode` stacked in sequence. This is semantically equivalent to combining them with AND but allows the optimizer to reorder or merge filters independently.

<!-- concept:99 -->
## Sort Operation

The `sort` method creates a `SortRelNode` that orders rows by one or more columns. The `descending` parameter controls sort direction and can be a single boolean or a list of booleans (one per column).

```python
import mountainash as ma

# Sort ascending by name
by_name = ma.relation(df).sort("name")

# Sort descending by age
by_age_desc = ma.relation(df).sort("age", descending=True)

# Multi-column sort
ordered = ma.relation(df).sort("dept", "age", descending=[False, True])
```

Internally, `sort` normalizes its arguments into `SortField` objects that capture the column name, sort direction, and null ordering (nulls last by default). These `SortField` objects are stored in the `SortRelNode`.

<!-- concept:100 -->
## Head Fetch Operation

The `head` method creates a `FetchRelNode` that limits the output to the first N rows. The complementary `tail` method returns the last N rows, and `slice` provides offset-based row selection.

```python
import mountainash as ma

# First 10 rows
top_10 = ma.relation(df).head(10)

# Last 5 rows
bottom_5 = ma.relation(df).tail(5)

# Rows 20 through 30
page = ma.relation(df).slice(offset=20, length=10)
```

The `FetchRelNode` stores a count (number of rows), an optional offset (starting position), and a `from_end` flag (for tail operations). This aligns with Substrait's FetchRel specification.

#### Diagram: Relational Operations Pipeline
<iframe src="../../sims/relational-pipeline/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Relational Operations Pipeline</summary>
Type: microsim
**sim-id:** relational-pipeline<br/>
**Library:** p5.js<br/>
**Status:** Specified

An interactive pipeline visualization showing a small DataFrame (8 rows) flowing through a sequence of operations. Four operation stages are shown: Filter (grays out excluded rows), Sort (reorders remaining rows with animation), Select (removes columns), Head (keeps only top N). Each stage has a toggle to enable/disable it. The data flows visually from left to right, transforming at each stage. Row counts are displayed between stages. Clicking a stage shows the AST node it produces. Colors: Teal for relation operations. Learning objective: Predict the output of a chained relational pipeline given specific filter, sort, and fetch parameters (Bloom: Apply).
</details>

<!-- concept:101 -->
## Select Project Operation

The `select` method (and related methods `with_columns`, `drop`, `rename`) creates a `ProjectRelNode` that modifies the column set. These operations use different `ProjectOperation` variants to specify whether columns are being selected, added, removed, or renamed.

```python
import mountainash as ma

# Select specific columns
subset = ma.relation(df).select("name", "age")

# Add computed columns
enriched = ma.relation(df).with_columns(
    (ma.col("price") * ma.col("qty")).alias("total")
)

# Drop columns
trimmed = ma.relation(df).drop("internal_id", "debug_flag")

# Rename columns
renamed = ma.relation(df).rename({"old_name": "new_name"})
```

Select accepts both string column names and expression objects. When expressions are passed, they define computed columns in the output. The `with_columns` variant preserves all existing columns and adds new ones, while `select` keeps only the specified columns.

<!-- concept:102 -->
## Join Operation

The `join` method creates a `JoinRelNode` that combines two relations based on matching column values. It supports all join types defined in the `JoinType` enum (inner, left, right, outer, semi, anti, cross, asof).

```python
import mountainash as ma

# Inner join on matching column
combined = ma.relation(orders).join(
    ma.relation(customers),
    on="customer_id",
    how="inner"
)

# Left join with different column names
matched = ma.relation(orders).join(
    ma.relation(products),
    left_on="product_code",
    right_on="sku",
    how="left",
    suffix="_product"
)
```

The join method accepts column specifications in three forms. `on` specifies columns that exist in both relations with the same name. `left_on` and `right_on` specify columns that have different names in each relation. The `suffix` parameter resolves naming conflicts when both relations have columns with the same name (the right relation's conflicting columns get the suffix appended).

| Parameter | Type | Purpose |
|-----------|------|---------|
| `other` | Relation or DataFrame | Right side of the join |
| `on` | str or list[str] | Matching column(s) in both relations |
| `left_on` | str or list[str] | Column(s) from left relation |
| `right_on` | str or list[str] | Column(s) from right relation |
| `how` | str | Join type (inner, left, right, outer, semi, anti, cross, asof) |
| `suffix` | str | Suffix for duplicate column names (default: "_right") |
| `execute_on` | ExecutionTarget | Which side determines execution backend |

<!-- concept:103 -->
## Group By Operation

The `group_by` method initiates a grouping operation by specifying one or more key columns. It returns a `GroupedRelation` object (not a `Relation`) that requires an aggregation step to produce results.

```python
import mountainash as ma

# Group by department
grouped = ma.relation(df).group_by("dept")

# Group by multiple keys
multi_grouped = ma.relation(df).group_by("dept", "region")
```

The `group_by` method does not produce a relational AST node directly. Instead, it creates a `GroupedRelation` that holds the group keys and waits for the `.agg()` call to produce the final `AggregateRelNode`.

<!-- concept:104 -->
## GroupedRelation

`GroupedRelation` is a transitional object returned by `group_by()`. It stores the group keys and provides the `agg()` method for specifying aggregation expressions. Calling `agg()` produces a standard `Relation` wrapping an `AggregateRelNode`.

```python
import mountainash as ma

result = (
    ma.relation(df)
    .group_by("dept")
    .agg(
        ma.col("salary").mean().alias("avg_salary"),
        ma.col("id").count().alias("headcount"),
    )
)
```

The `GroupedRelation` enforces the two-step pattern: you cannot filter or sort a grouped relation directly. You must first aggregate to produce a flat relation, then apply further operations to the result.

<!-- concept:105 -->
## Aggregation on Groups

Aggregation on groups is the combination of `group_by` and `agg` that produces summary statistics for each group. The `agg` method accepts one or more aggregation expressions, each of which reduces the group's rows to a single value per group.

```python
import mountainash as ma

summary = (
    ma.relation(df)
    .group_by("category")
    .agg(
        ma.col("amount").sum().alias("total"),
        ma.col("amount").mean().alias("average"),
        ma.col("amount").max().alias("max_amount"),
        ma.count_records().alias("count"),
    )
)
```

Each aggregation expression uses one of the aggregation functions (sum, mean, min, max, count, std, var, first, last, n_unique). The `.alias()` call names the output column. Without an alias, the column name defaults to the source column name, which can cause ambiguity when multiple aggregations reference the same column.

<!-- concept:106 -->
## Set Operations

Set operations combine multiple relations vertically (row-wise). The `SetType` enum defines two variants: `UNION_ALL` (keep all rows including duplicates) and `UNION_DISTINCT` (deduplicate after combining).

```python
import mountainash as ma

# Union all (preserves duplicates)
combined = ma.relation(df1).union(ma.relation(df2))

# Union distinct (removes duplicates)
unique_combined = ma.relation(df1).union(ma.relation(df2), distinct=True)
```

Set operations require that both relations have compatible schemas (same column names and compatible types). The result has the same schema as the input relations.

<!-- concept:107 -->
## concat Function

The `concat` function is a module-level function that vertically concatenates multiple relations. It is a convenience wrapper around set operations that accepts a list of relations and produces a single combined relation.

```python
import mountainash as ma

# Concatenate multiple relations
all_data = ma.concat([
    ma.relation(jan_data),
    ma.relation(feb_data),
    ma.relation(mar_data),
])
```

The `concat` function is equivalent to chaining union operations but is more readable when combining more than two relations. Internally, it produces a `SetRelNode` with `UNION_ALL` semantics and multiple inputs.

## Key Takeaways

- The `relation()` factory wraps any supported DataFrame type into a backend-agnostic `Relation` object backed by a `ReadRelNode`.
- Every relational method returns a new immutable `Relation` instance, building an AST chain without executing any operations.
- `RelationBase` provides the compilation machinery that detects backends, creates visitors, and walks the AST to produce native output.
- Filter, sort, head, and select/project operations each create specific AST node types (FilterRelNode, SortRelNode, FetchRelNode, ProjectRelNode).
- Join operations support eight join types and handle column matching via `on`, `left_on`/`right_on`, with conflict resolution through the `suffix` parameter.
- Group by produces a `GroupedRelation` that requires `.agg()` to produce the final `AggregateRelNode`, enforcing the two-step aggregation pattern.
- Set operations and `concat` combine relations vertically, requiring compatible schemas, with optional deduplication via UNION_DISTINCT.
- The entire pipeline is lazy: AST construction happens immediately, but compilation and execution occur only when a terminal operation is called.
