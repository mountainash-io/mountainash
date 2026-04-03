# Unified Type Aliases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `mountainash/core/types.py` the single source of truth for all shared type aliases (DataFrame, expression, series), eliminating duplicates across `core/types.py` and `dataframes/core/typing/`.

**Architecture:** Merge the comprehensive type definitions from `dataframes/core/typing/dataframes.py` into `core/types.py`. Convert the dataframes typing submodules (`dataframes.py`, `expressions.py`, `series.py`) into thin re-export shims that import from core. The `dataframes/core/typing/__init__.py` public API is unchanged — consumers don't need to update imports.

**Tech Stack:** Python `typing`, `typing_extensions` (TypeAlias, TypeGuard), pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/mountainash/core/types.py` | Rewrite | Single source for all shared type aliases, runtime fallbacks, type guards, protocols |
| `src/mountainash/dataframes/core/typing/dataframes.py` | Rewrite | Re-export shim from core + dataframes-specific callable aliases |
| `src/mountainash/dataframes/core/typing/expressions.py` | Modify | Import type aliases from core, keep dataframes-specific guards |
| `src/mountainash/dataframes/core/typing/series.py` | Modify | Import type aliases from core, keep series guards |
| `tests/core/test_unified_types.py` | Create | Identity and smoke tests |

---

### Task 1: Rewrite core/types.py with all shared types

**Files:**
- Rewrite: `src/mountainash/core/types.py`

- [ ] **Step 1: Replace entire file with merged content**

Replace `src/mountainash/core/types.py` with the following. This merges the runtime fallback imports and type aliases from `dataframes/core/typing/dataframes.py` with the existing expression types, and adds DataFrame/series type guards:

```python
"""
Unified typing system for the mountainash package.

Single source of truth for all shared type aliases, runtime fallback imports,
type guards, and protocols used across expressions, dataframes, schema, and pydata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard
from collections.abc import Sequence, Mapping, Callable

if TYPE_CHECKING:
    import ibis as ibis
    import ibis.expr.types as ir
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import narwhals as nw
else:
    # Runtime fallback for optional imports
    # This enables runtime type introspection (e.g., Hamilton) while keeping dependencies optional
    import types

    # Pandas
    try:
        import pandas as pd
    except ImportError:
        pd = types.ModuleType('pandas')
        pd.DataFrame = Any
        pd.Series = Any

    # Polars
    try:
        import polars as pl
    except ImportError:
        pl = types.ModuleType('polars')
        pl.DataFrame = Any
        pl.LazyFrame = Any
        pl.Series = Any
        pl.Expr = Any

    # PyArrow
    try:
        import pyarrow as pa
    except ImportError:
        pa = types.ModuleType('pyarrow')
        pa.Table = Any
        pa.Array = Any

    # Ibis
    try:
        import ibis as ibis
        import ibis.expr.types as ir
    except ImportError:
        ibis = types.ModuleType('ibis')
        ibis.BaseBackend = Any
        ir = types.ModuleType('ibis.expr.types')
        ir.Table = Any
        ir.Expr = Any
        ir.Column = Any
        ir.Scalar = Any
        # Add to ibis module for ibis.expr.schema.Schema reference
        ibis.expr = types.ModuleType('ibis.expr')
        ibis.expr.schema = types.ModuleType('ibis.expr.schema')
        ibis.expr.schema.Schema = Any

    # Narwhals
    try:
        import narwhals as nw
    except ImportError:
        nw = types.ModuleType('narwhals')
        nw.DataFrame = Any
        nw.LazyFrame = Any
        nw.Series = Any
        nw.Expr = Any


# ============================================================================
# Type Aliases — DataFrames
# ============================================================================

PandasFrame: TypeAlias = pd.DataFrame
PolarsFrame: TypeAlias = pl.DataFrame
PolarsLazyFrame: TypeAlias = pl.LazyFrame
PyArrowTable: TypeAlias = pa.Table
IbisTable: TypeAlias = ir.Table
IbisBaseBackend: TypeAlias = ibis.BaseBackend
IbisSchema: TypeAlias = ibis.expr.schema.Schema
NarwhalsFrame: TypeAlias = nw.DataFrame
NarwhalsLazyFrame: TypeAlias = nw.LazyFrame

# ============================================================================
# Type Aliases — Expressions
# ============================================================================

PolarsExpr: TypeAlias = pl.Expr
IbisExpr: TypeAlias = Union[ir.Expr, ir.Column, ir.Scalar]
NarwhalsExpr: TypeAlias = nw.Expr

# ============================================================================
# Type Aliases — Series
# ============================================================================

PandasSeries: TypeAlias = pd.Series
PolarsSeries: TypeAlias = pl.Series
NarwhalsSeries: TypeAlias = nw.Series
PyArrowArray: TypeAlias = pa.Array

# ============================================================================
# Composite Type Unions
# ============================================================================

PolarsFrameTypes: TypeAlias = Union[PolarsFrame, PolarsLazyFrame]
NarwhalsFrameTypes: TypeAlias = Union[NarwhalsFrame, NarwhalsLazyFrame]

SupportedDataFrames: TypeAlias = Union[
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    NarwhalsFrame,
    NarwhalsLazyFrame,
]

SupportedExpressions: TypeAlias = Union[PolarsExpr, IbisExpr, NarwhalsExpr]

SupportedSeries: TypeAlias = Union[PandasSeries, PolarsSeries, NarwhalsSeries, PyArrowArray]

# ============================================================================
# Generic Type Variables
# ============================================================================

DataFrameT = TypeVar("DataFrameT", bound=SupportedDataFrames)
ExpressionT = TypeVar("ExpressionT", bound=SupportedExpressions)
SeriesT = TypeVar("SeriesT", bound=SupportedSeries)

# ============================================================================
# Protocols for Structural Typing
# ============================================================================

class DataFrameLike(Protocol):
    """Protocol for dataframe-like objects with common interface."""

    @property
    def shape(self) -> tuple[int, int]:
        """Return (n_rows, n_columns) tuple."""
        ...

    @property
    def columns(self) -> Sequence[str]:
        """Return column names."""
        ...

    def __len__(self) -> int:
        """Return number of rows."""
        ...

class LazyFrameLike(Protocol):
    """Protocol for lazy dataframe-like objects."""

    def collect(self) -> DataFrameLike:
        """Materialize the lazy frame."""
        ...

    @property
    def columns(self) -> Sequence[str]:
        """Return column names."""
        ...

class ExpressionLike(Protocol):
    """Protocol for expression-like objects."""

    def alias(self, name: str) -> ExpressionLike:
        """Rename the expression."""
        ...

# ============================================================================
# Column Type Mappings
# ============================================================================

ColumnTypes: TypeAlias = Union[type, str]

if TYPE_CHECKING:
    ColumnMapping: TypeAlias = Mapping[str, ColumnTypes]
else:
    ColumnMapping: TypeAlias = "Mapping[str, ColumnTypes]"

# ============================================================================
# Type Guards — DataFrame Detection
# ============================================================================

def is_pandas_dataframe(obj: Any) -> TypeGuard[PandasFrame]:
    """Type guard for pandas DataFrames."""
    return type(obj).__module__.startswith("pandas") and type(obj).__name__ == "DataFrame"

def is_polars_dataframe(obj: Any) -> TypeGuard[PolarsFrame]:
    """Type guard for polars DataFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "DataFrame"

