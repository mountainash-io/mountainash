---
title: Expression Operations
description: Concrete expression operations including comparison, arithmetic, boolean, string, datetime, aggregation, window functions, cast, duration, count_records, and correlation.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 5: Expression Operations

## Summary

Concrete expression operations: comparison, arithmetic, boolean, string, and datetime operations; aggregation and window functions; cast, duration, count_records, and correlation.

## Concepts Covered

- Comparison Operations
- Arithmetic Operations
- Boolean Operations
- String Operations
- Datetime Operations
- Aggregation Functions
- Window Functions
- cast Operation
- duration Function
- count_records Function
- corr Function

## Prerequisites

- [Chapter 2. Core Infrastructure](../02-core-infrastructure/)
- [Chapter 3. Expression API Basics](../03-expression-api-basics/)
- [Chapter 4. Expression Namespaces and Functions](../04-expression-namespaces-and-functions/)

---

## Introduction

Previous chapters introduced the expression API's structure and namespaces. This chapter catalogs the concrete operations available within that framework, organized by category. Each operation maps to an enum value in the constants module, generates a specific AST node, and compiles to a backend-native function call.

Understanding the full operation catalog lets you determine, at a glance, whether a given data transformation can be expressed within mountainash's abstract layer or whether a `native()` escape hatch is needed.

## Comparison Operations

Comparison operations evaluate two expressions and produce a boolean result indicating the relationship between their values. These operations form the basis of filter predicates and conditional logic throughout mountainash.

Six comparison operators are defined in `CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS`. Each corresponds to a method on `BaseExpressionAPI` and a Python operator overload.

```python
import mountainash as ma

# Method syntax
adults = ma.col("age").ge(18)
premium = ma.col("tier").eq("gold")
outliers = ma.col("z_score").gt(3.0)

# Operator syntax (equivalent)
adults = ma.col("age") >= 18
premium = ma.col("tier") == "gold"
outliers = ma.col("z_score") > 3.0
```

| Operator | Method | Enum Value | Description |
|----------|--------|-----------|-------------|
| `==` | `eq` | EQ | Equal to |
| `!=` | `ne` | NE | Not equal to |
| `>` | `gt` | GT | Greater than |
| `<` | `lt` | LT | Less than |
| `>=` | `ge` | GE | Greater than or equal |
| `<=` | `le` | LE | Less than or equal |

Comparison operations follow SQL-style null semantics. Comparing any value to null produces null, not false. To test for null specifically, use `is_null()` or `is_not_null()` instead of equality comparison.

## Arithmetic Operations

Arithmetic operations perform mathematical computations on numeric expressions. They accept another expression (or a scalar that gets auto-wrapped as `lit()`) and produce a numeric result.

```python
import mountainash as ma

# Revenue calculation
revenue = ma.col("price") * ma.col("quantity")
margin = ma.col("revenue") - ma.col("cost")
pct_change = (ma.col("new") - ma.col("old")) / ma.col("old") * 100
remainder = ma.col("total") % ma.lit(12)
squared = ma.col("value") ** 2
```

The seven arithmetic operators are defined in `CONST_EXPRESSION_ARITHMETIC_OPERATORS`.

- `add` / `+` -- Addition
- `subtract` / `-` -- Subtraction
- `multiply` / `*` -- Multiplication
- `divide` / `/` -- Division (floating-point)
- `modulo` / `%` -- Remainder
- `power` / `**` -- Exponentiation
- `floor_divide` / `//` -- Integer division (rounds toward negative infinity)

Division by zero behavior varies by backend. Polars produces `inf` or `NaN` for floating-point division by zero. SQL backends may raise an error. Mountainash does not normalize this behavior across backends.

## Boolean Operations

Boolean operations combine or negate boolean expressions using logical connectives. They are defined in `CONST_EXPRESSION_LOGICAL_OPERATORS` and are only available on `BooleanExpressionAPI` objects (the result type of comparison operations).

```python
import mountainash as ma

# Logical AND
eligible = (ma.col("age") >= 18) & (ma.col("score") >= 80)

# Logical OR
flagged = (ma.col("risk") == "high") | (ma.col("amount") > 10000)

# Logical NOT
inactive = ~ma.col("is_active")
```

The boolean operations include AND, OR, NOT, and two XOR variants. XOR exclusive returns true when exactly one operand is true, while XOR parity returns true when an odd number of operands are true. In practice, `and_` and `or_` are used far more frequently than the XOR variants.

#### Diagram: Boolean Operation Truth Tables
<iframe src="../../sims/boolean-truth-tables/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Boolean Operation Truth Tables</summary>
Type: microsim
**sim-id:** boolean-truth-tables<br/>
**Library:** p5.js<br/>
**Status:** Specified

