---
title: Expression Namespaces and Functions
description: Namespace-based expression extensions (.str, .dt, .struct, .list, .name), the NamespaceDescriptor mechanism, and module-level helper functions.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 4: Expression Namespaces and Functions

## Summary

Namespace-based expression extensions (.str, .dt, .struct, .list, .name), the NamespaceDescriptor mechanism, and module-level helper functions (when, coalesce, greatest, least, native).

---

## Introduction

While the base expression API provides arithmetic, comparison, and boolean operations, many common transformations are specific to a particular data type. String operations like `upper()` and `contains()` only make sense on text columns. Datetime extraction like `year()` and `month()` only applies to temporal data. Mountainash organizes these type-specific operations into namespaces accessed via dot notation on any expression.

This chapter covers the five built-in namespaces, explains how the namespace descriptor mechanism works internally, and introduces module-level helper functions that operate across multiple expressions.

<!-- concept:37 -->
## NamespaceDescriptor

Before exploring individual namespaces, it is important to understand how they are implemented. The `NamespaceDescriptor` is a Python descriptor that provides lazy access to namespace objects. When you access `.str` on an expression, the descriptor creates a namespace instance bound to that expression and returns it.

The descriptor mechanism allows namespaces to be defined as separate classes with their own methods, while appearing as simple attribute access on the expression object. This keeps the base expression class clean while enabling unlimited type-specific extensions.

```python
class NamespaceDescriptor:
    """Descriptor that creates namespace instances on access."""

    def __init__(self, namespace_class):
        self.namespace_class = namespace_class

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.namespace_class(obj)
```

When you write `ma.col("name").str.upper()`, the following sequence occurs. First, `ma.col("name")` creates a `FieldReferenceNode`. Second, `.str` triggers the descriptor, which creates a string namespace bound to that expression. Third, `.upper()` calls the namespace method, which builds a new `ScalarFunctionNode` with the string upper function key.

#### Diagram: Namespace Descriptor Mechanism
<iframe src="../../sims/namespace-descriptor/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Namespace Descriptor Mechanism</summary>
Type: workflow
**sim-id:** namespace-descriptor<br/>
**Library:** vis-network<br/>
**Status:** Specified

A sequence diagram showing the interaction between user code, the expression object, the NamespaceDescriptor, and the namespace class. Step 1: user accesses `.str`. Step 2: descriptor `__get__` is called with the expression instance. Step 3: descriptor instantiates the namespace class with the expression. Step 4: user calls `.upper()` on the namespace. Step 5: namespace method builds a ScalarFunctionNode. Each step is a node connected by directed edges. Hovering over a step shows the Python code executing at that point. Colors: DarkGreen for expression API elements. Learning objective: Explain how Python descriptors enable clean namespace syntax without polluting the base class (Bloom: Understand).
</details>

<!-- concept:32 -->
## String Namespace

The string namespace (`.str`) provides operations for manipulating text data within expressions. It is accessed via the `.str` attribute on any expression and exposes methods for case conversion, searching, extraction, and transformation.

```python
import mountainash as ma

# Case conversion
upper_name = ma.col("name").str.upper()
lower_email = ma.col("email").str.lower()

# Searching
has_gmail = ma.col("email").str.contains("gmail")
starts_with_a = ma.col("name").str.starts_with("A")

# Extraction and transformation
trimmed = ma.col("input").str.trim()
first_five = ma.col("code").str.substring(0, 5)
replaced = ma.col("text").str.replace("old", "new")
```

The string namespace methods map to `CONST_EXPRESSION_STRING_OPERATORS` enum values internally. Each method creates a `ScalarFunctionNode` with the appropriate function key and arguments.

| Method | Operation | Description |
|--------|-----------|-------------|
| `upper()` | UPPER | Convert to uppercase |
| `lower()` | LOWER | Convert to lowercase |
| `trim()` | TRIM | Remove leading/trailing whitespace |
| `ltrim()` | LTRIM | Remove leading whitespace |
| `rtrim()` | RTRIM | Remove trailing whitespace |
| `contains(pat)` | CONTAINS | Check if string contains pattern |
| `starts_with(prefix)` | STARTS_WITH | Check if starts with prefix |
| `ends_with(suffix)` | ENDS_WITH | Check if ends with suffix |
| `substring(offset, length)` | SUBSTRING | Extract substring |
| `replace(old, new)` | REPLACE | Replace occurrences |
| `length()` | LENGTH | Get string length |

<!-- concept:33 -->
## Datetime Namespace

The datetime namespace (`.dt`) provides operations for extracting components from temporal values and performing date arithmetic. It is available on expressions that reference datetime, date, or time columns.

