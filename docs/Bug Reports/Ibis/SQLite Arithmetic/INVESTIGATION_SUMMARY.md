# Investigation Summary: SQLite Arithmetic Issues

## What I Found

Your `BACKEND_INCONSISTENCIES.md` documented two issues with SQLite arithmetic in Ibis. I investigated whether these are known issues and discovered some surprising findings:

### Issue 1: Division ❗ **NEW BUG DISCOVERED**

**Your documentation said:** SQLite performs integer division instead of float division.

**What I found:**
- ✅ SQL generation is CORRECT - Ibis properly casts to `CAST(a AS REAL)`
- ✅ SQLite returns CORRECT values - Raw SQL works fine
- ❌ **Result conversion loses precision** - `.execute()` rounds floats to integers!

**Example:**
- SQL returns: `223.33333...` ✓
- Ibis `.execute()` returns: `224.0` ✗

**This is a NEW bug** - not the division bug from 2015 (which was fixed). This is a result fetching/conversion bug in Ibis's SQLite backend.

### Issue 2: Modulo ✓ **Confirmed, Never Reported**

**Your documentation said:** SQLite uses remainder (sign of dividend) instead of modulo (sign of divisor).

**What I found:**
- ✓ Confirmed - SQLite uses remainder semantics
- ❗ **DuckDB ALSO has this problem** - Uses remainder, not modulo
- ✓ Polars is correct - Uses Python modulo semantics
- ❌ **Never been reported to Ibis** - Completely unknown issue

## Files Created

I've created two complete, working Ibis issue reports:

### 1. `ibis_issue_result_precision_loss.md`
**Title:** bug: SQLite backend loses float precision in complex expressions (result conversion bug)

**Key points:**
- SQL generation is correct
- Raw SQL returns correct values
- `.execute()` loses precision
- Critical data corruption issue

**Reproduction:** ✓ Tested and working

### 2. `ibis_issue_modulo_remainder_semantics.md`
**Title:** bug: SQLite and DuckDB backends use remainder instead of Python modulo semantics

**Key points:**
- Affects SQLite AND DuckDB (not just SQLite!)
- Polars is correct
- Only affects negative operands
- Never been reported before

**Reproduction:** ✓ Tested and working

## Test Files Created

In `docs/Bug Reports/Ibis/SQLite Arithmetic/`:

1. **`test_division_repro.py`** - Initial test (found division works in simple cases)
2. **`test_division_repro_v2.py`** - Tests with actual SQLite INTEGER columns
3. **`test_modulo_repro.py`** - Confirms modulo issue
4. **`test_modulo_all_backends.py`** - Tests modulo across all backends (found DuckDB also broken!)
5. **`test_actual_behavior.py`** - Comprehensive test showing both issues
6. **`debug_division.py`** - Deep dive into division behavior
7. **`test_raw_sql.py`** - Tests raw SQLite SQL (works correctly!)
8. **`test_ibis_fetch.py`** - **Found the smoking gun** - raw cursor vs `.execute()`
9. **`test_precision_loss_all_backends.py`** - **Confirms precision loss is SQLite-only**

## Key Discoveries

### Division Issue is NOT What We Thought
- PR #692 (2015) DID fix SQL generation
- SQL works correctly
- **NEW bug**: Result conversion loses precision
- **Critical severity**: Silent data corruption

### Modulo Issue is Bigger Than Expected
- Not just SQLite - **DuckDB also affected**
- Polars is the only correct backend we tested
- Never been reported to Ibis
- Needs backend-specific rewrites: `((a % b) + b) % b`

## Exa Research Findings

From my Exa searches:

### Division:
- ✅ Found historical issue #671 and PR #692
- ✅ Confirmed it was "fixed" in 2015
- ✅ But fix was for SQL generation, not result conversion
- ❌ No reports of precision loss in result fetching

### Modulo:
- ❌ Found NO Ibis issues about modulo/remainder semantics
- ❌ Found NO PRs addressing this
- ✅ Found general modulo documentation showing Python uses modulo, C uses remainder
- ✅ SQLite documentation confirms it uses remainder

## Recommendations

### For Filing Issues:

1. **File Issue #1: Result Precision Loss**
   - Use `ibis_issue_result_precision_loss.md`
   - This is a **critical** bug (silent data corruption)
   - Reference that SQL generation was fixed in #671/#692
   - Emphasize this is a **different** bug in result conversion

2. **File Issue #2: Modulo Semantics**
   - Use `ibis_issue_modulo_remainder_semantics.md`
   - Note it affects **multiple backends** (SQLite + DuckDB)
   - Provide the fix formula: `((a % b) + b) % b`
   - Mention Polars backend does it correctly

### For Your Library:

Since Ibis hasn't fixed these (and one is a new discovery), you should implement workarounds in `mountainash-expressions`:

#### Division Workaround:
```python
# For SQLite backend, use raw SQL execution
if backend == 'ibis-sqlite':
    sql = ibis.to_sql(expression, dialect='sqlite')
    cursor = connection.con.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    # Convert to your expected format
```

#### Modulo Workaround:
```python
# For SQLite and DuckDB backends, rewrite modulo
if backend in ['ibis-sqlite', 'ibis-duckdb']:
    # Transform: a % b
    # Into: ((a % b) + b) % b
    modulo_expr = ((dividend % divisor) + divisor) % divisor
```

## Test Results Summary

| Test | SQLite | DuckDB | Polars |
|------|--------|--------|--------|
| **Division (simple)** | ✓ | ✓ | ✓ |
| **Division (complex)** | ✗ Precision loss | ✓ | ✓ |
| **Modulo (positive)** | ✓ | ✓ | ✓ |
| **Modulo (negative)** | ✗ Remainder | ✗ Remainder | ✓ Modulo |

### Important: Precision Loss is SQLite-Only

Cross-backend testing confirms:
- **SQLite**: Returns `[55.0, 224.0, 503.0]` - ✗ Wrong (precision loss)
- **DuckDB**: Returns `[55.0, 223.333..., 502.5]` - ✓ Correct
- **Polars**: Returns `[55.0, 223.333..., 502.5]` - ✓ Correct

This proves the precision loss bug is **specific to SQLite backend's result conversion**, not a general Ibis issue.

## Next Steps

1. ✅ Review the two issue markdown files
2. ⬜ Submit to https://github.com/ibis-project/ibis/issues
3. ⬜ Cross-reference the issues after both are filed
4. ⬜ Implement workarounds in mountainash-expressions
5. ⬜ Update your `BACKEND_INCONSISTENCIES.md` with new findings
6. ⬜ Update your tests if they were based on wrong assumptions

## Questions?

- Do you want me to help implement the workarounds in your library?
- Should I update your `BACKEND_INCONSISTENCIES.md` with the new findings?
- Need help with anything else related to filing these issues?
