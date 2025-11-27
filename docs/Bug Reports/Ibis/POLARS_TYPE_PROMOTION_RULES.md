# Polars Type Promotion Rules: The Complete Picture

## Summary

Polars type promotion behavior is **operation-dependent** and **type-dependent**.

---

## Key Finding

**Polars promotes types for binary operations ONLY when types are MIXED, NOT when both operands have the same narrow type.**

---

## Multiplication Behavior

### Mixed Types (Promotes) ✅

```python
# int8 × int64 → promotes to avoid overflow
pl.lit(64, dtype=pl.Int8) * pl.col('y')  # where y is int64
# Result: 4096 ✅

# int64 × int8 → promotes to avoid overflow
pl.col('x') * pl.lit(64, dtype=pl.Int8)  # where x is int64
# Result: 4096 ✅
```

**Rule:** When types differ, Polars calls `get_supertype()` and promotes.

### Same Types (No Promotion) ❌

```python
# int8 × int8 → NO promotion, uses int8
pl.lit(64, dtype=pl.Int8) * pl.Series([64], dtype=pl.Int8)
# Result: 0 ❌ (overflow in int8)

# Cast both to int8
pl.col('x').cast(pl.Int8) * pl.col('y').cast(pl.Int8)
# Result: 0 ❌ (overflow in int8)
```

**Rule:** When both types are the same, no promotion occurs.

---

## Power Behavior

### Any Type Combination (No Promotion) ❌

```python
# int8 ** int64 → NO promotion
pl.lit(2, dtype=pl.Int8) ** pl.lit(10)
# Result: 0 ❌ (overflow in int8 base)

# int64 ** int8 → Uses left operand type
pl.lit(2) ** pl.lit(10, dtype=pl.Int8)
# Result: 1024 ✅ (base is wider type)

# int8 ** int8 → NO promotion
pl.lit(2, dtype=pl.Int8) ** pl.lit(10, dtype=pl.Int8)
# Result: 0 ❌ (overflow in int8)
```

**Rule:** Power operations use the base (left operand) type, no promotion.

---

## Code Path Differences

### Binary Operators (*, +, -, /)

**File:** `polars/crates/polars-plan/src/dsl/arithmetic.rs`

```rust
impl Mul for Expr {
    fn mul(self, rhs: Self) -> Self::Output {
        binary_expr(self, Operator::Multiply, rhs)  // ← Uses binary_expr
    }
}
```

**Type Resolution:** `polars/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs:242`

```rust
let st = unpack!(get_supertype(&type_left, &type_right));  // ← Promotes!
```

### Function Expressions (pow)

**File:** `polars/crates/polars-plan/src/dsl/arithmetic.rs`

```rust
impl Expr {
    pub fn pow<E: Into<Expr>>(self, exponent: E) -> Self {
        self.map_binary(PowFunction::Generic, exponent.into())  // ← Uses map_binary
    }
}
```

**Type Resolution:** `polars/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs:711-720`

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();
    let dtype2 = self.fields[1].dtype();
    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() { dtype2 } else { dtype1 }  // ← NO get_supertype()!
    } else {
        dtype1
    };
    Ok(Field::new(self.fields[0].name().clone(), out_dtype.clone()))
}
```

**No call to `get_supertype()`** - uses naive type logic.

---

## Test Matrix

### Multiplication: 64 × 64 = 4096

| Left Type | Right Type | Result | Explanation |
|-----------|------------|--------|-------------|
| untyped   | int64      | 4096   | Left becomes int32/int64, promotes |
| int64     | untyped    | 4096   | Right becomes int32/int64, promotes |
| int64     | int64      | 4096   | Both wide enough |
| int8      | int64      | 4096   | **Mixed types → promotes** ✅ |
| int64     | int8       | 4096   | **Mixed types → promotes** ✅ |
| int8      | int8       | 0      | **Same type → NO promotion** ❌ |

### Power: 2^10 = 1024

| Base Type | Exp Type | Result | Explanation |
|-----------|----------|--------|-------------|
| untyped   | any      | 1024   | Base becomes int32/int64 |
| int64     | any      | 1024   | Base wide enough |
| int8      | int64    | 0      | **Base type used, no promotion** ❌ |
| int8      | int8     | 0      | **Base type used, no promotion** ❌ |

---

## Why Ibis Tests Pass for Multiplication

### The Test

```python
# From test_raw_numbers_vs_literals.py
pl_df = pl.DataFrame({'y': [64]})  # ← Polars defaults to int64!
table = ibis.connect().create_table('test', pl_df)

