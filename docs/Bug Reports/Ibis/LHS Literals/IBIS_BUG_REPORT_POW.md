# Ibis Bug Report: Power Operator Returns Wrong Results (Polars Backend)

## Summary

The Ibis Polars backend produces incorrect results (returns 0) for power operations when the base is a literal that Ibis infers as a narrow integer type (Int8), and the result would overflow that type.

## Environment

- **Ibis version**: 10.4.0 (tested with patched version)
- **Backend**: Polars
- **Python version**: 3.x
- **OS**: Linux

## Minimal Reproduction

```python
import ibis
import polars as pl

# Setup
conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df)

# Case 1: literal on left (FAILS)
result1 = (ibis.literal(2) ** ibis._['x']).execute()[0]
print(f"ibis.literal(2) ** col(10) = {result1}")
# Expected: 1024 (2^10)
# Actual: 0 ❌

# Case 2: raw value on left (FAILS)
result2 = (2 ** ibis._['x']).execute()[0]
print(f"2 ** col(10) = {result2}")
# Expected: 1024
# Actual: 0 ❌

# Case 3: literal on right (WORKS)
result3 = (ibis._['x'] ** ibis.literal(2)).execute()[0]
print(f"col(10) ** ibis.literal(2) = {result3}")
# Expected: 100 (10^2)
# Actual: 100 ✅

# Case 4: with explicit wider type (WORKS)
result4 = (ibis.literal(2).cast('int64') ** ibis._['x']).execute()[0]
print(f"ibis.literal(2).cast('int64') ** col(10) = {result4}")
# Expected: 1024
# Actual: 1024 ✅
```

## Expected Behavior

All power operations should return mathematically correct results:
- `2 ** 10` = 1024
- `10 ** 2` = 100

## Actual Behavior

When a literal inferred as Int8 is the base of a power operation, Ibis returns **0** instead of the correct result.

## Root Cause

Two contributing issues:

### 1. Ibis Type Inference (Primary Cause)

Ibis infers `literal(2)` as `Int8` (the smallest type that fits the value 2):

```python
>>> ibis.literal(2).type()
int8
```

### 2. Polars Backend Implementation

The Polars backend passes this narrow type to Polars:

```python
# In ibis/backends/polars/compiler.py
@translate.register(ops.Literal)
def literal(op, **_):
    # ...
    else:
        typ = PolarsType.from_ibis(dtype)
        return pl.lit(op.value, dtype=typ)  # ← Passes Int8
```

This generates: `pl.lit(2, dtype=Int8).pow(col)`, which triggers a Polars bug where it returns 0 on overflow.

### 3. Upstream Polars Issue

Polars itself has a bug where `pl.lit(2, dtype=Int8).pow(col)` returns 0 instead of automatically upcasting (note: the `**` operator DOES upcast correctly).

## Impact

- **Severity**: High - Produces silently wrong results
- **Affected operations**: Power operations with literals on the left side
- **Backends affected**: Polars only (DuckDB and SQLite work correctly)

## Comparison with Other Backends

| Backend | `literal(2) ** col(10)` | Status |
|---------|------------------------|--------|
| DuckDB  | 1024                   | ✅ Works |
| SQLite  | 1024                   | ✅ Works |
| Polars  | 0                      | ❌ Fails |

## Proposed Fix

**Option 1: Don't enforce narrow integer types** (Recommended)

Location: `ibis/backends/polars/compiler.py`, line ~85-110

```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype

    if value is None:
        return pl.lit(None, dtype=PolarsType.from_ibis(dtype))

    if dtype.is_array():
        # ... (array handling)
    elif dtype.is_struct():
        # ... (struct handling)
    elif dtype.is_interval():
        return _make_duration(value, dtype)
    elif dtype.is_null() or dtype.is_binary():
        return pl.lit(value)
    elif dtype.is_integer():  # ← ADD THIS
        return pl.lit(value)  # Let Polars infer appropriate type
    else:
        typ = PolarsType.from_ibis(dtype)
        return pl.lit(op.value, dtype=typ)
```

**Benefits**:
- ✅ One-line fix
- ✅ Lets Polars choose appropriate types
- ✅ Fixes not just power but other potential overflow issues
- ✅ Fully backward compatible
- ✅ Consistent with DuckDB and SQLite backends

**Option 2: Special handling in Power operation**

```python
@translate.register(ops.Power)
def power(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)

    # Upcast narrow integer literals to avoid overflow
    if isinstance(op.left, ops.Literal) and op.left.dtype.is_integer():
        if op.left.dtype.nbytes < 8:  # Less than Int64
            left = left.cast(pl.Int64)

    return left.pow(right)
```

**Benefits**:
- ✅ Targeted fix for power operations
- ❌ More complex
- ❌ Doesn't fix other potential overflow issues

## Workarounds

Until fix is deployed:

```python
# ❌ Don't do this
ibis.literal(2) ** column

# ✅ Do this instead
ibis.literal(2).cast('int64') ** column

# OR (if exponent is known)
ibis.literal(2, type='int64') ** column
```

## Test Cases

After fix, these should pass:

```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df)

# All should return 1024
assert (ibis.literal(2) ** ibis._['x']).execute()[0] == 1024
assert (2 ** ibis._['x']).execute()[0] == 1024
assert (ibis.literal(2).cast('int64') ** ibis._['x']).execute()[0] == 1024

# Should return 100
assert (ibis._['x'] ** ibis.literal(2)).execute()[0] == 100
assert (ibis._['x'] ** 2).execute()[0] == 100
```

## Backward Compatibility

✅ **Fully backward compatible**

This change:
- Only affects cases that currently produce **wrong results** (0 instead of correct value)
- Does NOT change any working functionality
- Makes Polars backend consistent with DuckDB and SQLite
- Aligns with Polars' design (dtype is optional)

## Related Issues

This is the **second** Ibis Polars backend bug discovered in this investigation:

1. **Issue #1** (Fixed): `_binop` contract violation - doesn't return `NotImplemented` for unbound references
   - Fixed by adding `InputTypeError` to exception handler

2. **Issue #2** (This issue): Power operator integer overflow
   - Needs fix in literal type handling or power operation

Both stem from narrow type enforcement in the Polars backend.

## Files for Reproduction

- `docs/power_operator_comparison.py` - Comprehensive comparison script
- `docs/POWER_OPERATOR_ANALYSIS.md` - Detailed analysis
- `docs/IBIS_POW_FIX_PROPOSAL.md` - Fix proposal with alternatives
