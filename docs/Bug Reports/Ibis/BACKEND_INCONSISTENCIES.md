# Backend Inconsistencies and Known Issues

This document tracks known inconsistencies between different DataFrame backends when using mountainash-expressions. These are areas where the library should either normalize behavior or explicitly warn users.

## Critical: Arithmetic Operation Inconsistencies

### 1. SQLite Integer Division vs Float Division

**Status:** ⚠️ **KNOWN ISSUE - NEEDS NORMALIZATION**

**Affected Backend:** `ibis-sqlite`

**Issue:**
SQLite performs integer division when both operands are integers, while other backends (Polars, Pandas, Narwhals, Ibis-Polars, Ibis-DuckDB) perform float division.

**Example:**
```python
# Expected behavior (Polars, Pandas, Narwhals, Ibis-Polars, Ibis-DuckDB)
20 / 3 = 6.666666...

# SQLite behavior
20 / 3 = 6  # Integer division!
```

**Impact:**
- **HIGH** - Users get different numeric results depending on backend
- Breaks cross-backend compatibility guarantees
- Silent data errors in calculations

**Test Case:**
`tests/cross_backend/test_arithmetic.py::TestArithmeticEdgeCases::test_complex_chained_operations[ibis-sqlite]`

**Recommended Solutions (Priority Order):**
1. **Normalize in library (RECOMMENDED):** Cast operands to float before division for SQLite backend
2. **Add explicit operators:** Provide `int_divide()` and `float_divide()` methods
3. **Warning system:** Warn users when using division with SQLite backend
4. **Document limitation:** Add prominent warning in documentation

**Related:**
- SQLite documentation: https://www.sqlite.org/lang_expr.html#operators
- Upstream issue: [To be filed with Ibis]

---

### 2. SQLite Modulo Semantics (Remainder vs Modulus)

**Status:** ⚠️ **KNOWN ISSUE - NEEDS NORMALIZATION**

**Affected Backend:** `ibis-sqlite`

**Issue:**
SQLite implements the remainder operation (result has sign of dividend), while Python/Polars/Pandas implement modulo operation (result has sign of divisor).

**Example:**
```python
# Expected behavior (Python/Polars/Pandas/Narwhals)
-10 % 3 = 2   # Result has sign of divisor (3)
10 % -3 = -2  # Result has sign of divisor (-3)

# SQLite behavior
-10 % 3 = -1  # Result has sign of dividend (-10) - REMAINDER operation
10 % -3 = 1   # Result has sign of dividend (10) - REMAINDER operation
```

**Impact:**
- **HIGH** - Different results for negative operands
- Breaks mathematical expectations from Python users
- Silent data errors in calculations involving negative numbers

**Test Case:**
`tests/cross_backend/test_arithmetic.py::TestArithmeticEdgeCases::test_modulo_with_negatives[ibis-sqlite]`

**Background:**
The modulo operation has two common implementations:
- **Modulo (Python, Polars):** Result takes sign of divisor
- **Remainder (SQLite, C):** Result takes sign of dividend

See: https://en.wikipedia.org/wiki/Modulo_operation

**Recommended Solutions (Priority Order):**
1. **Normalize in library (RECOMMENDED):** Implement Python-style modulo for SQLite using: `((a % b) + b) % b`
2. **Add explicit operators:** Provide both `modulo()` and `remainder()` methods
3. **Warning system:** Warn users when using modulo with negative numbers on SQLite
4. **Document limitation:** Add prominent warning in documentation

**Related:**
- Upstream issue: [To be filed with Ibis]

---

## Critical: Ibis DuckDB Backend Completely Broken

**Status:** 🚨 **BLOCKING - EXTERNAL DEPENDENCY ISSUE**

**Affected Backend:** `ibis-duckdb`

**Issue:**
DuckDB backend is completely non-functional due to a dependency incompatibility. All ~100+ tests for this backend are failing.

**Error:**
```
AttributeError: module 'duckdb' has no attribute 'functional'
```

**Impact:**
- **CRITICAL** - Entire backend is unusable
- Blocks ~100+ tests from running
- Users cannot use DuckDB backend at all

