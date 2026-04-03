# Import Principles Standardisation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish consistent import conventions across the codebase — add ruff linting rules, sweep `from __future__ import annotations` into all files, refactor `core/types.py` to eliminate runtime stubs, fix duplicate imports, and write the principle document.

**Architecture:** Four import categories (stdlib, runtime, annotation-only, package re-export) enforced by ruff's FA and TCH rules. `core/types.py` moves all optional-backend type aliases under `TYPE_CHECKING`, deleting ~55 lines of runtime stub machinery. Type guards remain the runtime type-checking mechanism.

**Tech Stack:** ruff 0.3.7 (FA100, TCH001-005 rules), Python `from __future__ import annotations`, `lazy_loader`

---

## Pre-Implementation Baseline

Current ruff state (run `hatch -e ruff run ruff check ./src`): **42 errors** (all F-rules: F401, F811, F821, E402).

FA100 violations: **8** (files missing future annotations that use typing constructs).

TCH violations: **76** (imports that should move in/out of TYPE_CHECKING). Many are false positives for Pydantic model files and backend files — per-file-ignores will handle these.

---

### Task 1: Add ruff FA + TCH rules to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

This task adds ruff configuration with the new rules and per-file-ignores for legitimate exceptions. Currently there is NO `[tool.ruff]` section — only a hatch environment pinning ruff 0.3.7.

- [ ] **Step 1: Add ruff configuration to pyproject.toml**

Add this section after the existing `[tool.coverage.report]` section:

```toml
# ============================================================================
# Ruff Configuration
# ============================================================================

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "FA",     # flake8-future-annotations
    "TCH",    # flake8-type-checking
]

[tool.ruff.lint.per-file-ignores]
# __init__.py files re-export symbols intentionally
"__init__.py" = ["F401"]
# Expression backend files legitimately import their backend eagerly
"src/mountainash/expressions/backends/**" = ["TCH001", "TCH002"]
# Relation backend files legitimately import their backend eagerly
"src/mountainash/relations/backends/**" = ["TCH001", "TCH002"]
# Pydantic node files need enum/type imports at runtime for field definitions
"src/mountainash/expressions/core/expression_nodes/**" = ["TCH001", "TCH002", "TCH003"]
"src/mountainash/relations/core/relation_nodes/**" = ["TCH001", "TCH002", "TCH003"]
# Relation protocol files use types in Protocol definitions (Pydantic-based)
"src/mountainash/relations/core/relation_protocols/**" = ["TCH001", "TCH002"]
```

- [ ] **Step 2: Run ruff to verify configuration loads**

Run: `hatch -e ruff run ruff check ./src --select FA,TCH 2>&1 | wc -l`

Expected: Output with violation counts. The important thing is ruff runs without config errors.

- [ ] **Step 3: Run full ruff to check baseline**

Run: `hatch -e ruff run ruff check ./src 2>&1 | tail -5`

