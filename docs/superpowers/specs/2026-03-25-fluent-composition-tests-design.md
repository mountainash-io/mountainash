# Fluent Composition Test Suite Design

**Date:** 2026-03-25
**Status:** Approved
**Branch:** feature/substrait_alignment

## Problem

The mountainash-expressions package has 11,000+ lines of tests, but coverage of API builders sits at 0-51% for many files. The existing cross-backend tests are operationally specific — they test individual operations (`.gt()`, `.str.upper()`, `.add()`) in isolation. What's missing are tests for **fluent composition**: how expressions chain, combine across namespaces, and compose into the patterns real users write.

Coverage gaps targeted by this spec:
- `api_bldr_scalar_string.py` — 47%
- `api_bldr_ext_ma_scalar_datetime.py` — 51%
- `api_bldr_scalar_rounding.py` — 48%
- `api_bldr_scalar_set.py` / `api_bldr_ext_ma_scalar_set.py` — 42-46%
- `api_bldr_ext_ma_null.py` — indirect coverage only

Not targeted (deferred to future work):
- `api_bldr_ext_ma_scalar_aggregate.py` — 0% (aggregate composition out of scope)
- `api_bldr_ext_ma_scalar_comparison.py` — 0% (`is_close` only; low priority)
- `api_bldr_ext_ma_scalar_string.py` — 0% (extension string builder; `.str` descriptor points to substrait builder)

## Design

### File Structure

10 new test files in `tests/cross_backend/`, each targeting a composition category:

| File | Category | ~Tests | Coverage Target |
|------|----------|--------|-----------------|
| `test_compose_string.py` | String namespace chains | 6 | `api_bldr_scalar_string.py` |
| `test_compose_datetime.py` | Datetime namespace chains | 5 | `api_bldr_ext_ma_scalar_datetime.py`, `api_bldr_scalar_datetime.py` |
| `test_compose_cross_namespace.py` | Cross-namespace composition | 7 | Multiple builders composed together |
| `test_compose_null.py` | Null handling in chains | 4 | `api_bldr_ext_ma_null.py` |
| `test_compose_conditional.py` | Conditional with expressions | 4 | `api_bldr_conditional.py` |
| `test_compose_entrypoints.py` | coalesce/greatest/least | 4 | `api_base.py` entrypoints |
| `test_compose_cast.py` | Cast in chains | 4 | `api_bldr_cast.py` |
| `test_compose_name.py` | Name ops in chains | 3 | `api_bldr_ext_ma_name.py` |
| `test_compose_ternary.py` | Ternary composition | 4 | `api_bldr_ext_ma_scalar_ternary.py` |
| `test_compose_set.py` | Set operations | 4 | `api_bldr_scalar_set.py`, `api_bldr_ext_ma_scalar_set.py` |

~48 tests total, all parametrized across 6 backends (polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite).

**Pandas note:** The pandas backend has limited implementation. Tests that fail on pandas should be xfailed with a clear message referencing the limitation. Expect most pandas failures in datetime, conditional, and entrypoint categories.

### Test Design Principles

1. **Realistic data** — columns with types that make sense for the operation. Not toy single-column datasets.

2. **Fluent chains of 2-3+ operations** — every test crosses at least one builder boundary. `col("x").gt(5)` is not a composition test. `col("x").add(5).gt(10).and_(col("y").str.contains("a"))` is.

3. **Assert on results, not AST** — compile, execute, and verify actual output matches expectations across all backends.

4. **Known xfails with clear reasons** — same pattern as existing tests. SQLite temporal limitations, Ibis-Polars interval gaps, etc. Each xfail states the backend limitation.

5. **Shared parametrize decorator** — all 6 backends on every test class.

6. **Inline test data** — each test creates its own data dict via `backend_factory.create(data, backend_name)`, same pattern as `test_expression_builder_api.py`. Uses existing conftest fixtures for extraction (`get_result_count`, `get_column_values`, `select_and_extract`) but no shared data fixtures.

### Test Categories Detail

#### 1. String Namespace Chains (`test_compose_string.py`)

Tests fluent `.str` method chaining:
- `col("name").str.lower().str.contains("john")` — case-insensitive search
- `col("name").str.replace("_", " ").str.upper()` — sequential transforms
- `col("name").str.trim().str.len().gt(3)` — string to numeric to boolean
- `~col("status").str.contains("archived")` — negation of string match
- `col("email").str.lower().str.ends_with("@gmail.com")` — real-world pattern
- `col("name").str.trim().str.lower().str.contains("admin")` — 3-deep chain

#### 2. Datetime Namespace Chains (`test_compose_datetime.py`)