def is_polars_lazyframe(obj: Any) -> TypeGuard[PolarsLazyFrame]:
    """Type guard for polars LazyFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "LazyFrame"

def is_pyarrow_table(obj: Any) -> TypeGuard[PyArrowTable]:
    """Type guard for PyArrow Tables."""
    return type(obj).__module__.startswith("pyarrow") and type(obj).__name__ == "Table"

def is_ibis_table(obj: Any) -> TypeGuard[IbisTable]:
    """Type guard for Ibis Tables."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_dataframe(obj: Any) -> TypeGuard[NarwhalsFrame]:
    """Type guard for Narwhals DataFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "DataFrame"

def is_narwhals_lazyframe(obj: Any) -> TypeGuard[NarwhalsLazyFrame]:
    """Type guard for Narwhals LazyFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "LazyFrame"

def is_supported_dataframe(obj: Any) -> TypeGuard[SupportedDataFrames]:
    """Type guard for any supported dataframe type."""
    return any([
        is_pandas_dataframe(obj),
        is_polars_dataframe(obj),
        is_polars_lazyframe(obj),
        is_pyarrow_table(obj),
        is_ibis_table(obj),
        is_narwhals_dataframe(obj),
        is_narwhals_lazyframe(obj),
    ])

def detect_dataframe_backend_type(obj: Any) -> str:
    """
    Detect the backend type of a dataframe object without importing libraries.

    Returns:
        Backend name: 'pandas', 'polars', 'pyarrow', 'ibis', 'narwhals'

    Raises:
        ValueError: If the object type is not recognized
    """
    if is_pandas_dataframe(obj):
        return "pandas"
    elif is_polars_dataframe(obj) or is_polars_lazyframe(obj):
        return "polars"
    elif is_pyarrow_table(obj):
        return "pyarrow"
    elif is_ibis_table(obj):
        return "ibis"
    elif is_narwhals_dataframe(obj) or is_narwhals_lazyframe(obj):
        return "narwhals"
    else:
        raise ValueError(f"Unknown dataframe type: {type(obj).__module__}.{type(obj).__name__}")

