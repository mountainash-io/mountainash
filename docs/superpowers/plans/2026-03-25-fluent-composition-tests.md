# Fluent Composition Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 10 cross-backend test files (~48 tests) that exercise fluent expression composition — chaining, namespace crossing, and real-world builder patterns.

**Architecture:** Each file is an independent test module in `tests/cross_backend/` following the existing pattern: parametrized across 6 backends, inline data via `backend_factory.create()`, assertions on executed results. No new infrastructure.

**Tech Stack:** pytest, mountainash_expressions public API (`ma.col`, `ma.lit`, `ma.when`, `ma.coalesce`, `ma.greatest`, `ma.least`, `ma.t_col`)

**Spec:** `docs/superpowers/specs/2026-03-25-fluent-composition-tests-design.md`

---

## File Map

All files are new, created in `tests/cross_backend/`:

| File | Tests | Dependencies |
|------|-------|-------------|
| `test_compose_string.py` | 6 | `ma.col().str.*` |
| `test_compose_datetime.py` | 5 | `ma.col().dt.*` |
| `test_compose_cross_namespace.py` | 7 | `.str`, `.dt`, arithmetic, boolean, rounding, between |
| `test_compose_null.py` | 4 | `fill_null`, `is_null`, arithmetic |
| `test_compose_conditional.py` | 4 | `ma.when().then().otherwise()` |
| `test_compose_entrypoints.py` | 4 | `ma.coalesce`, `ma.greatest`, `ma.least` |
| `test_compose_cast.py` | 4 | `.cast()` |
| `test_compose_name.py` | 3 | `.name.alias()`, `.name.suffix()`, `.name.prefix()` |
| `test_compose_ternary.py` | 4 | `t_gt`, `t_eq`, `t_and`, `t_col`, booleanizers |
| `test_compose_set.py` | 4 | `is_in`, `is_not_in` |

No existing files are modified.

---

## Common Patterns

Every test file uses the same boilerplate. Reference this for all tasks:

```python
"""Cross-backend tests for [category] fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCompose[Category]:
    """Test [category] fluent composition patterns."""

    def test_example(self, backend_name, backend_factory, get_result_count):
        data = {"col": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("col").some_chain()
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == expected, f"[{backend_name}] Expected {expected}, got {count}"
```

**Fixture usage:**
- `get_result_count(result, backend_name)` — returns int row count after filter
- `select_and_extract(df, backend_expr, "alias", backend_name)` — returns list of values from a computed column
- `get_column_values(result, "col", backend_name)` — returns list of values from a named column
- `backend_factory.create(data_dict, backend_name)` — creates a DataFrame for the backend

**xfail pattern:** When a backend has known limitations, add at the top of the test method:
```python
if backend_name == "ibis-sqlite":
    pytest.xfail("SQLite limitation: ...")
```

---

### Task 1: test_compose_string.py

