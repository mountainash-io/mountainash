# Phase 2: Port Dataframes to Unified Package — Design Spec

## Goal

Port `mountainash-dataframes` into `mountainash.dataframes` within the unified `mountainash` package, preserving all existing functionality and adding expression integration to `TableBuilder.filter()`.

## Context

### Phase 1 Complete

The unified `mountainash` package now exists:
- `src/mountainash/core/` — shared constants and types
- `src/mountainash/expressions/` — column-level ops (mature, 2842+ tests)
- `src/mountainash/dataframes/__init__.py` — stub that raises ImportError
- `src/mountainash_expressions/` — backwards-compat shim with import hook

### mountainash-dataframes Current State

The existing `mountainash-dataframes` project at `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-dataframes/` is production-ready but stale (last commit Nov 2025):

- **28 operations** fully implemented across all 3 backends (Polars, Ibis, Narwhals)
- **7 protocol categories:** Cast, Introspect, Select, Join, Filter, Row, Lazy
- **TableBuilder fluent API** with 6 namespaces (select, filter, join, row, cast, lazy)
- **DataFrameUtils** high-level API
- **59 test files, ~25,400 lines**
- No stubs or NotImplementedError anywhere

### Key Decision: Port As-Is

The dataframes code works. This phase ports it into the unified package with minimal changes. Architectural alignment (Substrait naming, wiring audit, file prefix conventions) is deferred to a later phase.

## What Gets Ported

### Source Code

The new-architecture code from `mountainash-dataframes` moves into `src/mountainash/dataframes/`:

```
src/mountainash/dataframes/
├── __init__.py                          # Exports: table, TableBuilder, DataFrameUtils, from_*
├── core/
│   ├── __init__.py
│   ├── constants.py                     # Dataframes-specific constants (imports CONST_BACKEND from mountainash.core)
│   ├── dataframe_system/
│   │   ├── __init__.py
│   │   ├── base.py                      # DataFrameSystem abstract base (inherits 7 protocols)
│   │   ├── constants.py                 # CONST_DATAFRAME_BACKEND enum
│   │   └── factory.py                   # DataFrameSystemFactory + @register_dataframe_system
│   ├── operations/
│   │   ├── __init__.py
│   │   ├── context.py                   # Operation context
│   │   ├── detection.py                 # DataFrame type detection (3-tier)
│   │   └── resolver.py                  # Operation resolver
│   ├── protocols/
│   │   ├── __init__.py                  # Re-exports all protocols
│   │   └── builder_protocols.py         # Select, Filter, Join, Row, Cast, Lazy protocols
│   ├── table_builder/
│   │   ├── __init__.py
│   │   ├── base.py                      # BaseTableBuilder + BaseNamespace + NamespaceDescriptor
│   │   ├── table_builder.py             # TableBuilder class + entry points (table, from_*)
│   │   └── namespaces/
│   │       ├── __init__.py
│   │       ├── select.py
│   │       ├── filter.py                # Modified: expression integration
│   │       ├── join.py
│   │       ├── row.py
│   │       ├── cast.py
│   │       └── lazy.py
│   ├── typing/
│   │   ├── __init__.py
│   │   ├── dataframes.py               # SupportedDataFrames (imports from mountainash.core.types)
│   │   ├── expressions.py
│   │   ├── python_data.py
│   │   └── series.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── dataframe_utils.py           # DataFrameUtils high-level API
│   ├── conversion/
│   │   └── series/                      # Series conversion utilities
│   │       ├── __init__.py
│   │       ├── backends.py
│   │       └── converter.py
│   └── utils/
│       └── expression_compiler/         # Expression compiler utility
│           ├── __init__.py
│           └── compiler.py
└── backends/
    ├── __init__.py
    ├── polars/
    │   ├── __init__.py
    │   └── dataframe_system.py          # 307 lines, all ops implemented
    ├── ibis/
    │   ├── __init__.py
    │   └── dataframe_system.py          # 255 lines, all ops implemented
    └── narwhals/
        ├── __init__.py
        └── dataframe_system.py          # 356 lines, all ops implemented
```

### What Changes During the Port