# ============================================================================
# Type Guards — Expression Detection
# ============================================================================

def is_polars_expression(obj: Any) -> TypeGuard[PolarsExpr]:
    """Type guard for polars Expressions."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "Expr"

def is_ibis_expression(obj: Any) -> TypeGuard[IbisExpr]:
    """Type guard for Ibis Expressions."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_expression(obj: Any) -> TypeGuard[NarwhalsExpr]:
    """Type guard for Narwhals Expressions."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "Expr"
```

- [ ] **Step 2: Run existing tests to check for import breakage**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: All previously passing tests still pass. The `expressions/types.py` shim (`from mountainash.core.types import *`) automatically picks up the new types.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/core/types.py
git commit -m "feat: expand core/types.py with all shared type aliases"
```

---

### Task 2: Rewrite dataframes/core/typing/dataframes.py as re-export shim

**Files:**
- Rewrite: `src/mountainash/dataframes/core/typing/dataframes.py`

- [ ] **Step 1: Replace entire file**

Replace `src/mountainash/dataframes/core/typing/dataframes.py` with:

```python
"""
DataFrame type aliases and detection utilities.

Type aliases and guards are imported from mountainash.core.types (single source of truth).
This module re-exports them and adds dataframes-specific callable type aliases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard
from collections.abc import Sequence, Mapping, Callable

# Re-export all shared types from core
from mountainash.core.types import (
    # Runtime modules (needed for callable type aliases below)
    pd, pl, pa, ir, ibis, nw,
    # DataFrame type aliases
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    IbisBaseBackend,
    IbisSchema,
    NarwhalsFrame,
    NarwhalsLazyFrame,
    # Expression type aliases
    PolarsExpr,
    IbisExpr,
    NarwhalsExpr,
    # Series type aliases
    PandasSeries,
    PolarsSeries,
    NarwhalsSeries,
    PyArrowArray,
    # Composite unions
    PolarsFrameTypes,
    NarwhalsFrameTypes,
    SupportedDataFrames,
    SupportedExpressions,
    SupportedSeries,
    # Type variables
    DataFrameT,
    ExpressionT,
    SeriesT,
    # Protocols
    DataFrameLike,
    LazyFrameLike,
    ExpressionLike,
    # Column types
    ColumnTypes,
    ColumnMapping,
    # DataFrame type guards
    is_pandas_dataframe,
    is_polars_dataframe,
    is_polars_lazyframe,
    is_pyarrow_table,
    is_ibis_table,
    is_narwhals_dataframe,
    is_narwhals_lazyframe,
    is_supported_dataframe,
    detect_dataframe_backend_type,
)


