# Unified Backend Constants Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse 11 backend-related enums across 6 files into a clean StrEnum hierarchy in `mountainash.core.constants`, with re-export shims for backwards compatibility.

**Architecture:** New canonical enums (`CONST_BACKEND`, `CONST_BACKEND_SYSTEM`, `CONST_DATAFRAME_TYPE`, `CONST_IBIS_INMEMORY_BACKEND`) defined once in `mountainash/core/constants.py`. Old enum locations become thin re-export shims. Internal consumers updated to import from core.

**Tech Stack:** Python 3.11+ `StrEnum`, `Enum`, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/mountainash/core/constants.py` | Modify | Add `CONST_BACKEND`, `CONST_BACKEND_SYSTEM`, `CONST_DATAFRAME_TYPE`, `CONST_IBIS_INMEMORY_BACKEND`, `backend_to_system()`, `CONST_VISITOR_BACKENDS` alias |
| `src/mountainash/dataframes/constants.py` | Rewrite | Replace 7 enum definitions with re-export shim |
| `src/mountainash/dataframes/core/constants.py` | Rewrite | Import from core, keep groupings + `InputType` |
| `src/mountainash/dataframes/core/dataframe_system/constants.py` | Rewrite | Import from core, keep `BACKEND_DETECTION_ORDER` |
| `src/mountainash/expressions/constants.py` | Modify | Replace local `CONST_VISITOR_BACKENDS` with import from core |
| `src/mountainash/schema/schema_utils.py` | Modify | Fix broken `from .constants` import |
| `src/mountainash/pydata/egress/egress_factory.py` | Modify | Update import path |
| `src/mountainash/core/factories.py` | Modify | Update lazy import path |
| `src/mountainash/schema/transform/cast_schema_factory.py` | Modify | Update import path |
| `src/mountainash/dataframes/__init__.py` | Modify | Update constant imports |
| `tests/core/test_unified_constants.py` | Create | Unification tests |

---

### Task 1: Add unified enums to core/constants.py

**Files:**
- Modify: `src/mountainash/core/constants.py:1-23`

- [ ] **Step 1: Add StrEnum import and new enums at top of file**

Add the following right after line 2 (`from enum import Enum, IntEnum, auto`), before the existing `CONST_VISITOR_BACKENDS` class:

```python
from enum import Enum, IntEnum, StrEnum, auto


# =============================================================================
# Unified Backend Enums
# =============================================================================

class CONST_BACKEND(StrEnum):
    """
    Unified backend enumeration — detection level.

    "What library produced this object?"

    Uses StrEnum so CONST_BACKEND.POLARS == "polars" — preserving
    string-based registry lookups while providing enum identity comparison.
    """
    POLARS   = "polars"
    PANDAS   = "pandas"
    PYARROW  = "pyarrow"
    IBIS     = "ibis"
    NARWHALS = "narwhals"


class CONST_BACKEND_SYSTEM(StrEnum):
    """
    Backend routing targets — system level.

    "Which system implementation handles this type?"

    Three routing targets:
    - POLARS: Native Polars operations
    - NARWHALS: pandas, PyArrow, cuDF routed through Narwhals adapter
    - IBIS: SQL backends (DuckDB, PostgreSQL, etc.)
    """
    POLARS   = "polars"
    NARWHALS = "narwhals"
    IBIS     = "ibis"


class CONST_DATAFRAME_TYPE(Enum):
    """
    Granular DataFrame variant types.

    "What specific DataFrame type is this?"
    Used by schema, pydata, and core factories for strategy dispatch.
    """
    IBIS_TABLE           = auto()
    PANDAS_DATAFRAME     = auto()
    POLARS_DATAFRAME     = auto()
    POLARS_LAZYFRAME     = auto()
    PYARROW_TABLE        = auto()
    NARWHALS_DATAFRAME   = auto()
    NARWHALS_LAZYFRAME   = auto()


class CONST_IBIS_INMEMORY_BACKEND(StrEnum):
    """
    Ibis in-memory backend variants.

    "Which SQL engine is Ibis using?"
    """
    POLARS = "polars"
    DUCKDB = "duckdb"
    SQLITE = "sqlite"


