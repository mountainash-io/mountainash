# Relation-Based Test Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ad-hoc test extraction fixtures with relation-based extraction that mirrors real-world usage and correctly handles nulls.

**Architecture:** New `collect_expr` and `collect_col` fixtures use `ma.relation(df).select(expr).to_dict()` to extract results through the egress layer (Polars as hub). Existing `select_and_extract` is retained only for booleanizer tests. Migration proceeds one file at a time.

**Tech Stack:** pytest fixtures, mountainash relations API, mountainash expressions API

**Spec:** `docs/superpowers/specs/2026-04-02-relation-based-test-extraction-design.md`

---

### Task 1: Add `collect_expr` and `collect_col` Fixtures, Update `assert_parameter_sensitivity`

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add `collect_expr` fixture**

Add after the `select_and_extract` fixture (after line 432):

```python
@pytest.fixture
def collect_expr():
    """Extract expression results via the relation API.

    Mirrors real-world usage: wraps the DataFrame in a relation, projects
    the expression, and extracts via .to_dict() (which routes through
    Polars for null-safe extraction).

    Usage:
        actual = collect_expr(df, expr)
        actual = collect_expr(df, expr, alias="custom_name")
    """
    def _collect(df, expr, alias="result"):
        import mountainash as ma
        return ma.relation(df).select(expr.name.alias(alias)).to_dict()[alias]
    return _collect
```

- [ ] **Step 2: Add `collect_col` fixture**

Add after `collect_expr`:

```python
@pytest.fixture
def collect_col():
    """Extract column values via the relation API.

    Usage:
        values = collect_col(df, "age")
    """
    def _collect(df, column):
        import mountainash as ma
        return ma.relation(df).select(column).to_dict()[column]
    return _collect
```

- [ ] **Step 3: Update `assert_parameter_sensitivity` to use `collect_expr`**

Replace lines 436-464 in `tests/conftest.py`:

```python
@pytest.fixture
def assert_parameter_sensitivity(collect_expr) -> Callable:
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
        result_a = collect_expr(df, expr_a)
        result_b = collect_expr(df, expr_b)
        assert result_a != result_b, (
            f"[{backend_name}] param_a={param_a} and param_b={param_b} produced "
            f"identical results {result_a} — parameter may be silently ignored"
        )

    return _assert_parameter_sensitivity
```

- [ ] **Step 4: Update `select_and_extract` docstring**

Update the docstring of the `select_and_extract` fixture to mark it as booleanizer-only:

```python
@pytest.fixture
def select_and_extract() -> Callable:
    """
    Extract compiled expression results — for booleanizer/internal tests only.

    Most tests should use `collect_expr` instead. This fixture exists only for
    tests that need to pass explicit booleanizer parameters to .compile(),
    which the relation API does not support.

    Usage:
        backend_expr = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, backend_expr, "result", backend_name)
    """
```

- [ ] **Step 5: Verify existing tests still pass**

Run: `hatch run test:test-target-quick tests/cross_backend/test_parameter_sensitivity.py -v`
Expected: All tests pass (assert_parameter_sensitivity now uses collect_expr internally)

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py
git commit -m "feat: add collect_expr and collect_col fixtures for relation-based test extraction"
```

---

### Task 2: Migrate `test_arithmetic.py`

This is the first file migration and establishes the pattern for all subsequent tasks.

**Files:**
- Modify: `tests/cross_backend/test_arithmetic.py`

- [ ] **Step 1: Understand the current file**

Read `tests/cross_backend/test_arithmetic.py`. Every test method follows this pattern:

```python
def test_addition(self, backend_name, backend_factory, select_and_extract):
    data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("a").add(ma.col("b"))
    backend_expr = expr.compile(df)
    actual = select_and_extract(df, backend_expr, "result", backend_name)
    assert actual == expected, f"[{backend_name}] ..."
```

- [ ] **Step 2: Apply the migration pattern to every test method**

For each test method:

1. Replace `select_and_extract` with `collect_expr` in the method signature
2. Remove the `backend_expr = expr.compile(df)` line
3. Replace `select_and_extract(df, backend_expr, "result", backend_name)` with `collect_expr(df, expr)`

The result for each test looks like:

```python
def test_addition(self, backend_name, backend_factory, collect_expr):
    data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("a").add(ma.col("b"))
    actual = collect_expr(df, expr)
    assert actual == expected, f"[{backend_name}] ..."
