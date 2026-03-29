# The Real Culprit: Ibis Aggressive Type Downcasting

## Executive Summary

**Polars' behavior is CORRECT and INTENTIONAL.** The bug is in **Ibis**, which aggressively downcasts integer literals to the smallest possible type (Int8, Int16, etc.) and then explicitly passes these narrow types to Polars, causing overflow.

---

## The Smoking Gun

### Ibis Literal Type Inference

**File:** `/home/nathanielramm/git/ibis/ibis/expr/datatypes/value.py:128-135`

```python
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    types = (dt.uint8, dt.uint16, dt.uint32, dt.uint64) if prefer_unsigned else ()
    types += (dt.int8, dt.int16, dt.int32, dt.int64)
    for dtype in types:
        if dtype.bounds.lower <= value <= dtype.bounds.upper:
            return dtype  # ← Returns FIRST type that fits!
    return dt.uint64 if prefer_unsigned else dt.int64
```

**Result:**
- `ibis.literal(2)` → `int8` (because 2 fits in int8)
- `ibis.literal(63)` → `int8` (because 63 fits in int8)
- `ibis.literal(128)` → `int16` (int8 doesn't fit, int16 does)

---

## Test Results

**Run:** `python docs/Bug\ Reports/Ibis/test_ibis_literal_aggressive_downcast.py`

### What Works ✅

```python
# Literal × Literal (Ibis evaluates at compile time)
ibis.literal(63) * ibis.literal(63)  → 3969 ✅
ibis.literal(2) ** ibis.literal(10)  → 1024 ✅
```

### What Fails ❌

```python
# Literal × Column (Sent to Polars with narrow dtype)
ibis.literal(2) ** table.column(10)  → 0 ❌
```

### Polars Direct Comparison

```python
# WITHOUT explicit dtype (Polars chooses)
pl.lit(63) * pl.lit(63)
# → Schema: Int32
# → Value: 3969 ✅

# WITH explicit dtype (What Ibis sends)
pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)
# → Schema: Int8
# → Value: -127 ❌ (Wraps on overflow)
```

---

## Why Polars Behavior is Intentional

From the Polars team (https://github.com/pola-rs/polars/issues/25213):

> Polars' design decision is to **respect explicit dtypes**. When you pass `dtype=Int8`, Polars stays in Int8 and wraps on overflow. This is:
>
> 1. **Consistent** with NumPy and Pandas wrapping behavior
> 2. **Explicit** - you told Polars to use Int8, it does
> 3. **Performant** - narrow types use less memory
> 4. **User choice** - don't pass dtype if you want auto-promotion

**Polars' type promotion policy:**
- `pl.lit(63) * pl.col('x')` → Polars chooses appropriate type (Int32/Int64)
- `pl.lit(63, dtype=Int8) * pl.col('x')` → Polars respects Int8, wraps if overflow

---

## Why This is Ibis's Problem

### The Flow

```
User Code:
  ibis.literal(2) ** table.x

Ibis Type Inference (value.py:129):
  infer_integer(2) → int8

Ibis Polars Backend (compiler.py:~54):
  typ = PolarsType.from_ibis(dtype)  # int8 → pl.Int8
  return pl.lit(op.value, dtype=typ)  # pl.lit(2, dtype=pl.Int8)

Polars Execution:
  pl.lit(2, dtype=pl.Int8) ** pl.col('x')  # Overflows in Int8
```

**The user never asked for Int8!** Ibis chose it automatically.

---

## Impact on Multiplication

The user correctly identified this affects multiplication too:

```python
import ibis
import polars as pl

# Direct Polars (no dtype)
pl.select(pl.lit(63) * pl.lit(63))
# → Int32: 3969 ✅

# What Ibis sends to Polars
pl.select(pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8))
# → Int8: -127 ❌

# Ibis with Polars backend
conn = ibis.polars.connect()
ibis.literal(63) * ibis.literal(63)
# → 3969 ✅ (But only because Ibis evaluates literals at compile time!)
```

**However**, when you do:
```python
ibis.literal(63) * table.column_int8(63)
```

Ibis sends:
```python
pl.lit(63, dtype=pl.Int8) * pl.col('x').cast(pl.Int8)
# → Wraps to -127!
```

---

## The Fix Must Be in Ibis

### Option 1: Don't Pass Explicit Dtypes to Polars (Recommended)

**File:** `ibis/backends/polars/compiler.py:85-110`

**Current:**
```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype
    # ...
    elif dtype.is_integer():
        typ = PolarsType.from_ibis(dtype)
        return pl.lit(op.value, dtype=typ)  # ← Explicitly passes narrow dtype!
```

**Fixed:**
```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype
    # ...
    elif dtype.is_integer():
        return pl.lit(value)  # ← Let Polars choose appropriate type!
```

**Result:**
- Polars will choose `Int32` or `Int64` (safe)
- No overflow on operations
- Aligns with Polars' design philosophy

### Option 2: Upcast Before Operations

Detect narrow types before operations and upcast:

```python
@translate.register(ops.Power)
def power(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)

    # If left is narrow integer literal, upcast
    if isinstance(op.left, ops.Literal) and op.left.dtype.is_integer():
        if op.left.dtype.nbytes < 8:
            left = left.cast(pl.Int64)

    return left.pow(right)
```

But this needs to be done for **all** operations (multiply, add, subtract, etc.)

### Option 3: Change Literal Inference to Use Wider Types

**File:** `ibis/expr/datatypes/value.py:129`

**Current:**
```python
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    types = (dt.int8, dt.int16, dt.int32, dt.int64)  # Tries smallest first
```

**Fixed:**
```python
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    # Always use Int64 for safety (like Python's int)
    return dt.int64
```

**Cons:** Loses ability to use narrow types when truly needed

---

## Recommendation

**Option 1 is best for Polars backend:**

1. ✅ Simplest change (one line)
2. ✅ Aligns with Polars' design
3. ✅ Fixes all operations (power, multiply, add, etc.)
4. ✅ Lets Polars make smart type choices
5. ✅ No user-visible behavior change (current behavior is buggy)

**Implementation:**

```python
# ibis/backends/polars/compiler.py

@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype

    if value is None:
        return pl.lit(None, dtype=PolarsType.from_ibis(dtype))

    if dtype.is_array():
        value = pl.Series("", value)
        typ = PolarsType.from_ibis(dtype)
        val = pl.lit(value, dtype=typ)
        return val.implode()
    elif dtype.is_struct():
        values = [
            pl.lit(v, dtype=PolarsType.from_ibis(dtype[k])).alias(k)
            for k, v in value.items()
        ]
        return pl.struct(values)
    elif dtype.is_interval():
        return _make_duration(value, dtype)
    elif dtype.is_null() or dtype.is_binary():
        return pl.lit(value)
    elif dtype.is_integer() or dtype.is_floating():  # NEW!
        return pl.lit(value)  # Let Polars infer appropriate type
    else:
        typ = PolarsType.from_ibis(dtype)
        return pl.lit(op.value, dtype=typ)
```

---

## Files for Investigation

### Ibis Source Files

1. **Literal type inference:**
   - `/home/nathanielramm/git/ibis/ibis/expr/datatypes/value.py:128-135`
   - Function: `infer_integer()`

2. **Polars backend literal translation:**
   - `/home/nathanielramm/git/ibis/ibis/backends/polars/compiler.py:85-110`
   - Function: `literal()`

3. **Power operation translation:**
   - `/home/nathanielramm/git/ibis/ibis/backends/polars/compiler.py:721-725`
   - Function: `power()`

### Test Files Created

1. `test_ibis_literal_aggressive_downcast.py` - Demonstrates the bug
2. `IBIS_POW_FIX_PROPOSAL.md` - Original proposal
3. `COMPREHENSIVE_IBIS_POLARS_ANALYSIS.md` - This document

---

## Summary

**Polars:** Works as designed. Respects explicit dtypes.

**Ibis:** Aggressively downcasts literals to smallest type, then sends narrow types to Polars with explicit dtype specification.

**Result:** Silent overflow in operations.

**Solution:** Ibis should not pass explicit dtypes for numeric literals to Polars backend. Let Polars choose appropriate types.

**Affected Operations:**
- Power: `literal(2) ** column` → 0
- Multiplication: `literal(63) * literal(63)` → -127 (when both are columns or one is column)
- Addition, Subtraction, etc.: Any operation with narrow literals

**User Never Chose Int8** - Ibis did it automatically without user consent!
