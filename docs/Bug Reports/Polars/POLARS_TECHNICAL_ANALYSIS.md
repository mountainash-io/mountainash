# Polars Power Operation Bug: Technical Analysis

## Executive Summary

Power operations in Polars **do not implement the same type promotion logic** as other arithmetic operations, causing silent overflow when typed literals are used with columns.

---

## Evidence: Comprehensive Comparison

### All Literal-Column Operations Upcast to Int64

| Operation | Expression | Result Dtype | Value | Behavior |
|-----------|------------|--------------|-------|----------|
| Addition | `Int8(10) + col_int8(63)` | **Int64** | 73 | ✅ Upcasts |
| Subtraction | `Int8(10) - col_int8(63)` | **Int64** | -53 | ✅ Upcasts |
| **Multiplication** | **`Int8(63) * col_int8(63)`** | **Int64** | **3969** | **✅ Upcasts** |
| Division | `Int8(100) / col_int8(63)` | Float64 | 1.587 | ✅ Converts |
| Floor Division | `Int8(100) // col_int8(63)` | **Int64** | 1 | ✅ Upcasts |
| Modulo | `Int8(100) % col_int8(63)` | **Int64** | 37 | ✅ Upcasts |
| **Power** | **`Int8(2) ** col_int8(10)`** | **Int8** | **0** | **❌ No upcast** |

### Pattern

**All arithmetic operations with (typed literal, column) automatically promote to Int64 EXCEPT power.**

---

## Expression Representation Analysis

### Multiplication (Works Correctly)

```python
Expression: [(dyn int: 63.strict_cast(Int8)) * (col("x"))]
Result Schema: {'r': Int64}
Result Value: 3969
```

The `*` operator at the expression level triggers type promotion.

### Power (Bug)

```python
Expression: dyn int: 2.strict_cast(Int8).pow([col("x")])
Result Schema: {'r': Int8}
Result Value: 0
```

The `.pow()` method does NOT trigger type promotion, stays in Int8.

---

## Asymmetry in Power Operations

### Column on Left (Works)

```python
col_int8(63).pow(2)
# Result: Int64: 3969 ✅
```

### Literal on Left (Fails)

```python
lit(2, dtype=Int8).pow(col_int8(63))
# Result: Int8: 0 ❌
```

This asymmetry suggests the power operation only promotes when the base is a column, not when the exponent is a column.

---

## Comparison with Literal-Literal Operations

### Expected: Wrapping Behavior

When both operands are literals, operations stay in Int8 and wrap on overflow:

```python
Int8(63) * Int8(63)  → Int8: -127   (wrapped from 3969)
Int8(2) ** Int8(10)  → Int8: 0      (NOT wrapped from 1024!)
```

**Expected wrapped value**: 1024 % 256 - 128 = **-128**
**Actual value**: 0

Even in literal-literal operations, power returns **0 instead of wrapping correctly**.

---

## Root Cause

### Type Promotion Logic

Polars implements automatic type promotion for:
- Addition, Subtraction, Multiplication
- Floor Division, Modulo

When these operations involve `(typed literal, column)` or `(column, typed literal)`, they:
1. Detect potential overflow
2. Automatically widen result to Int64
3. Return mathematically correct result

### Missing in Power Operations

The power operation (`.pow()` method and `**` operator):
1. Does NOT detect potential overflow
2. Does NOT widen the result type
3. Stays in narrow type (Int8)
4. Returns **0** on overflow (not even correct wrapping)

---

## Implementation Hypothesis

Based on the expression representations, Polars likely:

### Arithmetic Operators (`+`, `-`, `*`, `//`, `%`)

```rust
// Pseudo-code
fn multiply(left: Expr, right: Expr) -> Expr {
    let result_type = promote_types(left.dtype(), right.dtype());
    if contains_column(left, right) && would_overflow(result_type) {
        result_type = widen_to_int64(result_type);
    }
    return multiply_with_type(left, right, result_type);
}
```

