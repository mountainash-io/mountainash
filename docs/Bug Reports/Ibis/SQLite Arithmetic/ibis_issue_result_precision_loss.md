# bug: SQLite backend loses float precision in complex expressions (result conversion bug)

## Core Problem

The SQLite backend loses floating-point precision when executing complex arithmetic expressions. The generated SQL is correct and returns precise float values, but Ibis's `.execute()` method rounds them to integers, causing silent data corruption.

This is a bug in the **SQLite backend's result conversion layer**, NOT a SQL generation issue. **Other backends (DuckDB, Polars) work correctly.**

## Key Example

```python
import ibis
import pandas as df

df = pd.DataFrame({'a': [20], 'b': [3], 'c': [10]})
con = ibis.sqlite.connect()
t = con.create_table('test', df)

# Complex expression with division
expr = (t.a + t.b) * t.c - t.a / t.b
result = t.select(expr.name('result')).execute()

print(result['result'][0])
# Actual:   224.0  (WRONG - rounded!)
# Expected: 223.333...  (what SQL actually returns)
```

## Expected vs Actual Behavior

### SQL Generated (Correct)
```sql
SELECT ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test
```

### Raw SQL Result (Correct)
```python
cursor.execute(sql)
cursor.fetchall()
# Returns: [(223.33333333333334,)]  ✓ Correct!
```

### Ibis `.execute()` Result (WRONG)
```python
t.select(expr).execute()['result'].tolist()
# Returns: [224.0]  ✗ Precision lost!
```

## Reproduction Code

```python
import ibis
import pandas as pd

# Test data
df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

# Create Ibis table
con = ibis.sqlite.connect()
t = con.create_table('test', df)

# Complex expression: (a + b) * c - a / b
expr = (t.a + t.b) * t.c - t.a  / t.b

# Test 1: Ibis execute (WRONG)
result_ibis = t.select(expr.name('result')).execute()
print("Ibis execute():", result_ibis['result'].tolist())

# Test 2: Raw SQL on same connection (CORRECT)
sql = ibis.to_sql(t.select(expr.name('result')), dialect='sqlite')
cursor = con.con.cursor()
cursor.execute(sql)
result_raw = cursor.fetchall()
print("Ibis cursor.fetchall():", [row[0] for row in result_raw])

# Expected values (Python)
expected = [
    (10+2)*5 - 10/2,    # 55.0
    (20+3)*10 - 20/3,   # 223.333...
    (30+4)*15 - 30/4    # 502.5
]
print("Expected:", expected)
```

## Analysis

1. **SQL generation is CORRECT** - Ibis properly casts to REAL
2. **SQLite returns CORRECT values** - Raw cursor fetch works fine
3. **Result conversion is WRONG** - `.execute()` loses precision

The bug is in how Ibis converts SQLite results to pandas DataFrames. It appears to be rounding float results to integers somewhere in the conversion pipeline.

## Impact

- **CRITICAL**: Silent data corruption in arithmetic operations
- **HIGH**: Users get wrong calculation results without any warning
- **HIGH**: Affects all complex expressions involving division
- **CRITICAL**: Precision loss is undetectable to end users

This is particularly dangerous because:
- No error is raised
- SQL is correct (so debugging tools won't help)
- Only affects certain expression types (making it hard to detect)
- Results "look reasonable" but are mathematically wrong

## Cross-Backend Testing

Testing the same expression across multiple backends:

| Backend | Result | Status |
|---------|--------|--------|
| SQLite  | `[55.0, 224.0, 503.0]` | ✗ Precision loss |
| DuckDB  | `[55.0, 223.333..., 502.5]` | ✓ Correct |
| Polars  | `[55.0, 223.333..., 502.5]` | ✓ Correct |

**This confirms the bug is specific to the SQLite backend.**

## Environment

- Ibis version: 10.4.0
- Affected backend: SQLite only
- Working backends: DuckDB, Polars
- Python version: 3.12.9
- Pandas version: 2.2.3

## Workaround

Use raw SQL execution instead of `.execute()`:
```python
sql = ibis.to_sql(expression, dialect='sqlite')
cursor = con.con.cursor()
cursor.execute(sql)
results = cursor.fetchall()
```

## Related Issues

- #671 - Original division fix (SQL generation - already fixed)
- #692 - PR for true division (SQL generation - already fixed)
- This issue is about result conversion, not SQL generation