**Files:**
- Create: `tests/cross_backend/test_compose_string.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for string namespace fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeString:
    """Test fluent .str method chaining patterns."""

    def test_lower_then_contains(self, backend_name, backend_factory, get_result_count):
        """Case-insensitive search via .str.lower().str.contains()."""
        data = {"name": ["John Smith", "JOHNNY B", "Jane Doe", "johnson"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.lower().str.contains("john")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 (John Smith, JOHNNY B, johnson), got {count}"

    def test_replace_then_upper(self, backend_name, backend_factory, select_and_extract):
        """Sequential transforms: replace then uppercase."""
        data = {"code": ["a_b", "c_d", "e_f"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("code").str.replace("_", "-").str.upper()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["A-B", "C-D", "E-F"], f"[{backend_name}] got {actual}"

    def test_trim_then_char_length_then_filter(self, backend_name, backend_factory, get_result_count):
        """String to numeric to boolean: .str.trim().str.len().gt(3)."""
        data = {"name": ["  Al  ", " Bob ", " Charlotte ", "  Di  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.trim().str.len().gt(3)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 (Charlotte), got {count}"

    def test_negation_of_contains(self, backend_name, backend_factory, get_result_count):
        """Negation: ~col('status').str.contains('archived')."""
        data = {"status": ["active", "archived", "pending", "archived_old"]}
        df = backend_factory.create(data, backend_name)

        expr = ~ma.col("status").str.contains("archived")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 (active, pending), got {count}"

    def test_lower_then_ends_with(self, backend_name, backend_factory, get_result_count):
        """Real-world pattern: case-insensitive email domain check."""
        data = {"email": ["user@Gmail.COM", "admin@yahoo.com", "test@GMAIL.com", "x@other.org"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("email").str.lower().str.ends_with("@gmail.com")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 gmail addresses, got {count}"

    def test_three_deep_chain(self, backend_name, backend_factory, get_result_count):
        """3-deep chain: trim -> lower -> contains."""
        data = {"name": ["  Admin ", " ADMIN_USER ", "guest", "  root_admin  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.trim().str.lower().str.contains("admin")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 (Admin, ADMIN_USER, root_admin), got {count}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_string.py -v`