def backend_to_system(backend: CONST_BACKEND) -> CONST_BACKEND_SYSTEM:
    """
    Map a detected backend to its system routing target.

    Examples:
        >>> backend_to_system(CONST_BACKEND.POLARS)
        <CONST_BACKEND_SYSTEM.POLARS: 'polars'>
        >>> backend_to_system(CONST_BACKEND.PANDAS)
        <CONST_BACKEND_SYSTEM.NARWHALS: 'narwhals'>
    """
    mapping = {
        CONST_BACKEND.POLARS:   CONST_BACKEND_SYSTEM.POLARS,
        CONST_BACKEND.PANDAS:   CONST_BACKEND_SYSTEM.NARWHALS,
        CONST_BACKEND.PYARROW:  CONST_BACKEND_SYSTEM.NARWHALS,
        CONST_BACKEND.IBIS:     CONST_BACKEND_SYSTEM.IBIS,
        CONST_BACKEND.NARWHALS: CONST_BACKEND_SYSTEM.NARWHALS,
    }
    return mapping[backend]


# Backwards-compat alias for expressions code
CONST_VISITOR_BACKENDS = CONST_BACKEND
```

- [ ] **Step 2: Remove the old CONST_VISITOR_BACKENDS class definition**

Delete the old `CONST_VISITOR_BACKENDS` class (lines 4-23 in current file) since it's now replaced by the alias above.

- [ ] **Step 3: Run existing tests to verify no regressions**

Run: `hatch run test:test-quick 2>&1 | tail -5`
Expected: All previously passing tests still pass. The `CONST_VISITOR_BACKENDS` alias ensures existing code sees no change.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/core/constants.py
git commit -m "feat: add unified backend enums to core/constants.py"
```

---

### Task 2: Write unification tests

**Files:**
- Create: `tests/core/test_unified_constants.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for unified backend constants in mountainash.core.constants."""

from enum import StrEnum, Enum

import pytest

from mountainash.core.constants import (
    CONST_BACKEND,
    CONST_BACKEND_SYSTEM,
    CONST_DATAFRAME_TYPE,
    CONST_IBIS_INMEMORY_BACKEND,
    CONST_VISITOR_BACKENDS,
    backend_to_system,
)


class TestConstBackend:
    """Tests for CONST_BACKEND unified detection enum."""

    def test_is_strenum(self):
        assert issubclass(CONST_BACKEND, StrEnum)

    def test_has_five_members(self):
        assert len(CONST_BACKEND) == 5

    def test_string_equality(self):
        """StrEnum values must equal their string for registry lookups."""
        assert CONST_BACKEND.POLARS == "polars"
        assert CONST_BACKEND.PANDAS == "pandas"
        assert CONST_BACKEND.PYARROW == "pyarrow"
        assert CONST_BACKEND.IBIS == "ibis"
        assert CONST_BACKEND.NARWHALS == "narwhals"

    def test_visitor_backends_alias(self):
        """CONST_VISITOR_BACKENDS is an alias for CONST_BACKEND."""
        assert CONST_VISITOR_BACKENDS is CONST_BACKEND


class TestConstBackendSystem:
    """Tests for CONST_BACKEND_SYSTEM unified routing enum."""

    def test_is_strenum(self):
        assert issubclass(CONST_BACKEND_SYSTEM, StrEnum)

    def test_has_three_members(self):
        assert len(CONST_BACKEND_SYSTEM) == 3

    def test_members(self):
        assert CONST_BACKEND_SYSTEM.POLARS == "polars"
        assert CONST_BACKEND_SYSTEM.NARWHALS == "narwhals"
        assert CONST_BACKEND_SYSTEM.IBIS == "ibis"


class TestBackendToSystem:
    """Tests for backend_to_system() mapping."""

    @pytest.mark.parametrize(
        "backend, expected_system",
        [
            (CONST_BACKEND.POLARS, CONST_BACKEND_SYSTEM.POLARS),
            (CONST_BACKEND.PANDAS, CONST_BACKEND_SYSTEM.NARWHALS),
            (CONST_BACKEND.PYARROW, CONST_BACKEND_SYSTEM.NARWHALS),
            (CONST_BACKEND.IBIS, CONST_BACKEND_SYSTEM.IBIS),
            (CONST_BACKEND.NARWHALS, CONST_BACKEND_SYSTEM.NARWHALS),
        ],
    )
    def test_mapping(self, backend, expected_system):
        assert backend_to_system(backend) == expected_system


class TestConstDataframeType:
    """Tests for CONST_DATAFRAME_TYPE."""

    def test_is_enum(self):
        assert issubclass(CONST_DATAFRAME_TYPE, Enum)

    def test_has_seven_members(self):
        assert len(CONST_DATAFRAME_TYPE) == 7

    def test_all_members_exist(self):
        expected = {
            "IBIS_TABLE", "PANDAS_DATAFRAME", "POLARS_DATAFRAME",
            "POLARS_LAZYFRAME", "PYARROW_TABLE",
            "NARWHALS_DATAFRAME", "NARWHALS_LAZYFRAME",
        }
        actual = {m.name for m in CONST_DATAFRAME_TYPE}
        assert actual == expected


class TestConstIbisInmemoryBackend:
    """Tests for CONST_IBIS_INMEMORY_BACKEND."""

    def test_is_strenum(self):
        assert issubclass(CONST_IBIS_INMEMORY_BACKEND, StrEnum)

    def test_has_three_members(self):
        assert len(CONST_IBIS_INMEMORY_BACKEND) == 3

    def test_string_values(self):
        assert CONST_IBIS_INMEMORY_BACKEND.POLARS == "polars"
        assert CONST_IBIS_INMEMORY_BACKEND.DUCKDB == "duckdb"
        assert CONST_IBIS_INMEMORY_BACKEND.SQLITE == "sqlite"


class TestShimImports:
    """Tests that old import paths resolve to the unified enums."""

    def test_dataframes_constants_dataframe_type(self):
        from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE as df_type
        from mountainash.core.constants import CONST_DATAFRAME_TYPE as core_type
        assert df_type is core_type

    def test_dataframes_constants_framework_is_backend(self):
        from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK
        assert CONST_DATAFRAME_FRAMEWORK is CONST_BACKEND

    def test_dataframes_core_backend_is_const_backend(self):
        from mountainash.dataframes.core.constants import Backend
        assert Backend is CONST_BACKEND

    def test_dataframes_core_system_is_const_backend_system(self):
        from mountainash.dataframes.core.constants import DataFrameSystemBackend
        assert DataFrameSystemBackend is CONST_BACKEND_SYSTEM

    def test_dataframe_system_backend_is_const_backend_system(self):
        from mountainash.dataframes.core.dataframe_system.constants import CONST_DATAFRAME_BACKEND
        assert CONST_DATAFRAME_BACKEND is CONST_BACKEND_SYSTEM

    def test_expressions_visitor_backends(self):
        from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
        assert CONST_VISITOR_BACKENDS is CONST_BACKEND
```

