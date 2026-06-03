---
title: Relation API Advanced Features
description: Advanced relation operations including conform for TypeSpec-driven transformation, unnest, the build-then-collect pattern, and terminal operations for materializing results.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 11: Relation API Advanced Features

## Summary

Advanced relation operations: conform (TypeSpec-driven transformation), unnest, the build-then-collect pattern, terminal operations, output methods (to_polars, to_pandas, collect).

## Concepts Covered

- Conform Operation
- Unnest Operation
- Build Then Collect
- Terminal Operations
- to_polars Method
- to_pandas Method
- collect Method

## Prerequisites

- [Chapter 4. Expression Namespaces and Functions](../04-expression-namespaces-and-functions/)
- [Chapter 6. Expression AST and Function Keys](../06-expression-ast-and-function-keys/)
- [Chapter 9. Type System and Schema](../09-type-system-and-schema/)
- [Chapter 10. Relation API Core Operations](../10-relation-api-core/)

---

## Introduction

The core relational operations (filter, sort, select, join, group_by) handle standard data transformations. This chapter covers advanced operations that bridge the relation system with other mountainash subsystems: `conform` connects relations to the type system for schema-driven transformation, `unnest` handles nested data structures, and terminal operations trigger compilation and return results in the desired format.

## Conform Operation

The `conform` operation transforms a relation to match a `TypeSpec` schema. It handles column renaming (via `rename_from`), type casting to target types, null filling (via `null_fill`), missing value replacement (via `missing_values`), and column filtering based on the `fields_match` setting.

```python
import mountainash as ma

spec = ma.typespec({
    "customer_id": "integer",
    "full_name": "string",
    "signup_date": "date",
})

# Conform the relation to the target schema
result = (
    ma.relation(raw_data)
    .conform(spec)
    .to_polars()
)
```

The conform operation stores a `ConformRelNode` in the AST. At compile time (not build time), the compiler examines the available columns in the input and generates the necessary transformations. This deferred evaluation is essential because column information may not be available until earlier operations in the pipeline have been resolved.

Conform handles several transformation types automatically:

- **Column renaming**: If a FieldSpec has `rename_from="old_col"`, the compiler generates a rename from "old_col" to the FieldSpec's `name`
- **Type casting**: If a column's actual type differs from the FieldSpec's `type`, a cast expression is generated
- **Null filling**: If `null_fill` is set, a `fill_null` expression is generated
- **Missing values**: If `missing_values` lists strings that represent null, they are replaced before other processing
- **Column filtering**: Depending on `fields_match` mode, extra columns are kept or dropped

| fields_match Mode | Extra Columns | Missing Columns |
|-------------------|---------------|-----------------|
| "open" | Kept | Ignored |
| "partial" | Dropped | Ignored |
| "strict" | Error | Error |

#### Diagram: Conform Transformation Pipeline
<iframe src="../../sims/conform-pipeline/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Conform Transformation Pipeline</summary>
Type: workflow
**sim-id:** conform-pipeline<br/>
**Library:** vis-network<br/>
**Status:** Specified

A step-by-step workflow diagram showing the conformance process. Input: a DataFrame with columns [old_name, value_str, extra]. TypeSpec: fields [{name: new_name, rename_from: old_name}, {name: value, type: integer}]. Steps flow left to right: 1) Detect rename_from mappings, 2) Apply renames, 3) Cast types, 4) Fill nulls, 5) Filter columns based on fields_match. Each step shows the intermediate column state. Interactive: clicking a step highlights which FieldSpec properties drive that transformation. Colors: MediumPurple for type system elements, Teal for relation operations. Learning objective: Predict the output schema after a conform operation given a TypeSpec with various field specifications (Bloom: Apply).
</details>

## Unnest Operation

The `unnest` operation expands struct (nested object) columns into top-level columns. Each field within the struct becomes a separate column, named using the pattern `{struct_col}{separator}{field_name}`.

```python
import mountainash as ma

# Expand the "address" struct column into separate columns
flattened = (
    ma.relation(df)
    .unnest("address", separator="_")
    .to_polars()
)
# If address had fields {city, state, zip}, produces columns:
# address_city, address_state, address_zip
```

The unnest operation creates an `ExtensionRelNode` with `operation=UNNEST`. It requires at least one column name and a separator string. The separator prevents naming collisions when multiple struct columns are unnested simultaneously.

Unnest is the inverse of grouping operations that produce struct columns. It is commonly used when loading JSON or nested data formats where logical fields are stored as sub-objects within a parent column.

- The source column must be of struct type (contains named sub-fields)
- All fields in the struct are expanded (no selective extraction)
- The original struct column is removed from the output
- If multiple struct columns are unnested, each gets its own prefix

## Build Then Collect

The "build then collect" pattern is the fundamental usage model for the relation API. You build a pipeline of operations (constructing an AST) and then collect the results with a terminal operation. This separation is what enables lazy evaluation, optimization, and backend independence.

```python
import mountainash as ma

# BUILD phase: construct the pipeline (no execution)
pipeline = (
    ma.relation(df)
    .filter(ma.col("status") == "active")
    .select("name", "email", "signup_date")
    .sort("signup_date", descending=True)
    .head(100)
)

# COLLECT phase: trigger compilation and execution
result = pipeline.to_polars()
```

