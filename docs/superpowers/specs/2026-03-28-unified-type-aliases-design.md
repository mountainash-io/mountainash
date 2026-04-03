# Layer 2.4: Unified Type Aliases — Design Spec

## Goal

Eliminate duplicate type definitions between `core/types.py` and `dataframes/core/typing/`. Make `core/types.py` the single source of truth for all shared type aliases, runtime fallback imports, type guards, and protocols.

## Problem

Type aliases are defined in two places with significant overlap:

**`mountainash/core/types.py`** (~130 lines, expression-focused):
- Runtime fallback imports: polars, ibis, narwhals (no pandas, no pyarrow)
- Type aliases: `PolarsExpr`, `IbisExpr`, `NarwhalsExpr`, `SupportedExpressions`
- Type guards: `is_polars_expression()`, `is_ibis_expression()`, `is_narwhals_expression()`
- A broken `is_supported_dataframe()` that calls expression guards, not dataframe guards

**`mountainash/dataframes/core/typing/dataframes.py`** (~393 lines, comprehensive):
- Runtime fallback imports: ALL five backends (pandas, polars, pyarrow, ibis, narwhals)
- Type aliases: all DataFrame, expression, and series types
- Duplicates all three expression types from `core/types.py`
- Type guards for all DataFrame types
- TypeVars, Protocols (`DataFrameLike`, `LazyFrameLike`, `ExpressionLike`)

**`mountainash/dataframes/core/typing/expressions.py`** (~225 lines):
- Duplicates runtime fallback imports for polars, narwhals, ibis
- Duplicates `PolarsExpr`, `NarwhalsExpr`, `IbisExpr`, `SupportedExpressions`
- Duplicates `is_polars_expression()`, `is_narwhals_expression()`, `is_ibis_expression()`
- Adds dataframes-specific: `is_mountainash_expression()`, `is_native_expression()`, `is_supported_expression()`, `detect_expression_backend()`

**`mountainash/dataframes/core/typing/series.py`** (~216 lines):
- Own runtime fallback imports
- Series types and guards

**Result:** Runtime fallback imports for polars appear in 3 files. Expression type aliases defined in 3 files. Expression type guards in 3 files.

## Solution

### Expand `mountainash/core/types.py` to be the single source

Merge content from `dataframes/core/typing/dataframes.py` into `core/types.py`. The merged file (~400 lines) contains:

**Runtime fallback imports** (unified, no duplicates):
- pandas: `pd.DataFrame`, `pd.Series`
- polars: `pl.DataFrame`, `pl.LazyFrame`, `pl.Series`, `pl.Expr`
- pyarrow: `pa.Table`, `pa.Array`
- ibis: `ir.Table`, `ir.Expr`, `ir.Column`, `ir.Scalar`, `ibis.BaseBackend`, `ibis.expr.schema.Schema`
- narwhals: `nw.DataFrame`, `nw.LazyFrame`, `nw.Series`, `nw.Expr`

**Type aliases:**
- DataFrame: `PandasFrame`, `PolarsFrame`, `PolarsLazyFrame`, `PyArrowTable`, `IbisTable`, `NarwhalsFrame`, `NarwhalsLazyFrame`, `IbisBaseBackend`, `IbisSchema`
- Expression: `PolarsExpr`, `IbisExpr`, `NarwhalsExpr`
- Series: `PandasSeries`, `PolarsSeries`, `NarwhalsSeries`, `PyArrowArray`

**Union types:**
- `PolarsFrameTypes`, `NarwhalsFrameTypes`
- `SupportedDataFrames`, `SupportedExpressions`, `SupportedSeries`

**TypeVars:**
- `DataFrameT`, `ExpressionT`, `SeriesT`

**Protocols:**
- `DataFrameLike`, `LazyFrameLike`, `ExpressionLike`

**Type guards (DataFrame only):**
- `is_pandas_dataframe()`, `is_polars_dataframe()`, `is_polars_lazyframe()`, `is_pyarrow_table()`, `is_ibis_table()`, `is_narwhals_dataframe()`, `is_narwhals_lazyframe()`
- `is_supported_dataframe()`, `detect_dataframe_backend_type()`

**Type guards (Expression — basic):**
- `is_polars_expression()`, `is_ibis_expression()`, `is_narwhals_expression()`

**Column types:**
- `ColumnTypes`, `ColumnMapping`

### What stays in `dataframes/core/typing/`

These files have dataframes-specific logic that doesn't belong in core:

- **`expressions.py`** — `is_mountainash_expression()` (depends on mountainash expression API), `is_native_expression()`, `is_supported_expression()`, `detect_expression_backend()`. Rewrites its type aliases and basic guards as imports from `core/types.py`.
- **`series.py`** — Series type guards. Rewrites its type aliases as imports from `core/types.py`.
- **`python_data.py`** — Python data type aliases. No changes needed (no overlap with core).
- **`dataframes.py`** — Becomes a re-export shim from `core/types.py` plus keeps `DataFrameTransform`, `ExpressionBuilder`, `FilterPredicate` callable aliases and the commented-out factory type vars.

### `dataframes/core/typing/__init__.py`

Unchanged public API — still re-exports everything from its submodules. Since those submodules now import from core, all types are ultimately sourced from `core/types.py`.

### `expressions/types.py`

Already a shim (`from mountainash.core.types import *`). No changes needed — it will automatically pick up the new types.

### Broken import: `schema/schema_utils.py`

Imports `from .typing import SupportedDataFrames, ...` but `schema/typing.py` doesn't exist. This file is dead code (nothing imports it). Leave as-is per decision.

## Files Changed

| File | Action |
|------|--------|
| `src/mountainash/core/types.py` | Rewrite — merge in DataFrame/series types, guards, protocols from dataframes |
| `src/mountainash/dataframes/core/typing/dataframes.py` | Rewrite — re-export shim from core + keep callable aliases |
| `src/mountainash/dataframes/core/typing/expressions.py` | Modify — import type aliases from core, keep dataframes-specific guards |
| `src/mountainash/dataframes/core/typing/series.py` | Modify — import type aliases from core, keep series guards |
| `src/mountainash/dataframes/core/typing/__init__.py` | No change (API unchanged) |
| `src/mountainash/dataframes/core/typing/python_data.py` | No change |
| `src/mountainash/expressions/types.py` | No change (already a shim) |
| `tests/core/test_unified_types.py` | Create — identity and regression tests |

## Tests

### New tests (`tests/core/test_unified_types.py`)

1. All type aliases importable from `mountainash.core.types`
2. `SupportedDataFrames` is a Union of 7 types
3. `SupportedExpressions` is a Union of 3 types
4. `SupportedSeries` is a Union of 4 types
5. Identity: `from mountainash.dataframes.core.typing import PolarsExpr` is same as `from mountainash.core.types import PolarsExpr`
6. Identity: `from mountainash.dataframes.core.typing import SupportedDataFrames` is same as `from mountainash.core.types import SupportedDataFrames`
7. `from mountainash.expressions.types import PolarsExpr` is same as `from mountainash.core.types import PolarsExpr`

### Regression

All 2965 existing tests pass. No logic changes — only source-of-truth relocation.

## Scope

**In scope:**
- Merge shared type aliases into `core/types.py`
- Make dataframes typing submodules import from core
- Add identity tests

**Out of scope:**
- Fixing `schema/schema_utils.py` broken `.typing` import (dead code, leave for Layer 4.4)
- Renaming `core/types.py` to `core/typing.py` (unnecessary churn)
- Moving `python_data.py` types to core (pydata-specific, not shared)