- [ ] **Step 2: Run tests — they should mostly fail (shims not yet created)**

Run: `hatch run test:test-target-quick tests/core/test_unified_constants.py -v 2>&1 | tail -20`
Expected: `TestConstBackend`, `TestConstBackendSystem`, `TestBackendToSystem`, `TestConstDataframeType`, `TestConstIbisInmemoryBackend` PASS. `TestShimImports` FAIL (shims not created yet).

- [ ] **Step 3: Commit**

```bash
git add tests/core/test_unified_constants.py
git commit -m "test: add unified backend constants tests"
```

---

### Task 3: Rewrite dataframes/constants.py as re-export shim

**Files:**
- Rewrite: `src/mountainash/dataframes/constants.py`

- [ ] **Step 1: Replace entire file with re-export shim**

```python
"""
Backwards-compatibility shim for mountainash.dataframes.constants.

All canonical definitions now live in mountainash.core.constants.
This module re-exports them under their old names.
"""

from mountainash.core.constants import (
    CONST_BACKEND as CONST_DATAFRAME_FRAMEWORK,
    CONST_BACKEND as CONST_DATAFRAME_BACKEND,
    CONST_BACKEND_SYSTEM as CONST_EXPRESSION_TYPE,
    CONST_BACKEND_SYSTEM as CONST_JOIN_BACKEND_TYPE,
    CONST_DATAFRAME_TYPE,
    CONST_IBIS_INMEMORY_BACKEND,
)
from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

__all__ = [
    "CONST_DATAFRAME_FRAMEWORK",
    "CONST_DATAFRAME_BACKEND",
    "CONST_EXPRESSION_TYPE",
    "CONST_JOIN_BACKEND_TYPE",
    "CONST_DATAFRAME_TYPE",
    "CONST_IBIS_INMEMORY_BACKEND",
    "CONST_PYTHON_DATAFORMAT",
]
```

- [ ] **Step 2: Run shim identity tests**

Run: `hatch run test:test-target-quick tests/core/test_unified_constants.py::TestShimImports::test_dataframes_constants_dataframe_type tests/core/test_unified_constants.py::TestShimImports::test_dataframes_constants_framework_is_backend -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/dataframes/constants.py
git commit -m "refactor: replace dataframes/constants.py with re-export shim"
```

---

### Task 4: Rewrite dataframes/core/constants.py