The build phase is entirely backend-agnostic. No backend library is imported or invoked during AST construction. You can inspect, store, serialize, or compose pipeline objects without any data processing occurring.

The collect phase performs the full compilation pipeline in one shot: optimize the AST, detect the backend, instantiate systems, create visitors, walk the tree, and return the result. This all-at-once approach allows the compiler to see the entire plan before generating code.

!!! note "Reusability of Built Pipelines"
    A built pipeline (a `Relation` object) can be collected multiple times and can serve as the basis for further extensions. Because each operation creates new immutable nodes, the original pipeline is never modified by subsequent operations or collections.

## Terminal Operations

Terminal operations are methods that trigger compilation and execution, ending the lazy pipeline and producing a concrete result. They mark the boundary between the build phase and the collect phase.

Mountainash provides three primary terminal operations:

- `to_polars()` -- Compile and return a Polars DataFrame
- `to_pandas()` -- Compile and return a pandas DataFrame
- `collect()` -- Compile and return in the backend's native format

Terminal operations are the only methods on `Relation` that perform actual data processing. Every other method simply constructs AST nodes. This design makes it clear where computation costs occur in your code.

```python
import mountainash as ma

pipeline = ma.relation(df).filter(ma.col("active")).sort("name")

# Three ways to materialize the same pipeline
polars_df = pipeline.to_polars()
pandas_df = pipeline.to_pandas()
native_result = pipeline.collect()
```

## to_polars Method

The `to_polars` method compiles the relational AST and returns the result as a Polars DataFrame. If the input data was already a Polars DataFrame, this is the most efficient terminal operation because no format conversion is needed.

```python
import mountainash as ma

result = (
    ma.relation(polars_df)
    .filter(ma.col("amount") > 100)
    .select("customer", "amount")
    .to_polars()
)
# result is a pl.DataFrame
```

When the input is from a different backend (pandas or Ibis), `to_polars()` performs the necessary conversion after compilation. For pandas input, the Narwhals system compiles the pipeline, executes it, and converts the result to Polars format. For Ibis input, the SQL query executes and the result is converted to a Polars DataFrame.

## to_pandas Method

The `to_pandas` method compiles the relational AST and returns the result as a pandas DataFrame. This is useful when downstream code expects pandas format or when integrating with libraries that only support pandas.

```python
import mountainash as ma

result = (
    ma.relation(data)
    .filter(ma.col("year") >= 2020)
    .to_pandas()
)
# result is a pd.DataFrame
```

If the input was a Polars DataFrame, `to_pandas()` compiles through the Polars system and converts the result using Polars' built-in `.to_pandas()` conversion. If the input was already pandas, the Narwhals compilation path is used and the result is naturally in pandas format.

## collect Method

The `collect` method compiles and returns the result in whatever format the backend natively produces. For Polars input, this returns a Polars DataFrame. For pandas input (via Narwhals), this returns a pandas DataFrame. For Ibis input, this may return an Ibis table or a materialized DataFrame depending on the configuration.

```python
import mountainash as ma

# Returns whatever the backend produces natively
result = ma.relation(data).filter(ma.col("x") > 0).collect()
```

The `collect` method is the most general terminal operation. Use it when you do not need a specific output format and want to avoid unnecessary format conversions. It is also the method used internally by `RelationDAG.collect()` when materializing named relations.

#### Diagram: Terminal Operations Decision Tree
<iframe src="../../sims/terminal-operations/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Terminal Operations Decision Tree</summary>
Type: diagram
**sim-id:** terminal-operations<br/>
**Library:** vis-network<br/>
**Status:** Specified

A decision tree diagram helping users choose the right terminal operation. Root node: "What format do you need?" Three branches: "Polars DataFrame" leads to to_polars(), "pandas DataFrame" leads to to_pandas(), "Don't care / native" leads to collect(). Each terminal node shows when it involves format conversion (with a warning icon for performance cost) vs native output (with a green checkmark). A secondary layer shows input backend x output format matrix with conversion cost indicators. Clicking a terminal operation shows the internal compilation path. Colors: Teal for relation elements. Learning objective: Select the appropriate terminal operation based on output format requirements and performance considerations (Bloom: Evaluate).
</details>

## Key Takeaways

- The `conform` operation applies TypeSpec-driven transformations (rename, cast, null-fill, column filter) at compile time when column information becomes available.
- `unnest` expands struct columns into separate top-level columns using a separator-based naming convention, handling nested data denormalization.
- The build-then-collect pattern separates AST construction (free, backend-agnostic) from compilation and execution (costly, backend-specific).
- Terminal operations (`to_polars`, `to_pandas`, `collect`) are the only methods that trigger actual computation; everything else is lazy AST construction.
- `to_polars()` and `to_pandas()` guarantee a specific output format, performing conversion if needed, while `collect()` returns the backend's native format.
- Built pipelines are reusable and composable: they can be collected multiple times and extended with additional operations without modifying the original.
- The conform operation's deferred evaluation design handles cases where schema information depends on upstream operations in the same pipeline.
