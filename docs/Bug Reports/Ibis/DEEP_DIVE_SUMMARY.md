# Deep Dive: Ibis Type Inference and Downcast Asymmetry

## The Question

**"Can we dig into the ibis resolution of types and the difference between type downcasting of literals and columns?"**

---

## The Answer in One Sentence

**Ibis aggressively downcasts literals to the smallest possible type (int8 for value 2) but preserves column types from DataFrames (int64), creating a fundamental asymmetry that causes overflow when they interact.**

---

## The Two Code Paths

### Path 1: Literal → int8

```python
ibis.literal(2)
    ↓
Ibis infers type: dt.int8 (smallest that fits)
    ↓
Polars receives: pl.lit(2, dtype=pl.Int8)
    ↓
Result: 8-bit integer
```

**Decision maker:** Ibis
**Philosophy:** Optimize memory (use smallest type)
**Code:** `ibis/expr/datatypes/value.py:128-135`

### Path 2: Column → int64

```python
pl.DataFrame({'x': [2]})
    ↓
Polars chooses type: Int64 (safe default)
    ↓
Ibis reads schema: int64
    ↓
Result: 64-bit integer
```

**Decision maker:** Polars
**Philosophy:** Safety and convenience
**Code:** Polars internal type system

---

## The Asymmetry

| Aspect | Literals | Columns |
|--------|----------|---------|
| Type decision by | Ibis | DataFrame library (Polars/Pandas) |
| For value 2 | int8 (8-bit) | int64 (64-bit) |
| Philosophy | Minimize memory | Maximize safety |
| Risk of overflow | HIGH | LOW |
| Matches Python int | NO | YES |

---

## Key Source Code

### Literal Type Inference

**File:** `ibis/expr/datatypes/value.py:128-135`

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

**For value 2:**
- Check int8 bounds: -128 <= 2 <= 127? ✓
- Return: dt.int8

**The problem:** Doesn't consider future operations!

### Polars Backend Translation

**File:** `ibis/backends/polars/compiler.py:~54`

```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype
    # ...
    typ = PolarsType.from_ibis(dtype)  # int8 → pl.Int8
    return pl.lit(op.value, dtype=typ)  # ← Explicitly passes narrow type!
```

**The problem:** Tells Polars to use int8 explicitly!

### Column Type Preservation

**How it works:**
1. User creates DataFrame: `pl.DataFrame({'x': [2]})`
2. Polars chooses Int64 (default for Python ints)
3. Ibis reads schema: `{'x': int64}`
4. Ibis preserves type: `table.x.type()` → `int64`

**No downcasting happens for columns!**

---

## Test Results

**Run:** `python docs/Bug\ Reports/Ibis/test_literal_vs_column_types.py`

### Type Inference Pattern

```
| Value | Literal Type | Column Type | Ratio |
|-------|--------------|-------------|-------|
|     2 | int8         | int64       | 1:8   |
|    10 | int8         | int64       | 1:8   |
|   127 | int8         | int64       | 1:8   |
|   128 | int16        | int64       | 1:4   |
|  1000 | int16        | int64       | 1:4   |
| 100000| int32        | int64       | 1:2   |
```

Columns are **consistently wider** than literals for the same value!

### Operation Results

```
| Expression | Result | Expected | Status |
|------------|--------|----------|--------|
| lit(2) ** int64_col(10) | 0 | 1024 | ❌ FAIL |
| col(2) ** lit(10) | 1024 | 1024 | ✅ PASS |
| col(int8) ** col(int8) | 0 | 1024 | ❌ FAIL |
```

**Pattern:** When literal is on left of power operation → overflow!

---

## Why This Design Exists

### Possible Rationale for Aggressive Downcasting

1. **Memory efficiency** - Smaller types use less memory
2. **Precise representation** - Match value exactly
3. **Embedded systems** - Memory-constrained environments
4. **Legacy compatibility** - Maybe older SQL systems did this?

### Why It's Wrong for Modern Use

1. **Memory is cheap** - 8 bytes vs 1 byte doesn't matter today
2. **Correctness > memory** - Wrong answer is worse than using more RAM
3. **User expectations** - Python int has unlimited precision
4. **DataFrame standards** - Polars/Pandas use int64 by default

---