An interactive truth table visualization. Four tabs at the top select AND, OR, NOT, and XOR operations. Each tab shows a grid with input values (True, False, Null) on axes and result values in cells. Cells are color-coded: green for True, red for False, gray for Null. Clicking a cell highlights the corresponding row and column headers. A special "three-valued" toggle adds the Null row/column to show SQL-style ternary logic behavior. Learning objective: Predict the output of boolean operations including null propagation behavior (Bloom: Apply).
</details>

## String Operations

String operations transform text data within expressions. They are accessed through the `.str` namespace (covered in Chapter 4) and map to `CONST_EXPRESSION_STRING_OPERATORS` enum values.

Beyond the basic operations listed in the namespace chapter, string operations also include pattern matching through `CONST_EXPRESSION_PATTERN_OPERATORS`. These enable SQL-style LIKE patterns and regular expression matching.

```python
import mountainash as ma

# Pattern matching
sql_like = ma.col("name").str.like("J%")         # SQL LIKE pattern
regex_match = ma.col("email").str.regex_match(r"^[\w.]+@[\w.]+$")
regex_find = ma.col("text").str.regex_contains(r"\d{3}-\d{4}")
cleaned = ma.col("phone").str.regex_replace(r"\D", "")
```

String operations that return boolean results (contains, starts_with, ends_with, like, regex_match, regex_contains) produce `BooleanExpressionAPI` objects, enabling their use as filter predicates.

- Case conversion: `upper()`, `lower()`
- Whitespace: `trim()`, `ltrim()`, `rtrim()`
- Searching: `contains()`, `starts_with()`, `ends_with()`, `length()`
- Extraction: `substring(offset, length)`
- Transformation: `replace()`, `concat()`
- Pattern: `like()`, `regex_match()`, `regex_contains()`, `regex_replace()`

## Datetime Operations

Datetime operations extract components from temporal values, perform date arithmetic, and truncate timestamps to specific precision levels. They are accessed through the `.dt` namespace and map to `CONST_EXPRESSION_TEMPORAL_OPERATORS`.

```python
import mountainash as ma

# Extraction
fiscal_quarter = ma.col("invoice_date").dt.quarter()
hour_of_day = ma.col("login_time").dt.hour()

# Arithmetic
deadline = ma.col("created_at").dt.add_days(30)
age_days = ma.col("today").dt.diff_days(ma.col("birth_date"))

# Truncation
monthly_bucket = ma.col("timestamp").dt.truncate("month")

# Flexible offset
shifted = ma.col("event_time").dt.offset_by("2h30m")
```

The temporal operator enum contains 24 operations organized into four groups. Extraction operations return integer values. Add operations return temporal values shifted forward. Difference operations return numeric durations between two temporal values. Truncation rounds a timestamp down to the specified unit boundary.

| Category | Operations | Return Type |
|----------|-----------|-------------|
| Extraction | year, month, day, hour, minute, second, weekday, week, quarter | Integer |
| Add | add_days, add_hours, add_minutes, add_seconds, add_months, add_years | Temporal |
| Difference | diff_days, diff_hours, diff_minutes, diff_seconds, diff_months, diff_years | Numeric |
| Truncation | truncate | Temporal |
| Flexible | offset_by | Temporal |

## Aggregation Functions

Aggregation functions reduce multiple values to a single value. They operate vertically across rows within a column (or within a group when used with `group_by`). Common aggregations include sum, mean, count, min, max, and standard deviation.

```python
import mountainash as ma

# Column-level aggregations (used in group_by context)
total = ma.col("amount").sum()
average = ma.col("score").mean()
highest = ma.col("price").max()
lowest = ma.col("price").min()
records = ma.col("id").count()
spread = ma.col("value").std()
```

Aggregation functions are typically used within a `group_by(...).agg(...)` context on relations (covered in Chapter 10). When used outside a group-by, they aggregate the entire column into a single scalar value.

The aggregation functions available on expressions include:

- **Numeric**: `sum()`, `mean()`, `std()`, `var()`, `min()`, `max()`
- **Counting**: `count()`, `n_unique()`
- **Positional**: `first()`, `last()`
- **Collection**: `list()` (collect values into an array)

## Window Functions

Window functions compute values across a set of rows related to the current row, without collapsing them into a single result. Unlike aggregations that reduce rows, window functions add computed values while preserving the original row count.

Window functions require a window specification that defines the partition (grouping), ordering, and optional frame bounds. The `.over()` method on an expression defines this specification.

```python
import mountainash as ma

# Running total within each department
running_total = ma.col("salary").sum().over(
    partition_by="department",
    order_by="hire_date"
)

# Rank within each group
rank = ma.col("score").rank().over(partition_by="team")
```

Window functions are one of the more complex expression types because they involve both the aggregation logic (sum, rank, lag, lead) and the windowing logic (partition, order, frame). The AST represents these as `WindowFunctionNode` objects that reference a `WindowSpec` for their partition and ordering configuration.