Expected: Error count shown. Note the count — we'll reduce it through subsequent tasks.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add ruff FA + TCH lint rules for import conventions"
```

---

### Task 2: Sweep `from __future__ import annotations` into all source files

**Files:**
- Modify: 48 files (40 `__init__.py` + 8 other `.py` files) — see list below

These files are missing `from __future__ import annotations` and need it added. Files that are exempt (empty `__init__.py`, `__version__.py`, pure `lazy_loader.attach()` `__init__.py`) are NOT included.

**`__init__.py` files (40):**
```
src/mountainash/__init__.py
src/mountainash/conform/__init__.py
src/mountainash/expressions/__init__.py
src/mountainash/expressions/backends/__init__.py
src/mountainash/expressions/backends/expression_systems/__init__.py
src/mountainash/expressions/core/__init__.py
src/mountainash/expressions/core/expression_api/__init__.py
src/mountainash/expressions/core/expression_api/api_builders/__init__.py
src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py
src/mountainash/expressions/core/expression_api/api_builders/substrait/__init__.py
src/mountainash/expressions/core/expression_nodes/__init__.py
src/mountainash/expressions/core/expression_nodes/enums/__init__.py
src/mountainash/expressions/core/expression_nodes/mountainash_extensions/__init__.py
src/mountainash/expressions/core/expression_protocols/api_builders/extensions_mountainash/__init__.py
src/mountainash/expressions/core/expression_protocols/api_builders/substrait/__init__.py
src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py
src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/__init__.py
src/mountainash/expressions/core/expression_system/__init__.py
src/mountainash/expressions/core/expression_system/function_mapping/__init__.py
src/mountainash/expressions/core/unified_visitor/__init__.py
src/mountainash/expressions/core/utils/__init__.py
src/mountainash/pydata/__init__.py
src/mountainash/relations/__init__.py
src/mountainash/relations/backends/__init__.py
src/mountainash/relations/backends/relation_systems/ibis/__init__.py
src/mountainash/relations/backends/relation_systems/ibis/extensions_mountainash/__init__.py
src/mountainash/relations/backends/relation_systems/ibis/substrait/__init__.py
src/mountainash/relations/backends/relation_systems/narwhals/__init__.py
src/mountainash/relations/backends/relation_systems/narwhals/extensions_mountainash/__init__.py
src/mountainash/relations/backends/relation_systems/narwhals/substrait/__init__.py
src/mountainash/relations/backends/relation_systems/polars/__init__.py
src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash/__init__.py
src/mountainash/relations/backends/relation_systems/polars/substrait/__init__.py
src/mountainash/relations/core/relation_api/__init__.py
src/mountainash/relations/core/relation_nodes/__init__.py
src/mountainash/relations/core/relation_nodes/extensions_mountainash/__init__.py
src/mountainash/relations/core/relation_nodes/substrait/__init__.py
src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/__init__.py
src/mountainash/relations/core/relation_protocols/relation_systems/substrait/__init__.py
src/mountainash/relations/core/unified_visitor/__init__.py
```

**Non-`__init__.py` files (8):**
```
src/mountainash/core/constants.py
src/mountainash/core/lazy_imports.py
src/mountainash/expressions/constants.py
src/mountainash/expressions/core/constants.py
src/mountainash/expressions/core/expression_system/function_mapping/definitions.py
src/mountainash/expressions/runtime_imports.py
src/mountainash/expressions/types.py
src/mountainash/pydata/constants.py
```

- [ ] **Step 1: Add `from __future__ import annotations` to all 48 files**

For each file, add `from __future__ import annotations` as the first import statement. If the file has a module docstring, add it after the docstring. If the file already has imports, add it before the first import.

Pattern for files WITH a docstring:
```python
"""Module docstring."""
from __future__ import annotations

# ... existing imports
```

Pattern for files WITHOUT a docstring:
```python
from __future__ import annotations