## Why Columns Use int64

### Polars Default

```python
pl.DataFrame({'x': [2]})
# Schema: {'x': Int64}
```

**Why Int64?**
- Matches Python int semantics (unlimited precision)
- Safe default (no overflow for normal operations)
- Standard across data libraries
- Aligns with SQL BIGINT

### Pandas Default

```python
pd.DataFrame({'x': [2]})
# dtypes: {'x': dtype('int64')}
```

**Same reasoning!**

---

## The Consequence

### Substitutability Broken

```python
# With column value
table = ibis.table([('x', 'int64')], name='t')
table.x ** ibis.literal(10)  # Works if x=2

# Substitute with literal
ibis.literal(2) ** ibis.literal(10)  # FAILS!
```

**Same mathematical operation, different results!**

### Principle of Least Surprise Violated

```python
# Python
2 ** 10  # → 1024

# Ibis
ibis.literal(2) ** ibis.literal(10)  # → 0 ❌
```

**Users expect Ibis to behave like Python!**

---

## Comparison with Other Systems

### NumPy

```python
# Auto type
np.array([2])  # dtype: int64 (default)

# Explicit type
np.int8(2) ** np.int8(10)  # Wraps to 0
```

**NumPy defaults to int64, like DataFrames!**

### SQL

```sql
SELECT 2;  -- No explicit type
-- Database chooses INT or BIGINT (32/64-bit)
```

**SQL uses wide types for untyped literals!**

### R

```r
2  # Stored as numeric (double)
2L  # Stored as integer (32-bit)
```

**R defaults to 32-bit for integers!**

---

## The Fix

### Option 1: Change Literal Inference (Recommended Long-term)

```python
# ibis/expr/datatypes/value.py
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    # Match DataFrame defaults
    return dt.int64
```

**Pros:**
- Matches DataFrame behavior
- Fixes root cause
- Aligns with Python semantics

**Cons:**
- Breaking change
- Uses more memory (minimal impact)

### Option 2: Don't Pass Type to Polars (Quick Fix)

```python
# ibis/backends/polars/compiler.py
elif dtype.is_integer():
    return pl.lit(value)  # Let Polars choose
```

**Pros:**
- One-line fix
- Polars will choose Int32/Int64
- Fixes immediate problem

**Cons:**
- Doesn't fix conceptual issue
- Only fixes Polars backend

### Option 3: Use int32 as Minimum

```python
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    # Use int32 minimum (like SQL INT)
    types = (dt.int32, dt.int64)
    for dtype in types:
        if dtype.bounds.lower <= value <= dtype.bounds.upper:
            return dtype
    return dt.int64
```

**Pros:**
- Compromise between memory and safety
- Matches SQL INT
- Still narrower than int64

**Cons:**
- int32 can still overflow (2^31)
- Partial fix

---

## Recommended Approach

**Two-phase fix:**

### Phase 1: Immediate (Polars Backend)

Don't pass explicit narrow types:

```python
# ibis/backends/polars/compiler.py:~54
elif dtype.is_integer() or dtype.is_floating():
    return pl.lit(value)  # Let Polars choose
```

**Result:**
- Polars chooses Int32/Int64
- Fixes overflow issues
- Minimal code change

### Phase 2: Long-term (Core Ibis)

Change literal inference to match DataFrames:

```python
# ibis/expr/datatypes/value.py:128
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    return dt.int64  # Always use int64
```

**Result:**
- Conceptual consistency
- Matches all DataFrame libraries
- No surprises for users

---

## Summary

**The asymmetry:**

| What | Literal | Column | Why Different? |
|------|---------|--------|----------------|
| Type decision | Ibis | Polars/Pandas | Different libraries |
| Algorithm | Smallest fits | Safe default | Different philosophy |
| For value 2 | int8 (8-bit) | int64 (64-bit) | 8x difference! |
| Risk | High overflow | Low overflow | Safety vs memory |

**The consequence:**
- `literal(2) ** literal(10)` → 0 ❌
- `column(2) ** literal(10)` → 1024 ✅

**The fix:**
- Make literals use int64 (like columns do)
- Or don't pass explicit types to Polars

**The principle:**
- Literals and columns should have same types
- Both should match Python int behavior
- Safety over memory optimization
