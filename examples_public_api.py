#!/usr/bin/env python3
"""
Mountain Ash Expressions - Public API Examples

This file demonstrates how to use the Mountain Ash public API for building
cross-backend DataFrame expressions.

The API is designed to work identically across Polars, Pandas (via Narwhals),
and Ibis backends.
"""

import polars as pl
import pandas as pd
import ibis
import mountainash_expressions as ma

# ============================================================
# Example 1: Basic Column References and Comparisons
# ============================================================

print("=" * 60)
print("Example 1: Basic Comparisons")
print("=" * 60)

# Create sample DataFrame
df_polars = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "age": [25, 30, 35, 28, 32],
    "score": [85, 92, 78, 95, 88]
})

# Build expression: age > 30
expr = ma.col("age").gt(30)

# Compile and use with Polars
result = ma.filter(df_polars, expr)
print(f"\nPeople older than 30:")
print(result)

# ============================================================
# Example 2: Chained Operations
# ============================================================

print("\n" + "=" * 60)
print("Example 2: Chained Operations")
print("=" * 60)

# Build complex expression: (age > 25) AND (score >= 85)
expr = ma.col("age").gt(25).and_(ma.col("score").ge(85))

result = ma.filter(df_polars, expr)
print(f"\nPeople over 25 with score >= 85:")
print(result)

# ============================================================
# Example 3: Using Python Magic Operators
# ============================================================

print("\n" + "=" * 60)
print("Example 3: Python Magic Operators")
print("=" * 60)

# Same as above, but using Python operators: (age > 30) & (score >= 85)
expr = (ma.col("age") > 30) & (ma.col("score") >= 85)

result = ma.filter(df_polars, expr)
print(f"\nUsing Python operators - People over 30 with score >= 85:")
print(result)

# ============================================================
# Example 4: Collection Operations (IN / NOT IN)
# ============================================================

print("\n" + "=" * 60)
print("Example 4: Collection Operations")
print("=" * 60)

# Check if name is in list
expr = ma.col("name").is_in(["Alice", "Bob", "Eve"])

result = ma.filter(df_polars, expr)
print(f"\nPeople named Alice, Bob, or Eve:")
print(result)

# Check if age NOT in list
expr = ma.col("age").is_not_in([25, 30])

result = ma.filter(df_polars, expr)
print(f"\nPeople whose age is not 25 or 30:")
print(result)

# ============================================================
# Example 5: Null Checks
# ============================================================

print("\n" + "=" * 60)
print("Example 5: Null Checks")
print("=" * 60)

# DataFrame with nulls
df_with_nulls = pl.DataFrame({
    "name": ["Alice", "Bob", None, "David", None],
    "age": [25, 30, 35, None, 32],
    "score": [85, 92, 78, 95, None]
})

# Find rows where score is null
expr = ma.col("score").is_null()

result = df_with_nulls.filter(expr.compile(df_with_nulls))
print(f"\nRows where score is null:")
print(result)

# Find rows where score is not null
expr = ma.col("score").is_not_null()

result = df_with_nulls.filter(expr.compile(df_with_nulls))
print(f"\nRows where score is not null:")
print(result)

# ============================================================
# Example 6: Logical Combinators
# ============================================================

print("\n" + "=" * 60)
print("Example 6: Logical Combinators")
print("=" * 60)

# Combine multiple conditions with and_()
conditions = [
    ma.col("age").gt(25),
    ma.col("score").ge(85),
    ma.col("score").lt(90)  # Changed to numeric comparison to avoid string literal issues
]
expr = ma.and_(*conditions)

result = ma.filter(df_polars, expr)
print(f"\nUsing and_() combinator:")
print(result)

# Combine with or_()
conditions = [
    ma.col("age").lt(26),
    ma.col("score").gt(90)
]
expr = ma.or_(*conditions)

result = ma.filter(df_polars, expr)
print(f"\nUsing or_() combinator (age < 26 OR score > 90):")
print(result)

# ============================================================
# Example 7: Negation
# ============================================================

print("\n" + "=" * 60)
print("Example 7: Negation")
print("=" * 60)

# NOT (age > 30)
expr = ma.not_(ma.col("age").gt(30))

result = ma.filter(df_polars, expr)
print(f"\nPeople NOT older than 30:")
print(result)

# Using ~ operator
expr = ~(ma.col("age") > 30)

result = ma.filter(df_polars, expr)
print(f"\nUsing ~ operator - People NOT older than 30:")
print(result)

# ============================================================
# Example 8: Cross-Backend Compatibility
# ============================================================

print("\n" + "=" * 60)
print("Example 8: Cross-Backend Compatibility")
print("=" * 60)

