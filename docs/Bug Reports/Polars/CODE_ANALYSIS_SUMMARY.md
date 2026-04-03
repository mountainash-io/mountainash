# Polars Power Operation Bug: Complete Code Analysis

## Executive Summary

The power operation (`**`) in Polars **does not use the same type promotion logic** as other arithmetic operators like multiplication (`*`). This causes silent overflow when narrow types are used.

**Edge Case:** `Int8(2) ** col_int64(10)` returns `0` instead of `1024`

---

## The Minimal Reproduction

```python
import polars as pl

df = pl.DataFrame({'x': [63]})  # Int64 column by default

# Multiplication: Works ✅
result = df.select((pl.lit(63, dtype=pl.Int8) * pl.col('x')).alias('r'))
# Schema: Int64
# Value:  3969 ✅

# Power: Broken ❌
df_pow = pl.DataFrame({'x': [10]})
result = df_pow.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
# Schema: Int8
# Value:  0 ❌ (should be 1024)
```

**Run:** `python docs/Bug Reports/Polars/minimal_multiplication_upcast_example.py`

---

## Root Cause: Different Code Paths

### Multiplication Path (Correct)

```rust
// File: polars-plan/src/dsl/arithmetic.rs:30
impl Mul for Expr {
    fn mul(self, rhs: Self) -> Self::Output {
        binary_expr(self, Operator::Multiply, rhs)  // ← Goes through binary_expr
    }
}

// File: polars-plan/src/plans/conversion/type_coercion/binary.rs:242
pub(super) fn process_binary(...) -> PolarsResult<Option<AExpr>> {
    // ...
    let st = unpack!(get_supertype(&type_left, &type_right));  // ← Calls get_supertype!
    // Casts both operands to supertype
}
```

**Result:** `get_supertype(Int8, Int64)` → **Int64** ✅

### Power Path (Broken)

```rust
// File: polars-plan/src/dsl/arithmetic.rs:61
impl Expr {
    pub fn pow<E: Into<Expr>>(self, exponent: E) -> Self {
        self.map_binary(PowFunction::Generic, exponent.into())  // ← Goes through map_binary
    }
}

// File: polars-plan/src/plans/aexpr/function_expr/schema.rs:711-720
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();  // base
    let dtype2 = self.fields[1].dtype();  // exponent
    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() { dtype2 } else { dtype1 }  // ← Returns base dtype!
    } else {
        dtype1
    };
    Ok(Field::new(self.fields[0].name().clone(), out_dtype.clone()))
}
```

**Result:** Returns `dtype1` (Int8) without calling `get_supertype()` ❌

---

## The Three Key Files

### 1. Type Coercion (Works for `*`, `+`, `-`, `/`, `%`)

**File:** `/home/nathanielramm/git/polars/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs`

**Line 242:**
```rust
let st = unpack!(get_supertype(&type_left, &type_right));
```

This promotes types for **all binary operators** (Plus, Minus, Multiply, Divide, Modulus, etc.)

### 2. Power Type Determination (Broken)

**File:** `/home/nathanielramm/git/polars/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs`

**Lines 711-720:**
```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();
    let dtype2 = self.fields[1].dtype();
    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() { dtype2 } else { dtype1 }  // ← BUG
    } else {
        dtype1
    };
    Ok(Field::new(self.fields[0].name().clone(), out_dtype.clone()))
}
```

**Problem:** Uses naive logic instead of `get_supertype()`

### 3. Power Runtime (Uses Wrong Dtype)

**File:** `/home/nathanielramm/git/polars/crates/polars-expr/src/dispatch/pow.rs`

**Lines 108-160:**
```rust
fn pow_on_series(base: &Column, exponent: &Column) -> PolarsResult<Column> {
    let base_dtype = base.dtype();  // Uses whatever schema determined (wrong!)
    // ...
    if base_dtype.is_integer() {
        with_match_physical_integer_type!(base_dtype, |$native_type| {
            // ...
            pow_to_uint_dtype(ca, exponent.u32().unwrap())  // Performs operation in base dtype
        })
    }
}
```

Performs the operation in whatever dtype was determined by `pow_dtype()` (which is wrong).

---

## The Fix

**File:** `polars-plan/src/plans/aexpr/function_expr/schema.rs:711`

**Option 1: Use `get_supertype()` (Recommended)**

```rust
use polars_core::utils::get_supertype;

pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();
    let dtype2 = self.fields[1].dtype();

    // Use same type promotion as other arithmetic operations
    let out_dtype = if let Some(st) = get_supertype(dtype1, dtype2) {
        st
    } else if dtype1.is_integer() {
        if dtype2.is_float() { dtype2.clone() } else { dtype1.clone() }
    } else {
        dtype1.clone()
    };

    Ok(Field::new(self.fields[0].name().clone(), out_dtype))
}
```

**Option 2: Always promote integer power to Int64 (Simpler)**

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();
    let dtype2 = self.fields[1].dtype();

    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() {
            dtype2.clone()
        } else if dtype2.is_integer() {
            &DataType::Int64  // Promote to prevent overflow
        } else {
            dtype1.clone()
        }
    } else {
        dtype1.clone()
    };

    Ok(Field::new(self.fields[0].name().clone(), out_dtype))
}
```

---

## Why This Is Critical

### 1. Inconsistency

All arithmetic operations auto-promote **except** power:

```python
Int8(63) * Int64(63)  → Int64 ✅
Int8(63) + Int64(63)  → Int64 ✅
Int8(63) - Int64(63)  → Int64 ✅
Int8(63) / Int64(63)  → Float64 ✅
Int8(2) ** Int64(10)  → Int8 ❌  # Returns 0!
```

### 2. Silent Data Corruption

No error, no warning, just **wrong results**:

```python
2 ** 10 = 1024  # Mathematically correct
Int8(2) ** col_int64(10) = 0  # Polars returns 0!
```

### 3. Real-World Impact

- **Compound interest calculations** (finance)
- **Scientific computing** (exponentiation is common)
- **Statistical transformations** (power transforms)
- **Any downstream library** (Ibis, etc.) that passes explicit dtypes

---

## Testing

After implementing the fix, verify:

```python
import polars as pl

df = pl.DataFrame({'x': [10]})

# Should return Int64: 1024
result = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
assert result.schema['r'] == pl.Int64
assert result['r'][0] == 1024

# Should be symmetric with column on left
df2 = pl.DataFrame({'base': [2]})
result2 = df2.select((pl.col('base').cast(pl.Int8) ** pl.lit(10)).alias('r'))
assert result2.schema['r'] == pl.Int64
assert result2['r'][0] == 1024
```

---

## Related Files Generated

- `minimal_multiplication_upcast_example.py` - Minimal reproduction
- `test_polars_overflow_behavior.py` - Comprehensive overflow testing
- `POLARS_TECHNICAL_ANALYSIS.md` - Detailed analysis
- `POLARS_BUG_REPORT.md` - Formal bug report
- `CODE_ANALYSIS_SUMMARY.md` - This file

---

## Summary

**The Bug:**
- Power operation doesn't call `get_supertype()`
- Returns base dtype without promotion
- Causes silent overflow (returns 0)

**The Fix:**
- Make `pow_dtype()` call `get_supertype()` like multiplication does
- Or always promote integer power to Int64
- One-line change in `schema.rs:711-720`

**Impact:**
- High severity (silent data corruption)
- Common operation (exponentiation)
- Inconsistent with established patterns