result = (ibis.literal(64) * table.y).execute()
# Result: 4096 ✅
```

### What's Happening

1. **Column type:** int64 (Polars default for Python ints)
2. **Literal type:** int8 (Ibis aggressive downcasting)
3. **Operation:** int8 × int64 (MIXED types)
4. **Polars behavior:** Calls `get_supertype(int8, int64)` → int64
5. **Result:** Promotes to int64, no overflow ✅

### What Would Happen with Both int8

```python
# Force column to int8
pl_df = pl.DataFrame({'y': pl.Series([64], dtype=pl.Int8)})
table = ibis.connect().create_table('test', pl_df)

result = (ibis.literal(64) * table.y).execute()
# Result: 0 ❌ (overflow!)
```

**Explanation:** Both operands are int8 → no type promotion → overflow.

---

## Why Ibis Tests Fail for Power

### The Test

```python
result = (ibis.literal(2) ** table.x).execute()  # where x=10
# Result: 0 ❌
```

### What's Happening

1. **Base type:** int8 (Ibis literal)
2. **Exponent type:** int64 (Polars column default)
3. **Operation:** int8 ** int64 (MIXED types)
4. **Polars behavior:** Uses base type (int8), NO promotion
5. **Result:** 2^10 = 1024 overflows int8 → wraps to 0 ❌

---

## Implications for Ibis

### The Problem

Ibis aggressively downcasts literals to int8, but:
- **For multiplication:** Often works because columns are int64 (mixed types → promotes)
- **For power:** Always fails because power doesn't promote

### The Illusion

It **appears** multiplication is safer, but it's only because:
1. DataFrame columns default to int64
2. Mixed types trigger promotion
3. Pure luck that they differ

### The Danger

If a user creates an int8 column:
```python
df = pl.DataFrame({'x': pl.Series([64], dtype=pl.Int8)})
table = ibis.connect().create_table('test', df)
result = (ibis.literal(64) * table.x).execute()
# Result: 0 ❌ (both int8, no promotion!)
```

**Users have no idea this can happen!**

---

## The Fix (Still Required in Ibis)

### Short-term: Don't Pass Explicit Types to Polars

**File:** `ibis/backends/polars/compiler.py`

```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype
    # ...
    elif dtype.is_integer() or dtype.is_floating():
        return pl.lit(value)  # ← Let Polars choose (int32/int64)
```

**Why this works:**
- Polars defaults to int32 or int64 for untyped literals
- Mixed with int64 columns → both wide types
- No overflow issues

### Long-term: Change Ibis Literal Inference

**File:** `ibis/expr/datatypes/value.py:128`

```python
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    return dt.int64  # ← Always use int64 (match DataFrame defaults)
```

**Why this works:**
- Matches Polars/Pandas DataFrame defaults
- Eliminates asymmetry between literals and columns
- Safer default for users

---

## Polars Team's Position

From [Issue #25213](https://github.com/pola-rs/polars/issues/25213):

> "This is correct and expected behavior. When you explicitly pass `dtype=pl.Int8`, Polars respects it."

**They're technically correct:**
- Explicit types should be honored
- Consistent with strict typing philosophy
- The bug is upstream in Ibis

---

## Conclusion

### What We Learned

1. **Polars promotes multiplication for mixed types only**
2. **Polars never promotes power operations**
3. **Ibis literal(64) × column(64) works by accident** (types differ)
4. **The fix must still be in Ibis** (don't pass explicit narrow types)

### The Real Problem

**Ibis aggressive downcast + Polars explicit types = Silent overflow**

**The fix:** Make Ibis stop sending explicit narrow types to Polars, OR change Ibis to use int64 by default.

### User Impact

**Current behavior:** Mysterious, unpredictable failures depending on:
- Operation type (power always fails, multiplication sometimes works)
- Column types (int64 vs int8)
- Literal values (2 vs 128 use different types)

**After fix:** Consistent, safe behavior across all operations.
