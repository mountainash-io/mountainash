# Ibis Type Resolution: Literals vs Columns

## The Asymmetry

**The core problem:** Ibis treats literals and columns completely differently when inferring types, creating a fundamental mismatch.

---

## Summary of Findings

| Value | As Literal | As Column | Difference |
|-------|-----------|-----------|------------|
| 2 | int8 | int64 | 8x wider! |
| 10 | int8 | int64 | 8x wider! |
| 127 | int8 | int64 | 8x wider! |
| 1000 | int16 | int64 | 4x wider! |
| 100000 | int32 | int64 | 2x wider! |

**Pattern:** Columns use int64 by default, literals use smallest type.

---

## Path 1: Literal Type Inference

### Code Location

**File:** `/home/nathanielramm/git/ibis/ibis/expr/datatypes/value.py:128-135`

```python
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    """Infer the smallest integer type that can hold this value."""
    types = (dt.uint8, dt.uint16, dt.uint32, dt.uint64) if prefer_unsigned else ()
    types += (dt.int8, dt.int16, dt.int32, dt.int64)
    for dtype in types:
        if dtype.bounds.lower <= value <= dtype.bounds.upper:
            return dtype  # ← Returns FIRST type that fits!
    return dt.uint64 if prefer_unsigned else dt.int64
```

### The Algorithm

1. Try types in order: int8, int16, int32, int64
2. Return the **first** type where value fits in bounds
3. For value = 2: bounds check `(-128 <= 2 <= 127)` → **int8** ✓

### Design Rationale

**Goal:** Minimize memory usage by choosing narrowest type

**Assumption:** Literals are constants, so we know the exact value and can optimize

**Problem:** Doesn't consider how the literal will be used!

---

## Path 2: Column Type Inference

### Code Location

Columns don't get "inferred" - they come from DataFrame schemas.

### The Flow

```
User creates DataFrame:
  pl.DataFrame({'x': [2]})
     ↓
Polars chooses type:
  Python int → Int64 (Polars default)
     ↓
Ibis reads schema:
  table.schema() → int64
     ↓
Ibis uses schema type:
  table.x.type() → int64
```

### Why Int64?

**Polars default for Python ints:**
```python
pl.DataFrame({'x': [2]})
# Schema: {'x': Int64}
```

**Pandas default for Python ints:**
```python
pd.DataFrame({'x': [2]})
# dtypes: {'x': dtype('int64')}
```

**Rationale:**
- Python's `int` has unlimited precision
- int64 is the widest commonly-used integer type
- Safe default to avoid overflow
- Standard across data libraries

---

## The Mismatch

### Same Value, Different Types

```python
value = 2

# Path 1: Literal
ibis.literal(2)
# → Ibis infers: int8 (smallest that fits)

# Path 2: Column
pl.DataFrame({'x': [2]})
table = conn.create_table('t', df)
table.x
# → Polars chooses: int64 (safe default)
```

### When They Interact

```python
# Both represent value "2", but different types!
ibis.literal(2) ** table.x

# Becomes:
pl.lit(2, dtype=pl.Int8) ** pl.col('x')  # col is Int64
```

**Type promotion in power:**
- Polars uses base type (Int8)
- Overflows!

---

## Why This Is Wrong

### 1. Inconsistent with DataFrame Philosophy

DataFrames use **wide types by default**:
- Polars: Int64
- Pandas: int64
- R: integer (32-bit)
- Julia: Int64

Ibis literals should match this!

### 2. Breaks Substitutability

You should be able to replace a column with a literal of the same value:

```python
# With column (works)
df = pl.DataFrame({'base': [2], 'exp': [10]})
table = conn.create_table('t', df)
table.base ** table.exp  # → 1024 ✅

# Replace column with literal (breaks!)
ibis.literal(2) ** table.exp  # → 0 ❌
```

**Same mathematical operation, different results!**

### 3. Violates Principle of Least Surprise

```python
# Python
2 ** 10  # → 1024

# Ibis
ibis.literal(2) ** ibis.literal(10)  # → 0 ❌
```

**Users expect Ibis to behave like Python!**

---

## Test Results

**Run:** `python docs/Bug\ Reports/Ibis/test_literal_vs_column_types.py`

### Literal Type Inference

```
| Value | Ibis Literal Type |
|-------|-------------------|
|     2 | int8              |
|    10 | int8              |
|    63 | int8              |
|   127 | int8              | ← Maximum int8!
|   128 | int16             | ← Jumps to int16
|  1000 | int16             |
| 100000 | int32            |
```

### Column Type Preservation

```
Original Polars DataFrame:
  {'x': Int64}

Ibis table schema:
  x: int64
```

Columns **preserve** their DataFrame type (usually Int64).

### Operation Results

```
| Expression | Literal Type | Column Type | Result |
|------------|--------------|-------------|--------|
| lit(2) * int8_col | int8 | int8 | 4 ✅ |
| lit(2) ** int8_col | int8 | int8 | 4.0 ✅ (small value) |
| lit(2) * int64_col | int8 | int64 | 20000000000 ✅ |
| lit(2) ** int64_col | int8 | int64 | 0.0 ❌ (OVERFLOW!) |
```

