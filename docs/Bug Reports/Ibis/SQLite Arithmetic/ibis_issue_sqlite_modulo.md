# bug: SQLite backend implements remainder instead of modulo (wrong semantics for negative operands)

## Core Problem

The SQLite backend implements **remainder** (C-style) semantics for the modulo operator (`%`), which differs from Python's **modulo** semantics. This causes incorrect results when either operand is negative, breaking cross-backend compatibility.

Unlike the division issue (#671/#692), this problem has **never been addressed** in Ibis.

## Key Example

```python
import ibis

# SQLite backend
con = ibis.sqlite.connect()
t = con.create_table('test', {'a': [-10], 'b': [3]})

# Modulo with negative operand
result = t.select((t.a % t.b).name('modulo')).execute()
# Expected (Python): 2  (result takes sign of divisor)
# Actual (SQLite):  -1  (result takes sign of dividend - WRONG!)
```

## Expected vs Actual Behavior

### Python/Polars/Pandas/DuckDB (Modulo - Expected)
Result takes the **sign of the divisor** (right operand):

- `-10 % 3` → `2`  (positive, like divisor)
- `10 % -3` → `-2` (negative, like divisor)
- `-10 % -3` → `-1` (negative, like divisor)

### SQLite (Remainder - Actual)
Result takes the **sign of the dividend** (left operand):

- `-10 % 3` → `-1` (negative, like dividend - **WRONG**)
- `10 % -3` → `1` (positive, like dividend - **WRONG**)
- `-10 % -3` → `-1` (negative, like dividend - correct by coincidence)

## Reproduction Code

```python
import ibis
import pandas as pd

# Test data with negative operands
df = pd.DataFrame({
    'dividend': [-10, 10, -10, -17, 17],
    'divisor': [3, -3, -3, 4, -4]
})

# SQLite backend
con_sqlite = ibis.sqlite.connect()
t_sqlite = con_sqlite.create_table('test', df)
result_sqlite = t_sqlite.select(
    (t_sqlite.dividend % t_sqlite.divisor).name('result')
).execute()

print("SQLite results (WRONG):")
print(result_sqlite)
# Output: [-1, 1, -1, -1, 1]

# DuckDB backend (for comparison)
con_duckdb = ibis.duckdb.connect()
t_duckdb = con_duckdb.create_table('test', df)
result_duckdb = t_duckdb.select(
    (t_duckdb.dividend % t_duckdb.divisor).name('result')
).execute()

print("\nDuckDB results (CORRECT):")
print(result_duckdb)
# Output: [2, -2, -1, 3, -3]

# Verify Python semantics
print("\nPython native (expected):")
for i, row in df.iterrows():
    print(f"{row['dividend']} % {row['divisor']} = {row['dividend'] % row['divisor']}")
# Output: -10 % 3 = 2, etc. (matches DuckDB)
```

## Mathematical Background

There are two common implementations of the modulo/remainder operation:

### Modulo (Python, Ruby, Polars, Pandas)
```
a mod n = a - n * floor(a/n)
```
Result has the same sign as the **divisor** (right operand).

### Remainder (C, Java, SQLite)
```
a rem n = a - n * trunc(a/n)
```
Result has the same sign as the **dividend** (left operand).

For positive operands, both produce identical results. They differ only with negative operands.

See: https://en.wikipedia.org/wiki/Modulo_operation

## Root Cause

SQLite's `%` operator implements remainder (C-style), not modulo (Python-style). From SQLite documentation and behavior:
```sql
SELECT -10 % 3;  -- Returns -1 (remainder)
```

Python's modulo operation:
```python
-10 % 3  # Returns 2 (modulo)
```

## Suggested Fix

The SQLite backend should rewrite modulo operations to emulate Python semantics:

```sql
-- Current (broken):
SELECT dividend % divisor FROM test

-- Should generate:
SELECT ((dividend % divisor) + divisor) % divisor FROM test
```

This formula converts remainder to modulo:
- For positive results: `(result + divisor) % divisor = result` (unchanged)
- For negative results: Shifts by divisor to match Python semantics

**Example:**
- `-10 % 3` in SQLite returns `-1`
- `((-1) + 3) % 3 = 2 % 3 = 2` ✓ (correct)

## Impact

- **HIGH**: Breaks cross-backend compatibility for negative operands
- **MEDIUM**: Mathematical operations involving negative numbers produce wrong results
- **HIGH**: Violates user expectations (Python semantics)
- Silent errors in:
  - Circular buffer indexing with negative indices
  - Periodic calculations with negative values
  - Hash table implementations
  - Modular arithmetic in algorithms

## Use Cases Affected

Common patterns that fail with negative values:
```python
# Circular indexing (wrapping negative indices)
index % array_length

# Periodic time calculations
hours_offset % 24

# Hash distribution
hash_value % bucket_count

# Modular arithmetic
(a - b) % modulus
```

## Environment

- Ibis version: 10.4.0 (also affects all versions)
- Backend: SQLite
- Python version: 3.11+

## Related Issues

- #671 - Division issue (addressed in 2015, though may not be working)
- #692 - PR for division fix (modulo was not included)
- #11742 - Similar arithmetic operator issue (my previous report)

## Historical Note

Unlike the division issue which was addressed in PR #692 (2015), the modulo/remainder semantic difference has **never been fixed** or even reported to Ibis. This appears to be a completely unknown issue.
