# Ibis Backend Comparison Results: The Smoking Gun

## Executive Summary

**Only the Polars backend fails**, and it fails in a very specific pattern that proves Ibis is passing explicit Int8 dtypes.

---

## Test Results

### Power Operations (2^10 = 1024)

| Backend | lit ** col | col ** lit | lit ** lit | col ** col |
|---------|------------|------------|------------|------------|
| **Polars** | **0** ❌ | 1024 ✅ | **0** ❌ | 1024 ✅ |
| DuckDB | 1024 ✅ | 1024 ✅ | 1024 ✅ | 1024 ✅ |
| SQLite | 1024 ✅ | 1024 ✅ | 1024 ✅ | 1024 ✅ |

### Multiplication Operations (63 * 63 = 3969)

| Backend | lit * col | col * lit | lit * lit | col * col |
|---------|-----------|-----------|-----------|-----------|
| **Polars** | 3969 ✅ | 3969 ✅ | **-127** ❌ | 3969 ✅ |
| DuckDB | 3969 ✅ | 3969 ✅ | 3969 ✅ | 3969 ✅ |
| SQLite | 3969 ✅ | 3969 ✅ | 3969 ✅ | 3969 ✅ |

---

## Key Findings

### 1. Literal Type Inference

```python
ibis.literal(2).type()   # → int8
ibis.literal(10).type()  # → int8
ibis.literal(63).type()  # → int8
```

**All literals inferred as int8** (smallest type that fits the value)

### 2. Pattern of Failure

**Polars backend failures:**
- `lit(2) ** col(10)` → 0 ❌ (literal on left)
- `lit(2) ** lit(10)` → 0 ❌ (both literals)
- `lit(63) * lit(63)` → -127 ❌ (both literals)

**Polars backend successes:**
- `col(2) ** lit(10)` → 1024 ✅ (column on left)
- `lit(63) * col(63)` → 3969 ✅ (literal * column)
- `col(63) * col(63)` → 3969 ✅ (both columns)

### 3. The Smoking Gun: Direct Polars Comparison

```python
# Without dtype (Polars chooses)
pl.lit(2) ** pl.lit(10)                           # → Int32: 1024 ✅
pl.lit(63) * pl.lit(63)                           # → Int32: 3969 ✅

# With Int8 dtype (what Ibis sends)
pl.lit(2, dtype=pl.Int8) ** pl.lit(10, dtype=pl.Int8)   # → Int8: 0 ❌
pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)   # → Int8: -127 ❌
```

**Proof:** When Polars chooses types itself → works. When Ibis specifies Int8 → fails.

---

## Why Only Polars Fails

### The Three Backends Behave Differently

**DuckDB/SQLite backends:**
- Don't pass explicit narrow dtypes for literals
- Let the backend choose appropriate types
- Everything works ✅

**Polars backend:**
- Explicitly passes `dtype=Int8` for `literal(2)`
- Polars respects this explicit dtype
- Operations overflow ❌

---

## Surprising Finding: lit ** lit Also Fails!

```
lit(2) ** lit(10) = 0  (Expected: 1024)
```

This means Ibis is **NOT constant-folding** power operations, or the constant folding is happening AFTER the Polars backend translation.

**Multiplication is different:**
- Some lit * lit operations work (when types fit)
- But `lit(63) * lit(63)` → -127 (wraps in Int8)

---

## Edge Cases Table

| Literal | Ibis Type | value * value | Notes |
|---------|-----------|---------------|-------|
| 2 | int8 | 4 | Fits in int8 ✅ |
| 63 | int8 | **-127** | Overflows int8 ❌ |
| 127 | int8 | **1** | Wraps around ❌ |
| 128 | int16 | 16384 | Now fits ✅ |
| 255 | int16 | **-511** | Still overflows! ❌ |
| 256 | int16 | **0** | Overflows ❌ |

**Pattern:** Even int16 isn't safe! 255*255 = 65025, which overflows int16 (-32768 to 32767).

---

## Why Literal × Column Works (Sometimes)

Looking at the multiplication results:

```
lit(63) * col(63) = 3969 ✅  (Works!)
```

**Why?** When one operand is a column, Polars likely promotes the literal to match the column's type (Int64), avoiding overflow.

But power doesn't have the same behavior:
```
lit(2) ** col(10) = 0 ❌  (Doesn't work!)
```

This confirms Polars' statement that power operations don't auto-promote like multiplication does.

---

## The Fix

**File:** `ibis/backends/polars/compiler.py`

**Current code (~line 54):**
```python
elif dtype.is_integer():
    typ = PolarsType.from_ibis(dtype)
    return pl.lit(op.value, dtype=typ)  # ← Explicitly passes Int8!
```

**Fixed code:**
```python
elif dtype.is_integer() or dtype.is_floating():
    return pl.lit(value)  # ← Let Polars choose appropriate type
```

---

## Test Evidence

Run: `python docs/Bug\ Reports/Ibis/comprehensive_backend_comparison.py`

**Output shows:**
1. ✅ DuckDB: All operations return correct values
2. ✅ SQLite: All operations return correct values
3. ❌ Polars: Multiple failures with literal operands

**Direct Polars test shows:**
- Polars without dtype → Int32, correct values ✅
- Polars with Int8 dtype → Int8, overflow ❌

---

## Conclusion

**The evidence is overwhelming:**

1. Only Polars backend fails
2. DuckDB and SQLite work perfectly
3. Direct Polars (without dtype) works perfectly
4. Direct Polars (with Int8 dtype) fails identically to Ibis
5. The failure pattern matches exactly what we'd expect from Int8 overflow

**Verdict:** Ibis Polars backend is explicitly passing Int8 dtypes, causing Polars to overflow. The fix is simple: don't pass explicit dtypes for numeric literals.

---

## Impact

**Affected operations with literals in Polars backend:**
- ❌ Power: `literal ** column`, `literal ** literal`
- ❌ Multiplication: `literal * literal` (when result overflows narrow type)
- ✅ Column-based operations: Mostly work (Polars promotes)

**Users affected:**
- Anyone using Ibis with Polars backend
- Any code with numeric literals in expressions
- Scientific computing, data transformations, financial calculations

**Workarounds (until fixed):**
1. Use column expressions instead of literals
2. Cast literals to Int64: `ibis.literal(2).cast('int64')`
3. Use DuckDB or SQLite backend instead of Polars