Expected: All pass (or xfail pandas if needed)

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_string.py
git commit -m "test: add fluent string composition tests"
```

---

### Task 2: test_compose_datetime.py

**Files:**
- Create: `tests/cross_backend/test_compose_datetime.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for datetime namespace fluent composition."""

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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetime:
    """Test fluent .dt method chaining patterns."""

    def test_extract_year_then_compare(self, backend_name, backend_factory, get_result_count):
        """Extract year then filter: .dt.year().eq(2024)."""
        data = {
            "ts": [
                datetime(2023, 6, 15),
                datetime(2024, 1, 10),
                datetime(2024, 8, 20),
                datetime(2025, 3, 1),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.year().eq(2024)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows in year 2024, got {count}"

    def test_add_days_then_extract_month(self, backend_name, backend_factory, select_and_extract):
        """Arithmetic then extract: .dt.add_days(20).dt.month()."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Interval addition not supported.")
        data = {
            "ts": [
                datetime(2024, 1, 20),  # +20 days = Feb 9
                datetime(2024, 2, 15),  # +20 days = Mar 6
                datetime(2024, 12, 20), # +20 days = Jan 9 (2025)
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.add_days(20).dt.month()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == [2, 3, 1], f"[{backend_name}] Expected [2, 3, 1], got {actual}"

    def test_extract_year_then_compare_to_column(self, backend_name, backend_factory, get_result_count):
        """Extract then compare to column: .dt.year().gt(col('threshold'))."""
        data = {
            "ts": [
                datetime(2022, 1, 1),
                datetime(2024, 6, 1),
                datetime(2025, 1, 1),
            ],
            "threshold": [2023, 2025, 2020],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.year().gt(ma.col("threshold"))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: 2022 > 2023 -> False
        # Row 1: 2024 > 2025 -> False
        # Row 2: 2025 > 2020 -> True
        assert count == 1, f"[{backend_name}] Expected 1 row, got {count}"

    def test_business_hours_filter(self, backend_name, backend_factory, get_result_count):
        """Dual extract + boolean: hour >= 9 AND hour < 17."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Sub-day extraction unreliable.")
        data = {
            "ts": [
                datetime(2024, 1, 15, 8, 0),   # 8am - before
                datetime(2024, 1, 15, 9, 0),   # 9am - in
                datetime(2024, 1, 15, 12, 30),  # 12:30 - in
                datetime(2024, 1, 15, 16, 59),  # 4:59pm - in
                datetime(2024, 1, 15, 17, 0),  # 5pm - after
                datetime(2024, 1, 15, 22, 0),  # 10pm - after
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.hour().ge(9).and_(ma.col("ts").dt.hour().lt(17))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 business-hours rows, got {count}"

    def test_truncate_then_weekday(self, backend_name, backend_factory, select_and_extract):
        """Truncate to day then extract weekday: .dt.truncate('day').dt.weekday()."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Truncation and weekday extraction not supported.")
        data = {
            "ts": [
                datetime(2024, 1, 15, 10, 30),  # Monday morning
                datetime(2024, 1, 16, 23, 59),  # Tuesday night
                datetime(2024, 1, 20, 8, 0),    # Saturday morning
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.truncate("day").dt.weekday()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Weekday numbering may vary by backend — assert Monday < Saturday
        assert actual[0] < actual[2], f"[{backend_name}] Monday should be before Saturday: {actual}"
        # Tuesday should be between Monday and Saturday
        assert actual[0] < actual[1] < actual[2], f"[{backend_name}] Expected Mon < Tue < Sat: {actual}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_datetime.py -v`
Expected: Pass (with xfails on ibis-sqlite)

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_datetime.py
git commit -m "test: add fluent datetime composition tests"
```

---

### Task 3: test_compose_cross_namespace.py

**Files:**
- Create: `tests/cross_backend/test_compose_cross_namespace.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for cross-namespace fluent composition."""

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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeCrossNamespace:
    """Test expressions combining different namespaces."""

    def test_string_length_and_numeric_filter(self, backend_name, backend_factory, get_result_count):
        """String + comparison: name length > 3 AND score >= 80."""
        data = {"name": ["Al", "Bob", "Charlotte", "Diana"], "score": [90, 60, 85, 70]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.len().gt(3).and_(ma.col("score").ge(80))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 (Charlotte/85), got {count}"

    def test_string_upper_or_age_filter(self, backend_name, backend_factory, get_result_count):
        """String + boolean: uppercased name is 'ADMIN' OR age > 30."""
        data = {"name": ["admin", "user", "guest", "Admin"], "age": [25, 35, 20, 28]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.upper().eq(ma.lit("ADMIN")).or_(ma.col("age").gt(30))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # admin->ADMIN matches, user age 35 matches, Admin->ADMIN matches = 3
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_datetime_year_and_string_status(self, backend_name, backend_factory, get_result_count):
        """Datetime + string: year is 2024 AND lowercased status is 'active'."""
        data = {
            "ts": [datetime(2024, 1, 1), datetime(2024, 6, 1), datetime(2023, 1, 1), datetime(2024, 9, 1)],
            "status": ["Active", "INACTIVE", "Active", "ACTIVE"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.year().eq(2024).and_(
            ma.col("status").str.lower().eq(ma.lit("active"))
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: 2024 + active -> yes
        # Row 1: 2024 + inactive -> no
        # Row 2: 2023 -> no
        # Row 3: 2024 + active -> yes
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_arithmetic_and_string_contains(self, backend_name, backend_factory, get_result_count):
        """Arithmetic + string: (price * qty) > 1000 AND name contains 'premium'."""
        data = {
            "name": ["premium widget", "basic bolt", "premium gear", "standard"],
            "price": [100, 200, 500, 300],
            "qty": [5, 3, 3, 10],
        }
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("price") * ma.col("qty")).gt(1000).and_(
            ma.col("name").str.contains("premium")
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # premium widget: 500 > 1000? No
        # basic bolt: 600 > 1000? No
        # premium gear: 1500 > 1000 AND premium? Yes
        # standard: 3000 > 1000 but no premium? No
        assert count == 1, f"[{backend_name}] Expected 1 (premium gear), got {count}"

    def test_null_fill_and_string_length(self, backend_name, backend_factory, get_result_count):
        """Null + comparison + string: fill_null then gt, AND string length > 0."""
        data = {
            "value": [10, None, 30, None],
            "label": ["yes", "no", "", "ok"],
            "threshold": [5, 5, 5, 5],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").fill_null(0).gt(ma.col("threshold")).and_(
            ma.col("label").str.len().gt(0)
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: 10 > 5 AND len("yes") > 0 -> yes
        # Row 1: 0 > 5 -> no
        # Row 2: 30 > 5 AND len("") > 0 -> no (empty string)
        # Row 3: 0 > 5 -> no
        assert count == 1, f"[{backend_name}] Expected 1, got {count}"

    def test_arithmetic_rounding_comparison(self, backend_name, backend_factory, get_result_count):
        """Arithmetic + rounding + comparison: (price * 1.07).round(2) > 100."""
        data = {"price": [90.0, 95.0, 100.0, 50.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").multiply(ma.lit(1.07)).round(2).gt(ma.lit(100.0))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 90 * 1.07 = 96.30 -> no
        # 95 * 1.07 = 101.65 -> yes
        # 100 * 1.07 = 107.00 -> yes
        # 50 * 1.07 = 53.50 -> no
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_between_and_boolean(self, backend_name, backend_factory, get_result_count):
        """Between + boolean: score in range AND active."""
        data = {
            "score": [45, 65, 75, 85, 95],
            "min_score": [60, 60, 60, 60, 60],
            "max_score": [90, 90, 90, 90, 90],
            "active": [True, True, False, True, True],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").between(
            ma.col("min_score"), ma.col("max_score")
        ).and_(ma.col("active").eq(True))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 45: out of range
        # 65: in range, active -> yes
        # 75: in range, not active -> no
        # 85: in range, active -> yes
        # 95: out of range
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_cross_namespace.py -v`
Expected: Pass (xfail as needed for backend limitations)

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_cross_namespace.py
git commit -m "test: add fluent cross-namespace composition tests"
```

---

### Task 4: test_compose_null.py

**Files:**
- Create: `tests/cross_backend/test_compose_null.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for null handling fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeNull:
    """Test null handling composed with other operations."""

    def test_fill_null_then_arithmetic(self, backend_name, backend_factory, select_and_extract):
        """Fill nulls then add: fill_null(0) + tax."""
        data = {"price": [100, None, 300], "tax": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").fill_null(0) + ma.col("tax")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == [110, 20, 330], f"[{backend_name}] Expected [110, 20, 330], got {actual}"

    def test_fill_null_multiply_then_compare(self, backend_name, backend_factory, get_result_count):
        """Chain: fill_null -> multiply -> gt."""
        data = {"value": [60, None, 40, None, 80]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").fill_null(ma.lit(0)).multiply(2).gt(100)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 60*2=120 > 100 yes, 0*2=0 no, 40*2=80 no, 0*2=0 no, 80*2=160 yes
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_is_null_or_negative(self, backend_name, backend_factory, get_result_count):
        """Null check in boolean chain: is_null OR value < 0."""
        data = {"a": [10, None, -5, 20, None], "b": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").is_null().or_(ma.col("a").lt(0))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 1: null -> yes, Row 2: -5 < 0 -> yes, Row 4: null -> yes
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_cascading_fill_null(self, backend_name, backend_factory, select_and_extract):
        """Cascading fill: fill_null(col_b).fill_null(0)."""
        data = {"a": [1, None, None], "b": [10, None, 30]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").fill_null(ma.col("b")).fill_null(0)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: a=1 -> 1
        # Row 1: a=None, b=None -> fill with b=None, then fill with 0 -> 0
        # Row 2: a=None, b=30 -> fill with b=30 -> 30
        assert actual == [1, 0, 30], f"[{backend_name}] Expected [1, 0, 30], got {actual}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_null.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_null.py
git commit -m "test: add fluent null composition tests"
```

---

### Task 5: test_compose_conditional.py

**Files:**
- Create: `tests/cross_backend/test_compose_conditional.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for conditional fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeConditional:
    """Test when/then/otherwise with composed expressions."""

    def test_conditional_string_transform(self, backend_name, backend_factory, select_and_extract):
        """when(score >= 70) then uppercase name, else keep."""
        data = {"score": [85, 45, 70], "name": ["alice", "bob", "carol"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(ma.col("score").ge(70)).then(
            ma.col("name").str.upper()
        ).otherwise(ma.col("name"))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["ALICE", "bob", "CAROL"], f"[{backend_name}] got {actual}"

    def test_conditional_arithmetic(self, backend_name, backend_factory, select_and_extract):
        """when(a > 0) then a * 2, else 0."""
        data = {"a": [5, -3, 10, 0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(ma.col("a").gt(0)).then(
            ma.col("a") * 2
        ).otherwise(ma.lit(0))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, 0, 20, 0], f"[{backend_name}] got {actual}"

    def test_conditional_null_handling(self, backend_name, backend_factory, select_and_extract):
        """when(x is null) then -1, else x."""
        data = {"x": [10, None, 30, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(ma.col("x").is_null()).then(
            ma.lit(-1)
        ).otherwise(ma.col("x"))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, -1, 30, -1], f"[{backend_name}] got {actual}"

    def test_conditional_composed_condition(self, backend_name, backend_factory, select_and_extract):
        """when(a > 0 AND b > 0) then a + b, else 0."""
        data = {"a": [5, -3, 10, 0], "b": [2, 4, -1, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(
            ma.col("a").gt(0).and_(ma.col("b").gt(0))
        ).then(
            ma.col("a") + ma.col("b")
        ).otherwise(ma.lit(0))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        # Row 0: 5>0 AND 2>0 -> 7
        # Row 1: -3>0 -> no -> 0
        # Row 2: 10>0 AND -1>0 -> no -> 0
        # Row 3: 0>0 -> no -> 0
        assert actual == [7, 0, 0, 0], f"[{backend_name}] got {actual}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_conditional.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_conditional.py
git commit -m "test: add fluent conditional composition tests"
```

---

### Task 6: test_compose_entrypoints.py

**Files:**
- Create: `tests/cross_backend/test_compose_entrypoints.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for entrypoint fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeEntrypoints:
    """Test coalesce/greatest/least with composed expressions."""

    def test_coalesce_with_string_transform(self, backend_name, backend_factory, select_and_extract):
        """coalesce(trimmed phone, email, default)."""
        data = {
            "phone": ["  555-1234  ", None, "  ", None],
            "email": [None, "a@b.com", None, "c@d.com"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.coalesce(ma.col("phone").str.trim(), ma.col("email"), ma.lit("N/A"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: trimmed phone "555-1234" (non-null) -> "555-1234"
        # Row 1: phone is None, email "a@b.com" -> "a@b.com"
        # Row 2: trimmed phone is "" (non-null empty string) -> ""
        # Row 3: phone is None, email "c@d.com" -> "c@d.com"
        assert actual[0] == "555-1234", f"[{backend_name}] Row 0: {actual[0]}"
        assert actual[1] == "a@b.com", f"[{backend_name}] Row 1: {actual[1]}"
        assert actual[2] == "", f"[{backend_name}] Row 2: trimmed empty string is non-null: {actual[2]}"
        assert actual[3] == "c@d.com", f"[{backend_name}] Row 3: {actual[3]}"

    def test_greatest_with_arithmetic(self, backend_name, backend_factory, select_and_extract):
        """greatest(a + 1, b * 2)."""
        data = {"a": [10, 1, 5], "b": [3, 20, 2]}
        df = backend_factory.create(data, backend_name)

        expr = ma.greatest(ma.col("a") + 1, ma.col("b") * 2)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: max(11, 6) = 11
        # Row 1: max(2, 40) = 40
        # Row 2: max(6, 4) = 6
        assert actual == [11, 40, 6], f"[{backend_name}] got {actual}"

    def test_least_with_null_handling(self, backend_name, backend_factory, select_and_extract):
        """least(x, y.fill_null(999))."""
        data = {"x": [10, 50, 30], "y": [5, None, 20]}
        df = backend_factory.create(data, backend_name)

        expr = ma.least(ma.col("x"), ma.col("y").fill_null(ma.lit(999)))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: min(10, 5) = 5
        # Row 1: min(50, 999) = 50
        # Row 2: min(30, 20) = 20
        assert actual == [5, 50, 20], f"[{backend_name}] got {actual}"

    def test_coalesce_then_compare(self, backend_name, backend_factory, get_result_count):
        """coalesce(a, b) > 0 — entrypoint then comparison."""
        data = {"a": [None, 5, None, -3], "b": [10, None, -1, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.coalesce(ma.col("a"), ma.col("b")).gt(0)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: coalesce(None, 10) = 10 > 0 yes
        # Row 1: coalesce(5, None) = 5 > 0 yes
        # Row 2: coalesce(None, -1) = -1 > 0 no
        # Row 3: coalesce(-3, None) = -3 > 0 no
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_entrypoints.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_entrypoints.py
git commit -m "test: add fluent entrypoint composition tests"
```

---

### Task 7: test_compose_cast.py

**Files:**
- Create: `tests/cross_backend/test_compose_cast.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for cast fluent composition."""

import math

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeCast:
    """Test cast operations composed with other builders."""

    def test_cast_float_then_divide(self, backend_name, backend_factory, select_and_extract):
        """Cast to float then divide: .cast(float).divide(total)."""
        data = {"value": [10, 20, 30], "total": [100.0, 100.0, 100.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(float).divide(ma.col("total"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        for i, (a, e) in enumerate(zip(actual, [0.1, 0.2, 0.3])):
            assert math.isclose(a, e, rel_tol=1e-9), f"[{backend_name}] Row {i}: {a} != {e}"

    def test_cast_to_string_then_contains(self, backend_name, backend_factory, get_result_count):
        """Cast int to string then search: .cast(str).str.contains('5')."""
        data = {"count": [15, 25, 30, 50, 55]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("count").cast(str).str.contains("5")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # "15" has 5, "25" has 5, "30" no, "50" has 5, "55" has 5
        assert count == 4, f"[{backend_name}] Expected 4, got {count}"

    def test_cast_then_compare(self, backend_name, backend_factory, get_result_count):
        """Cast float to int then compare: .cast(int).gt(70)."""
        data = {"score": [70.5, 69.9, 71.0, 50.3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").cast(int).gt(70)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 70.5 -> 70 (truncated), not > 70
        # 69.9 -> 69, not > 70
        # 71.0 -> 71, > 70 yes
        # 50.3 -> 50, no
        assert count == 1, f"[{backend_name}] Expected 1 (71), got {count}"

    def test_fill_null_cast_multiply(self, backend_name, backend_factory, select_and_extract):
        """Chain: fill_null -> cast -> multiply."""
        data = {"price": [10, None, 30], "rate": [1.1, 1.2, 1.3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").fill_null(0).cast(float).multiply(ma.col("rate"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert math.isclose(actual[0], 11.0, rel_tol=1e-9), f"[{backend_name}] Row 0: {actual[0]}"
        assert math.isclose(actual[1], 0.0, rel_tol=1e-9), f"[{backend_name}] Row 1: {actual[1]}"
        assert math.isclose(actual[2], 39.0, rel_tol=1e-9), f"[{backend_name}] Row 2: {actual[2]}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_cast.py -v`
Expected: Pass (may need xfail on ibis-duckdb for banker's rounding in test 3)

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_cast.py
git commit -m "test: add fluent cast composition tests"
```

---

### Task 8: test_compose_name.py

**Files:**
- Create: `tests/cross_backend/test_compose_name.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for name operations fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeName:
    """Test .name accessor in composed expressions."""

    def test_arithmetic_then_alias(self, backend_name, backend_factory):
        """(col_a + col_b).name.alias('sum') — verify column name."""
        data = {"a": [1, 2, 3], "b": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("a") + ma.col("b")).name.alias("total")
        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        # Verify the column exists with the aliased name
        if backend_name.startswith("ibis-"):
            cols = result.columns
        elif backend_name == "pandas":
            cols = list(result.columns)
        else:
            cols = result.columns

        assert "total" in cols, f"[{backend_name}] Expected 'total' column, got {cols}"

    def test_string_upper_then_suffix(self, backend_name, backend_factory):
        """col.str.upper().name.suffix('_clean') — verify column name."""
        data = {"name": ["alice", "bob"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.upper().name.suffix("_clean")
        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        if backend_name.startswith("ibis-"):
            cols = result.columns
        elif backend_name == "pandas":
            cols = list(result.columns)
        else:
            cols = result.columns

        assert any("_clean" in c for c in cols), f"[{backend_name}] Expected column with '_clean' suffix, got {cols}"

    def test_fill_null_then_prefix(self, backend_name, backend_factory):
        """col.fill_null(0).name.prefix('filled_') — verify column name."""
        data = {"value": [1, None, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").fill_null(0).name.prefix("filled_")
        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        if backend_name.startswith("ibis-"):
            cols = result.columns
        elif backend_name == "pandas":
            cols = list(result.columns)
        else:
            cols = result.columns

        assert any("filled_" in c for c in cols), f"[{backend_name}] Expected column with 'filled_' prefix, got {cols}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_name.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_name.py
git commit -m "test: add fluent name composition tests"
```

---

### Task 9: test_compose_ternary.py

**Files:**
- Create: `tests/cross_backend/test_compose_ternary.py`

- [ ] **Step 1: Write the test file**

Note: Ternary tests use a smaller backend set (no pandas, no ibis-sqlite) following the pattern in `test_ternary.py`.

```python
"""Cross-backend tests for ternary fluent composition."""

import pytest
import mountainash_expressions as ma


# Ternary tests use reduced backend set — same as test_ternary.py
TERNARY_BACKENDS = [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
]

T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TERNARY_BACKENDS)
class TestComposeTernary:
    """Test ternary expressions with composed operands."""

    def test_ternary_with_null_safe_operand(self, backend_name, backend_factory, select_and_extract):
        """t_gt with fill_null operand: score.t_gt(threshold.fill_null(0))."""
        data = {
            "score": [80, None, 60],
            "threshold": [70, 50, None],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(ma.col("threshold").fill_null(ma.lit(0)))
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: 80 > 70 -> TRUE (1)
        # Row 1: NULL > 50 -> UNKNOWN (0)
        # Row 2: 60 > 0 (filled) -> TRUE (1)
        assert actual[0] == T_TRUE, f"[{backend_name}] Row 0: {actual[0]}"
        assert actual[1] == T_UNKNOWN, f"[{backend_name}] Row 1: {actual[1]}"
        assert actual[2] == T_TRUE, f"[{backend_name}] Row 2: {actual[2]}"

    def test_ternary_logical_chain(self, backend_name, backend_factory, select_and_extract):
        """Ternary chain: t_eq AND t_gt."""
        data = {"a": [1, 1, 0, None], "b": [5, -1, 5, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_eq(ma.lit(1)).t_and(ma.col("b").t_gt(ma.lit(0)))
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: (1==1)=T AND (5>0)=T -> T
        # Row 1: (1==1)=T AND (-1>0)=F -> F
        # Row 2: (0==1)=F AND ... -> F
        # Row 3: (NULL==1)=U AND (5>0)=T -> U
        assert actual[0] == T_TRUE, f"[{backend_name}] Row 0"
        assert actual[1] == T_FALSE, f"[{backend_name}] Row 1"
        assert actual[2] == T_FALSE, f"[{backend_name}] Row 2"
        assert actual[3] == T_UNKNOWN, f"[{backend_name}] Row 3"

    def test_t_col_with_composition(self, backend_name, backend_factory, get_result_count):
        """t_col with custom unknown then filter with is_true booleanizer."""
        data = {"value": [100, -999, 50, -999, 80], "active": [True, True, False, True, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("value", unknown={-999}).t_gt(ma.lit(60)).t_and(
            ma.col("active").t_eq(ma.lit(True))
        )
        result = df.filter(expr.compile(df, booleanizer="is_true"))

        count = get_result_count(result, backend_name)
        # Row 0: 100 > 60 = T AND active=T -> T (pass is_true)
        # Row 1: -999 -> UNKNOWN AND active=T -> U (fail is_true)
        # Row 2: 50 > 60 = F -> F (fail)
        # Row 3: -999 -> UNKNOWN AND active=T -> U (fail)
        # Row 4: 80 > 60 = T AND active=T -> T (pass)
        assert count == 2, f"[{backend_name}] Expected 2 with is_true, got {count}"

    def test_booleanizer_maybe_true(self, backend_name, backend_factory, get_result_count):
        """Same expression with maybe_true gives more rows."""
        data = {"value": [100, -999, 50, -999, 80], "active": [True, True, False, True, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("value", unknown={-999}).t_gt(ma.lit(60)).t_and(
            ma.col("active").t_eq(ma.lit(True))
        )
        result = df.filter(expr.compile(df, booleanizer="maybe_true"))

        count = get_result_count(result, backend_name)
        # maybe_true: TRUE and UNKNOWN pass
        # Row 0: T (pass), Row 1: U (pass), Row 2: F (fail), Row 3: U (pass), Row 4: T (pass)
        assert count == 4, f"[{backend_name}] Expected 4 with maybe_true, got {count}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_ternary.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_ternary.py
git commit -m "test: add fluent ternary composition tests"
```

---

### Task 10: test_compose_set.py

**Files:**
- Create: `tests/cross_backend/test_compose_set.py`

- [ ] **Step 1: Write the test file**

```python
"""Cross-backend tests for set operations fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeSet:
    """Test is_in/is_not_in composed with other operations."""

    def test_is_in_and_comparison(self, backend_name, backend_factory, get_result_count):
        """Set membership + comparison: status in [active, pending] AND score > 50."""
        data = {
            "status": ["active", "archived", "pending", "active", "deleted"],
            "score": [80, 90, 40, 60, 70],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("status").is_in(["active", "pending"]).and_(ma.col("score").gt(50))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # active/80 yes, archived no, pending/40 score too low, active/60 yes, deleted no
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_is_not_in_filter(self, backend_name, backend_factory, get_result_count):
        """Exclusion: category NOT IN [archived, deleted]."""
        data = {"category": ["active", "archived", "pending", "deleted", "draft"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("category").is_not_in(["archived", "deleted"])
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 (active, pending, draft), got {count}"

    def test_string_transform_then_is_in(self, backend_name, backend_factory, get_result_count):
        """String transform then set: .str.lower().is_in(['admin', 'root'])."""
        data = {"role": ["Admin", "USER", "Root", "GUEST", "admin"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("role").str.lower().is_in(["admin", "root"])
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Admin->admin yes, USER->user no, Root->root yes, GUEST->guest no, admin yes
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_is_in_or_is_null(self, backend_name, backend_factory, get_result_count):
        """Set + null: value in [1,2,3] OR value is null."""
        data = {"value": [1, 5, None, 2, 10, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").is_in([1, 2, 3]).or_(ma.col("value").is_null())
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 1 yes, 5 no, None yes, 2 yes, 10 no, None yes
        assert count == 4, f"[{backend_name}] Expected 4, got {count}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_set.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_compose_set.py
git commit -m "test: add fluent set composition tests"
```

---

### Task 11: Final verification

- [ ] **Step 1: Run all composition tests together**

Run: `hatch run test:test-target-quick tests/cross_backend/test_compose_*.py -v`
Expected: All pass (with expected xfails)

- [ ] **Step 2: Run full test suite to check no regressions**

Run: `hatch run test:test`
Expected: 1790+ passed, 0 failed, xfails similar to before

- [ ] **Step 3: Push**

```bash
git push
```
