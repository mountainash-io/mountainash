# Design: mountainash.datacontracts v2 — Native Integration

**Date:** 2026-05-01
**Status:** Approved
**Scope:** Make datacontracts relation-centric, add composable constraints/expressions libraries, convert result processor to expression-based internals

## Goals

1. Replace polars/pandas-centric internals with mountainash Relations
2. Add a reusable constraints library (`FieldConstraints` constants + combinators)
3. Add a reusable expression combinators library for common rule patterns
4. Convert `ValidationResultProcessor` from raw polars to mountainash expressions

## Non-Goals

- DQ dashboard profiling pipeline (separate spec)
- Changing the public API surface (Validator, Rule, RuleRegistry stay the same)
- Replacing pandera (it remains the validation engine)

## Changes

### 1. Relation-Centric Validator

`Validator` wraps input in `ma.relation()` internally, then extracts a polars DataFrame for pandera validation. The interface speaks Relations; pandera's polars requirement is an implementation detail.

```python
class Validator:
    def validate(self, data, *, context=None, **kwargs):
        prepared = self._prepare_data(data)
        rel = ma.relation(prepared)
        df = rel.collect()
        # ephemeral contract + pandera validation as before
```

`prepare` callables return anything `ma.relation()` can wrap. When pandera adds backend support, only `collect("polars")` changes.

**Files changed:** `validator.py`

### 2. Composable Constraints Library

New module: `mountainash.datacontracts.constraints`

Pre-defined `FieldConstraints` constants for common patterns:

```python
from dataclasses import replace
from mountainash.typespec.spec import FieldConstraints

# String patterns
SINGLE_CHAR = FieldConstraints(min_length=1, max_length=1)
ISO_DATE = FieldConstraints(min_length=10, max_length=10, pattern=r"\d{4}-\d{2}-\d{2}")
ISO_DATETIME = FieldConstraints(min_length=19, max_length=19, pattern=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

# Numeric
POSITIVE_INT = FieldConstraints(required=True, minimum=0)
PERCENTAGE = FieldConstraints(minimum=0, maximum=100)

# Combinators
def required(base: FieldConstraints) -> FieldConstraints:
    """Return a copy with required=True."""
    return replace(base, required=True)

def with_enum(base: FieldConstraints, values: list) -> FieldConstraints:
    """Return a copy with enum values added."""
    return replace(base, enum=values)

def with_range(base: FieldConstraints, *, minimum=None, maximum=None) -> FieldConstraints:
    """Return a copy with numeric range."""
    return replace(base, minimum=minimum, maximum=maximum)
```

Clients build domain-specific constants on top:

```python
ACRDS_BATCH_ID = FieldConstraints(min_length=10, max_length=20)
ACRDS_YES_NO = with_enum(SINGLE_CHAR, ["Y", "N"])
ACRDS_RECORD_ID = FieldConstraints(required=True, minimum=0, maximum=99999999)
```

**Files created:** `constraints.py`

### 3. Composable Expression Combinators

New module: `mountainash.datacontracts.expressions`

Library of functions returning `BaseExpressionAPI`:

```python
import mountainash as ma
from mountainash.expressions import BaseExpressionAPI
from functools import reduce
import operator
from typing import Any

# Null patterns
def any_not_null(*cols: str) -> BaseExpressionAPI:
    return reduce(operator.or_, (ma.col(c).is_not_null() for c in cols))

def all_not_null(*cols: str) -> BaseExpressionAPI:
    return reduce(operator.and_, (ma.col(c).is_not_null() for c in cols))

def any_null(*cols: str) -> BaseExpressionAPI:
    return reduce(operator.or_, (ma.col(c).is_null() for c in cols))

def all_null(*cols: str) -> BaseExpressionAPI:
    return reduce(operator.and_, (ma.col(c).is_null() for c in cols))

# Value patterns
def col_equals(col: str, value: Any) -> BaseExpressionAPI:
    return ma.col(col).eq(ma.lit(value))

def col_not_equals(col: str, value: Any) -> BaseExpressionAPI:
    return ma.col(col).ne(ma.lit(value))

def col_in(col: str, values: list) -> BaseExpressionAPI:
    return ma.col(col).is_in(values)

# Cross-column patterns
def col_le_col(col_a: str, col_b: str) -> BaseExpressionAPI:
    return ma.col(col_a).le(ma.col(col_b))

def col_ge_col(col_a: str, col_b: str) -> BaseExpressionAPI:
    return ma.col(col_a).ge(ma.col(col_b))
```