**Test Marking:**
All `ibis-duckdb` tests are marked with `pytest.mark.xfail` to:
- Show the issue is visible and being tracked
- Allow test suite to pass while issue is unresolved
- Automatically pass when the issue is fixed (no code changes needed)

**Root Cause:**
Likely a version mismatch between:
- `duckdb` Python package version
- `ibis-framework` DuckDB backend requirements
- Our dependency constraints

**Recommended Solutions (Priority Order):**
1. **Update dependencies (IMMEDIATE):** Update `duckdb` and `ibis-framework` to compatible versions
2. **Pin compatible versions:** Document and pin working version combinations
3. **Add version checks:** Validate dependency versions at import time
4. **Report upstream:** File issue with Ibis if it's their bug

**Investigation Needed:**
```bash
# Check installed versions
pip list | grep -E "duckdb|ibis"

# Try to reproduce the error
python -c "import duckdb; print(duckdb.functional)"
python -c "import ibis; conn = ibis.duckdb.connect()"
```

**Related:**
- Upstream issue: [To be filed]
- All tests: Search for `backend_name == "ibis-duckdb"` in test files

---

## Resolved: Ibis Reverse Operator Bug

**Status:** ✅ **HANDLED - Tests expect and document the error**

**Affected Backends:** `ibis-polars`, `ibis-sqlite`, potentially other Ibis backends

**Issue:**
Reverse arithmetic operators with literals fail with `InputTypeError` in Ibis.

**Example:**
```python
# This works
ma.col("a") + 5

# This fails with InputTypeError
5 + ma.col("a")
```

**Handling:**
Tests now expect `InputTypeError` for reverse operators and reference the upstream issue.

**Related:**
- Upstream issue: https://github.com/ibis-project/ibis/issues/11742
- Affected tests: Multiple tests in `test_expression_builder_api.py`

---

## Testing Strategy for Backend Inconsistencies

### Expected Failures (pytest.xfail)

Tests that expose backend inconsistencies use `pytest.xfail()` to:
1. Document the specific issue
2. Prevent false positives (tests don't hide real failures)
3. Track when backend behavior changes
4. Make inconsistencies visible in test reports

**Example:**
```python
if backend_name == "ibis-sqlite":
    pytest.xfail(
        "SQLite performs integer division instead of float division. "
        "This creates cross-backend inconsistency. "
        "Needs normalization or documentation."
    )
```

### When to Use xfail vs Skip

- **Use `xfail`:** When we WANT the backend to pass but it currently doesn't (known bugs/inconsistencies)
- **Use `skip`:** When the backend genuinely doesn't support a feature

---

## Action Items

### Immediate (Critical Priority)
- [ ] **FIX DuckDB:** Resolve dependency incompatibility (BLOCKS ~100+ tests)
  - Investigate `duckdb` and `ibis-framework` version compatibility
  - Update to compatible versions or pin known-good versions
  - Verify all DuckDB tests pass
- [ ] **Normalize SQLite division:** Implement float division for SQLite backend
- [ ] **Normalize SQLite modulo:** Implement Python-style modulo for SQLite backend

### High Priority
- [ ] Add integration tests for normalized behavior
- [ ] Add runtime warnings when using affected operations
- [ ] File upstream issues with Ibis project for DuckDB dependency

### Medium Priority
- [ ] Add explicit `int_divide()` / `float_divide()` methods
- [ ] Add explicit `modulo()` / `remainder()` methods
- [ ] Update documentation with backend compatibility matrix
- [ ] Add dependency version validation at startup

### Long Term
- [ ] Comprehensive backend compatibility testing
- [ ] Automated detection of backend-specific behavior
- [ ] Runtime warnings for operations with inconsistent behavior
- [ ] CI/CD testing against multiple backend versions

---

## Backend Compatibility Philosophy

**Core Principle:** Users should get **identical results** regardless of backend choice, unless explicitly documented otherwise.

When backend inconsistencies are discovered:
1. **First choice:** Normalize in the library
2. **Second choice:** Provide explicit alternatives for different behaviors
3. **Last resort:** Document prominently and warn at runtime

**Never acceptable:** Silent backend-dependent behavior changes.