```python
import mountainash as ma

# Component extraction
year = ma.col("created_at").dt.year()
month = ma.col("created_at").dt.month()
day_of_week = ma.col("created_at").dt.weekday()

# Date arithmetic
future = ma.col("start_date").dt.add_days(30)
diff = ma.col("end_date").dt.diff_days(ma.col("start_date"))

# Truncation
monthly = ma.col("timestamp").dt.truncate("month")
```

The datetime namespace maps to `CONST_EXPRESSION_TEMPORAL_OPERATORS`. Operations are grouped into extraction (read components), arithmetic (add/subtract durations), and truncation (round to a unit boundary).

- **Extraction**: `year()`, `month()`, `day()`, `hour()`, `minute()`, `second()`, `weekday()`, `week()`, `quarter()`
- **Add**: `add_days(n)`, `add_hours(n)`, `add_minutes(n)`, `add_seconds(n)`, `add_months(n)`, `add_years(n)`
- **Difference**: `diff_days(other)`, `diff_hours(other)`, `diff_minutes(other)`, `diff_seconds(other)`
- **Truncation**: `truncate(unit)` where unit is "day", "hour", "month", "year", etc.
- **Flexible**: `offset_by(duration_string)` for complex duration offsets like "1d2h30m"

<!-- concept:34 -->
## Struct Namespace

The struct namespace (`.struct`) provides operations for working with nested structured data. A struct column contains named fields within each cell, similar to a JSON object or a Python dictionary. The struct namespace enables field extraction and manipulation without flattening the entire structure.

```python
import mountainash as ma

# Extract a field from a struct column
city = ma.col("address").struct.field("city")
zip_code = ma.col("address").struct.field("zip")
```

Struct operations are particularly important when working with semi-structured data sources (JSON files, nested API responses). The struct namespace allows you to drill into nested fields while remaining within the expression system, deferring actual extraction to compile time.

When combined with the `unnest` relation operation (covered in Chapter 11), struct namespaces provide a complete story for denormalizing nested data into flat tabular form.

<!-- concept:35 -->
## List Namespace

The list namespace (`.list`) provides operations for working with array-typed columns where each cell contains a list of values. Common operations include getting list lengths, accessing elements by index, and aggregating list contents.

```python
import mountainash as ma

# List operations
lengths = ma.col("tags").list.len()
first_tag = ma.col("tags").list.get(0)
contains_urgent = ma.col("tags").list.contains("urgent")
```

List columns arise naturally from group-by aggregations that collect values into arrays, from JSON parsing, and from data sources with repeated fields. The list namespace keeps these operations within the expression system rather than requiring Python-level iteration.

<!-- concept:36 -->
## Name Namespace

The name namespace (`.name`) provides operations for renaming, prefixing, and suffixing the output column name of an expression. While `alias()` on `BaseExpressionAPI` sets an absolute name, the name namespace provides relative transformations.

```python
import mountainash as ma

# Absolute naming
total = ma.col("price").multiply(ma.col("qty")).alias("total")

# Relative naming via .name namespace
prefixed = ma.col("revenue").name.prefix("annual_")
suffixed = ma.col("count").name.suffix("_total")
```

The name namespace is particularly useful in `with_columns` operations where you want to create derived columns with systematic naming conventions. Rather than manually constructing each alias, you can apply prefix or suffix transformations that adapt to the source column name.

<!-- concept:38 -->
## when Function

The `when` function creates conditional (if-then-else) expressions. It takes a boolean predicate and returns a builder that accepts `.then()` and `.otherwise()` clauses, enabling SQL-style CASE WHEN logic within the expression system.

```python
import mountainash as ma

# Simple conditional
category = (
    ma.when(ma.col("age") >= 65)
    .then(ma.lit("senior"))
    .when(ma.col("age") >= 18)
    .then(ma.lit("adult"))
    .otherwise(ma.lit("minor"))
    .alias("age_category")
)
```

The `when` function accepts a `BooleanExpressionAPI` expression as its predicate. The `.then()` method specifies the value to use when the predicate is true. Multiple `.when().then()` pairs can be chained (evaluated top-to-bottom, first match wins). The `.otherwise()` clause provides a default value for rows that match none of the predicates.

Under the hood, `when` produces an `IfThenNode` in the expression AST. This node stores paired lists of conditions and values, plus an optional else value. The backend compiler translates this into the native conditional mechanism (Polars `when/then/otherwise`, SQL `CASE WHEN`, etc.).

<!-- concept:39 -->
## coalesce Function

