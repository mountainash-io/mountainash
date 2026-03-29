# Polars Bug Report: Silent Integer Overflow in Power Operations

## Summary

When using `.pow()` on a literal with an explicit small integer dtype (Int8), Polars silently returns 0 when the result would overflow, instead of either automatically upcasting or raising an error.

## Environment

- **Polars version**: 1.16.0
- **Python version**: 3.x
- **OS**: Linux

## Minimal Reproduction

```python
import polars as pl

df = pl.DataFrame({'x': [10]})

# Case 1: With Int8 dtype - FAILS (returns 0)
result1 = df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('x')))
print(f"pl.lit(2, dtype=Int8).pow(col(10)) = {result1['literal'][0]}")
# Expected: 1024 or OverflowError
# Actual: 0

# Case 2: Without dtype - WORKS (returns 1024)
result2 = df.select(pl.lit(2).pow(pl.col('x')))
print(f"pl.lit(2).pow(col(10)) = {result2['literal'][0]}")
# Expected: 1024
# Actual: 1024 ✅

# Case 3: With Int16 dtype - WORKS (returns 1024)
result3 = df.select(pl.lit(2, dtype=pl.Int16).pow(pl.col('x')))
print(f"pl.lit(2, dtype=Int16).pow(col(10)) = {result3['literal'][0]}")
# Expected: 1024
# Actual: 1024 ✅

# Case 4: Using ** operator with Int8 - ALSO FAILS
result4 = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')))
print(f"pl.lit(2, dtype=Int8) ** col(10) = {result4['literal'][0]}")
# Expected: 1024
# Actual: 0 ❌

# Case 5: Using ** operator WITHOUT dtype - WORKS
result5 = df.select((pl.lit(2) ** pl.col('x')))
print(f"pl.lit(2) ** col(10) = {result5['literal'][0]}")
# Expected: 1024
# Actual: 1024 ✅
```

## Expected Behavior

When computing `2^10 = 1024` with an Int8 base, Polars should either:

1. **Automatically upcast** the result to a wider type (like the `**` operator does), OR
2. **Raise an overflow error** to alert the user

## Actual Behavior

Polars silently returns **0** when using `.pow()` method with an Int8 dtype that would overflow.

## Analysis

**Mathematical correctness**:
- 2^10 = 1024
- Int8 range: -128 to 127
- 1024 > 127, so overflow occurs

**Inconsistent behavior within power operations**:
- With explicit Int8 dtype: Both `.pow()` and `**` return 0 ❌
- Without explicit dtype: Both `.pow()` and `**` return 1024 ✅

**Inconsistent with other operations**:

| Operation | Operands | Result Type | Value | Behavior |
|-----------|----------|-------------|-------|----------|
| `Int8(63) * Int8(63)` | lit * lit | Int8 | -127 | ✅ Wraps |
| `Int8(63) * col(63)` | lit * col | **Int64** | 3969 | ✅ **Auto-upcasts!** |
| `Int8(2) ** col(10)` | lit ** col | Int8 | **0** | ❌ **Returns 0** |

**Key finding**: Multiplication with a column **automatically upcasts to Int64**, but power operations with a column **do not upcast and return 0**.

**Expected behavior**: Power operations should upcast like multiplication does when overflow would occur.

## Why This Matters

1. **Silent data corruption**: Returns plausible-looking wrong results (0)
2. **Inconsistent with multiplication**: Multiplication auto-upcasts with columns, power doesn't
3. **Not even wrapping behavior**: Result is 0, not -128 (expected wrapped value)
4. **Impacts downstream users**: Ibis framework relies on power operations with typed literals

## Workarounds

```python
# Option 1: Don't specify dtype (BEST)
pl.lit(2).pow(col)  # ✅
pl.lit(2) ** col    # ✅

# Option 2: Use wider type
pl.lit(2, dtype=pl.Int64).pow(col)  # ✅
pl.lit(2, dtype=pl.Int64) ** col    # ✅

# Option 3: Cast after creation
pl.lit(2, dtype=pl.Int8).cast(pl.Int64).pow(col)  # ✅
pl.lit(2, dtype=pl.Int8).cast(pl.Int64) ** col    # ✅
```

## Proposed Fix

Make power operations consistent with multiplication:
- When one operand is a column, automatically upcast to Int64 (like multiplication does)
- This would match the existing behavior for multiplication operations
- Ensures mathematical correctness without silent failures

**Comparison**:
```python
# Current behavior
Int8(63) * col(63)  → Int64: 3969 ✅  (auto-upcasts)
Int8(2) ** col(10)  → Int8:  0    ❌  (doesn't upcast, returns 0)

# Desired behavior
Int8(2) ** col(10)  → Int64: 1024 ✅  (should auto-upcast like multiplication)
```

## Related

This bug affects Ibis framework users, as Ibis Polars backend uses `.pow()` method and passes explicit dtypes for type consistency.
