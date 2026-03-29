# Ibis SQLite Precision Loss Bug - Investigation Summary

## Bug Confirmed in Ibis 11.0.0

**Affected Version:** Ibis 11.0.0 (official release)
**Backends Affected:** SQLite only (DuckDB and Polars work correctly)

## The Bug

When executing complex arithmetic expressions containing division, the SQLite backend returns rounded integer values instead of precise floating-point results.

### Reproduction

```python
import ibis
import pandas as pd

df = pd.DataFrame({'a': [10, 20, 30], 'b': [2, 3, 4], 'c': [5, 10, 15]})

con = ibis.sqlite.connect()
t = con.create_table('test', df)

expr = (t.a + t.b) * t.c - t.a / t.b
result = t.select(expr.name('result')).execute()

print(result['result'].tolist())
# Actual:   [55.0, 224.0, 503.0]  ← WRONG (rounded)
# Expected: [55.0, 223.333..., 502.5]  ← Correct
```

## Investigation Findings

### 1. SQL Generation is Correct ✓

The generated SQL properly casts to REAL:
```sql
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test
```

### 2. Direct SQL Execution Returns Correct Values ✓

When executing the same SQL directly on the cursor:
```python
cursor = con.con.cursor()
cursor.execute(sql)
rows = cursor.fetchall()
# Returns: [(55.0,), (223.33333333333334,), (502.5,)]  ✓ Correct!
```

### 3. The Cursor Passed to `_fetch_from_cursor()` Has Integers ✗

When intercepting the cursor in `_fetch_from_cursor()`:
```python
rows = list(cursor)
# Returns: [(55,), (224,), (503,)]  ✗ WRONG - integers, not floats!
```

### 4. Issue is Between `raw_sql()` and `_fetch_from_cursor()`

The execution flow:
```python
# In execute() method:
with self._safe_raw_sql(sql) as cur:
    result = self._fetch_from_cursor(cur, schema)
```

Somewhere between `raw_sql()` returning the cursor and `_fetch_from_cursor()` receiving it, the float values become integers.

### 5. Cross-Backend Testing Confirms SQLite-Only Issue

| Backend | Result | Status |
|---------|--------|--------|
| SQLite  | `[55.0, 224.0, 503.0]` | ✗ Precision loss |
| DuckDB  | `[55.0, 223.333..., 502.5]` | ✓ Correct |
| Polars  | `[55.0, 223.333..., 502.5]` | ✓ Correct |

## Root Cause Analysis

Based on extensive testing, the issue appears to be:

1. **Not in SQL generation** - The SQL is correct with `CAST(a AS REAL)`
2. **Not in SQLite itself** - Direct cursor execution returns correct floats
3. **Not in pandas** - `pd.DataFrame.from_records()` works correctly with float data
4. **Not in type conversion** - `convert_table()` works correctly

The problem is that **the cursor being passed to `_fetch_from_cursor()` already contains rounded integer values** instead of the float values that SQLite actually returns.

### Hypothesis

There may be:
1. A PRAGMA or connection setting that affects numeric type handling
2. A cursor wrapper or interceptor that's converting types
3. An issue with how `con.execute()` is being called vs `cursor.execute()`
4. Some interaction between schema inference and result type coercion

## Test Files Created

All test files are in `/docs/Bug Reports/Ibis/SQLite Arithmetic/`:

1. `test_precision_loss_all_backends.py` - Confirms SQLite-only issue
2. `test_exact_failing_expression.py` - Shows cursor returns correct floats but Ibis returns rounded values
3. `definitive_cursor_test.py` - **Proves cursor has integers when passed to `_fetch_from_cursor()`**
4. `test_execute_methods.py` - Shows `con.execute()` vs `cursor.execute()` both return floats correctly
5. Plus 15+ other test files documenting the investigation

## Impact

- **CRITICAL**: Silent data corruption
- **HIGH**: Affects all complex arithmetic expressions with division
- **HIGH**: Users get wrong results without any error/warning
- **MEDIUM**: Only affects SQLite backend

## Workaround

Use raw SQL execution:
```python
sql = ibis.to_sql(expression, dialect='sqlite')
cursor = con.con.cursor()
cursor.execute(sql)
results = cursor.fetchall()
# Convert to DataFrame manually
```

## Next Steps

1. File bug report with Ibis project
2. Include all test cases and findings
3. Suggest investigating:
   - Connection configuration in `do_connect()`
   - Any cursor wrappers or interceptors
   - Difference between context manager path vs direct execution
   - PRAGMA settings that might affect type inference

## Modulo Bug (Separate Issue)

The modulo/remainder semantic difference is a SEPARATE bug affecting both SQLite and DuckDB. See `ibis_issue_modulo_remainder_semantics.md` for details.