The `coalesce` function accepts multiple expressions and returns the first non-null value for each row. It is a module-level function (not a method) because it operates across multiple independent expressions rather than transforming a single expression.

```python
import mountainash as ma

# Return first non-null name
display_name = ma.coalesce(
    ma.col("nickname"),
    ma.col("preferred_name"),
    ma.col("legal_name"),
).alias("display_name")
```

Coalesce evaluates its arguments left to right. For each row, it returns the value from the first expression that is not null. If all expressions are null for a given row, the result is null.

This function is essential for handling optional data with fallback chains. Common use cases include choosing between preferred and default values, merging data from multiple sources with varying completeness, and implementing "last known value" logic.

<!-- concept:40 -->
## greatest Function

The `greatest` function returns the maximum value across multiple expressions for each row. Unlike aggregation functions that operate vertically (across rows within a column), `greatest` operates horizontally (across columns within a row).

```python
import mountainash as ma

# Find the highest score across three attempts
best_score = ma.greatest(
    ma.col("attempt_1"),
    ma.col("attempt_2"),
    ma.col("attempt_3"),
).alias("best_score")
```

The function compares values element-wise across its arguments. For each row, it selects the largest value. Null values are typically skipped (the greatest non-null value is returned), though exact null semantics may vary by backend.

<!-- concept:41 -->
## least Function

The `least` function is the complement of `greatest`. It returns the minimum value across multiple expressions for each row, operating horizontally across columns within each row.

```python
import mountainash as ma

# Find the earliest date across multiple events
first_contact = ma.least(
    ma.col("email_date"),
    ma.col("call_date"),
    ma.col("meeting_date"),
).alias("first_contact")
```

Together, `greatest` and `least` enable row-level min/max computations without restructuring data. They are particularly useful when comparing values that are naturally stored in separate columns rather than in a single array column.

#### Diagram: Horizontal vs Vertical Operations
<iframe src="../../sims/horizontal-vs-vertical/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Horizontal vs Vertical Operations</summary>
Type: infographic
**sim-id:** horizontal-vs-vertical<br/>
**Library:** p5.js<br/>
**Status:** Specified

A visual comparison showing a small DataFrame grid (4 rows x 3 columns). The left panel highlights a vertical aggregation (sum down a column, producing one value). The right panel highlights a horizontal operation (greatest across a row, producing one value per row). Arrows indicate direction of operation. Toggle button switches between "vertical" (aggregation) and "horizontal" (greatest/least) modes. Color coding: blue for input cells being compared, gold for the output value. Learning objective: Distinguish between vertical aggregation functions and horizontal row-level functions like greatest and least (Bloom: Analyze).
</details>

<!-- concept:42 -->
## native Function

The `native` function provides an escape hatch from mountainash's backend-agnostic expression system. It wraps a backend-specific expression object directly into the mountainash AST, allowing you to use features that mountainash does not yet abstract.

```python
import mountainash as ma
import polars as pl

# Use a Polars-specific expression directly
native_expr = ma.native(pl.col("text").str.extract(r"(\d+)", 1))
```

The `native` function should be used sparingly because it breaks backend portability. An expression containing a `native()` call will only compile correctly on the backend that produced the wrapped expression. However, it is invaluable when you need access to backend-specific functionality that mountainash's abstract layer does not yet cover.

The native expression participates in the AST like any other node, meaning it can be composed with other mountainash expressions. The compiler detects the native node and passes the wrapped expression through without transformation. The backend detection system uses the native expression to verify that the correct backend is being targeted.

## Key Takeaways

- Namespaces (`.str`, `.dt`, `.struct`, `.list`, `.name`) organize type-specific operations into clean, discoverable groups accessed via dot notation.
- The `NamespaceDescriptor` mechanism uses Python descriptors to lazily create namespace instances bound to their parent expression, keeping the base class uncluttered.
- String namespace provides case conversion, searching, extraction, and replacement operations that compile to backend-native string functions.
- Datetime namespace covers component extraction, date arithmetic, and truncation, mapping to the extensive `CONST_EXPRESSION_TEMPORAL_OPERATORS` enum.
- `when().then().otherwise()` creates conditional expressions equivalent to SQL CASE WHEN, producing IfThenNode AST nodes.
- `coalesce()`, `greatest()`, and `least()` are horizontal functions operating across multiple expressions per row, unlike vertical aggregation functions.
- The `native()` function provides a backend-specific escape hatch for operations not yet abstracted by mountainash, at the cost of portability.
- All namespace methods and helper functions produce the same AST node types as base operations, ensuring uniform compilation across backends.