Tests fluent `.dt` method chaining:
- `col("ts").dt.year().eq(2024)` — extract then compare
- `col("ts").dt.add_days(7).dt.month()` — arithmetic then extract
- `col("ts").dt.year().gt(col("threshold"))` — extract then compare to column
- `col("ts").dt.hour().ge(9).and_(col("ts").dt.hour().lt(17))` — business hours filter
- `col("ts").dt.truncate("day").dt.weekday()` — truncate then extract

Known xfails: ibis-sqlite (sub-day temporal), ibis-polars (TimestampDelta, calendar intervals).

#### 3. Cross-Namespace Composition (`test_compose_cross_namespace.py`)

Tests combining different namespaces in one expression:
- `col("name").str.len().gt(3).and_(col("score").ge(80))` — string + comparison
- `col("name").str.upper().eq(lit("ADMIN")).or_(col("age").gt(30))` — string + boolean
- `col("ts").dt.year().eq(2024).and_(col("status").str.lower().eq(lit("active")))` — datetime + string
- `(col("price") * col("qty")).gt(1000).and_(col("name").str.contains("premium"))` — arithmetic + string
- `col("value").fill_null(0).gt(col("threshold")).and_(col("label").str.len().gt(0))` — null + comparison + string
- `col("price").multiply(lit(1.07)).round(2).gt(lit(100.0))` — arithmetic + rounding + comparison
- `col("score").between(col("min_score"), col("max_score")).and_(col("active").eq(True))` — between + boolean

#### 4. Null Handling in Chains (`test_compose_null.py`)

Tests null operations composed with other builders:
- `col("price").fill_null(0) + col("tax")` — fill then arithmetic
- `col("value").fill_null(lit(0)).multiply(2).gt(100)` — fill → arithmetic → comparison
- `col("a").is_null().or_(col("b").lt(0))` — null check in boolean chain
- `col("a").fill_null(col("b")).fill_null(lit(0))` — cascading fill_null

#### 5. Conditional with Expressions (`test_compose_conditional.py`)

Tests when/then/otherwise with composed expressions:
- `when(col("score").ge(70)).then(col("name").str.upper()).otherwise(col("name"))` — conditional string transform
- `when(col("a").gt(0)).then(col("a") * 2).otherwise(lit(0))` — conditional arithmetic
- `when(col("x").is_null()).then(lit(-1)).otherwise(col("x"))` — null-handling conditional
- `when(col("a").gt(0).and_(col("b").gt(0))).then(col("a") + col("b")).otherwise(lit(0))` — composed condition

#### 6. Entrypoint Composition (`test_compose_entrypoints.py`)

Tests coalesce/greatest/least with chained expressions:
- `coalesce(col("phone").str.trim(), col("email"), lit("N/A"))` — coalesce with string transform
- `greatest(col("a") + 1, col("b") * 2)` — greatest with arithmetic
- `least(col("x"), col("y").fill_null(lit(999)))` — least with null handling
- `coalesce(col("a"), col("b")).gt(0)` — entrypoint then comparison

#### 7. Cast in Chains (`test_compose_cast.py`)

Tests cast operations composed with other operations:
- `col("value").cast(float).divide(col("total"))` — cast then arithmetic
- `col("count").cast(str).str.contains("5")` — cast to string then string ops
- `col("score").cast(int).gt(70)` — cast then comparison
- `col("price").fill_null(0).cast(float).multiply(col("rate"))` — null → cast → arithmetic

#### 8. Name Operations in Chains (`test_compose_name.py`)

Tests `.name` accessor in composed expressions:
- `(col("a") + col("b")).name.alias("sum")` — arithmetic then alias
- `col("name").str.upper().name.suffix("_clean")` — string transform then suffix
- `col("value").fill_null(0).name.prefix("filled_")` — null handling then prefix

#### 9. Ternary Composition (`test_compose_ternary.py`)

Tests ternary expressions with composed operands:
- `col("score").t_gt(col("threshold").fill_null(lit(0)))` — ternary with null-safe operand
- `col("a").t_eq(lit(1)).t_and(col("b").t_gt(lit(0)))` — ternary logical chain
- `t_col("value", unknown={-999}).t_gt(lit(50)).t_and(col("active").t_eq(lit(True)))` — t_col with chained ternary
- Compile with different booleanizers: `is_true` vs `maybe_true`

#### 10. Set Operations (`test_compose_set.py`)

Tests is_in/is_not_in in composed expressions:
- `col("status").is_in(["active", "pending"]).and_(col("score").gt(50))` — set + comparison
- `col("category").is_not_in(["archived", "deleted"])` — basic exclusion
- `col("name").str.lower().is_in(["admin", "root"])` — string transform then set
- `col("value").is_in([1, 2, 3]).or_(col("value").is_null())` — set + null check

## Out of Scope

- AST-level unit tests (verifying node structure without backends)
- Window function composition (not yet fully implemented)
- Aggregate function composition (limited backend support)
- New fixtures or test infrastructure changes
- Performance benchmarks
