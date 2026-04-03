# Import Principles & TYPE_CHECKING Standardisation

## Goal

Establish clear, enforceable principles for how imports work across the mountainash-expressions codebase. Eliminate inconsistencies between four co-existing import mechanisms, fix duplicate imports, remove runtime stub machinery, and add linting rules to prevent regressions.

## Current State — Four Mechanisms, No Principles

The codebase currently uses four import mechanisms inconsistently:

1. **`lazy_loader.attach()`** — in `pydata/egress/__init__.py` and `pydata/ingress/__init__.py`. PEP 562-based lazy submodule loading.
2. **`core/lazy_imports.py`** — manual `importlib.import_module()` wrappers (`import_polars()`, `import_narwhals()`, etc.) for runtime access to optional backends.
3. **`core/types.py` runtime stubs** — ~40 lines of `try/except ImportError` creating `types.ModuleType` fake objects with `Any` attributes, so `TypeAlias` definitions evaluate at runtime when optional backends are missing.
4. **`if TYPE_CHECKING:` guards** — used in 159 files with no consistent rule about what goes under the guard vs unconditional.

**Problems:**
- Duplicate imports: some files import the same symbol both under `TYPE_CHECKING` and unconditionally (e.g., `egress_helpers.py` imports `TypeSpec` twice).
- Internal mountainash modules (always available) are inconsistently guarded.
- Optional backend type aliases resolve to `Any` at runtime, defeating runtime introspection.
- No rule about when to use which mechanism — developers guess.

## Design

### Import Classification — Four Categories

Every import falls into exactly one category with one correct pattern:

| Category | Example | Pattern |
|----------|---------|---------|
| **Standard library** | `typing`, `logging`, `datetime` | Unconditional top-level import |
| **Runtime import** | Any module whose functions/classes are called at runtime | Unconditional top-level import (or `lazy_imports` for optional backends) |
| **Annotation-only import** | Types used only in parameter/return annotations, TypeAlias, generic params | `if TYPE_CHECKING:` guard |
| **Package re-export** | `__init__.py` files exposing submodule contents | `lazy_loader.attach()` where beneficial |

**Decision rule:** If an import is *called, instantiated, or used as a value* at runtime → unconditional (or lazy_imports). If it appears *only in type annotations* → `TYPE_CHECKING` guard. No exceptions, no dual imports.

### Three Import Mechanisms — When to Use Each

#### Mechanism 1: `lazy_loader.attach()` — Package `__init__.py` only

For `__init__.py` files where eagerly importing all submodules would pull in heavy dependencies or many files. Defers actual import until attribute access.

```python
import lazy_loader
__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submod_attrs={"module_name": ["ClassName"], ...}
)
```

Not every `__init__.py` needs this. Simple packages with few lightweight modules can use plain imports.

#### Mechanism 2: `core/lazy_imports.py` — Runtime optional backends

For non-backend code that needs to call an optional library at runtime. Provides helpful error messages when dependencies are missing.

```python
from mountainash.core.lazy_imports import import_narwhals

def _to_pandas(cls, df):
    nw = import_narwhals()
    return nw.from_native(df).to_pandas()
```

#### Mechanism 3: `if TYPE_CHECKING:` — Annotation-only imports

For anything used only in type annotations. Requires `from __future__ import annotations` in the file.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames
    from mountainash.typespec.spec import TypeSpec
    import polars as pl
```

This applies to both optional backend types AND internal mountainash types when they're only used in annotations. Guarding annotation-only internal imports reduces coupling and prevents accidental circular imports.

### `core/types.py` Refactoring

The runtime stub machinery (`types.ModuleType` with `Any` attributes) is deleted. All optional-backend type aliases move under `TYPE_CHECKING`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Union, Protocol, Any, TypeVar
from typing_extensions import TypeAlias, TypeGuard

if TYPE_CHECKING:
    import ibis
    import ibis.expr.types as ir
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import narwhals as nw

    PandasFrame: TypeAlias = pd.DataFrame
    PolarsFrame: TypeAlias = pl.DataFrame
    PolarsLazyFrame: TypeAlias = pl.LazyFrame
    PyArrowTable: TypeAlias = pa.Table
    IbisTable: TypeAlias = ir.Table
    IbisBaseBackend: TypeAlias = ibis.BaseBackend
    NarwhalsFrame: TypeAlias = nw.DataFrame
    NarwhalsLazyFrame: TypeAlias = nw.LazyFrame

    PolarsExpr: TypeAlias = pl.Expr
    IbisExpr: TypeAlias = Union[ir.Expr, ir.Column, ir.Scalar]
    NarwhalsExpr: TypeAlias = nw.Expr

    PandasSeries: TypeAlias = pd.Series
    PolarsSeries: TypeAlias = pl.Series
    NarwhalsSeries: TypeAlias = nw.Series
    PyArrowArray: TypeAlias = pa.Array

    PolarsFrameTypes: TypeAlias = Union[PolarsFrame, PolarsLazyFrame]
    NarwhalsFrameTypes: TypeAlias = Union[NarwhalsFrame, NarwhalsLazyFrame]
    SupportedDataFrames: TypeAlias = Union[
        PandasFrame, PolarsFrame, PolarsLazyFrame,
        PyArrowTable, IbisTable, NarwhalsFrame, NarwhalsLazyFrame,
    ]
    SupportedExpressions: TypeAlias = Union[PolarsExpr, IbisExpr, NarwhalsExpr]
    SupportedSeries: TypeAlias = Union[PandasSeries, PolarsSeries, NarwhalsSeries, PyArrowArray]

    DataFrameT = TypeVar("DataFrameT", bound=SupportedDataFrames)
    ExpressionT = TypeVar("ExpressionT", bound=SupportedExpressions)
    SeriesT = TypeVar("SeriesT", bound=SupportedSeries)

    # Ibis domain-specific
    IbisNumericExpr: TypeAlias = ir.NumericValue
    IbisBooleanExpr: TypeAlias = ir.BooleanValue
    IbisStringExpr: TypeAlias = ir.StringValue
    IbisTemporalExpr: TypeAlias = Union[ir.TimestampValue, ir.DateValue, ir.TimeValue]
    IbisColumnExpr: TypeAlias = ir.Column
    IbisNumericColumnExpr: TypeAlias = ir.NumericColumn
    IbisBooleanColumnExpr: TypeAlias = ir.BooleanColumn
    IbisStringColumnExpr: TypeAlias = ir.StringColumn
    IbisValueExpr: TypeAlias = ir.Value
    IbisScalarExpr: TypeAlias = ir.Scalar
```