These are pure functions returning expressions. Client-side named constants provide local reuse:

```python
from mountainash.datacontracts.expressions import any_not_null, all_null

REMOVE_FLAGS_SET = any_not_null("remove_account", "remove_rhi_fhi", "remove_default", "remove_account_holders")
ALL_REMOVE_FLAGS_CLEAR = all_null("remove_account", "remove_rhi_fhi", "remove_default", "remove_account_holders")

VR20 = Rule("VR20", expr=guarded(precondition=REMOVE_FLAGS_SET, test=ma.col("date_corrected").is_not_null()))
```

**Files created:** `expressions.py`

### 4. Expression-Based Result Processor

`ValidationResultProcessor` currently uses raw polars expressions (`pl.col(...)`, `.filter()`, `.group_by()`). In v2, these become mountainash expressions compiled via the relation layer:

```python
class ValidationResultProcessor:
    def __init__(self, failure_cases: pl.DataFrame) -> None:
        self._failure_cases = failure_cases
        self._rel = ma.relation(failure_cases)

    def failure_cases(self) -> pl.DataFrame:
        return self._failure_cases

    def failure_cases_for_column(self, column: str) -> pl.DataFrame:
        return (self._rel
            .filter(
                ma.col("schema_context").eq(ma.lit("Column"))
                & ma.col("column").eq(ma.lit(column))
            )
            .collect())

    def failure_cases_for_rule(self, rule_id: str) -> pl.DataFrame:
        return (self._rel
            .filter(
                ma.col("schema_context").eq(ma.lit("DataFrameSchema"))
                & ma.col("check").eq(ma.lit(rule_id))
            )
            .collect())

    def failure_count(self) -> int:
        return len(self._failure_cases)

    def failure_count_by_column(self) -> pl.DataFrame:
        return (self._rel
            .filter(ma.col("schema_context").eq(ma.lit("Column")))
            .group_by("column")
            .agg(ma.count_records().alias("count"))
            .collect())

    def failure_count_by_rule(self) -> pl.DataFrame:
        return (self._rel
            .filter(ma.col("schema_context").eq(ma.lit("DataFrameSchema")))
            .group_by("check")
            .agg(ma.count_records().alias("count"))
            .collect())

    def passed(self) -> bool:
        return len(self._failure_cases) == 0

    def passed_for_column(self, column: str) -> bool:
        return len(self.failure_cases_for_column(column)) == 0

    def passed_for_rule(self, rule_id: str) -> bool:
        return len(self.failure_cases_for_rule(rule_id)) == 0
```

Same API surface. Internal logic is backend-agnostic. If failure cases come from a database (DQ dashboard scenario), the processor works unchanged.

**Files changed:** `result_processor.py`

## Package Structure

```
mountainash/src/mountainash/datacontracts/
├── __init__.py              # Updated exports (add constraints, expressions)
├── contract.py              # Unchanged
├── compiler.py              # Unchanged
├── constraints.py           # NEW: reusable FieldConstraints constants + combinators
├── expressions.py           # NEW: reusable expression combinators
├── rule.py                  # Unchanged (guarded stays here)
├── registry.py              # Unchanged
├── validator.py             # CHANGED: relation-centric internals
├── result.py                # Unchanged
└── result_processor.py      # CHANGED: expression-based internals
```

## Testing

- `test_constraints.py` — constraint constants produce correct FieldConstraints, combinators compose correctly
- `test_expressions.py` — each combinator evaluates correctly against sample DataFrames
- `test_result_processor.py` — existing tests pass unchanged (API surface didn't change)
- `test_validator.py` — existing tests pass unchanged (API surface didn't change)

## Dependencies

No new dependencies. Uses existing mountainash Relations and expressions.
