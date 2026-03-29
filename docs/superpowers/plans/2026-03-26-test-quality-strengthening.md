# Test Quality Strengthening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the testing philosophy principle, add a parameter sensitivity helper, and audit/fix all parameterized operations so that silent parameter-dropping bugs cannot hide behind weak assertions.

**Architecture:** Four deliverables executed sequentially — (1) amend the testing principle, (2) add the conftest helper, (3) write new parameter sensitivity tests, (4) fix the existing non-discriminating rounding test. Each deliverable is committed independently.

**Tech Stack:** Python, pytest, mountainash_expressions cross-backend test fixtures (`backend_factory`, `select_and_extract`, `get_result_count`).

**Spec:** `docs/superpowers/specs/2026-03-26-test-quality-strengthening-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/g.development-practices/testing-philosophy.md` | Add discriminating data, filter-count vs value-extract, and parameter coverage sections |
| Modify | `tests/conftest.py` | Add `assert_parameter_sensitivity` fixture |
| Create | `tests/cross_backend/test_parameter_sensitivity.py` | New value-correctness + sensitivity tests for all parameterized operations |
| Modify | `tests/cross_backend/test_compose_cross_namespace.py` | Fix non-discriminating `round(2)` test |

---

### Task 1: Amend testing-philosophy.md

**Files:**
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/g.development-practices/testing-philosophy.md`

- [ ] **Step 1: Add Discriminating Test Data section**

Insert after the "Handling Known Backend Differences" section (after line 88), before "Anti-Patterns":

```markdown
### Discriminating Test Data

Test data must be chosen so that if a parameter were wrong, ignored, or defaulted, the assertion would fail. When writing a test for a parameterized operation, ask: **"Would this test still pass if the parameter were silently dropped?"**

```python
# BAD: round(2) vs round(0) produces the same filter result
data = {"price": [90.0, 95.0, 100.0, 50.0]}
expr = ma.col("price").multiply(ma.lit(1.07)).round(2).gt(ma.lit(100.0))
assert count == 2  # Passes with round(0) too — the bug is invisible

# GOOD: value extraction with data that distinguishes round(2) from round(0)
data = {"val": [1.555, 2.345, 3.789]}
expr = ma.col("val").round(2)
actual = select_and_extract(df, expr.compile(df), "result", backend_name)
assert actual == [1.56, 2.35, 3.79]  # Fails if round(0) → [2, 2, 4]
```

### Filter-Count vs Value-Extract Assertions

Filter-count assertions (`get_result_count`) are appropriate when the operation under test IS a boolean/filter (eq, gt, contains, is_null). When the operation transforms data (arithmetic, string manipulation, rounding, datetime arithmetic), use `select_and_extract` to verify actual output values.

Filter-count is still allowed for transformation operations only if the test data is **discriminating** -- a different parameter value would produce a different count.

### Parameter Coverage

Every argument that flows through `node.arguments` (visited by the unified visitor) must have at least one cross-backend test that:

1. Uses a non-default parameter value.
2. Verifies the output value (not just compilation success or filter count).
3. Would fail if the parameter were silently dropped or defaulted.

Use `assert_parameter_sensitivity` (see `tests/conftest.py`) to mechanically verify that changing a parameter value changes the output.
```

- [ ] **Step 2: Add the new anti-pattern entry**

Add to the existing Anti-Patterns list (after line 107):

```markdown
- **Testing an operation without exercising its parameters.** If an operation accepts a parameter (e.g., `round(decimals)`, `trim(chars)`, `log(base)`), the test must use a non-default parameter value and verify the output changes. A test that only exercises the default is not testing the parameter path.
```

- [ ] **Step 3: Update Technical Reference**

Update the Technical Reference section to mention the new test file (after line 115):

```markdown
- `tests/cross_backend/test_parameter_sensitivity.py` -- Parameter sensitivity and value correctness tests
```

- [ ] **Step 4: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/g.development-practices/testing-philosophy.md
git commit -m "principle: add discriminating data, parameter coverage, and filter-count rules to testing philosophy"
```

---

### Task 2: Add `assert_parameter_sensitivity` helper to conftest.py

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add the helper function and fixture**