```

Keep `backend_name` in the signature — it's still needed for `backend_factory.create()` and assertion messages.

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_arithmetic.py -v`
Expected: All tests pass across all 6 backends

- [ ] **Step 4: Commit**

```bash
git add tests/cross_backend/test_arithmetic.py
git commit -m "refactor: migrate test_arithmetic.py to relation-based extraction"
```

---

### Task 3: Migrate Arithmetic and Numeric Test Files

Apply the same migration pattern from Task 2 to these files. Each file follows the identical `select_and_extract` → `collect_expr` transformation.

**Files:**
- Modify: `tests/cross_backend/test_arithmetic_essentials.py`
- Modify: `tests/cross_backend/test_negate.py`
- Modify: `tests/cross_backend/test_trig_hyperbolic.py`
- Modify: `tests/cross_backend/test_least.py`
- Modify: `tests/cross_backend/test_null_nan_clip.py`

- [ ] **Step 1: Migrate `test_arithmetic_essentials.py`**

Same pattern as Task 2: replace `select_and_extract` with `collect_expr`, remove `.compile(df)`, replace extraction call.

- [ ] **Step 2: Migrate `test_negate.py`**

Same pattern. Example transformation:

```python
# Before:
def test_negate_method(self, backend_name, backend_factory, select_and_extract):
    ...
    expr = ma.col("val").negate()
    actual = select_and_extract(df, expr.compile(df), "result", backend_name)

# After:
def test_negate_method(self, backend_name, backend_factory, collect_expr):
    ...
    expr = ma.col("val").negate()
    actual = collect_expr(df, expr)
```

- [ ] **Step 3: Migrate `test_trig_hyperbolic.py`**

Same pattern.

- [ ] **Step 4: Migrate `test_least.py`**

Same pattern.

- [ ] **Step 5: Migrate `test_null_nan_clip.py`**

Same pattern.

- [ ] **Step 6: Run all migrated files**

Run: `hatch run test:test-target-quick tests/cross_backend/test_arithmetic_essentials.py tests/cross_backend/test_negate.py tests/cross_backend/test_trig_hyperbolic.py tests/cross_backend/test_least.py tests/cross_backend/test_null_nan_clip.py -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add tests/cross_backend/test_arithmetic_essentials.py tests/cross_backend/test_negate.py tests/cross_backend/test_trig_hyperbolic.py tests/cross_backend/test_least.py tests/cross_backend/test_null_nan_clip.py
git commit -m "refactor: migrate numeric test files to relation-based extraction"
```

---

### Task 4: Migrate String Test Files

**Files:**
- Modify: `tests/cross_backend/test_string.py`
- Modify: `tests/cross_backend/test_string_aspirational.py`
- Modify: `tests/cross_backend/test_string_strip_prefix_suffix.py`
- Modify: `tests/cross_backend/test_pattern.py`

**Important:** `test_string.py` and `test_pattern.py` use both `select_and_extract` AND `get_column_values`. Migrate both:

- `select_and_extract` → `collect_expr` (expression result extraction)
- `get_column_values` → `collect_col` (column extraction from filtered DataFrames)

- [ ] **Step 1: Migrate `test_string.py`**

Two patterns in this file:

Pattern A (expression extraction — same as before):
```python
# Before:
actual = select_and_extract(df, backend_expr, "result", backend_name)
# After:
actual = collect_expr(df, expr)
```

Pattern B (column extraction from filter result):
```python
# Before:
backend_expr = expr.compile(df)
result = df.filter(backend_expr)
actual = get_column_values(result, "text", backend_name)

# After:
import mountainash as ma_top  # add at top of file
actual = ma_top.relation(df).filter(expr).to_dict()["text"]
```

This replaces `.compile()` + `.filter()` + `get_column_values()` with a single relation chain. The relation handles backend detection, compilation, and null-safe extraction.

**Import note:** `relation()` lives on `mountainash`, not `mountainash.expressions`. Files using Pattern B need to add `import mountainash as ma_top` alongside the existing `import mountainash.expressions as ma`. The `collect_expr` and `collect_col` fixtures handle this internally — only direct relation usage in test bodies needs the extra import.

- [ ] **Step 2: Migrate `test_string_aspirational.py`**

Same pattern as Task 2 (only uses `select_and_extract`).