**Files:**
- Rewrite: `src/mountainash/dataframes/core/constants.py`

- [ ] **Step 1: Replace with imports from core + local groupings**

```python
"""
Unified constants for mountainash-dataframes core framework.

Backend enums are imported from mountainash.core.constants.
This module adds dataframes-specific groupings and InputType.
"""

from __future__ import annotations

from enum import Enum, auto

from mountainash.core.constants import (
    CONST_BACKEND as Backend,
    CONST_BACKEND_SYSTEM as DataFrameSystemBackend,
    backend_to_system,
)


class InputType(Enum):
    """
    Category of input object.

    Used to determine which resolution strategy to apply.

    Members:
        DATAFRAME: Tabular data (pl.DataFrame, pd.DataFrame, pa.Table, etc.)
        EXPRESSION: Lazy column expression (pl.Expr, nw.Expr, ir.BooleanColumn, etc.)
        SERIES: Physical column data (pl.Series, pd.Series, pa.Array, etc.)
    """

    DATAFRAME = auto()
    EXPRESSION = auto()
    SERIES = auto()


# =============================================================================
# Backend Groupings
# =============================================================================

# Backends that can be wrapped by Narwhals
NARWHALS_WRAPPABLE_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.PANDAS,
    Backend.PYARROW,
})

# Backends that support lazy evaluation
LAZY_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.IBIS,
    Backend.NARWHALS,
})

# Backends that support native expressions (not just series filtering)
EXPRESSION_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.NARWHALS,
    Backend.IBIS,
})


__all__ = [
    # Re-exported from core
    "Backend",
    "DataFrameSystemBackend",
    "backend_to_system",
    # Local
    "InputType",
    "NARWHALS_WRAPPABLE_BACKENDS",
    "LAZY_BACKENDS",
    "EXPRESSION_BACKENDS",
]
```

- [ ] **Step 2: Run shim identity tests**

Run: `hatch run test:test-target-quick tests/core/test_unified_constants.py::TestShimImports::test_dataframes_core_backend_is_const_backend tests/core/test_unified_constants.py::TestShimImports::test_dataframes_core_system_is_const_backend_system -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/dataframes/core/constants.py
git commit -m "refactor: replace dataframes/core/constants.py with core imports + groupings"
```

---

### Task 5: Rewrite dataframes/core/dataframe_system/constants.py

**Files:**
- Rewrite: `src/mountainash/dataframes/core/dataframe_system/constants.py`

- [ ] **Step 1: Replace with import from core + detection order**

```python
"""
Constants for the DataFrameSystem.

Backend enum is imported from mountainash.core.constants.
This module adds the detection order specific to DataFrameSystem routing.
"""

from mountainash.core.constants import CONST_BACKEND_SYSTEM as CONST_DATAFRAME_BACKEND


# Backend detection order (important - more specific first)
BACKEND_DETECTION_ORDER = [
    CONST_DATAFRAME_BACKEND.IBIS,
    CONST_DATAFRAME_BACKEND.NARWHALS,
    CONST_DATAFRAME_BACKEND.POLARS,
]
```

- [ ] **Step 2: Run shim identity test**

Run: `hatch run test:test-target-quick tests/core/test_unified_constants.py::TestShimImports::test_dataframe_system_backend_is_const_backend_system -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/dataframes/core/dataframe_system/constants.py
git commit -m "refactor: replace dataframe_system/constants.py with core import"
```

---

### Task 6: Update expressions/constants.py

**Files:**
- Modify: `src/mountainash/expressions/constants.py:1-18`

- [ ] **Step 1: Replace local CONST_VISITOR_BACKENDS with import from core**

Replace the first 18 lines of `src/mountainash/expressions/constants.py` (the `CONST_VISITOR_BACKENDS` class definition) with:

```python
from typing import Optional
from enum import Enum, IntEnum

# Import unified backend enum from core
from mountainash.core.constants import CONST_BACKEND as CONST_VISITOR_BACKENDS

# Import shared constants from core
from mountainash.core.constants import CONST_LOGIC_TYPES, CONST_EXPRESSION_NODE_TYPES
```

Also remove the local `CONST_LOGIC_TYPES` class definition (lines 23-36) and `CONST_EXPRESSION_NODE_TYPES` class definition (lines 38-55) since they're already defined in `core/constants.py`.

- [ ] **Step 2: Run shim identity test**

Run: `hatch run test:test-target-quick tests/core/test_unified_constants.py::TestShimImports::test_expressions_visitor_backends -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/expressions/constants.py
git commit -m "refactor: expressions/constants.py imports from core"
```