# ... existing imports
```

For `__init__.py` files that are just re-exports (no docstring, just imports), prepend the future import before all other imports.

- [ ] **Step 2: Verify FA100 violations are resolved**

Run: `hatch -e ruff run ruff check ./src --select FA100 2>&1`

Expected: `All checks passed!` or 0 FA100 errors.

- [ ] **Step 3: Run full test suite to verify nothing broke**

Run: `hatch run test:test-quick 2>&1 | tail -5`

Expected: All tests pass. The `from __future__ import annotations` import should have no runtime effect on correct code.

- [ ] **Step 4: Commit**

```bash
git add -A src/mountainash/
git commit -m "chore: add from __future__ import annotations to all source files"
```

---

### Task 3: Refactor `core/types.py` — delete runtime stubs, move aliases under TYPE_CHECKING

**Files:**
- Modify: `src/mountainash/core/types.py`

This is the highest-impact change. The current file has:
- Lines 14-78: `if TYPE_CHECKING:` block importing backends, THEN an `else:` block creating `types.ModuleType` stubs with `Any` attributes
- Lines 80-131: Type aliases defined unconditionally (relying on the runtime stubs)
- Lines 133-138: TypeVars
- Lines 184-205: A second `if TYPE_CHECKING:` block for Ibis domain-specific aliases and ColumnMapping

The new structure: ALL optional-backend imports and type aliases move under a single `TYPE_CHECKING` block. Protocols and type guards stay outside.

- [ ] **Step 1: Rewrite `core/types.py`**

Replace the entire file with:

```python
"""
Unified typing system for the mountainash package.

Single source of truth for all shared type aliases, runtime fallback imports,
type guards, and protocols used across expressions, dataframes, schema, and pydata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard
from collections.abc import Sequence, Mapping

if TYPE_CHECKING:
    import ibis as ibis
    import ibis.expr.types as ir
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import narwhals as nw

    # ========================================================================
    # Type Aliases — DataFrames
    # ========================================================================

    PandasFrame: TypeAlias = pd.DataFrame
    PolarsFrame: TypeAlias = pl.DataFrame
    PolarsLazyFrame: TypeAlias = pl.LazyFrame
    PyArrowTable: TypeAlias = pa.Table
    IbisTable: TypeAlias = ir.Table
    IbisBaseBackend: TypeAlias = ibis.BaseBackend
    IbisSchema: TypeAlias = ibis.expr.schema.Schema
    NarwhalsFrame: TypeAlias = nw.DataFrame
    NarwhalsLazyFrame: TypeAlias = nw.LazyFrame

    # ========================================================================
    # Type Aliases — Expressions
    # ========================================================================

    PolarsExpr: TypeAlias = pl.Expr
    IbisExpr: TypeAlias = Union[ir.Expr, ir.Column, ir.Scalar]
    NarwhalsExpr: TypeAlias = nw.Expr

    # ========================================================================
    # Type Aliases — Series
    # ========================================================================

    PandasSeries: TypeAlias = pd.Series
    PolarsSeries: TypeAlias = pl.Series
    NarwhalsSeries: TypeAlias = nw.Series
    PyArrowArray: TypeAlias = pa.Array

    # ========================================================================
    # Composite Type Unions
    # ========================================================================

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

    # ========================================================================
    # Generic Type Variables
    # ========================================================================

    DataFrameT = TypeVar("DataFrameT", bound=SupportedDataFrames)
    ExpressionT = TypeVar("ExpressionT", bound=SupportedExpressions)
    SeriesT = TypeVar("SeriesT", bound=SupportedSeries)

    # ========================================================================
    # Ibis Domain-Specific Type Aliases
    # ========================================================================

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

# ============================================================================
# Column Type Mappings (stdlib only — no backend dependency)
# ============================================================================

ColumnTypes: TypeAlias = Union[type, str]

if TYPE_CHECKING:
    ColumnMapping: TypeAlias = Mapping[str, ColumnTypes]
else:
    ColumnMapping: TypeAlias = "Mapping[str, ColumnTypes]"

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
# Type Guards — DataFrame Detection
# ============================================================================

def is_pandas_dataframe(obj: Any) -> TypeGuard['PandasFrame']:
    """Type guard for pandas DataFrames."""
    return type(obj).__module__.startswith("pandas") and type(obj).__name__ == "DataFrame"

def is_polars_dataframe(obj: Any) -> TypeGuard['PolarsFrame']:
    """Type guard for polars DataFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "DataFrame"

def is_polars_lazyframe(obj: Any) -> TypeGuard['PolarsLazyFrame']:
    """Type guard for polars LazyFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "LazyFrame"

def is_pyarrow_table(obj: Any) -> TypeGuard['PyArrowTable']:
    """Type guard for PyArrow Tables."""
    return type(obj).__module__.startswith("pyarrow") and type(obj).__name__ == "Table"

def is_ibis_table(obj: Any) -> TypeGuard['IbisTable']:
    """Type guard for Ibis Tables."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_dataframe(obj: Any) -> TypeGuard['NarwhalsFrame']:
    """Type guard for Narwhals DataFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "DataFrame"

def is_narwhals_lazyframe(obj: Any) -> TypeGuard['NarwhalsLazyFrame']:
    """Type guard for Narwhals LazyFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "LazyFrame"

