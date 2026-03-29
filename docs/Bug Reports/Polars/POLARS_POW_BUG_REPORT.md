# Polars Bug: `pl.lit(value, dtype=X).pow(col)` Returns Wrong Results

## Summary

When using `pl.lit()` with an explicit `dtype` parameter in a power operation with a column, Polars returns incorrect results (typically 0). The same operation works correctly when:
- Using `pl.lit()` without explicit dtype
- Adding a `.cast()` operation after `pl.lit()`
- Using the `**` operator directly

## Environment

- Polars version: 1.16.0
- Python version: 3.x

## Minimal Reproduction

```python
import polars as pl

df = pl.DataFrame({'x': [10]})

# FAILS: Returns 0 instead of 1024
expr1 = pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))
result1 = df.select(expr1.alias('r'))['r'][0]
print(f"pl.lit(2, dtype=Int8).pow(col(10)) = {result1}")  # Expected: 1024, Got: 0

# FAILS: Even with Int16 which can hold 1024
expr2 = pl.lit(128, dtype=pl.Int16).pow(pl.col('x'))
result2 = df.select(expr2.alias('r'))['r'][0]
print(f"pl.lit(128, dtype=Int16).pow(col(10)) = {result2}")  # Expected: 1024, Got: 0

# WORKS: Without explicit dtype
expr3 = pl.lit(2).pow(pl.col('x'))
result3 = df.select(expr3.alias('r'))['r'][0]
print(f"pl.lit(2).pow(col(10)) = {result3}")  # Expected: 1024, Got: 1024 ✅

# WORKS: With cast after lit
expr4 = pl.lit(2, dtype=pl.Int8).cast(pl.Int16).pow(pl.col('x'))
result4 = df.select(expr4.alias('r'))['r'][0]
print(f"pl.lit(2, dtype=Int8).cast(Int16).pow(col(10)) = {result4}")  # Expected: 1024, Got: 1024 ✅

# WORKS: Using ** operator
expr5 = pl.lit(2) ** pl.col('x')
result5 = df.select(expr5.alias('r'))['r'][0]
print(f"pl.lit(2) ** col(10) = {result5}")  # Expected: 1024, Got: 1024 ✅
```

## Expected Behavior

All expressions should return 1024 (2^10).

## Actual Behavior

Expressions using `pl.lit(value, dtype=X).pow(col)` return 0, even when the dtype can hold the result.

## Analysis

The bug appears to be in how `.pow()` handles typed literals. The issue is NOT overflow (Int16 can hold 1024), but something specific to the interaction between:
1. Explicit dtype in `pl.lit()`
2. The `.pow()` method
3. A column expression as the exponent

## Workarounds

1. Don't specify dtype: `pl.lit(2).pow(col)` ✅
2. Add a cast: `pl.lit(2, dtype=X).cast(Y).pow(col)` ✅
3. Use ** operator: `pl.lit(2) ** col` ✅

## Impact

This affects Ibis users, as the Ibis Polars backend always passes explicit dtypes to `pl.lit()` for type consistency.

