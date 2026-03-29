# Polars Power Operation Bug: Root Cause Found

## Location

**File**: `/home/nathanielramm/git/polars/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs`

**Function**: `pow_dtype()` (lines 711-720)

**Introduced by**: [Commit 30edab06f](https://github.com/pola-rs/polars/commit/30edab06f) (December 2023)

## The Bug

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();  // base
    let dtype2 = self.fields[1].dtype();  // exponent
    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() { dtype2 } else { dtype1 }  // ← BUG HERE
    } else {
        dtype1
    };
    Ok(Field::new(self.fields[0].name().clone(), out_dtype.clone()))
}
```

### The Problem

When computing the output type for power operations:
- If base is integer and exponent is float → uses exponent type (float)
- **If base is integer and exponent is integer → uses base type** ← **BUG!**

So when you have `Int8(2) ** col_int8(10)`, it returns `Int8`, not `Int64`.

## How Other Operations Do It

**File**: `/home/nathanielramm/git/polars/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs`

**Function**: `process_binary()` (lines 118-283)

```rust
pub(super) fn process_binary(
    expr_arena: &mut Arena<AExpr>,
    input_schema: &Schema,
    node_left: Node,
    op: Operator,
    node_right: Node,
) -> PolarsResult<Option<AExpr>> {
    // ... validation ...

    // Coerce types:
    let st = unpack!(get_supertype(&type_left, &type_right));  // ← KEY LINE
    let mut st = modify_supertype(st, left, right, &type_left, &type_right);

    // ... cast both operands to supertype ...
}
```

Binary operators (like `*`, `+`, `-`) call `get_supertype()` which automatically promotes narrow types when needed.

## The Fix

Replace the simple type logic in `pow_dtype()` with proper type promotion:

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();  // base
    let dtype2 = self.fields[1].dtype();  // exponent

    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() {
            dtype2
        } else if dtype2.is_integer() {
            // FIX: Use supertype logic like binary operators do
            use polars_core::datatypes::get_supertype;
            get_supertype(dtype1, dtype2).unwrap_or(dtype1)
        } else {
            dtype1
        }
    } else {
        dtype1
    };

    Ok(Field::new(self.fields[0].name().clone(), out_dtype.clone()))
}
```

## Why This Matters

### Multiplication (uses `get_supertype`)
```
Int8(63) * col_int8(63)
→ get_supertype(Int8, Int8) → Int64  ← Auto-widens!
→ Result: Int64
→ Value: 3969 ✅
```

### Power (uses base type only)
```
Int8(2) ** col_int8(10)
→ dtype1.is_integer() && !dtype2.is_float()
→ Returns dtype1 = Int8  ← No widening!
→ Result: Int8
→ Value: 0 ❌ (overflow)
```

## Test to Verify Fix

After applying the fix:

```python
import polars as pl

df = pl.DataFrame({'x': [10]})

# Should return Int64: 1024
result = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
assert str(result.schema['r']) == 'Int64'
assert result['r'][0] == 1024
```

## Related Code

The actual computation happens in:
- **File**: `/home/nathanielramm/git/polars/crates/polars-expr/src/dispatch/pow.rs`
- **Function**: `pow_on_series()` and `pow_to_uint_dtype()`

But those use the dtype determined by `pow_dtype()`, so fixing the type inference fixes the computation.

## Additional Investigation

### Why do some operations work?

From our tests:
- `col.pow(lit)` → Works (Int64) ✅
- `lit.pow(col)` → Fails (Int8) ❌

This is because when the base (`dtype1`) is a column, the supertype logic might be handled elsewhere in the pipeline. But when the base is a literal with explicit narrow type, `pow_dtype()` just returns that narrow type.

## Summary

**Root cause**: `pow_dtype()` doesn't call `get_supertype()` like binary operators do.

**Fix**: Make `pow_dtype()` use `get_supertype()` for integer-integer power operations.

**Impact**: Would fix all integer power operations to auto-widen like multiplication does.