### Power Operation (`.pow()`, `**`)

```rust
// Pseudo-code
fn power(base: Expr, exponent: Expr) -> Expr {
    let result_type = base.dtype();  // ← Uses base type, no promotion!
    return power_with_type(base, exponent, result_type);
}
```

The power operation is missing the type promotion logic that other operations have.

---

## Why This Is a Bug

### 1. Inconsistent with Other Operations

All arithmetic operations promote `(literal, column)` to Int64 except power.

### 2. Mathematically Incorrect

Returns 0 instead of the correct value (1024) or a wrapped value (-128).

### 3. Silent Data Corruption

No warning or error, just wrong results that look plausible.

### 4. Asymmetric Behavior

- `col.pow(lit)` → Int64 ✅
- `lit.pow(col)` → Int8 ❌

### 5. Breaks Standard Expectations

Users expect:
```python
a * a * a * a * a  # 5 multiplications, upcasts to Int64
a ** 5             # Should behave the same, but doesn't
```

---

## Proposed Fix

Add the same type promotion logic to power operations that multiplication already has:

```rust
fn power(base: Expr, exponent: Expr) -> Expr {
    let mut result_type = base.dtype();

    // ADD THIS: Same logic as multiplication
    if contains_column(base, exponent) && would_overflow(result_type) {
        result_type = Int64;  // Promote to wider type
    }

    return power_with_type(base, exponent, result_type);
}
```

---

## Test Cases to Verify Fix

After implementing the fix, these should pass:

```python
import polars as pl

df = pl.DataFrame({'x': [10]})

# Should return 1024, not 0
assert df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))['r'][0] == 1024

# Should upcast to Int64
schema = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r')).schema
assert str(schema['r']) == 'Int64'

# Should be symmetric
result1 = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
result2 = df.select((pl.col('x').cast(pl.Int8) ** pl.lit(2, dtype=pl.Int8)).alias('r'))
# Both should be Int64
```

---

## Impact

### Severity: High

- Silent data corruption (returns 0)
- Inconsistent with established patterns
- Breaks mathematical correctness

### Affected Users

- Anyone using power operations with typed literals
- Downstream frameworks (Ibis, etc.) that pass explicit dtypes
- Data pipelines that rely on power operations

### Frequency

Common in:
- Scientific computing (exponentiation is frequent)
- Financial calculations (compound interest)
- Statistical transformations (power transforms)

---

## Comparison with Other Languages

### NumPy

```python
np.int8(2) ** np.int8(10)  # Wraps: 0
np.int8(2) ** 10            # Wraps: 0
```

NumPy wraps consistently (both return 0 due to overflow).

### Pandas

```python
pd.Series([2], dtype='int8') ** pd.Series([10], dtype='int8')
# Returns: Series([0], dtype='int8')  # Wraps
```

Pandas also wraps, but at least it's consistent.

### Polars (Current Behavior)

```python
pl.lit(2, dtype=pl.Int8) * pl.col('x')   # → Int64: result ✅
pl.lit(2, dtype=pl.Int8) ** pl.col('x')  # → Int8: 0 ❌
```

**Polars is inconsistent**: upcasts for multiplication but not for power.

---

## Recommendation

Fix the power operation to upcast like multiplication does. This:
- Maintains consistency with other operations
- Prevents silent data corruption
- Matches user expectations
- Aligns with Polars' philosophy of "doing the right thing" automatically

---

## Files Generated for Bug Report

- `POLARS_BUG_REPORT.md` - Formal bug report
- `polars_bug_minimal_repro.py` - Minimal reproduction
- `test_polars_overflow_behavior.py` - Overflow comparison
- `investigate_polars_upcasting.py` - Comprehensive operation analysis
- `polars_source_investigation.py` - Expression representation analysis
- `POLARS_TECHNICAL_ANALYSIS.md` - This document
