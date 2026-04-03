# Test Quality Strengthening — Design Spec

> **Date:** 2026-03-26
> **Status:** Draft
> **Triggered by:** isinstance anti-pattern audit revealed silent parameter-dropping bugs (round defaulting to 0 decimals, trim ignoring custom characters) that existing tests did not catch

## Problem Statement

Three anti-patterns in the existing test suite allowed parameterized operation bugs to go undetected:

### Anti-pattern 1: Coincidental pass — non-discriminating test data

The `round(2)` test used values where `round(0)` produces the same downstream filter result. The test passed whether the parameter was used or not.

```python
# round(2) bug was invisible because the filter outcome is identical
data = {"price": [90.0, 95.0, 100.0, 50.0]}
expr = ma.col("price").multiply(ma.lit(1.07)).round(2).gt(ma.lit(100.0))
assert count == 2  # Passes with round(0) too — 96.3 and 53.5 stay below 100 either way
```

### Anti-pattern 2: Count-not-verify — filter-count assertions on transformation operations

`get_result_count` is appropriate for boolean/filter operations (where the answer IS a count), but when applied to transformations like rounding, it cannot detect parameter bugs.

- 238 tests use `get_result_count` (filter-count pattern)
- 587 tests use `select_and_extract` (value extraction pattern)
- Parameterized transformation operations were disproportionately in the filter-count group

### Anti-pattern 3: Untested parameters — operations with arguments that have no dedicated test

`trim(chars)`, `center(width, char)`, `replace_slice(start, len, repl)`, `log(base)` had zero cross-backend value tests. The operation existed, the protocol was satisfied, but nobody verified the parameter actually reached the backend.

### Root cause

The existing testing philosophy enforces cross-backend *consistency* ("same expression, same result across backends") but is silent on *parameter correctness* ("the parameter value actually affects the output").

## Design

### Deliverable 1: Amend testing-philosophy.md

Add three new sections and one new anti-pattern to the existing `g.development-practices/testing-philosophy.md` principle.

#### New section: Discriminating Test Data

**Rule:** Test data must be chosen so that if a parameter were wrong, ignored, or defaulted, the assertion would fail. When writing a test, ask: "Would this test still pass if the parameter were silently dropped?"

**Example (bad):**
```python
data = {"price": [90.0, 95.0, 100.0, 50.0]}
expr = ma.col("price").multiply(ma.lit(1.07)).round(2).gt(ma.lit(100.0))
assert count == 2  # Passes with round(0) too
```

**Example (good):**
```python
data = {"val": [1.555, 2.345, 3.789]}
expr = ma.col("val").round(2)
actual = select_and_extract(df, expr.compile(df), "result", backend_name)
assert actual == [1.56, 2.35, 3.79]  # Fails if round(0) → [2, 2, 4]
```

#### New section: Filter-Count vs Value-Extract

**Rule:** Filter-count assertions (`get_result_count`) are appropriate when the operation under test IS a boolean/filter (eq, gt, contains, is_null). When the operation transforms data (arithmetic, string manipulation, rounding, datetime arithmetic), use `select_and_extract` to verify actual output values.

Filter-count is still allowed for transformation operations *only if* the test data is discriminating — i.e., a different parameter value would produce a different count.

#### New section: Parameter Coverage

**Rule:** Every argument that flows through `node.arguments` (visited by the unified visitor) must have at least one cross-backend test that:

1. Uses a non-default parameter value
2. Verifies the output value (not just compilation success or filter count)
3. Would fail if the parameter were silently dropped or defaulted

#### New anti-pattern entry

"Testing an operation without exercising its parameters" — added to the existing Anti-Patterns list.

### Deliverable 2: `assert_parameter_sensitivity` helper

Add to `tests/conftest.py`:

