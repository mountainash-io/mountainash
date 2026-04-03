# Relation-Based Test Extraction Design

**Date:** 2026-04-02
**Status:** Approved
**Scope:** Cross-backend expression test infrastructure — result extraction

## Problem

Cross-backend expression tests extract results through ad-hoc test fixtures (`select_and_extract`, `select_and_collect`) that bypass the egress layer. These fixtures must implement their own backend-specific extraction logic, leading to:

1. **Pandas NaN/null conflation.** Ibis backends route through `.execute().tolist()` which produces pandas Series, converting null to NaN. Pandas-via-narwhals uses `.to_list()` with the same problem. Tests that assert `is None` fail with `nan`.

2. **Tests don't reflect real-world usage.** No user extracts results this way. The real extraction path is the relations API (`.to_dict()`, `.to_dicts()`, `.to_polars()`) which routes through the egress layer via Polars. Tests pass with PyArrow workarounds but validate a code path nobody uses.

3. **Duplicated extraction logic.** `select_and_extract` (conftest.py, 588 uses across 33 files), `select_and_collect` (backend_helpers.py, 109 uses across 8 files), and `get_column_values` (conftest.py) all implement the same backend-routing logic independently.

### Current Test Pattern

```python
def test_addition(self, backend_name, backend_factory, select_and_extract):
    data = {"a": [10, 20], "b": [2, 3]}
    df = backend_factory.create(data, backend_name)

    expr = ma.col("a").add(ma.col("b"))
    backend_expr = expr.compile(df)
    actual = select_and_extract(df, backend_expr, "result", backend_name)

    assert actual == [12, 23]
```

The fixture handles:
- Ibis: `df.select(backend_expr.name(alias))` → `.to_pyarrow()[alias].to_pylist()`
- Pandas: `df.select(backend_expr.alias(alias))` → `.to_arrow()[alias].to_pylist()`
- Polars/Narwhals: `df.select(backend_expr.alias(alias))` → `[alias].to_list()`

This is test-only code that no user would write.

### The Egress Layer Already Solves This

The relations API terminal operations (`.to_dict()`, `.to_polars()`, etc.) route all backends through Polars before extraction. Null handling is correct by construction — no PyArrow workarounds needed.

Verified: `ma.relation(df).select(expr.name.alias("result")).to_dict()["result"]` returns `None` (not `nan`) for null values across all 6 backends (Polars, Pandas, Narwhals, Ibis-DuckDB, Ibis-Polars, Ibis-SQLite).

## Design

### 1. New Fixture: `collect_expr`

**File:** `tests/conftest.py`

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

### 2. Migrated Test Pattern

```python
def test_addition(self, backend_name, backend_factory, collect_expr):
    data = {"a": [10, 20], "b": [2, 3]}
    df = backend_factory.create(data, backend_name)

    expr = ma.col("a").add(ma.col("b"))
    actual = collect_expr(df, expr)

    assert actual == [12, 23]
```

Changes from current pattern:
- `select_and_extract` → `collect_expr` in fixture parameter
- No `.compile(df)` call — the relation handles compilation
- No `backend_name` in the extraction call — the relation handles backend detection
- No column alias gymnastics — defaults to `"result"`

### 3. Booleanizer Exception

Tests that pass explicit booleanizer parameters to `.compile()` cannot use the relation path because the relations API has no booleanizer concept. These tests keep the existing `select_and_extract` fixture (with its PyArrow-based implementation).

**5 files stay on `select_and_extract`:**
- `test_ternary.py` — raw sentinel value tests (`booleanizer=None`)
- `test_ternary_auto_booleanize.py` — explicit booleanizer parameter tests
- `test_t_col.py` — sentinel inspection tests (`booleanizer=None`)
- `test_compose_ternary.py` — ternary composition with `booleanizer=None`
- `test_compose_ternary_extended.py` — extended ternary composition with `booleanizer=None`

This exception is acceptable: these tests are explicitly testing internal compile-time booleanizer behavior, not the user-facing extraction path. The `select_and_extract` fixture's PyArrow workaround is appropriate here because the test is about compilation semantics, not egress correctness.

Migration granularity is at the file level: if a file has any booleanizer tests, the whole file stays on `select_and_extract`.

### 4. Column Extraction: `collect_col`

`get_column_values` extracts an existing column (no expression) from a DataFrame. Same NaN problem — uses `.execute().tolist()` for Ibis. 4 test files use it (64 occurrences).

**New fixture:**

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

### 5. Deletions

After migration:

| Item | Location | Action |
|------|----------|--------|
| `select_and_collect()` | `tests/fixtures/backend_helpers.py` | Delete (dead code) |
| `get_column_values()` fixture | `tests/conftest.py` | Delete (replaced by `collect_expr`) |
| `select_and_extract()` fixture | `tests/conftest.py` | Keep, update docstring to mark as booleanizer-only |

### 6. Migration Strategy

One file at a time. Run tests after each file migration. No big bang.

**Migration per file:**
1. Replace `select_and_extract` with `collect_expr` in fixture parameter
2. Remove `.compile(df)` calls (where no booleanizer is used)
3. Replace `select_and_extract(df, backend_expr, "result", backend_name)` with `collect_expr(df, expr)`
4. Remove `backend_name` from test signature if only used for extraction (keep if used for `backend_factory.create()` or assertion messages)
5. Run tests for that file across all backends

**28 files to migrate from `select_and_extract` (~500 calls), 5 files unchanged (~88 calls).**
**2 files to migrate from `select_and_collect` (~44 calls).**
**4 files to migrate from `get_column_values` (~64 calls).**

## Out of Scope

- Changes to the relations API (no new methods, no booleanizer support)
- Changes to the expressions `.compile()` API
- Migrating unit tests (only cross-backend tests use these fixtures)
- Refactoring `backend_factory` or test parametrization
- Changes to the egress layer itself