**What stays outside `TYPE_CHECKING`:**
- Structural `Protocol` classes (`DataFrameLike`, `LazyFrameLike`, `ExpressionLike`) — pure structural types with no backend dependency
- Type guard functions (`is_polars_dataframe()`, `detect_dataframe_backend_type()` etc.) — use string-based module/class name checks, not isinstance against aliases
- `ColumnTypes` and `ColumnMapping` aliases (use only stdlib types)

**Impact on consumers:**
- Annotations: use `from __future__ import annotations` (auto-quotes) or string-quote manually: `def foo(df: 'SupportedDataFrames')`
- Runtime type checking: use existing type guards, not `isinstance(df, PolarsFrame)`

### `from __future__ import annotations` Requirement

Every `.py` file under `src/mountainash/` that contains type annotations or `TYPE_CHECKING` guards must have `from __future__ import annotations` as its first import statement. Files that are purely re-export `__init__.py` (e.g., using only `lazy_loader.attach()`) are exempt.

All files will be swept and updated in this implementation. A ruff rule will enforce it going forward.

### Linting Enforcement

Add ruff rules to `pyproject.toml`:

```toml
[tool.ruff.lint]
select = [
    # ... existing rules ...
    "FA",    # flake8-future-annotations — enforces from __future__ import annotations
    "TC",    # flake8-type-checking — enforces annotation-only imports under TYPE_CHECKING
]

[tool.ruff.lint.per-file-ignores]
# Expression backend files legitimately import their backend eagerly for runtime use
"src/mountainash/expressions/backends/**" = ["TC001", "TC002"]
# Relation backend files — same
"src/mountainash/relations/backends/**" = ["TC001", "TC002"]
```

Rules:
- **FA100** — flags files using typing constructs without `from __future__ import annotations`
- **TC001** — flags application imports used only in annotations that should be under `TYPE_CHECKING`
- **TC002** — flags third-party imports used only in annotations that should be under `TYPE_CHECKING`
- **TC003** — flags stdlib imports used only in annotations that should be under `TYPE_CHECKING`

### Out of Scope

- **Expression/relation backend files' unconditional backend imports** — they legitimately import their backend eagerly for runtime use (class bases, native API calls)
- **Generic protocol binding pattern** (`Protocol[pl.Expr]` in class bases) — this is an architecture concern under `expression-type-generics.md`, not an import concern
- **`lazy_loader` usage in `__init__.py`** — already correct
- **`core/lazy_imports.py`** — already correct

### Principle Document

A new principle document will be created at:
`g.development-practices/import-conventions.md`

Status: **ENFORCED**

This codifies the four import categories, three mechanisms, and decision rule alongside the existing naming-conventions and testing-philosophy principles.

## Testing

- Full test suite must pass after `core/types.py` refactoring (verifies no runtime code depends on the type aliases)
- Ruff must pass with new FA + TC rules enabled
- Pyright must show no regressions (and should improve — real types instead of `Any` stubs)

## Implementation Order

1. Add ruff rules (FA, TC) to `pyproject.toml` — establishes the linting baseline
2. Sweep all source files: add `from __future__ import annotations` where missing
3. Refactor `core/types.py` — delete stubs, move aliases under TYPE_CHECKING
4. Fix duplicate imports and move annotation-only imports under TYPE_CHECKING (ruff TC violations guide this)
5. Write principle document
6. Run full test suite + pyright + ruff to verify