```python
def assert_parameter_sensitivity(
    df, build_expr, param_a, param_b,
    backend_name, select_and_extract,
):
    """Assert that different parameter values produce different results.

    Proves an operation's parameter actually reaches the backend by showing
    that two different parameter values produce two different outputs.

    Args:
        df: Backend DataFrame.
        build_expr: Callable(param) -> ma expression.
        param_a: First parameter value.
        param_b: Second parameter value (must differ from param_a).
        backend_name: Backend identifier.
        select_and_extract: Fixture for value extraction.
    """
    expr_a = build_expr(param_a)
    expr_b = build_expr(param_b)
    result_a = select_and_extract(df, expr_a.compile(df), "result", backend_name)
    result_b = select_and_extract(df, expr_b.compile(df), "result", backend_name)
    assert result_a != result_b, (
        f"[{backend_name}] param_a={param_a} and param_b={param_b} produced "
        f"identical results {result_a} — parameter may be silently ignored"
    )
```

Exposed as a pytest fixture alongside the existing `select_and_extract`.

### Deliverable 3: New test file `tests/cross_backend/test_parameter_sensitivity.py`

Systematic parameter sensitivity and value correctness tests for all operations that have arguments flowing through `node.arguments`. Organized by category.

#### Operations needing new tests

**No value test at all — must create:**

| Operation | Parameters | Test approach |
|-----------|-----------|---------------|
| `round(decimals)` | decimals | Value extract: `[1.555, 2.345]` → round(1) vs round(2), verify exact values |
| `log(base)` | base | Value extract: `[100.0, 1000.0]` → log(10) = [2.0, 3.0] |
| `center(width, char)` | width, char | Value extract: `["hi"]` → center(6, "*") = `["**hi**"]` |
| `replace_slice(start, len, repl)` | start, length, replacement | Value extract: `["hello"]` → replace_slice(1, 3, "XY") |
| `trim(chars)` | characters | Value extract: `["xxhelloxx"]` → trim("x") = `["hello"]` |
| `ltrim(chars)` | characters | Value extract: `["..hello"]` → ltrim(".") = `["hello"]` |
| `rtrim(chars)` | characters | Value extract: `["hello##"]` → rtrim("#") = `["hello"]` |

**Have value tests but need parameter sensitivity assertion:**

| Operation | Parameters | Test approach |
|-----------|-----------|---------------|
| `lpad(width, char)` | width, fill char | Sensitivity: lpad(5) vs lpad(8) must differ |
| `rpad(width, char)` | width, fill char | Sensitivity: rpad(5) vs rpad(8) must differ |
| `left(n)` | count | Sensitivity: left(2) vs left(4) must differ |
| `right(n)` | count | Sensitivity: right(2) vs right(4) must differ |
| `repeat(n)` | count | Sensitivity: repeat(2) vs repeat(3) must differ |
| `substring(start, length)` | start, length | Value extract with discriminating data |
| `add_days(n)` / `add_hours(n)` etc. | duration | Sensitivity: add_days(1) vs add_days(5) must differ |

**Already adequately tested (no action needed):**

| Operation | Why adequate |
|-----------|-------------|
| `contains(pattern)` | Pattern IS the operation — can't be ignored |
| `starts_with(prefix)` / `ends_with(suffix)` | Pattern is essential to output |
| `replace(old, new)` | Both params verified by output |
| `cast(dtype)` | Type is verified by output |
| `eq/ne/gt/lt/ge/le(other)` | Comparison value is the whole point |

### Deliverable 4: Fix existing non-discriminating test

In `tests/cross_backend/test_compose_cross_namespace.py`, the `test_arithmetic_rounding_comparison` test (line ~108) must be updated with discriminating test data where `round(2)` and `round(0)` produce different filter outcomes, OR supplemented with a value-extraction assertion.

## Backend coverage per test

All new tests use `ALL_BACKENDS` parametrization with `xfail` for known backend limitations, consistent with the existing testing philosophy.

## Out of scope

- Property-based testing (Hypothesis) — mentioned in testing-philosophy.md future considerations but not part of this spec
- Refactoring existing passing tests that already use value extraction — if they work, don't touch them
- Adding tests for operations that have no parameters (unary operations like `upper()`, `lower()`, `not_()`)