# ============================================================================
# Callable Type Aliases (dataframes-specific)
# ============================================================================

if TYPE_CHECKING:
    DataFrameTransform: TypeAlias = Callable[[DataFrameT], DataFrameT]
    ExpressionBuilder: TypeAlias = Callable[[str], ExpressionT]
    FilterPredicate: TypeAlias = Callable[[DataFrameT], DataFrameT]
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: All tests pass. The `dataframes/core/typing/__init__.py` imports from this file, and all its exports are preserved.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/dataframes/core/typing/dataframes.py
git commit -m "refactor: dataframes typing/dataframes.py re-exports from core"
```

---

### Task 3: Update dataframes/core/typing/expressions.py to import from core

**Files:**
- Modify: `src/mountainash/dataframes/core/typing/expressions.py`

- [ ] **Step 1: Replace the top section (imports, runtime fallbacks, type aliases, basic guards)**

Replace lines 1-107 (everything up to and including `is_ibis_expression`) with:

```python
"""
Expression type aliases and detection utilities.

Type aliases and basic guards are imported from mountainash.core.types.
This module adds dataframes-specific guards: is_mountainash_expression(),
is_native_expression(), is_supported_expression(), detect_expression_backend().
"""

from __future__ import annotations

from typing import Any
from typing_extensions import TypeAlias, TypeGuard

# Re-export type aliases and basic guards from core
from mountainash.core.types import (
    PolarsExpr,
    NarwhalsExpr,
    IbisExpr,
    SupportedExpressions,
    is_polars_expression,
    is_narwhals_expression,
)


# ============================================================================
# Ibis Expression Detection (more detailed than core version)
# ============================================================================

def is_ibis_expression(obj: Any) -> bool:
    """
    Check if object is an Ibis expression.

    Ibis has multiple expression types (Column, Scalar, etc.) so we check
    for common patterns rather than exact class name.
    """
    obj_type = type(obj)
    module = obj_type.__module__
    class_name = obj_type.__name__
    if module.startswith("ibis"):
        return "Column" in class_name or "Expr" in class_name or "Scalar" in class_name
    return False
```

Leave the rest of the file unchanged (lines 110-224: `is_mountainash_expression`, `is_native_expression`, `is_supported_expression`, `detect_expression_backend`, `__all__`).

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/dataframes/core/typing/expressions.py
git commit -m "refactor: expressions typing imports type aliases from core"
```

---

### Task 4: Update dataframes/core/typing/series.py to import from core

**Files:**
- Modify: `src/mountainash/dataframes/core/typing/series.py`

- [ ] **Step 1: Replace the top section (imports, runtime fallbacks, type aliases)**

Replace lines 1-64 (everything up to the type guards section) with:

```python
"""
Series type aliases and detection utilities.

Type aliases are imported from mountainash.core.types.
This module adds series-specific type guards and detection.
"""

from __future__ import annotations

from typing import Any
from typing_extensions import TypeGuard

# Re-export type aliases from core
from mountainash.core.types import (
    PolarsSeries,
    PandasSeries,
    NarwhalsSeries,
    PyArrowArray,
    SupportedSeries,
)
```

Leave the rest of the file unchanged (lines 67-215: all type guard functions and `__all__`).

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/dataframes/core/typing/series.py
git commit -m "refactor: series typing imports type aliases from core"
```

---

### Task 5: Write unification tests

**Files:**
- Create: `tests/core/test_unified_types.py`

- [ ] **Step 1: Write test file**

```python
"""Tests for unified type aliases in mountainash.core.types."""

import pytest