1. **Absolute imports rewritten:** `mountainash_dataframes.X` → `mountainash.dataframes.X` (same script approach as Phase 1)
2. **Shared constants:** `CONST_DATAFRAME_BACKEND` stays in dataframes (it's dataframes-specific), but any references to backend detection types use `mountainash.core.constants` where applicable
3. **Shared types:** `SupportedDataFrames` type aliases reference `mountainash.core.types` where shared
4. **Expression integration:** `FilterNamespace.filter()` gains `BaseExpressionAPI` support
5. **Top-level exports:** `mountainash/__init__.py` gains `table`, `TableBuilder` exports

### What Does NOT Port

- `_deprecated/` directory from mountainash-dataframes
- Old factory infrastructure (`factories/`, `cast/`, `convert/`, `reshape/`, `filter_expressions/` modules — superseded by `core/` + `backends/`)
- `dataframe_utils.py` at root level (replaced by `core/api/dataframe_utils.py`)
- Old typing modules (`typing/` at root — replaced by `core/typing/`)

## Expression Integration

The key new feature: `TableBuilder.filter()` accepts mountainash expressions.

### Implementation

In `src/mountainash/dataframes/core/table_builder/namespaces/filter.py`:

```python
def filter(self, expression):
    """Filter DataFrame rows by expression.

    Args:
        expression: Native backend expression, callable, or BaseExpressionAPI.
            If a BaseExpressionAPI is provided, it is compiled against the
            current DataFrame automatically.
    """
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI

    if isinstance(expression, BaseExpressionAPI):
        expression = expression.compile(self._df)

    system = self._get_system()
    result = system.filter(self._df, expression)
    return self._build(result)
```

The same pattern applies to `where()` and `query()` (aliases for `filter`).

### Why Lazy Import

`from mountainash.expressions...` is a lazy import inside the method body to avoid circular dependencies. The dataframes module can be imported without expressions being fully initialized.

## Public API

### Top-Level Exports

`mountainash/__init__.py` gains:

```python
# Dataframes (requires [dataframes] - but currently always available)
from mountainash.dataframes import table, TableBuilder  # noqa: F401
```

These imports are wrapped in a try/except so that if dataframes is eventually made optional, the top-level import doesn't break:

```python
try:
    from mountainash.dataframes import table, TableBuilder  # noqa: F401
except ImportError:
    pass  # dataframes not installed
```

### Namespace Exports

`mountainash.dataframes.__init__.py`:

```python
from mountainash.dataframes.core.table_builder.table_builder import (
    table, TableBuilder,
    from_polars, from_pandas, from_pyarrow, from_ibis,
    from_dict, from_records,
)
from mountainash.dataframes.core.api.dataframe_utils import DataFrameUtils
```

### Usage

```python
import mountainash as ma

# Build and filter in one pipeline
result = (
    ma.table(df)
    .select("id", "name", "age")
    .filter(ma.col("age").gt(30))
    .head(10)
    .to_pandas()
)

# Also available via explicit import
from mountainash.dataframes import table, TableBuilder, DataFrameUtils
```

## Test Strategy

### Ported Tests

The 59 existing test files are ported into `tests/dataframes/`, flattened from the deep nesting in the original project:

```
tests/dataframes/
├── conftest.py                          # Dataframes-specific fixtures (ported from original)
├── test_cast.py                         # Backend conversions
├── test_join.py                         # Join operations
├── test_select.py                       # Select/rename/drop/reorder
├── test_filter.py                       # Filter operations
├── test_row.py                          # Head/tail/sample
├── test_introspect.py                   # Schema/shape/columns
├── test_lazy.py                         # Lazy/eager operations
├── test_table_builder.py                # Fluent API chaining
├── test_dataframe_utils.py              # High-level API
└── test_expression_integration.py       # NEW: filter with ma.col()
```

### New Expression Integration Tests

```python
# tests/dataframes/test_expression_integration.py

@pytest.mark.parametrize("backend_name", ["polars", "narwhals", "ibis-duckdb"])
def test_table_filter_with_expression(backend_name, backend_factory):
    """TableBuilder.filter() accepts a mountainash expression."""
    import mountainash as ma
    df = backend_factory({"age": [25, 35, 45], "name": ["a", "b", "c"]})
    result = ma.table(df).filter(ma.col("age").gt(30)).to_polars()
    assert result.shape[0] == 2

def test_table_filter_with_native_expression():
    """TableBuilder.filter() still accepts native expressions."""
    import polars as pl
    df = pl.DataFrame({"x": [1, 2, 3]})
    result = table(df).filter(pl.col("x") > 1).to_polars()
    assert result.shape[0] == 2
```

### Test Preservation

All existing expression tests continue to pass unchanged. The dataframes tests run in a separate `tests/dataframes/` directory.

## Scope Boundaries

**In scope:**
- Port dataframes source into `mountainash.dataframes`
- Rewrite imports (migration script)
- Expression integration in `TableBuilder.filter()`
- Top-level exports (`ma.table()`, `ma.TableBuilder`)
- Port and flatten tests
- New expression integration tests

**Out of scope:**
- Architectural alignment (Substrait naming, wiring audit, file prefixes)
- Extracting shared detection to `mountainash.core`
- Adding new operations (group_by, sort, agg, with_columns, pivot/melt)
- Backwards-compat shim for `mountainash_dataframes` package
- Modifying any existing expression code or tests
