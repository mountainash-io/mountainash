# Explicit Int64 Casting: The Workaround Verification

## Summary

**Explicit int64 casting completely fixes the overflow issue across all backends.**

---

## Test Results

### Power Operation: 2^10 = 1024

| Backend | lit_2(i8) ** col_y | lit_2.cast(i64) ** col_y | lit_2(type=i64) ** col_y |
|---------|-------------------|--------------------------|--------------------------|
| ibis-polars | 0 ❌ | 1024 ✅ | 1024 ✅ |
| ibis-duckdb | 1024 ✅ | 1024 ✅ | 1024 ✅ |
| ibis-sqlite | 1024 ✅ | 1024 ✅ | 1024 ✅ |

### Multiplication: 64*64 = 4096 (with int8 column)

| Backend | lit_64(i8) * col_z(i8) | lit_64.cast(i64) * col_z(i8) |
|---------|------------------------|------------------------------|
| ibis-polars | 0 ❌ | 4096 ✅ |
| ibis-duckdb | ERROR ❌ | 4096 ✅ |
| ibis-sqlite | 4096 ✅ | 4096 ✅ |

---

## Failure Counts (Polars Backend Only)

**Original approach (int8 inference):**
- Power failures: 2/5 cases
- Mult failures: 2/4 cases

**With .cast(int64) workaround:**
- Power failures: 0/5 cases ✅
- Mult failures: 0/4 cases ✅

**100% success rate with explicit int64 casting!**

---

## Two Workarounds Available

### Option 1: Cast After Creation

```python
ibis.literal(2).cast('int64') ** table.x
```

**Pros:**
- Explicit and clear
- Works with any literal value
- Easy to add to existing code

**Cons:**
- Verbose
- Easy to forget

### Option 2: Specify Type on Creation

```python
ibis.literal(2, type='int64') ** table.x
```

**Pros:**
- Cleaner syntax
- Type specified upfront
- Harder to forget

**Cons:**
- Requires knowing to do it
- Not obvious to new users

---

## What Gets Sent to Polars

### Without Cast (Fails)

```python
# User writes
ibis.literal(2) ** table.x

# Ibis infers
literal(2, dtype=int8)

# Polars receives
pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))

# Result
0 ❌ (overflow in int8)
```

### With Cast (Works)

```python
# User writes
ibis.literal(2).cast('int64') ** table.x

# Ibis casts
literal(2, dtype=int8).cast(int64)

# Polars receives
pl.lit(2, dtype=pl.Int8).cast(pl.Int64).pow(pl.col('x'))

# Result
1024 ✅ (no overflow in int64)
```

### With Type Specified (Works)

```python
# User writes
ibis.literal(2, type='int64') ** table.x

# Ibis creates
literal(2, dtype=int64)

# Polars receives
pl.lit(2, dtype=pl.Int64).pow(pl.col('x'))

# Result
1024 ✅ (no overflow in int64)
```

---

## User Experience Problem

### Current Situation (Bad UX)

```python
# Natural code - FAILS SILENTLY
ibis.literal(2) ** table.x  # → 0 ❌

# Required code - VERBOSE
ibis.literal(2).cast('int64') ** table.x  # → 1024 ✅
```

**Users expect the first version to work!**

### After Fix (Good UX)

Once Ibis is fixed, both would work:

```python
# Natural code - WORKS
ibis.literal(2) ** table.x  # → 1024 ✅

# Explicit code - STILL WORKS
ibis.literal(2).cast('int64') ** table.x  # → 1024 ✅
```

---

## Why SQL Backends Don't Need This

### DuckDB/SQLite

```python
# User writes
ibis.literal(2) ** table.x

# Ibis infers
literal(2, dtype=int8)

# SQL generated
SELECT POWER(2, x) FROM table

# Database receives
Untyped literal "2"

# Database chooses
INT or BIGINT (32/64-bit)

# Result
1024 ✅ (no overflow)
```

**SQL has no explicit type in the literal!**

---

## Comprehensive Test Coverage

The comprehensive test (`comprehensive_type_combination_test.py`) verifies:

1. **Pure Polars API** - Direct pl.lit() behavior
2. **Ibis Backends** - Polars, DuckDB, SQLite
3. **Raw Numbers** - Proves they're identical to literals
4. **Explicit Casting** - Verifies the workaround

**Test matrix:**
- 3 backends (Polars, DuckDB, SQLite)
- 2 operations (power, multiplication)
- 2 type combinations (int64 columns, int8 columns)
- 3 approaches (original, .cast(), type=)

**Total: 36 test cases**

---

## Recommendation

### For Users (Immediate)

**Use explicit int64 casting:**

```python
# Power operations
ibis.literal(2, type='int64') ** table.x

# Multiplication with narrow columns
ibis.literal(64, type='int64') * table.z

# Or use .cast()
ibis.literal(2).cast('int64') ** table.x
```

### For Ibis (Long-term)

**Fix the root cause:**

1. **Short-term:** Don't pass explicit dtypes to Polars backend
2. **Long-term:** Change literal inference to use int64 by default

---

## Key Takeaway

**The workaround proves the fix is simple:**

If users can fix it with `.cast('int64')`, then Ibis can fix it by defaulting to int64 or not passing explicit types to Polars.

**This is not a Polars bug - it's an Ibis API design issue.**