- [ ] **Step 3: Migrate `test_string_strip_prefix_suffix.py`**

Same pattern as Task 2 (only uses `select_and_extract`).

- [ ] **Step 4: Migrate `test_pattern.py`**

Uses both `select_and_extract` and `get_column_values`. Apply both patterns from Step 1.

- [ ] **Step 5: Run all migrated files**

Run: `hatch run test:test-target-quick tests/cross_backend/test_string.py tests/cross_backend/test_string_aspirational.py tests/cross_backend/test_string_strip_prefix_suffix.py tests/cross_backend/test_pattern.py -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add tests/cross_backend/test_string.py tests/cross_backend/test_string_aspirational.py tests/cross_backend/test_string_strip_prefix_suffix.py tests/cross_backend/test_pattern.py
git commit -m "refactor: migrate string test files to relation-based extraction"
```

---

### Task 5: Migrate Conditional and Comparison Test Files

**Files:**
- Modify: `tests/cross_backend/test_conditional.py`
- Modify: `tests/cross_backend/test_comparison_missing_close.py`
- Modify: `tests/cross_backend/test_expression_builder_api.py`

- [ ] **Step 1: Migrate `test_conditional.py`**

Same `select_and_extract` → `collect_expr` pattern.

- [ ] **Step 2: Migrate `test_comparison_missing_close.py`**

Same pattern.

- [ ] **Step 3: Migrate `test_expression_builder_api.py`**

Same pattern.

- [ ] **Step 4: Run all migrated files**

Run: `hatch run test:test-target-quick tests/cross_backend/test_conditional.py tests/cross_backend/test_comparison_missing_close.py tests/cross_backend/test_expression_builder_api.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add tests/cross_backend/test_conditional.py tests/cross_backend/test_comparison_missing_close.py tests/cross_backend/test_expression_builder_api.py
git commit -m "refactor: migrate conditional and comparison test files to relation-based extraction"
```

---

### Task 6: Migrate Temporal and DateTime Test Files

**Files:**
- Modify: `tests/cross_backend/test_temporal_advanced.py`
- Modify: `tests/cross_backend/test_temporal_natural.py`
- Modify: `tests/cross_backend/test_datetime_enrichment.py`

**Note:** `test_temporal_natural.py` uses both `select_and_extract` and `get_column_values`. Apply both patterns (see Task 4 Step 1 for dual-pattern migration).

- [ ] **Step 1: Migrate `test_temporal_advanced.py`**

Same `select_and_extract` → `collect_expr` pattern.

- [ ] **Step 2: Migrate `test_temporal_natural.py`**

Uses both `select_and_extract` and `get_column_values`. Apply:
- `select_and_extract` → `collect_expr`
- `get_column_values` on filtered results → `ma.relation(df).filter(expr).to_dict()["col"]`

- [ ] **Step 3: Migrate `test_datetime_enrichment.py`**

Same `select_and_extract` → `collect_expr` pattern.

- [ ] **Step 4: Run all migrated files**

Run: `hatch run test:test-target-quick tests/cross_backend/test_temporal_advanced.py tests/cross_backend/test_temporal_natural.py tests/cross_backend/test_datetime_enrichment.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add tests/cross_backend/test_temporal_advanced.py tests/cross_backend/test_temporal_natural.py tests/cross_backend/test_datetime_enrichment.py
git commit -m "refactor: migrate temporal test files to relation-based extraction"
```

---

### Task 7: Migrate Composition Test Files (Non-Ternary)

**Files:**
- Modify: `tests/cross_backend/test_compose_string.py`
- Modify: `tests/cross_backend/test_compose_string_extended.py`
- Modify: `tests/cross_backend/test_compose_null.py`
- Modify: `tests/cross_backend/test_compose_conditional.py`
- Modify: `tests/cross_backend/test_compose_comparison_extended.py`
- Modify: `tests/cross_backend/test_compose_cast.py`
- Modify: `tests/cross_backend/test_compose_datetime.py`
- Modify: `tests/cross_backend/test_compose_datetime_extended.py`
- Modify: `tests/cross_backend/test_compose_entrypoints.py`

- [ ] **Step 1: Migrate all 9 composition test files**

Same `select_and_extract` → `collect_expr` pattern for all.