## cast Operation

The `cast` operation converts an expression from one data type to another. It accepts a target type specified as a `MountainashDtype` value, a canonical string, or an alias string, and produces a `CastNode` in the expression AST.

```python
import mountainash as ma

# Cast string to integer
age_int = ma.col("age_str").cast("i64")

# Cast integer to float
ratio = ma.col("count").cast("fp64")

# Cast using MountainashDtype enum
from mountainash.core.dtypes import MountainashDtype
amount = ma.col("amount").cast(MountainashDtype.FP64)
```

The cast operation uses the `resolve_dtype()` function internally to normalize the target type. This means all the alias forms described in Chapter 2 (MountainashDtype section) are accepted. The backend compiler translates the canonical type string to the appropriate backend-native type.

!!! note "Safe vs Unsafe Casts"
    Not all type conversions are safe. Casting a floating-point column to integer loses decimal precision. Casting a string column to integer fails if any value is not a valid number. Mountainash does not validate cast safety at build time; errors surface at execution time from the backend.

## duration Function

The `duration` function creates literal duration expressions from component values. It provides a way to construct temporal offsets as first-class expression values, suitable for date arithmetic.

```python
import mountainash as ma

# Create a duration of 7 days
week = ma.duration(days=7)

# Create a complex duration
interval = ma.duration(hours=2, minutes=30)

# Use in arithmetic
due_date = ma.col("created_at").dt.offset_by(week)
```

Duration expressions compile to the backend's native duration type. For Polars, this becomes a `Duration` literal. For SQL backends, this compiles to an INTERVAL expression. The `duration` function accepts keyword arguments for days, hours, minutes, seconds, and milliseconds.

## count_records Function

The `count_records` function returns the total number of rows in a relation or group. Unlike `col("x").count()`, which counts non-null values in a specific column, `count_records()` counts all rows regardless of null values.

```python
import mountainash as ma

# Count all rows (no column reference needed)
total = ma.count_records()

# In a group_by context
group_counts = (
    relation(df)
    .group_by("category")
    .agg(ma.count_records().alias("n"))
)
```

This function is equivalent to SQL's `COUNT(*)`. It does not take any column argument and always returns the full row count. It is particularly useful in aggregation contexts where you want to know how many rows fell into each group.

## corr Function

The `corr` function computes the Pearson correlation coefficient between two numeric expressions. It is an aggregation function that reduces pairs of values to a single scalar in the range \([-1, 1]\).

```python
import mountainash as ma

# Compute correlation between price and quantity
price_qty_corr = ma.corr(ma.col("price"), ma.col("quantity"))

# In a group_by context
group_corr = (
    relation(df)
    .group_by("region")
    .agg(ma.corr(ma.col("income"), ma.col("spending")).alias("income_spending_corr"))
)
```

The correlation coefficient measures linear association. A value of \(1\) indicates perfect positive correlation, \(-1\) indicates perfect negative correlation, and \(0\) indicates no linear relationship. The `corr` function is a module-level function because it requires two expression arguments rather than operating on a single expression.

#### Diagram: Expression Operation Categories
<iframe src="../../sims/expression-operation-categories/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Expression Operation Categories</summary>
Type: chart
**sim-id:** expression-operation-categories<br/>
**Library:** Chart.js<br/>
**Status:** Specified

A horizontal bar chart showing the number of operations in each category: Comparison (6), Arithmetic (7), Boolean (5), String (12), Pattern (4), Temporal (24), Conditional (3), Aggregation (8+), Window (varies). Bars are color-coded by taxonomy group (EXAPI in DarkGreen). Clicking a bar expands a popup listing all operations in that category. Hovering shows the enum class name. Learning objective: Survey the breadth of mountainash's expression operation catalog and identify which categories are most extensive (Bloom: Remember).
</details>

## Key Takeaways

- Comparison operations (eq, ne, gt, lt, ge, le) produce boolean expressions and follow SQL-style null semantics where comparing with null yields null.
- Arithmetic operations (+, -, *, /, %, **, //) support both method syntax and Python operator overloading, with division-by-zero behavior varying by backend.
- Boolean operations (and_, or_, not_, xor) combine boolean expressions using three-valued logic that propagates null through logical connectives.
- String operations span case conversion, searching, extraction, and pattern matching (LIKE, regex), with boolean-returning methods usable as filter predicates.
- Datetime operations cover 24 temporal transformations including extraction, arithmetic, difference calculation, and truncation.
- Aggregation functions reduce rows vertically (sum, mean, count) and are typically used within group_by contexts on relations.
- Window functions compute values across related rows without collapsing, requiring partition and ordering specifications via `.over()`.
- The `cast` operation normalizes type references through `resolve_dtype()`, accepting any alias form supported by MountainashDtype.
