# The Exact Difference: Multiplication vs Power with Int8

## TL;DR

**When operand types DIFFER:** Multiplication calls `get_supertype()` and promotes, but Power doesn't!

```python
Int8(63) * Int64(63)  → Int64: 3969 ✅  # Upcasts
Int8(2) ** Int64(10)  → Int8: 0     ❌  # Doesn't upcast, overflows
```

---

## The Complete Picture

### Case 1: Both Operands SAME Type (Int8, Int8)

```python
# Multiplication
Int8(63) * col_int8(63)
  → Result dtype: Int8
  → Result value: -127 (wrapped from 3969)
  → Behavior: Wraps on overflow

# Power
Int8(2) ** col_int8(10)
  → Result dtype: Int8
  → Result value: 0 (should be -128 if wrapped correctly, or 1024 if promoted)
  → Behavior: Returns 0 (BUG - doesn't even wrap correctly!)
```

**Both stay Int8 when types are the same**, but power has a wrapping bug too!

---

### Case 2: Operands DIFFERENT Types (Int8, Int64)

```python
# Multiplication
Int8(63) * col_int64(63)
  → Result dtype: Int64  ✅
  → Result value: 3969   ✅
  → Behavior: Calls get_supertype(Int8, Int64) → Int64

# Power
Int8(2) ** col_int64(10)
  → Result dtype: Int8   ❌
  → Result value: 0      ❌
  → Behavior: Returns base dtype (Int8), no get_supertype() call!
```

**This is THE BUG**: When types differ, multiplication promotes but power doesn't!

---

## Test Results

Run: `python docs/Bug\ Reports/Polars/exact_upcast_pattern.py`

```
| Base Type | Exp Type | Multiplication Result | Power Result | Match? |
|-----------|----------|-----------------------|--------------|--------|
| Int8      | Int8     | Int8                  | Int8         | ✅     |
| Int8      | Int64    | Int64 ✅              | Int8 ❌      | ❌     |
| Int16     | Int8     | Int16                 | Int16        | ✅     |
| Int32     | Int8     | Int32                 | Int32        | ✅     |
```

**The second row shows the bug:** `Int8 * Int64 → Int64`, but `Int8 ** Int64 → Int8`

---

## Why This Happens

### Multiplication Code Path

```rust
// File: polars-plan/src/plans/conversion/type_coercion/binary.rs:242
let st = unpack!(get_supertype(&type_left, &type_right));
// Returns: get_supertype(Int8, Int64) = Int64 ✅
```

### Power Code Path

```rust
// File: polars-plan/src/plans/aexpr/function_expr/schema.rs:714-715
let out_dtype = if dtype1.is_integer() {
    if dtype2.is_float() { dtype2 } else { dtype1 }  // ← Returns base dtype!
}
// Returns: dtype1 (Int8) - no get_supertype() call! ❌
```

---

## Practical Impact

When you have a narrow typed literal and a wider column:

```python
import polars as pl

# Common pattern: DataFrame columns are Int64 by default
df = pl.DataFrame({'power': [10]})

# This multiplication works
result = df.select((pl.lit(2, dtype=pl.Int8) * pl.col('power')).alias('r'))
# → Int64: 10 ✅

# This power fails silently
result = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('power')).alias('r'))
# → Int8: 0 ❌  (Silent data corruption!)
```

---

## The Fix

Make `pow_dtype()` call `get_supertype()` like multiplication does:

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();
    let dtype2 = self.fields[1].dtype();

    // ADD THIS: Use supertype like multiplication does
    let out_dtype = if let Some(st) = get_supertype(dtype1, dtype2) {
        st  // Will return Int64 for (Int8, Int64)
    } else if dtype1.is_integer() {
        if dtype2.is_float() { dtype2.clone() } else { dtype1.clone() }
    } else {
        dtype1.clone()
    };

    Ok(Field::new(self.fields[0].name().clone(), out_dtype))
}
```

---

## Files

- `exact_upcast_pattern.py` - Shows the exact pattern with different type combinations
- `int8_both_sides_comparison.py` - Shows behavior when both are Int8
- `minimal_multiplication_upcast_example.py` - Clean minimal reproduction
- `CODE_ANALYSIS_SUMMARY.md` - Complete code analysis with file locations