- [ ] **Step 2: Run all migrated files**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_string.py tests/cross_backend/test_compose_string_extended.py tests/cross_backend/test_compose_null.py tests/cross_backend/test_compose_conditional.py tests/cross_backend/test_compose_comparison_extended.py tests/cross_backend/test_compose_cast.py tests/cross_backend/test_compose_datetime.py tests/cross_backend/test_compose_datetime_extended.py tests/cross_backend/test_compose_entrypoints.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_string.py tests/cross_backend/test_compose_string_extended.py tests/cross_backend/test_compose_null.py tests/cross_backend/test_compose_conditional.py tests/cross_backend/test_compose_comparison_extended.py tests/cross_backend/test_compose_cast.py tests/cross_backend/test_compose_datetime.py tests/cross_backend/test_compose_datetime_extended.py tests/cross_backend/test_compose_entrypoints.py
git commit -m "refactor: migrate composition test files to relation-based extraction"
```

---

### Task 8: Migrate Remaining Files and `select_and_collect` Users

**Files:**
- Modify: `tests/cross_backend/test_parameter_sensitivity.py`
- Modify: `tests/cross_backend/test_cast.py`
- Modify: `tests/cross_backend/test_type_resolution.py`
- Modify: `tests/cross_backend/test_boolean.py`

- [ ] **Step 1: Migrate `test_parameter_sensitivity.py`**

This file uses `assert_parameter_sensitivity` which was already updated in Task 1. But check if it also directly uses `select_and_extract` — if so, migrate those calls too.

- [ ] **Step 2: Migrate `test_cast.py`**

This file uses `select_and_collect` (not `select_and_extract`). Same transformation:

```python
# Before:
from tests.fixtures.backend_helpers import select_and_collect
...
actual = select_and_collect(df, backend_expr, "result", backend_name)

# After (use collect_expr fixture):
actual = collect_expr(df, expr)
```

Remove the `select_and_collect` import. Add `collect_expr` to test method signatures.

- [ ] **Step 3: Migrate `test_type_resolution.py`**

Same as Step 2 — uses `select_and_collect`, migrate to `collect_expr`.

- [ ] **Step 4: Migrate `test_boolean.py`**

Uses `get_column_values` on filtered results. Apply the relation filter pattern. Add `import mountainash as ma_top` at the top of the file alongside the existing `import mountainash.expressions as ma`:

```python
# Before:
backend_expr = expr.compile(df)
result = df.filter(backend_expr)
actual = get_column_values(result, "name", backend_name)

# After:
actual = ma_top.relation(df).filter(expr).to_dict()["name"]
```

- [ ] **Step 5: Run all migrated files**

Run: `hatch run test:test-target-quick tests/cross_backend/test_parameter_sensitivity.py tests/cross_backend/test_cast.py tests/cross_backend/test_type_resolution.py tests/cross_backend/test_boolean.py -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add tests/cross_backend/test_parameter_sensitivity.py tests/cross_backend/test_cast.py tests/cross_backend/test_type_resolution.py tests/cross_backend/test_boolean.py
git commit -m "refactor: migrate remaining test files to relation-based extraction"
```

---

### Task 9: Delete Dead Code and Final Verification

**Files:**
- Modify: `tests/fixtures/backend_helpers.py` (delete `select_and_collect`)
- Modify: `tests/conftest.py` (delete `get_column_values`)

- [ ] **Step 1: Delete `select_and_collect` from `backend_helpers.py`**

Remove the `select_and_collect` function (lines 332-353) from `tests/fixtures/backend_helpers.py`.

- [ ] **Step 2: Delete `get_column_values` from `conftest.py`**

Remove the `get_column_values` fixture (lines 468-487) from `tests/conftest.py`.

- [ ] **Step 3: Verify no remaining references to deleted functions**

Run:
```bash
grep -r "select_and_collect" tests/ --include="*.py"
grep -r "get_column_values" tests/ --include="*.py"
```

Expected: No matches outside of conftest.py fixture definitions and the 5 booleanizer-excepted files.

- [ ] **Step 4: Run the full cross-backend test suite**

Run: `hatch run test:test-target-quick tests/cross_backend/ -v`
Expected: All tests pass. The only remaining uses of `select_and_extract` should be in the 5 booleanizer files.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/backend_helpers.py tests/conftest.py
git commit -m "chore: delete dead test extraction helpers after relation-based migration"
```