def is_supported_dataframe(obj: Any) -> TypeGuard['SupportedDataFrames']:
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

def is_polars_expression(obj: Any) -> TypeGuard['PolarsExpr']:
    """Type guard for polars Expressions."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "Expr"

def is_ibis_expression(obj: Any) -> TypeGuard['IbisExpr']:
    """Type guard for Ibis Expressions."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_expression(obj: Any) -> TypeGuard['NarwhalsExpr']:
    """Type guard for Narwhals Expressions."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "Expr"

# ============================================================================
# Type Guards — Series Detection
# ============================================================================

def is_pandas_series(obj: Any) -> TypeGuard['PandasSeries']:
    """Type guard for pandas Series."""
    return type(obj).__module__.startswith("pandas") and type(obj).__name__ == "Series"

def is_polars_series(obj: Any) -> TypeGuard['PolarsSeries']:
    """Type guard for polars Series."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "Series"

def is_narwhals_series(obj: Any) -> TypeGuard['NarwhalsSeries']:
    """Type guard for Narwhals Series."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "Series"

def is_pyarrow_array(obj: Any) -> TypeGuard['PyArrowArray']:
    """Type guard for PyArrow Arrays."""
    return type(obj).__module__.startswith("pyarrow") and type(obj).__name__ == "Array"
```

- [ ] **Step 2: Run tests to verify nothing depends on runtime type aliases**

Run: `hatch run test:test-quick 2>&1 | tail -10`

Expected: All tests pass. If any tests fail with `NameError` for a type alias, it means some code uses the alias at runtime (e.g., `isinstance(df, PolarsFrame)`). Those call sites need to switch to type guards.

- [ ] **Step 3: If tests fail — fix runtime usages**

Search for any runtime usage of the type aliases that now only exist under TYPE_CHECKING:

```bash
hatch -e ruff run ruff check ./src --select TCH004 2>&1
```

TCH004 flags imports inside TYPE_CHECKING that are used at runtime. Fix each by either:
- Switching to type guard: `isinstance(df, PolarsFrame)` → `is_polars_dataframe(df)`
- Moving the import back outside TYPE_CHECKING if it's genuinely needed at runtime

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/core/types.py
git commit -m "refactor: move type aliases under TYPE_CHECKING, delete runtime stubs"
```

---

### Task 4: Fix duplicate imports and annotation-only import violations

**Files:**
- Modify: `src/mountainash/pydata/egress/egress_helpers.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_set.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py`
- Modify: `src/mountainash/expressions/core/expression_system/expsys_base.py`
- Modify: Various files flagged by TCH001/TCH002/TCH003/TCH005

This task fixes all remaining TCH violations that aren't covered by per-file-ignores. The approach:
1. Run ruff with TCH rules to get the current violation list
2. Fix duplicates (remove the TYPE_CHECKING copy when import is needed at runtime)
3. Move annotation-only imports under TYPE_CHECKING
4. Remove empty TYPE_CHECKING blocks (TCH005)

- [ ] **Step 1: Get the current TCH violation list**

Run: `hatch -e ruff run ruff check ./src --select TCH 2>&1`

This shows all remaining violations after per-file-ignores are applied.

- [ ] **Step 2: Fix duplicate imports**

**`egress_helpers.py`** — Remove `TypeSpec, FieldSpec` from the TYPE_CHECKING block (they're imported unconditionally on line 25 and needed at runtime):

```python
# BEFORE (lines 20-25):
if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames
    from mountainash.typespec.spec import TypeSpec, FieldSpec   # DUPLICATE

from mountainash.typespec.spec import TypeSpec, FieldSpec       # Runtime import

# AFTER:
if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames

from mountainash.typespec.spec import TypeSpec, FieldSpec
```

**`api_bldr_ext_ma_scalar_set.py`** — Remove the duplicate `ExpressionNode, ScalarFunctionNode` from TYPE_CHECKING (they're used at runtime):

```python
# BEFORE:
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode  # unconditional

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode  # DUPLICATE
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode  # TRIPLE duplicate

# AFTER:
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
```

**`api_bldr_scalar_string.py`** — Same pattern: remove duplicate from TYPE_CHECKING:

```python
# BEFORE:
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode  # unconditional

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode  # DUPLICATE
    from ...api_base import BaseExpressionAPI

# AFTER:
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
```

**`expsys_base.py`** — Remove `CONST_VISITOR_BACKENDS` from TYPE_CHECKING (it's imported unconditionally and used at runtime):

```python
# BEFORE:
from ..constants import CONST_VISITOR_BACKENDS  # unconditional

if TYPE_CHECKING:
    from ..constants import CONST_VISITOR_BACKENDS  # DUPLICATE

# AFTER:
from ..constants import CONST_VISITOR_BACKENDS

if TYPE_CHECKING:
    # ... remaining TYPE_CHECKING imports (if any)
```

- [ ] **Step 3: Fix annotation-only imports (move under TYPE_CHECKING)**

Use ruff's unsafe-fixes to auto-fix the straightforward TCH001/TCH002/TCH003 violations:

```bash
hatch -e ruff run ruff check ./src --select TCH001,TCH002,TCH003 --fix --unsafe-fixes 2>&1
```

Review the changes with `git diff` to verify ruff didn't break anything. Ruff should:
- Move annotation-only imports into `if TYPE_CHECKING:` blocks
- Add `from __future__ import annotations` if missing
- Add `from typing import TYPE_CHECKING` if missing

- [ ] **Step 4: Remove empty TYPE_CHECKING blocks (TCH005)**

```bash
hatch -e ruff run ruff check ./src --select TCH005 --fix 2>&1
```

- [ ] **Step 5: Run ruff to verify zero TCH violations**

Run: `hatch -e ruff run ruff check ./src --select TCH 2>&1`

Expected: `All checks passed!` or only violations covered by per-file-ignores.

- [ ] **Step 6: Run full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -10`

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add -A src/mountainash/
git commit -m "refactor: fix duplicate imports and move annotation-only imports under TYPE_CHECKING"
```

---

### Task 5: Run full verification — ruff + tests + pyright

**Files:** None (verification only)

- [ ] **Step 1: Run ruff with all configured rules**

Run: `hatch -e ruff run ruff check ./src 2>&1`

Expected: Remaining errors should be only pre-existing F401/E402 issues (not related to this work). Zero FA100, TCH001-005 violations.

- [ ] **Step 2: Run full test suite with coverage**

Run: `hatch run test:test 2>&1 | tail -15`

Expected: All tests pass. Coverage should be similar to baseline (~4400 tests).

- [ ] **Step 3: Run pyright if available**

Run: `hatch run pyright:check 2>&1 | tail -20` or `npx pyright src/mountainash/ 2>&1 | tail -20`

Expected: No new type errors introduced. Ideally some existing `Any` type issues should improve now that type aliases are properly resolved by the type checker.

- [ ] **Step 4: Document results**

Note the final ruff error count, test count, and any pyright changes. This becomes the new baseline.

---

### Task 6: Write principle document

**Files:**
- Create: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/g.development-practices/import-conventions.md`
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/CLAUDE.md` (update principles table)

- [ ] **Step 1: Write the principle document**

Create `import-conventions.md`:

```markdown
# Import Conventions

**Status:** ENFORCED
**Governs:** All import statements in `src/mountainash/`
**Enforced by:** ruff rules FA100, TCH001-005

## Import Classification

Every import falls into exactly one category:

| Category | Example | Pattern |
|----------|---------|---------|
| **Standard library** | `typing`, `logging`, `datetime` | Unconditional top-level import |
| **Runtime import** | Any module called/instantiated at runtime | Unconditional top-level (or `lazy_imports` for optional backends) |
| **Annotation-only** | Types in signatures, TypeAlias, generics | `if TYPE_CHECKING:` guard |
| **Package re-export** | `__init__.py` exposing submodule contents | `lazy_loader.attach()` where beneficial |

## Decision Rule

**If the import is called, instantiated, or used as a value at runtime → unconditional.**
**If it appears only in type annotations → `TYPE_CHECKING` guard.**

No dual imports. No exceptions.

## Three Import Mechanisms

### 1. `lazy_loader.attach()` — Package `__init__.py` only

Defers submodule loading in packages with heavy or numerous submodules:

```python
import lazy_loader
__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submod_attrs={"module_name": ["ClassName"]}
)
```

Not every `__init__.py` needs this — use for packages where eager loading would import heavy deps.

### 2. `core/lazy_imports.py` — Runtime optional backends

For non-backend code calling optional libraries at runtime:

```python
from mountainash.core.lazy_imports import import_narwhals

def to_pandas(df):
    nw = import_narwhals()
    return nw.from_native(df).to_pandas()
```

### 3. `if TYPE_CHECKING:` — Annotation-only imports

For anything used only in type annotations:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames
    import polars as pl
```

Requires `from __future__ import annotations` in every file.

## `from __future__ import annotations` Requirement

Every `.py` file under `src/mountainash/` that contains type annotations or TYPE_CHECKING guards must have `from __future__ import annotations` as its first import. Enforced by ruff FA100.

Exempt: empty `__init__.py` files, `__version__.py`, pure `lazy_loader.attach()` `__init__.py`.

## `core/types.py` — Type Aliases

All optional-backend type aliases (`PolarsFrame`, `SupportedDataFrames`, etc.) live under `TYPE_CHECKING` in `core/types.py`. They are only available to type checkers (Pyright/mypy), not at runtime.

Runtime type checking uses type guard functions: `is_polars_dataframe()`, `is_ibis_table()`, `detect_dataframe_backend_type()`, etc.

## Expression/Relation Backend Files

Backend files (under `expressions/backends/` and `relations/backends/`) legitimately import their backend unconditionally — they only execute when that backend is detected. These are excluded from TCH rules via per-file-ignores.

Pydantic model files (nodes) also legitimately import types at runtime for field definitions.

## Anti-Patterns

These are principle violations:

- **Duplicate imports:** Same symbol imported both under TYPE_CHECKING and unconditionally
- **Runtime stubs:** `types.ModuleType` fakes for missing optional backends
- **Missing future annotations:** Files using TYPE_CHECKING without `from __future__ import annotations`
- **Annotation-only imports outside guard:** Imports used only in signatures but not guarded
```

- [ ] **Step 2: Update CLAUDE.md principles table**

Add to the `g. Development Practices` section of the principles table in CLAUDE.md:

```markdown
| import-conventions.md | ENFORCED | Four import categories; lazy_loader for __init__.py, lazy_imports for runtime optional backends, TYPE_CHECKING for annotations; ruff FA+TCH enforcement |
```

- [ ] **Step 3: Commit**

```bash
git add /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/g.development-practices/import-conventions.md
git add CLAUDE.md
git commit -m "docs: add import-conventions principle (ENFORCED)"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Import classification (4 categories) — Task 6 principle doc
- ✅ Three mechanisms (lazy_loader, lazy_imports, TYPE_CHECKING) — Task 6 principle doc
- ✅ `core/types.py` refactoring — Task 3
- ✅ `from __future__ import annotations` requirement — Task 2
- ✅ Ruff FA + TCH rules — Task 1
- ✅ Fix duplicate imports — Task 4
- ✅ Move annotation-only imports — Task 4
- ✅ Per-file-ignores for backends/nodes — Task 1
- ✅ Principle document — Task 6
- ✅ Full verification — Task 5

**Placeholder scan:** No TBDs, TODOs, or vague steps. All code shown.

**Type consistency:** `TypeGuard['PolarsFrame']` string-quoted in types.py matches the TYPE_CHECKING-only alias. All references use consistent naming.
