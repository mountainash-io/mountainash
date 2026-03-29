# Ibis Polars Backend - Calendar Intervals Bug

This directory contains documentation and reproduction scripts for an Ibis bug affecting the Polars backend.

## Files

- **`issue.md`** - Complete bug report ready to file on Ibis GitHub
- **`reproduction_test.py`** - Standalone script demonstrating the bug
- **`README.md`** - This file

## Quick Summary

**Problem:** Ibis Polars backend cannot add/subtract months or years to timestamps.

**Root Cause:** The compiler uses `pl.duration()` which doesn't support calendar-based intervals (months/years). Polars requires `Expr.dt.offset_by()` for calendar intervals.

**Impact:**
- ❌ `ibis.interval(months=3)` fails with Polars backend
- ❌ `ibis.interval(years=1)` fails with Polars backend
- ✅ `ibis.interval(days=30)` works (fixed duration)
- ✅ Other backends (DuckDB, SQLite) work fine with months/years

## Running the Reproduction

```bash
# From this directory
python reproduction_test.py
```

Expected output:
- ✅ Native Polars with offset_by() - SUCCESS
- ❌ Ibis Polars with months - FAILED
- ❌ Ibis Polars with years - FAILED
- ✅ Ibis Polars with days - SUCCESS
- ✅ Ibis DuckDB with months - SUCCESS

## Our Workaround

In our test suite (`tests/cross_backend/test_temporal_advanced.py`), we use `pytest.xfail()` to document this limitation:

```python
if backend_name == "ibis-polars":
    pytest.xfail(
        "Ibis Polars backend doesn't support calendar-based intervals (months/years). "
        "Only duration-based intervals (days/hours/minutes/seconds) are supported."
    )
```

## Status

- **Discovered:** 2025-01-09
- **Issue filed:** [Pending - add link when created]
- **Workaround:** Document with xfail, use native Polars or different Ibis backend

## Related Code

- Ibis compiler: `ibis/backends/polars/compiler.py::_make_duration()` (line 80-82)
- Our backend: `src/mountainash_expressions/backends/ibis/expression_system/ibis_expression_system.py`
- Our tests: `tests/cross_backend/test_temporal_advanced.py::TestFlexibleOffsetBy::test_offset_subtract_months`

## Technical Details

See `issue.md` for:
- Complete root cause analysis
- Proposed solutions
- Polars API documentation references
- Full technical context