**Pattern:**
- Multiplication promotes when types differ
- Power uses base type (doesn't promote)

---

## Why Columns Work Better

### DataFrame Creation

```python
# When you create a DataFrame
df = pl.DataFrame({'x': [2, 10, 100]})
```

**Polars decision tree:**
1. Is it a Python int? → Yes
2. Choose Int64 (safe, standard)
3. **Result:** All values in Int64

**Why this works:**
- Int64 can hold 2^63-1 (9 quintillion)
- 2^10 = 1024 fits comfortably
- No overflow possible for normal operations

### Literal Creation

```python
# When you create a literal
lit = ibis.literal(2)
```

**Ibis decision tree:**
1. Is it a Python int? → Yes
2. What's the smallest type? → int8
3. **Result:** Value 2 in int8

**Why this fails:**
- int8 can only hold -128 to 127
- 2^10 = 1024 > 127
- Overflow!

---

## The Root Cause Design Decision

### Ibis's Philosophy

From the code comments and design:

```python
def infer_integer(value: int, ...) -> dt.Integer:
    """Infer the smallest integer type that can hold this value."""
```

**Key word:** "smallest"

**Rationale (inferred):**
- Memory efficiency
- Matches value precisely
- Useful for embedded systems / memory-constrained environments

### DataFrame Libraries' Philosophy

Polars, Pandas, etc.:

**Key word:** "safe"

**Rationale:**
- Avoid overflow
- User convenience (don't think about types)
- Consistent behavior
- Match Python's int behavior

---

## Comparison with Other Systems

### NumPy

```python
import numpy as np

# Explicit type
np.int8(2) ** np.int8(10)  # → 0 (overflow, wraps)

# Auto type
np.array([2]) ** np.array([10])  # → array([1024])
# Default: int64
```

NumPy **defaults to int64** for Python int arrays!

### SQL Databases

```sql
-- No explicit type
SELECT 2, 10, 100;
-- Database chooses: INT or BIGINT (32/64-bit)
```

SQL **defaults to wide types** for integer literals!

### Python

```python
# Python 3 int
2 ** 10  # → 1024
2 ** 100  # → 1267650600228229401496703205376
```

Python int has **unlimited precision**!

---

## What Should Ibis Do?

### Option 1: Match DataFrame Default (Recommended)

```python
def infer_integer(value: int, ...) -> dt.Integer:
    """Infer integer type matching DataFrame defaults."""
    return dt.int64  # Always use int64, like DataFrames do
```

**Pros:**
- Matches Polars/Pandas behavior
- No overflow issues
- Consistent with columns
- Substitutability works

**Cons:**
- Uses more memory for small literals
- Not "optimal" type

### Option 2: Don't Pass Type to Backends

```python
# In Polars backend
return pl.lit(value)  # Let Polars choose
```

**Pros:**
- Polars will choose Int32/Int64 (safe)
- Fixes the immediate problem
- Minimal code change

**Cons:**
- Doesn't fix the conceptual mismatch
- Other backends might have same issue

### Option 3: Context-Aware Inference

```python
def infer_integer(value: int, context=None) -> dt.Integer:
    if context == 'operation':
        return dt.int64  # Wide type for operations
    else:
        # Smallest type for storage
        for dtype in (dt.int8, dt.int16, dt.int32, dt.int64):
            if dtype.bounds.lower <= value <= dtype.bounds.upper:
                return dtype
```

**Pros:**
- Optimal for both storage and operations
- Sophisticated

**Cons:**
- Complex
- Hard to reason about
- May have edge cases

---

## Recommendation

**Two-part fix:**

### 1. Immediate (Polars Backend)

Don't pass explicit narrow types:

```python
# ibis/backends/polars/compiler.py
elif dtype.is_integer():
    return pl.lit(value)  # Let Polars choose
```

### 2. Long-term (Core Ibis)

Change literal inference to match DataFrame defaults:

```python
# ibis/expr/datatypes/value.py
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    # Match DataFrame library defaults
    return dt.int64
```

Or at least use int32 as minimum:

```python
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    # Use int32 as minimum (like SQL INT)
    types = (dt.int32, dt.int64) if not prefer_unsigned else (dt.uint32, dt.uint64)
    for dtype in types:
        if dtype.bounds.lower <= value <= dtype.bounds.upper:
            return dtype
    return dt.int64
```

---

## Summary

**The asymmetry:**
- Literals: int8 (aggressive optimization)
- Columns: int64 (safe default)

**The consequence:**
- `literal(2) ** literal(10)` → 0 ❌
- `column(2) ** column(10)` → 1024 ✅

**The fix:**
- Make literals use int64 (or at least int32)
- Or don't pass explicit types to backends

**The principle:**
- Literals should behave like columns
- Both should behave like Python
- Avoid surprising users with overflow