# Same expression works with Polars, Pandas (via Narwhals), and Ibis
expr = ma.col("age").gt(28)

# Polars
df_polars = pl.DataFrame({
    "age": [25, 30, 35, 28, 32]
})
result_polars = ma.filter(df_polars, expr)
print(f"\nPolars result (age > 28):")
print(result_polars)

# Pandas via Narwhals
df_pandas = pd.DataFrame({
    "age": [25, 30, 35, 28, 32]
})
import narwhals as nw
df_nw = nw.from_native(df_pandas)
result_nw = ma.filter(df_nw, expr)
print(f"\nNarwhals/Pandas result (age > 28):")
print(result_nw.to_native())

# Ibis
ibis.set_backend("duckdb")
df_ibis = ibis.memtable({
    "age": [25, 30, 35, 28, 32]
})
result_ibis = ma.filter(df_ibis, expr)
print(f"\nIbis result (age > 28):")
print(result_ibis.execute())

# ============================================================
# Example 9: Manual Compilation (Advanced)
# ============================================================

print("\n" + "=" * 60)
print("Example 9: Manual Compilation (Advanced)")
print("=" * 60)

# Build expression
expr = ma.col("age").gt(30)

# Compile to backend-specific expression
polars_expr = expr.compile(df_polars)
print(f"\nCompiled to Polars expression: {type(polars_expr)}")

# Use compiled expression directly
result = df_polars.filter(polars_expr)
print(f"Result using compiled expression:")
print(result)

# ============================================================
# Example 10: Complex Real-World Query
# ============================================================

print("\n" + "=" * 60)
print("Example 10: Complex Real-World Query")
print("=" * 60)

# Create a more complex DataFrame
df_employees = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace"],
    "department": ["Engineering", "Sales", "Engineering", "HR", "Sales", "Engineering", "HR"],
    "age": [25, 30, 35, 28, 32, 29, 31],
    "salary": [70000, 65000, 85000, 60000, 75000, 72000, 68000],
    "years_experience": [2, 5, 10, 3, 7, 4, 6]
})

# Find engineering employees over 27 with more than 3 years experience
# and salary above 70k
expr = ma.and_(
    ma.col("age").gt(27),
    ma.col("years_experience").gt(3),
    ma.col("salary").ge(70000)
)

result = ma.filter(df_employees, expr)
print(f"\nSenior employees (age > 27, experience > 3, salary >= 70k):")
print(result)

# Alternative using chaining and magic operators
expr = (
    (ma.col("age") > 27) &
    (ma.col("years_experience") > 3) &
    (ma.col("salary") >= 70000)
)

result = ma.filter(df_employees, expr)
print(f"\nSame query using operators:")
print(result)

# ============================================================
# Example 11: Working with Literals
# ============================================================

print("\n" + "=" * 60)
print("Example 11: Working with Literals")
print("=" * 60)

# Compare column with literal value
expr = ma.col("age").eq(ma.lit(30))

result = ma.filter(df_polars, expr)
print(f"\nPeople exactly 30 years old:")
print(result)

# ============================================================
# Example 12: All Comparison Operators
# ============================================================

print("\n" + "=" * 60)
print("Example 12: All Comparison Operators")
print("=" * 60)

print("\nEqual (==):", df_polars.filter(ma.col("age").eq(30).compile(df_polars)).height, "rows")
print("Not Equal (!=):", df_polars.filter(ma.col("age").ne(30).compile(df_polars)).height, "rows")
print("Greater Than (>):", df_polars.filter(ma.col("age").gt(30).compile(df_polars)).height, "rows")
print("Less Than (<):", df_polars.filter(ma.col("age").lt(30).compile(df_polars)).height, "rows")
print("Greater or Equal (>=):", df_polars.filter(ma.col("age").ge(30).compile(df_polars)).height, "rows")
print("Less or Equal (<=):", df_polars.filter(ma.col("age").le(30).compile(df_polars)).height, "rows")

# ============================================================
# Summary
# ============================================================

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("""
Mountain Ash Expressions provides a unified API for building expressions
that work across Polars, Pandas (via Narwhals), and Ibis backends.

Key Features:
- Fluent, chainable API (col().gt().and_())
- Python magic operators (&, |, ~, ==, >, <, etc.)
- Collection operations (is_in, is_not_in)
- Null checks (is_null, is_not_null)
- Logical combinators (and_, or_, not_)
- Cross-backend compatibility (same code, different backends)
- Type-safe expression building

Import and use:
    >>> import mountainash_expressions as ma
    >>> expr = ma.col('age').gt(30)
    >>> result = ma.filter(df, expr)

For more information, see the test files and documentation.
""")

print("=" * 60)
print("All examples completed successfully!")
print("=" * 60)