from mountainash.core.types import (
    # DataFrame types
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    NarwhalsFrame,
    NarwhalsLazyFrame,
    # Expression types
    PolarsExpr,
    IbisExpr,
    NarwhalsExpr,
    # Series types
    PandasSeries,
    PolarsSeries,
    NarwhalsSeries,
    PyArrowArray,
    # Unions
    SupportedDataFrames,
    SupportedExpressions,
    SupportedSeries,
    # Protocols
    DataFrameLike,
    LazyFrameLike,
    ExpressionLike,
    # Type guards
    is_polars_dataframe,
    is_pandas_dataframe,
    is_polars_expression,
    detect_dataframe_backend_type,
)


class TestCoreTypesImportable:
    """All shared types are importable from core."""

    def test_dataframe_types(self):
        assert PandasFrame is not None
        assert PolarsFrame is not None
        assert PolarsLazyFrame is not None
        assert PyArrowTable is not None
        assert IbisTable is not None
        assert NarwhalsFrame is not None
        assert NarwhalsLazyFrame is not None

    def test_expression_types(self):
        assert PolarsExpr is not None
        assert IbisExpr is not None
        assert NarwhalsExpr is not None

    def test_series_types(self):
        assert PandasSeries is not None
        assert PolarsSeries is not None
        assert NarwhalsSeries is not None
        assert PyArrowArray is not None

    def test_protocols(self):
        assert DataFrameLike is not None
        assert LazyFrameLike is not None
        assert ExpressionLike is not None

    def test_type_guards(self):
        assert callable(is_polars_dataframe)
        assert callable(is_pandas_dataframe)
        assert callable(is_polars_expression)
        assert callable(detect_dataframe_backend_type)


class TestShimIdentity:
    """Types from old import paths are identical to core types."""

    def test_dataframes_typing_polars_expr(self):
        from mountainash.dataframes.core.typing import PolarsExpr as df_PolarsExpr
        assert df_PolarsExpr is PolarsExpr

    def test_dataframes_typing_supported_dataframes(self):
        from mountainash.dataframes.core.typing import SupportedDataFrames as df_SD
        assert df_SD is SupportedDataFrames

    def test_dataframes_typing_supported_expressions(self):
        from mountainash.dataframes.core.typing import SupportedExpressions as df_SE
        assert df_SE is SupportedExpressions

    def test_dataframes_typing_polars_frame(self):
        from mountainash.dataframes.core.typing import PolarsFrame as df_PF
        assert df_PF is PolarsFrame

    def test_dataframes_typing_pandas_series(self):
        from mountainash.dataframes.core.typing import PandasSeries as df_PS
        assert df_PS is PandasSeries

    def test_expressions_types_polars_expr(self):
        from mountainash.expressions.types import PolarsExpr as expr_PolarsExpr
        assert expr_PolarsExpr is PolarsExpr

    def test_expressions_types_supported_expressions(self):
        from mountainash.expressions.types import SupportedExpressions as expr_SE
        assert expr_SE is SupportedExpressions


class TestTypeGuardsWithRealObjects:
    """Type guards work with actual backend objects."""

    def test_polars_dataframe_detection(self):
        import polars as pl
        df = pl.DataFrame({"a": [1, 2, 3]})
        assert is_polars_dataframe(df)
        assert not is_pandas_dataframe(df)

    def test_polars_expression_detection(self):
        import polars as pl
        expr = pl.col("a")
        assert is_polars_expression(expr)

    def test_detect_polars_backend(self):
        import polars as pl
        df = pl.DataFrame({"a": [1]})
        assert detect_dataframe_backend_type(df) == "polars"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/core/test_unified_types.py -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/core/test_unified_types.py
git commit -m "test: add unified type alias tests"
```

---

### Task 6: Full regression test

- [ ] **Step 1: Run the full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: 2965+ passed, 27 failed (pre-existing), 278 xfailed. Zero new failures.

- [ ] **Step 2: Commit any fixups if needed**

```bash
git add -A
git commit -m "test: verify unified type aliases — all tests pass"
```