---

### Task 7: Fix schema broken import

**Files:**
- Modify: `src/mountainash/schema/schema_utils.py:16`

- [ ] **Step 1: Fix the broken import**

Replace line 16:
```python
from .constants import CONST_DATAFRAME_FRAMEWORK
```
with:
```python
from mountainash.core.constants import CONST_BACKEND as CONST_DATAFRAME_FRAMEWORK
```

- [ ] **Step 2: Verify the import works**

Run: `python -c "from mountainash.schema.schema_utils import CONST_DATAFRAME_FRAMEWORK; print(CONST_DATAFRAME_FRAMEWORK.POLARS)"`
Expected: `polars`

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/schema/schema_utils.py
git commit -m "fix: schema_utils broken import of CONST_DATAFRAME_FRAMEWORK"
```

---

### Task 8: Update cross-module CONST_DATAFRAME_TYPE consumers

**Files:**
- Modify: `src/mountainash/pydata/egress/egress_factory.py:15`
- Modify: `src/mountainash/schema/transform/cast_schema_factory.py:11`
- Modify: `src/mountainash/core/factories.py:170`

- [ ] **Step 1: Update pydata egress_factory.py**

Replace line 15:
```python
from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE
```
with:
```python
from mountainash.core.constants import CONST_DATAFRAME_TYPE
```

- [ ] **Step 2: Update schema cast_schema_factory.py**

Replace line 11:
```python
from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE
```
with:
```python
from mountainash.core.constants import CONST_DATAFRAME_TYPE
```

- [ ] **Step 3: Update core/factories.py lazy import**

In `src/mountainash/core/factories.py`, find the lazy import block (around line 170):
```python
from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE
```
Replace with:
```python
from mountainash.core.constants import CONST_DATAFRAME_TYPE
```

- [ ] **Step 4: Run full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -5`
Expected: All previously passing tests still pass.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/pydata/egress/egress_factory.py src/mountainash/schema/transform/cast_schema_factory.py src/mountainash/core/factories.py
git commit -m "refactor: update cross-module CONST_DATAFRAME_TYPE imports to core"
```

---

### Task 9: Update dataframes/__init__.py

**Files:**
- Modify: `src/mountainash/dataframes/__init__.py:4,11`

- [ ] **Step 1: Update the constants import line**

Replace line 4:
```python
from .constants import CONST_DATAFRAME_FRAMEWORK, CONST_IBIS_INMEMORY_BACKEND, CONST_EXPRESSION_TYPE, CONST_JOIN_BACKEND_TYPE, CONST_DATAFRAME_BACKEND, CONST_DATAFRAME_TYPE
```
with:
```python
from mountainash.core.constants import (
    CONST_BACKEND as CONST_DATAFRAME_FRAMEWORK,
    CONST_BACKEND as CONST_DATAFRAME_BACKEND,
    CONST_BACKEND_SYSTEM as CONST_EXPRESSION_TYPE,
    CONST_BACKEND_SYSTEM as CONST_JOIN_BACKEND_TYPE,
    CONST_DATAFRAME_TYPE,
    CONST_IBIS_INMEMORY_BACKEND,
)
```

- [ ] **Step 2: Update the CONST_DF_BACKEND alias on line 11**

Replace:
```python
    CONST_DATAFRAME_BACKEND as CONST_DF_BACKEND,  # New 3-backend enum
```
with:
```python
    CONST_DATAFRAME_BACKEND as CONST_DF_BACKEND,  # Re-export from core via dataframe_system
```

(The import still works because `dataframe_system/constants.py` now re-exports `CONST_BACKEND_SYSTEM` as `CONST_DATAFRAME_BACKEND`.)

- [ ] **Step 3: Run full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -5`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/dataframes/__init__.py
git commit -m "refactor: dataframes __init__ imports from core constants"
```

---

### Task 10: Run all shim tests and full regression

**Files:**
- Test: `tests/core/test_unified_constants.py`

- [ ] **Step 1: Run the full unification test suite**

Run: `hatch run test:test-target-quick tests/core/test_unified_constants.py -v`
Expected: All tests PASS (including all `TestShimImports`).

- [ ] **Step 2: Run the full project test suite**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: 2939+ passed, 278 xfailed, same pre-existing failures. Zero new failures.

- [ ] **Step 3: Commit (if any fixups needed)**

If any tests required fixes, commit them here.

```bash
git add -A
git commit -m "test: verify unified backend constants — all tests pass"
```