Add after the `select_and_extract` fixture (after line 428 in conftest.py):

```python
@pytest.fixture
def assert_parameter_sensitivity(select_and_extract) -> Callable:
    """
    Assert that different parameter values produce different results.

    Proves an operation's parameter actually reaches the backend by showing
    that two different parameter values produce two different outputs.

    Usage:
        assert_parameter_sensitivity(
            df, lambda d: ma.col("val").round(d), 1, 2, backend_name
        )
    """
    def _assert_parameter_sensitivity(
        df: Any,
        build_expr: Callable,
        param_a: Any,
        param_b: Any,
        backend_name: str,
    ) -> None:
        expr_a = build_expr(param_a)
        expr_b = build_expr(param_b)
        result_a = select_and_extract(df, expr_a.compile(df), "result", backend_name)
        result_b = select_and_extract(df, expr_b.compile(df), "result", backend_name)
        assert result_a != result_b, (
            f"[{backend_name}] param_a={param_a} and param_b={param_b} produced "
            f"identical results {result_a} — parameter may be silently ignored"
        )

    return _assert_parameter_sensitivity
```

- [ ] **Step 2: Run existing tests to verify no regressions**

Run: `hatch run test:test-quick 2>&1 | tail -5`
Expected: All existing tests pass (2501 passed).

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add assert_parameter_sensitivity fixture to conftest"
```

---

### Task 3: Create test_parameter_sensitivity.py — rounding, logarithmic, string trim

**Files:**
- Create: `tests/cross_backend/test_parameter_sensitivity.py`

- [ ] **Step 1: Write the test file with rounding tests**

```python
"""Cross-backend parameter sensitivity tests.

Verifies that operation parameters actually reach the backend and affect output.
Each test uses discriminating data: if the parameter were silently dropped or
defaulted, the assertion would fail.

See: g.development-practices/testing-philosophy.md § Discriminating Test Data
"""

import math
import pytest
from datetime import datetime

import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_IBIS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals limited")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

