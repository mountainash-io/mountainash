# Ibis Power Operator Fix Proposal

## Problem

The Ibis Polars backend produces incorrect results for power operations when the base is a literal:

```python
ibis.literal(2) ** ibis._['x']  # where x=10
# Expected: 1024
# Actual: 0
```

## Root Cause

1. `ibis.literal(2)` is inferred as `Int8` (smallest type that fits)
2. Polars backend passes explicit dtype: `pl.lit(2, dtype=Int8)`
3. Computing `2^10 = 1024` overflows Int8 (range: -128 to 127)
4. Polars returns 0 due to overflow

## Fix Options

### Option 1: Omit dtype for numeric literals in Polars backend (Simplest)

**Location**: `ibis/backends/polars/compiler.py`, line 85-110

```python
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
    elif dtype.is_integer():  # NEW: Don't enforce narrow int types
        return pl.lit(value)  # Let Polars infer appropriate type
    else:
        typ = PolarsType.from_ibis(dtype)
        return pl.lit(op.value, dtype=typ)
```

**Pros:**
- Simple one-line addition
- Fixes power operation overflow
- Polars will choose appropriate type automatically

**Cons:**
- May change behavior for other operations
- Loses explicit type information

### Option 2: Special handling in Power operation

**Location**: `ibis/backends/polars/compiler.py`, line 721-725

```python
@translate.register(ops.Power)
def power(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)

    # If left is a narrow integer literal, cast to wider type to avoid overflow
    if isinstance(op.left, ops.Literal) and op.left.dtype.is_integer():
        left_dtype = op.left.dtype
        if left_dtype.nbytes < 8:  # Less than Int64
            left = left.cast(pl.Int64)

    return left.pow(right)
```

**Pros:**
- Targeted fix for power operations only
- Preserves type information elsewhere
- Explicit about intent

**Cons:**
- More complex
- Only fixes power, not other potential overflow issues

### Option 3: Use ** operator instead of .pow() method

**Location**: `ibis/backends/polars/compiler.py`, line 721-725

```python
@translate.register(ops.Power)
def power(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)
    return left ** right  # Use operator instead of .pow()
```

**Pros:**
- Simplest change (one character!)
- May leverage Polars' operator overloading which might handle types better

**Cons:**
- Relies on Polars' operator implementation
- Not clear if this actually fixes the issue

## Recommendation

**Use Option 1** (omit dtype for integer literals) because:

1. ✅ Simplest and most robust fix
2. ✅ Lets Polars choose appropriate types
3. ✅ Fixes not just power but other potential overflow issues
4. ✅ Follows Polars' own recommendation (they don't require dtype)
5. ✅ Similar to how other backends (DuckDB, SQLite) handle it

## Test Cases

After fix, these should all work:

```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df)

# Should return 1024
(ibis.literal(2) ** ibis._['x']).execute()  # Currently returns 0

# Should return 1024
(2 ** ibis._['x']).execute()  # Currently returns 0

# Should return 100
(ibis._['x'] ** ibis.literal(2)).execute()  # Already works
```

## Backward Compatibility

✅ **Fully backward compatible**

This change:
- Only affects cases that currently produce wrong results
- Does NOT change any working functionality
- Makes Polars backend consistent with DuckDB and SQLite backends
- Aligns with Polars' own design (dtype is optional)

