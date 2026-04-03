# Type Alias Consistency: Use Type Guards and Aliases

**Date:** 2026-04-01
**Status:** Draft
**Scope:** `relations/`, `expressions/`, `pydata/`, `schema/` (excludes deprecated `dataframes/`)

## Problem

`mountainash.core.types` defines a comprehensive type alias and type guard system — `PandasFrame`, `PolarsLazyFrame`, `is_polars_dataframe()`, etc. — but ~15 places in the active codebase bypass these, using direct `isinstance(df, pl.LazyFrame)` checks and `pl.LazyFrame` annotations instead.

This causes:
- Inconsistent import patterns (some files import `polars` just for type checks)
- Missed benefit of string-based type guards that work without importing the library
- Harder grep-ability for "where do we check for Polars types?"

## Rules

1. **isinstance checks** → replace with type guards from `mountainash.core.types`
2. **Parameter/return type annotations** → replace with aliases from `mountainash.core.types`
3. **Constructor calls** (`pl.DataFrame(value)`) → keep as-is, these need the real constructor
4. **Docstrings** → leave as-is (lower priority, not functional)

## Files to Modify

### 1. `relations/core/unified_visitor/relation_visitor.py` (6 violations)

Lines 151-169: `_coerce_to_target_backend()` method.

**Before:**
```python
import polars as pl
if isinstance(target, (pl.DataFrame, pl.LazyFrame)):
    if isinstance(value, (pl.DataFrame, pl.LazyFrame)):
        return value.lazy() if isinstance(value, pl.DataFrame) else value
    import pandas as pd
    if isinstance(value, pd.DataFrame):
        return pl.from_pandas(value).lazy()
    import pyarrow as pa
    if isinstance(value, pa.Table):
        return pl.from_arrow(value).lazy()
```

**After:**
```python
from mountainash.core.types import (
    is_polars_dataframe, is_polars_lazyframe,
    is_pandas_dataframe, is_pyarrow_table,
)
if is_polars_dataframe(target) or is_polars_lazyframe(target):
    if is_polars_lazyframe(value):
        return value
    if is_polars_dataframe(value):
        return value.lazy()
    if is_pandas_dataframe(value):
        import polars as pl
        return pl.from_pandas(value).lazy()
    if is_pyarrow_table(value):
        import polars as pl
        return pl.from_arrow(value).lazy()
```

Note: `import polars as pl` is still needed for `pl.from_pandas()`, `pl.from_arrow()`, and `pl.DataFrame()` constructor calls — but only in the branches that actually use them, not for the isinstance checks.

### 2. `relations/backends/relation_systems/polars/substrait/relsys_pl_read.py` (3 violations)

**Before:**
```python
import polars as pl

class SubstraitPolarsReadRelationSystem:
    def read(self, dataframe: Any, /) -> pl.LazyFrame:
        if isinstance(dataframe, pl.LazyFrame):
            return dataframe
        if isinstance(dataframe, pl.DataFrame):
            return dataframe.lazy()
```

**After:**
```python
from mountainash.core.types import (
    PolarsLazyFrame, is_polars_lazyframe, is_polars_dataframe,
)

class SubstraitPolarsReadRelationSystem:
    def read(self, dataframe: Any, /) -> PolarsLazyFrame:
        if is_polars_lazyframe(dataframe):
            return dataframe
        if is_polars_dataframe(dataframe):
            return dataframe.lazy()
```

### 3. `relations/core/relation_api/relation.py` (2 violations)

Lines 389-393 in `to_polars()`:

**Before:**
```python
import polars as pl
result = self._compile_and_execute()
if isinstance(result, pl.DataFrame):
    return result
if isinstance(result, pl.LazyFrame):
    return result.collect()
```

**After:**
```python
from mountainash.core.types import is_polars_dataframe, is_polars_lazyframe
result = self._compile_and_execute()
if is_polars_dataframe(result):
    return result
if is_polars_lazyframe(result):
    return result.collect()
```

Note: `import polars as pl` still needed later for `pl.from_pandas()` fallback.

### 4. `pydata/ingress/custom_type_helpers.py` (1 violation)

Line 244:

**Before:**
```python
was_native = not isinstance(df, (nw.DataFrame, nw.LazyFrame))
```

**After:**
```python
from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe
was_native = not (is_narwhals_dataframe(df) or is_narwhals_lazyframe(df))
```

### 5. `schema/transform/cast_schema_narwhals.py` (1 violation)

Line 58:

**Before:**
```python
nw_df = nw.from_native(df) if not isinstance(df, (nw.DataFrame, nw.LazyFrame)) else df
```

**After:**
```python
from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe
nw_df = nw.from_native(df) if not (is_narwhals_dataframe(df) or is_narwhals_lazyframe(df)) else df
```

### 6. `expressions/backends/expression_systems/narwhals/base.py` (1 violation)

Line 70: `pd.DataFrame({"_": [0]})` — constructor call. Keep as-is per rule 3.

**No change needed.** The `import pandas as pd` + `pd.DataFrame()` constructor is functional, not a type check.

## Verification

1. `hatch run test:test-quick` — full test suite passes
2. `hatch run ruff:check` — no new violations introduced
3. Grep for remaining direct isinstance checks in scope:
   ```bash
   grep -rn 'isinstance.*\(pl\.\|pd\.\|pa\.\|nw\.\|ibis\.' src/mountainash/{relations,expressions,pydata,schema}/
   ```