TEMPORAL_BACKENDS = [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Rounding — round(decimals) must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRoundParameterSensitivity:
    """round(decimals) must produce different results for different decimals."""

    def test_round_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """round(2) produces correct 2-decimal values."""
        data = {"val": [1.555, 2.345, 3.789]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").round(2)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # 1.555 → 1.56 (or 1.55 with banker's rounding — both differ from round(0)=2)
        # Key: none of these should be whole numbers
        for val in actual:
            assert val != int(val), (
                f"[{backend_name}] round(2) produced whole number {val} — "
                f"parameter may be silently ignored (defaulting to round(0))"
            )

    def test_round_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """round(1) and round(2) must produce different results."""
        data = {"val": [1.555, 2.345, 3.789]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda d: ma.col("val").round(d),
            1, 2,
            backend_name,
        )


# =============================================================================
# Logarithmic — log(base) must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLogParameterSensitivity:
    """log(base) must use the base parameter."""

    def test_log_base10_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """log(10) of powers of 10 produces exact integers."""
        data = {"val": [10.0, 100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").log(10)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        for got, expected in zip(actual, [1.0, 2.0, 3.0]):
            assert math.isclose(got, expected, abs_tol=1e-9), (
                f"[{backend_name}] log(10) of {10 ** int(expected)} = {got}, expected {expected}"
            )

    def test_log_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """log(2) and log(10) must produce different results."""
        data = {"val": [100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda b: ma.col("val").log(b),
            2, 10,
            backend_name,
        )


# =============================================================================
# String trim — trim(chars) must use the characters parameter
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestTrimParameterSensitivity:
    """trim/ltrim/rtrim with custom characters must actually strip those chars."""

    def test_trim_custom_chars_value(self, backend_name, backend_factory, select_and_extract):
        """trim('x') strips x chars, not whitespace."""
        data = {"val": ["xxhelloxx", "xworldx"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.trim("x")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_ltrim_custom_chars_value(self, backend_name, backend_factory, select_and_extract):
        """ltrim('.') strips leading dots."""
        data = {"val": ["..hello", "...world"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.ltrim(".")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_rtrim_custom_chars_value(self, backend_name, backend_factory, select_and_extract):
        """rtrim('#') strips trailing hashes."""
        data = {"val": ["hello##", "world#"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.rtrim("#")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_trim_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """trim('x') and trim('.') must produce different results."""
        data = {"val": ["x.hello.x"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda c: ma.col("val").str.trim(c),
            "x", ".",
            backend_name,
        )


# =============================================================================
# String padding — lpad/rpad width must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestPadParameterSensitivity:
    """lpad/rpad width parameter must reach the backend."""

    def test_lpad_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """lpad(5) and lpad(8) must produce different results."""
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda w: ma.col("val").str.lpad(w, " "),
            5, 8,
            backend_name,
        )

    def test_rpad_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """rpad(5) and rpad(8) must produce different results."""
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda w: ma.col("val").str.rpad(w, " "),
            5, 8,
            backend_name,
        )


# =============================================================================
# String extraction — left/right count must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLeftRightParameterSensitivity:
    """left(n)/right(n) count parameter must reach the backend."""

    def test_left_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """left(2) and left(4) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda n: ma.col("val").str.left(n),
            2, 4,
            backend_name,
        )

    def test_right_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """right(2) and right(4) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda n: ma.col("val").str.right(n),
            2, 4,
            backend_name,
        )


# =============================================================================
# String repeat — repeat(n) count must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestRepeatParameterSensitivity:
    """repeat(n) count parameter must reach the backend."""

    def test_repeat_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """repeat(2) and repeat(3) must produce different results."""
        data = {"val": ["ab", "cd"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda n: ma.col("val").str.repeat(n),
            2, 3,
            backend_name,
        )


# =============================================================================
# Substring — start and length must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSubstringParameterSensitivity:
    """substring(start, length) parameters must reach the backend."""

    def test_substring_start_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """substring(0, 3) and substring(2, 3) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda s: ma.col("val").str.slice(s, 3),
            0, 2,
            backend_name,
        )

    def test_substring_length_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """substring(0, 2) and substring(0, 4) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda l: ma.col("val").str.slice(0, l),
            2, 4,
            backend_name,
        )


# =============================================================================
# Datetime arithmetic — duration must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDatetimeParameterSensitivity:
    """add_days/add_hours duration must reach the backend."""

    def test_add_days_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """add_days(1) and add_days(5) must produce different results."""
        data = {"ts": [datetime(2024, 1, 15, 10, 0, 0)]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda d: ma.col("ts").dt.add_days(d),
            1, 5,
            backend_name,
        )

    def test_add_hours_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """add_hours(1) and add_hours(12) must produce different results."""
        data = {"ts": [datetime(2024, 1, 15, 10, 0, 0)]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda h: ma.col("ts").dt.add_hours(h),
            1, 12,
            backend_name,
        )


# =============================================================================
# Center — width and char must affect output (Polars only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals limited")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis no center")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis no center")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="ibis no center")),
])
class TestCenterParameterSensitivity:
    """center(width, char) parameters must reach the backend."""

    def test_center_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """center(7, '*') pads both sides."""
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.center(7, "*")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # "hi" centered in 7 with '*' → "**hi***" or "***hi**" (implementation may vary)
        assert all(len(s) == 7 for s in actual), f"[{backend_name}] widths: {[len(s) for s in actual]}"
        assert all("*" in s for s in actual), f"[{backend_name}] no padding chars: {actual}"

    def test_center_width_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """center(5) and center(9) must produce different results."""
        data = {"val": ["hi"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda w: ma.col("val").str.center(w, "*"),
            5, 9,
            backend_name,
        )


# =============================================================================
# Replace slice — start, length, replacement must affect output (Polars only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals limited")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis no replace_slice")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis no replace_slice")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="ibis no replace_slice")),
])
class TestReplaceSliceParameterSensitivity:
    """replace_slice(start, length, replacement) parameters must reach backend."""

    def test_replace_slice_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """replace_slice(1, 3, 'XY') replaces characters 1-3."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.replace_slice(1, 3, "XY")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # "hello" → replace chars at pos 1 for length 3 → "XYlo" (0-indexed: h[ell]o → hXYo)
        # Exact result depends on 0-indexed vs 1-indexed convention
        # Key assertion: the result is NOT "hello" (parameter was used)
        assert actual[0] != "hello", f"[{backend_name}] replace_slice had no effect: {actual}"
        assert "XY" in actual[0], f"[{backend_name}] replacement not found in: {actual}"

    def test_replace_slice_length_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """replace_slice with length 1 and length 3 must differ."""
        data = {"val": ["hello"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda l: ma.col("val").str.replace_slice(1, l, "X"),
            1, 3,
            backend_name,
        )
```

- [ ] **Step 2: Run the new tests**

Run: `hatch run test:test-target tests/cross_backend/test_parameter_sensitivity.py -v 2>&1 | tail -40`
Expected: Tests pass for supported backends, xfail for known limitations.

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_parameter_sensitivity.py
git commit -m "test: add parameter sensitivity tests for all parameterized operations"
```

---

### Task 4: Fix existing non-discriminating rounding test

**Files:**
- Modify: `tests/cross_backend/test_compose_cross_namespace.py:108-121`

- [ ] **Step 1: Read the existing test to get exact context**

Run: Read `tests/cross_backend/test_compose_cross_namespace.py` lines 108-121.

- [ ] **Step 2: Update the test with discriminating data**

Replace the test body with data where `round(2)` and `round(0)` produce different filter outcomes:

```python
    def test_arithmetic_rounding_comparison(self, backend_name, backend_factory, get_result_count):
        """Arithmetic + rounding + comparison: (price * 1.07).round(2) > 100."""
        # Data chosen so round(2) and round(0) produce DIFFERENT filter counts:
        # 93.46 * 1.07 = 100.0022 → round(2) = 100.00 → NOT > 100 → excluded
        #                          → round(0) = 100    → NOT > 100 → excluded (same)
        # Use values where rounding precision changes the > threshold:
        # 93.45 * 1.07 = 99.9915 → round(2) = 99.99 → no
        #                         → round(0) = 100   → no
        # Better: use data where round(2) keeps it above, round(0) pushes it below
        data = {"price": [93.5, 95.0, 100.0, 50.0]}
        df = backend_factory.create(data, backend_name)

        # 93.5 * 1.07 = 100.045 → round(2) = 100.05 → yes (> 100)
        #                        → round(0) = 100    → no  (not > 100)
        # 95 * 1.07 = 101.65 → round(2) = 101.65 → yes
        #                     → round(0) = 102    → yes
        # 100 * 1.07 = 107.00 → yes either way
        # 50 * 1.07 = 53.50 → no either way
        expr = ma.col("price").multiply(ma.lit(1.07)).round(2).gt(ma.lit(100.0))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # With round(2): 100.05, 101.65, 107.00, 53.50 → 3 above 100
        # With round(0): 100, 102, 107, 54 → 2 above 100 (100 is NOT > 100)
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"
```

- [ ] **Step 3: Run the updated test**

Run: `hatch run test:test-target tests/cross_backend/test_compose_cross_namespace.py::TestComposeCrossNamespace::test_arithmetic_rounding_comparison -v`
Expected: PASS for all backends.

- [ ] **Step 4: Run full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -5`
Expected: All tests pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add tests/cross_backend/test_compose_cross_namespace.py
git commit -m "test: fix non-discriminating round(2) test — data now distinguishes round(2) from round(0)"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Deliverable 1 (amend testing-philosophy.md) → Task 1
- ✅ Deliverable 2 (assert_parameter_sensitivity helper) → Task 2
- ✅ Deliverable 3 (test_parameter_sensitivity.py) → Task 3
- ✅ Deliverable 4 (fix existing rounding test) → Task 4
- ✅ All operations from "no value test" table covered: round, log, center, replace_slice, trim, ltrim, rtrim
- ✅ All operations from "need sensitivity" table covered: lpad, rpad, left, right, repeat, substring, add_days, add_hours

**Placeholder scan:** No TBDs, TODOs, or "similar to Task N" references. All code blocks complete.

**Type consistency:** `assert_parameter_sensitivity` fixture signature matches between Task 2 (definition) and Task 3 (usage) — takes `(df, build_expr, param_a, param_b, backend_name)`.
