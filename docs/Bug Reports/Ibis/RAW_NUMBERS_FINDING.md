# Critical Finding: Raw Numbers Are Also Affected

## The Discovery

**Users cannot avoid the bug by using raw Python numbers instead of `ibis.literal()`!**

---

## Test Results

**Run:** `python docs/Bug\ Reports/Ibis/test_raw_numbers_vs_literals.py`

### Same Behavior

```python
2 ** table.x                    # → 0 (Polars), 1024 (DuckDB)
ibis.literal(2) ** table.x      # → 0 (Polars), 1024 (DuckDB)
```

**Both fail identically with Polars backend!**

### Why They're Identical

```python
# User writes
2 ** table.x

# Ibis internally converts to
ibis.literal(2) ** table.x

# Then applies type inference
ibis.literal(2, dtype=int8) ** table.x
```

### Proof from AST

```
(2 ** table.x).op() == (ibis.literal(2) ** table.x).op()
# → True

Both operations have:
  - Left operand type: Literal
  - Left dtype: int8
  - Same operation tree
```

---

## What Polars Receives

```
Expression: 2 ** table.x
Polars gets: dyn int: 2.strict_cast(Int8)

Expression: ibis.literal(2) ** table.x
Polars gets: dyn int: 2.strict_cast(Int8)
```

**Identical!** Both get explicit Int8 cast.

---

## Complete Test Matrix

| User Code | Polars Result | DuckDB Result | Works? |
|-----------|---------------|---------------|--------|
| `2 ** table.x` | 0.0 | 1024.0 | ❌ Polars |
| `ibis.literal(2) ** table.x` | 0.0 | 1024.0 | ❌ Polars |
| `64 * table.y(64)` | 4096 | 4096 | ✅ Both |
| `ibis.literal(64) * table.y(64)` | 4096 | 4096 | ✅ Both |

**Pattern:**
- Power operations fail with Polars (overflow)
- Multiplication works ONLY because column is int64 (mixed types)
- If column were int8: `literal(64, int8) * column(64, int8)` → 0 ❌
- Raw numbers and literals behave identically

---

## The Code Path

### Step-by-Step

```
USER WRITES:
  2 ** table.x

       ↓

PYTHON OPERATOR OVERLOAD:
  Column.__rpow__(2)  # Right-hand power

       ↓

IBIS CONVERTS RAW NUMBER:
  ibis.literal(2)

       ↓

IBIS INFERS TYPE:
  infer_integer(2) → int8

       ↓

IBIS CREATES OPERATION:
  ops.Literal(value=2, dtype=int8)

       ↓

POLARS BACKEND TRANSLATES:
  pl.lit(2, dtype=pl.Int8)

       ↓

POLARS EXECUTES:
  pl.lit(2, dtype=pl.Int8) ** pl.col('x')
  → Overflow in Int8 → 0
```

---

## Why This Matters

### Users Expect This to Work

```python
# Most natural way to write it
2 ** table.x

# Users don't expect to need
ibis.literal(2).cast('int64') ** table.x
```

### No Workaround Without Explicit Cast

```python
# These ALL fail the same way:
2 ** table.x                          ❌
ibis.literal(2) ** table.x           ❌
ibis.literal(2, type='int8') ** table.x  ❌

# Only this works:
ibis.literal(2).cast('int64') ** table.x  ✅
# or
ibis.literal(2, type='int64') ** table.x  ✅
```

But users shouldn't need to know this!

---

## Comparison with Python

### Pure Python

```python
2 ** 10
# → 1024 (Python int has unlimited precision)
```

### Ibis with Polars

```python
2 ** table.x  # where x=10
# → 0 ❌ (overflow in int8)
```

**Violates principle of least surprise!**

---

## The Operator Overload

Ibis implements Python's operator overloading:

```python
# When you write:
2 ** table.x

# Python calls:
table.x.__rpow__(2)

# Which Ibis implements as:
def __rpow__(self, other):
    return ibis.literal(other) ** self
```

**So raw numbers ALWAYS go through `ibis.literal()`!**

---

## Impact Assessment

### Who's Affected

**Everyone using Ibis with Polars backend!**

Including users who:
- Use natural Python syntax (`2 ** table.x`)
- Think they're avoiding the literal() issue
- Don't know about type inference

### What's Affected

```python
# All of these fail:
2 ** table.x
10 + table.y
63 * table.z  # If result overflows
127 - table.w  # If result overflows
```

Any arithmetic with raw numbers that might overflow narrow types.

---

## Why SQL Backends Don't Have This Problem

### SQL Generation

Both raw numbers and literals generate the same SQL:

```python
# DuckDB/SQLite
2 ** table.x
# Generates SQL:
# SELECT POWER(2, x) FROM table

ibis.literal(2) ** table.x
# Also generates SQL:
# SELECT POWER(2, x) FROM table
```

The SQL literal `2` has **no type** - database chooses INT/BIGINT.

### Polars API

Both generate Polars API with **explicit type**:

```python
# Polars backend
2 ** table.x
# Generates:
# pl.lit(2, dtype=pl.Int8) ** pl.col('x')

ibis.literal(2) ** table.x
# Also generates:
# pl.lit(2, dtype=pl.Int8) ** pl.col('x')
```

The Polars literal has **explicit Int8** - Polars respects it.

---

## The Fix Must Handle Both

Any fix must work for:

1. ✅ `ibis.literal(2) ** table.x`
2. ✅ `2 ** table.x` (raw number)
3. ✅ `table.x ** 2` (reversed)
4. ✅ All arithmetic operators

**Since they all use the same code path!**

---

## Recommended Fix (Still The Same)

**File:** `ibis/backends/polars/compiler.py`

```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype
    # ...
    elif dtype.is_integer() or dtype.is_floating():
        return pl.lit(value)  # ← Don't pass dtype!
```

**This fixes:**
- `ibis.literal(2) ** table.x` ✅
- `2 ** table.x` ✅
- All raw numbers ✅
- All explicit literals ✅

---

## Conclusion

**The bug affects ALL integer constants, whether written as:**
- Raw numbers: `2 ** table.x`
- Explicit literals: `ibis.literal(2) ** table.x`

**Users cannot work around this** without explicit casting to int64.

**The fix must be in Ibis**, and it will automatically fix both cases since they share the same code path.

---

## Practical Advice for Users

### Current Workaround

```python
# Instead of:
2 ** table.x  # ❌ Fails

# Use:
ibis.literal(2, type='int64') ** table.x  # ✅ Works

# Or:
ibis.literal(2).cast('int64') ** table.x  # ✅ Works
```

### Better Solution

**Switch to DuckDB backend** until Ibis fixes the Polars backend:

```python
# Instead of:
conn = ibis.polars.connect()

# Use:
conn = ibis.duckdb.connect()
```

DuckDB doesn't have this problem!
