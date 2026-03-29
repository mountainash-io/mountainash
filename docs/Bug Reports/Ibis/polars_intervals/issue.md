# Bug: Polars backend fails with calendar-based intervals (months/years)

**Labels:** `bug`, `backends`

## Summary

The Ibis Polars backend cannot add or subtract months/years to timestamps, even though native Polars fully supports this via `Expr.dt.offset_by()`. The issue is in the Ibis compiler's `_make_duration()` function which tries to use `pl.duration(months=...)`, but Polars `duration()` only supports fixed durations (days, hours, etc.), not calendar-based intervals.

## Environment

- **Ibis version:** 11.0.0
- **Polars version:** 1.35.1
- **Python version:** 3.12.9
- **Operating System:** Linux

## Minimal Reproduction

```python
import ibis
import polars as pl
from datetime import datetime

# Create Ibis table with Polars backend
conn = ibis.polars.connect()
data = {
    "timestamp": [
        datetime(2024, 1, 1, 10, 0, 0),
        datetime(2024, 6, 15, 14, 30, 0),
    ]
}
pl_df = pl.DataFrame(data)
t = conn.create_table("test", pl_df, overwrite=True)

# Try to add 3 months
result = t.timestamp + ibis.interval(months=3)
executed = t.select(result.name("result")).execute()
```

## Error

```
TypeError: duration() got an unexpected keyword argument 'months'
```

**Full traceback:**
```
File "ibis/backends/polars/compiler.py", line 82, in _make_duration
    return pl.duration(**kwargs)
TypeError: duration() got an unexpected keyword argument 'months'
```

## Expected Behavior

The operation should succeed. Native Polars supports calendar-based intervals:

```python
# Native Polars - WORKS ✅
pl_df = pl.DataFrame({"timestamp": [datetime(2024, 1, 1, 10, 0, 0)]})
result = pl_df.select(pl.col("timestamp").dt.offset_by("3mo"))
# Result: [datetime(2024, 4, 1, 10, 0, 0)]
```

Other Ibis backends also work correctly:

```python
# Ibis DuckDB backend - WORKS ✅
conn = ibis.duckdb.connect()
t = conn.create_table("test", data, overwrite=True)
result = t.timestamp + ibis.interval(months=3)
executed = t.select(result.name("result")).execute()
# Success!
```

## Root Cause Analysis

### Polars API Distinction

Polars provides two different APIs for temporal arithmetic:

1. **`pl.duration()`** - Fixed durations only
   - **Supports:** `weeks`, `days`, `hours`, `minutes`, `seconds`, `milliseconds`, `microseconds`, `nanoseconds`
   - **Does NOT support:** `months`, `years` (calendar-based)
   - Represents exact time spans (e.g., "exactly 720 hours")

2. **`Expr.dt.offset_by()`** - Calendar-based intervals
   - **Supports:** `mo` (months), `y` (years) in addition to fixed durations
   - Uses string format: `"3mo"`, `"1y"`, `"-2mo"`, `"1y2mo3d"`
   - Respects calendar semantics (e.g., "1 month" = 28-31 days depending on the month)

**From Polars documentation** ([`pl.duration()` API docs](https://docs.pola.rs/api/python/stable/reference/api/polars.duration.html)):
> A `duration` represents a **fixed amount of time**. For non-fixed durations such as "calendar month" or "calendar day", please use `Expr.dt.offset_by()` instead.

**See also:**
- [`Expr.dt.offset_by()` API docs](https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.dt.offset_by.html)
- [Polars Temporal Data Guide](https://docs.pola.rs/user-guide/expressions/temporal/)

### Ibis Compiler Bug

**File:** `ibis/backends/polars/compiler.py:80-82`

```python
def _make_duration(value, dtype):
    kwargs = {f"{dtype.resolution}s": value}
    return pl.duration(**kwargs)  # ❌ Fails for months/years!
```

This function blindly passes all interval types to `pl.duration()`, including months and years which aren't supported.

## Complete Test Script

See `reproduction_test.py` in this directory.

## Proposed Solution

Modify the Polars compiler to detect calendar-based intervals and use `offset_by()` instead of `duration()`:

```python
@translate.register(ops.TimestampAdd)
def timestamp_add(op, **kw):
    left = translate(op.left, **kw)
    right_op = op.right

    # Check if right is a calendar-based interval (months/years)
    if isinstance(right_op, ops.Literal) and right_op.dtype.is_interval():
        resolution = right_op.dtype.resolution
        if resolution in ('month', 'year'):
            # Use offset_by for calendar intervals
            unit_map = {'month': 'mo', 'year': 'y'}
            offset_str = f"{right_op.value}{unit_map[resolution]}"
            return left.dt.offset_by(offset_str)

    # Standard duration addition for fixed intervals
    right = translate(right_op, **kw)
    return left + right
```

Similar handling would be needed for:
- `TimestampSubtract`
- Potentially other temporal operations

## Impact

This limitation affects Ibis Polars users who need to:
- ❌ Add/subtract months or years to timestamps
- ❌ Perform calendar-based date arithmetic
- ❌ Port code from other Ibis backends that uses month/year intervals

## Workaround

Until fixed, users can execute to native Polars and use `offset_by()`:

```python
# Workaround
df = t.execute()  # Get Polars DataFrame
result = df.select(pl.col("timestamp").dt.offset_by("3mo"))
```

## Additional Context

The distinction between "fixed durations" and "calendar intervals" is semantically important:
- **Fixed:** `interval(days=30)` = exactly 720 hours
- **Calendar:** `interval(months=1)` = 28-31 days depending on the month

All other Ibis backends (DuckDB, SQLite, PostgreSQL, etc.) correctly handle calendar-based intervals. This is specific to the Polars backend due to the Polars API design choice to separate fixed durations from calendar intervals.

## Status

**Issue filed:** [Link to GitHub issue once created]

**Our workaround:** We document this limitation in our test suite with `pytest.xfail()` markers explaining the Ibis Polars backend limitation.
