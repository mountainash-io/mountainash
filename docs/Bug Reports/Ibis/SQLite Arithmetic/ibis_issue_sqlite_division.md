# bug: SQLite backend performs integer division instead of float division

## Core Problem

The SQLite backend performs integer division when both operands are integers, returning truncated integer results instead of Python-style true division (float results). This breaks cross-backend compatibility and violates Python 3 division semantics that Ibis claims to follow.

This was supposedly fixed in 2015 via PR #692 ("Make normal division true division (a la Python 3)"), but the issue persists in current Ibis versions.

## Key Example

```python
import ibis

# SQLite backend
con = ibis.sqlite.connect()
t = con.create_table('test', {'a': [20], 'b': [3]})

# Division should return float
result = t.select((t.a / t.b).name('division')).execute()
# Expected: 6.666666...
# Actual:   6 (integer!)
```

## Expected vs Actual Behavior

### Expected (Python 3 / Other Backends)
- `20 / 3` → `6.666666666666667` (float)
- `10 / 4` → `2.5` (float)
- `5 / 2` → `2.5` (float)

### Actual (SQLite Backend)
- `20 / 3` → `6` (integer)
- `10 / 4` → `2` (integer)
- `5 / 2` → `2` (integer)

**Other backends (Polars, DuckDB, Pandas) correctly return float results.**

## Reproduction Code

```python
import ibis
import pandas as pd

# Test data
df = pd.DataFrame({
    'dividend': [20, 10, 5, 7],
    'divisor': [3, 4, 2, 3]
})

# SQLite backend
con_sqlite = ibis.sqlite.connect()
t_sqlite = con_sqlite.create_table('test', df)
result_sqlite = t_sqlite.select(
    (t_sqlite.dividend / t_sqlite.divisor).name('result')
).execute()

print("SQLite results:")
print(result_sqlite)
# Output: [6, 2, 2, 2] - All integers!

# DuckDB backend (for comparison)
con_duckdb = ibis.duckdb.connect()
t_duckdb = con_duckdb.create_table('test', df)
result_duckdb = t_duckdb.select(
    (t_duckdb.dividend / t_duckdb.divisor).name('result')
).execute()

print("\nDuckDB results:")
print(result_duckdb)
# Output: [6.666..., 2.5, 2.5, 2.333...] - Correct floats!
```

## Root Cause

SQLite performs integer division when both operands have INTEGER affinity. From SQLite docs:
> "The result of a division is always a floating point value, except when both operands are INTEGER, in which case the result is also INTEGER."

## Historical Context

- **Issue #671** (Sep 2015): "Division by integer should automatically cast to float/real (emulate Python truediv)"
- **PR #692** (Oct 2015): "Make normal division true division (a la Python 3) and add floordiv operators"
  - Specifically mentions: "Implement floordiv / truediv semantics for sqlite"
- **Status**: Closed as completed in 2015

**However, this fix is not working in current Ibis versions (10.4.0+)**, suggesting either:
1. The fix was incomplete (only handled certain expression types)
2. A regression occurred in later versions
3. The fix only applied to literals, not column references

## Suggested Fix

The SQLite backend should cast operands to REAL before division:

```sql
-- Current (broken):
SELECT dividend / divisor FROM test

-- Should generate:
SELECT CAST(dividend AS REAL) / divisor FROM test
-- OR
SELECT dividend / CAST(divisor AS REAL) FROM test
```

This matches what was supposedly implemented in PR #692.

## Impact

- **HIGH**: Breaks cross-backend compatibility guarantees
- **HIGH**: Produces incorrect numeric results silently
- **HIGH**: Violates Python 3 division semantics
- Users get different calculation results depending on backend choice
- Critical for data analysis where precision matters (percentages, ratios, averages)
- Silent data errors are particularly dangerous as they go unnoticed

## Environment

- Ibis version: 10.4.0 (also affects recent versions)
- Backend: SQLite
- Python version: 3.11+

## Related Issues

- #671 - Original issue (closed as fixed, but not actually fixed)
- #692 - PR that supposedly fixed this
- #11742 - Similar issue with arithmetic operators (my previous report)
