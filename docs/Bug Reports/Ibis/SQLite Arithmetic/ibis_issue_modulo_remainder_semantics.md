# bug: SQLite and DuckDB backends use remainder instead of Python modulo semantics

## Core Problem

The SQLite and DuckDB backends implement **remainder** (C-style) semantics for the modulo operator (`%`), which differs from Python's **modulo** semantics. This causes incorrect results when either operand is negative, breaking cross-backend compatibility and violating user expectations from Python.

**Affected Backends:** SQLite, DuckDB
**Correct Backends:** Polars

## Key Example

```python
import ibis
import pandas as pd

df = pd.DataFrame({'a': [-10], 'b': [3]})

# SQLite backend
con = ibis.sqlite.connect()
t = con.create_table('test', df)
result = t.select((t.a % t.b).name('result')).execute()

print(result['result'][0])
# Actual (SQLite):  -1  (remainder - WRONG)
# Expected (Python): 2  (modulo - correct)
```

## Mathematical Background

There are two implementations of the modulo/remainder operation:

### Modulo (Python, Ruby, Polars)
```
a mod n = a - n * floor(a/n)
```
Result has the same sign as the **divisor** (right operand).

### Remainder (C, Java, SQLite, DuckDB)
```
a rem n = a - n * trunc(a/n)
```
Result has the same sign as the **dividend** (left operand).

**For positive operands, both produce identical results.
They differ ONLY with negative operands.**

See: https://en.wikipedia.org/wiki/Modulo_operation

## Expected vs Actual Behavior

### Python/Polars (Expected - Modulo)
Result takes the **sign of the divisor**:

| Expression | Python | Expected |
|------------|--------|----------|
| `-10 % 3`  | `2`    | ✓        |
| `10 % -3`  | `-2`   | ✓        |
| `-10 % -3` | `-1`   | ✓        |
| `-17 % 4`  | `3`    | ✓        |
| `17 % -4`  | `-3`   | ✓        |

### SQLite/DuckDB (Actual - Remainder)
Result takes the **sign of the dividend**:

| Expression | SQLite/DuckDB | Wrong |
|------------|---------------|-------|
| `-10 % 3`  | `-1`          | ✗     |
| `10 % -3`  | `1`           | ✗     |
| `-10 % -3` | `-1`          | ✓ (coincidence) |
| `-17 % 4`  | `-1`          | ✗     |
| `17 % -4`  | `1`           | ✗     |

## Reproduction Code

```python
import ibis
import pandas as pd

# Test data with negative operands
test_cases = [
    (-10, 3),
    (10, -3),
    (-10, -3),
    (-17, 4),
    (17, -4),
]

df = pd.DataFrame(test_cases, columns=['dividend', 'divisor'])

print("=== Expected (Python) ===")
for dividend, divisor in test_cases:
    result = dividend % divisor
    print(f"{dividend:3d} % {divisor:3d} = {result:3d}")
# Output: 2, -2, -1, 3, -3

# Test SQLite
print("\n=== SQLite (Ibis) ===")
con_sqlite = ibis.sqlite.connect()
t_sqlite = con_sqlite.create_table('test', df)
result_sqlite = t_sqlite.select(
    (t_sqlite.dividend % t_sqlite.divisor).name('result')
).execute()['result'].tolist()
print(result_sqlite)
# Output: [-1, 1, -1, -1, 1]  ✗ WRONG!

# Test DuckDB
print("\n=== DuckDB (Ibis) ===")
con_duckdb = ibis.duckdb.connect()
t_duckdb = con_duckdb.create_table('test', df)
result_duckdb = t_duckdb.select(
    (t_duckdb.dividend % t_duckdb.divisor).name('result')
).execute()['result'].tolist()
print(result_duckdb)
# Output: [-1, 1, -1, -1, 1]  ✗ WRONG!

# Test Polars (for comparison)
print("\n=== Polars (Ibis) ===")
con_polars = ibis.polars.connect()
t_polars = con_polars.create_table('test', df)
result_polars = t_polars.select(
    (t_polars.dividend % t_polars.divisor).name('result')
).execute()['result'].tolist()
print(result_polars)
# Output: [2, -2, -1, 3, -3]  ✓ CORRECT!
```

**Output:**
```
=== Expected (Python) ===
-10 %   3 =   2
 10 %  -3 =  -2
-10 %  -3 =  -1
-17 %   4 =   3
 17 %  -4 =  -3

=== SQLite (Ibis) ===
[-1, 1, -1, -1, 1]

=== DuckDB (Ibis) ===
[-1, 1, -1, -1, 1]

=== Polars (Ibis) ===
[2, -2, -1, 3, -3]
```

## Root Cause

### SQLite
SQLite's `%` operator and `MOD()` function both implement remainder:
```sql
SELECT -10 % 3;    -- Returns -1 (remainder)
SELECT MOD(-10, 3); -- Returns -1 (remainder)
```

### DuckDB
DuckDB's `%` operator also implements remainder:
```sql
SELECT -10 % 3;    -- Returns -1 (remainder)
```

## Suggested Fix

Ibis should rewrite modulo operations for backends that don't support Python-style modulo:

### For SQLite
```sql
-- Current (broken):
SELECT dividend % divisor FROM test

-- Should generate:
SELECT ((dividend % divisor) + divisor) % divisor FROM test
```

### For DuckDB
Same transformation as SQLite.

### Verification
This formula converts remainder to modulo:
- For positive results: `((result + divisor) % divisor) = result` (unchanged)
- For negative results: Shifts by divisor to match Python semantics

**Example:**
- `-10 % 3` in SQLite returns `-1` (remainder)
- `((-1 + 3) % 3) = (2 % 3) = 2` ✓ (correct modulo)

## Impact

- **HIGH**: Breaks cross-backend compatibility for negative operands
- **MEDIUM-HIGH**: Mathematical operations involving negative numbers produce wrong results
- **HIGH**: Violates Python semantics and user expectations
- **MEDIUM**: Silent errors (no exceptions raised)

### Use Cases Affected

Common patterns that fail with negative values:

```python
# Circular indexing (wrapping negative indices)
index % array_length

# Periodic time calculations (time zones, UTC offsets)
hours_offset % 24

# Hash distribution
hash_value % bucket_count

# Modular arithmetic in algorithms
(a - b) % modulus
```

## Examples of Silent Failures

```python
# Example 1: Circular buffer indexing
buffer_size = 10
negative_index = -3
wrapped_index = negative_index % buffer_size
# Python/Polars: 7 (correct - wraps to end of buffer)
# SQLite/DuckDB: -3 (wrong - causes IndexError)

# Example 2: Time zone offset
utc_offset_hours = -5  # EST
local_hour = utc_offset_hours % 24
# Python/Polars: 19 (correct - 7 PM)
# SQLite/DuckDB: -5 (wrong - invalid hour)

# Example 3: Hash table distribution
hash_code = -12345
bucket = hash_code % 100
# Python/Polars: 55 (correct bucket)
# SQLite/DuckDB: -45 (wrong - negative bucket index)
```

## Environment

- Ibis version: 10.4.0
- Affected backends: SQLite, DuckDB
- Correct backends: Polars
- Python version: 3.12.9

## Historical Note

Unlike the division issue which was addressed in PR #692 (2015), the modulo/remainder semantic difference has **never been reported** to Ibis. This appears to be a completely unknown issue affecting multiple backends.

## Related Issues

- #671 - Division issue (addressed in 2015)
- #692 - PR for division fix (modulo was not included)
- This issue affects both SQLite AND DuckDB (not SQLite-specific)
