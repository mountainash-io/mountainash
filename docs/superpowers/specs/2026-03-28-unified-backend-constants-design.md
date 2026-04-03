# Layer 2.3: Unified Backend Constants — Design Spec

## Goal

Collapse 11 backend-related enums across 6 files into a clean hierarchy in `mountainash.core.constants`. Eliminate duplicates, fix broken imports, and establish a single source of truth for backend identity across all modules.

## Problem

The four ported modules each brought their own backend enums from when they were separate packages. The result is 11 overlapping definitions:

| Enum | Location | Members | Used By |
|------|----------|---------|---------|
| `CONST_VISITOR_BACKENDS` | `core/constants.py` | 5 (str values) | expressions |
| `CONST_VISITOR_BACKENDS` | `expressions/constants.py` | 4 (missing NARWHALS) | expressions internal |
| `CONST_DATAFRAME_FRAMEWORK` | `dataframes/constants.py` | 5 (StrEnum) | schema |
| `CONST_DATAFRAME_BACKEND` | `dataframes/constants.py` | 5 (auto) | dataframes __init__ |
| `Backend` | `dataframes/core/constants.py` | 5 (auto) | dataframes core |
| `DataFrameSystemBackend` | `dataframes/core/constants.py` | 3 (auto) | dataframes core |
| `CONST_DATAFRAME_BACKEND` | `dataframes/core/dataframe_system/constants.py` | 3 (auto) | dataframe system |
| `CONST_EXPRESSION_TYPE` | `dataframes/constants.py` | 4 (auto) | dataframes __init__ only |
| `CONST_JOIN_BACKEND_TYPE` | `dataframes/constants.py` | 3 (auto) | dataframes __init__ only |
| `CONST_DATAFRAME_TYPE` | `dataframes/constants.py` | 7 (auto) | schema, pydata, core/factories |
| `CONST_IBIS_INMEMORY_BACKEND` | `dataframes/constants.py` | 3 (StrEnum) | dataframes __init__ only |

Additionally:
- `CONST_PYTHON_DATAFORMAT` is duplicated in both `dataframes/constants.py` and `pydata/constants.py`
- `schema/schema_utils.py` imports `from .constants import CONST_DATAFRAME_FRAMEWORK` but `schema/constants.py` does not exist (broken import)

## Solution

### New unified enums in `mountainash/core/constants.py`

#### `CONST_BACKEND` (StrEnum) — detection level

"What library produced this object?"

```python
class CONST_BACKEND(StrEnum):
    POLARS   = "polars"
    PANDAS   = "pandas"
    PYARROW  = "pyarrow"
    IBIS     = "ibis"
    NARWHALS = "narwhals"
```

Replaces: `CONST_VISITOR_BACKENDS` (both copies), `CONST_DATAFRAME_FRAMEWORK`, `CONST_DATAFRAME_BACKEND` (5-member), `Backend`

Uses `StrEnum` so that `CONST_BACKEND.POLARS == "polars"` — preserving string-based registry lookups in expressions while providing proper enum identity comparison.

#### `CONST_BACKEND_SYSTEM` (StrEnum) — routing level

"Which system implementation handles this type?"

```python
class CONST_BACKEND_SYSTEM(StrEnum):
    POLARS   = "polars"
    NARWHALS = "narwhals"
    IBIS     = "ibis"
```

Replaces: `DataFrameSystemBackend`, `CONST_DATAFRAME_BACKEND` (3-member), `CONST_JOIN_BACKEND_TYPE`, `CONST_EXPRESSION_TYPE`

#### `CONST_DATAFRAME_TYPE` (Enum) — granular DataFrame variant

"What specific DataFrame type is this?"

```python
class CONST_DATAFRAME_TYPE(Enum):
    IBIS_TABLE           = auto()
    PANDAS_DATAFRAME     = auto()
    POLARS_DATAFRAME     = auto()
    POLARS_LAZYFRAME     = auto()
    PYARROW_TABLE        = auto()
    NARWHALS_DATAFRAME   = auto()
    NARWHALS_LAZYFRAME   = auto()
```

Moved from `dataframes/constants.py`. Already a cross-module concern — imported by `schema/transform/cast_schema_factory.py`, `pydata/egress/egress_factory.py`, and `core/factories.py`.

#### `CONST_IBIS_INMEMORY_BACKEND` (StrEnum) — Ibis sub-backend

"Which SQL engine is Ibis using?"

```python
class CONST_IBIS_INMEMORY_BACKEND(StrEnum):
    POLARS = "polars"
    DUCKDB = "duckdb"
    SQLITE = "sqlite"
```

Moved from `dataframes/constants.py`. Relevant to any module that cares about Ibis backend variants (expressions tests already parameterize across these).

#### `backend_to_system()` mapping function

```python
def backend_to_system(backend: CONST_BACKEND) -> CONST_BACKEND_SYSTEM:
    mapping = {
        CONST_BACKEND.POLARS:   CONST_BACKEND_SYSTEM.POLARS,
        CONST_BACKEND.PANDAS:   CONST_BACKEND_SYSTEM.NARWHALS,
        CONST_BACKEND.PYARROW:  CONST_BACKEND_SYSTEM.NARWHALS,
        CONST_BACKEND.IBIS:     CONST_BACKEND_SYSTEM.IBIS,
        CONST_BACKEND.NARWHALS: CONST_BACKEND_SYSTEM.NARWHALS,
    }
    return mapping[backend]
```

Moved from `dataframes/core/constants.py`.

### Backwards compatibility

#### Aliases in `core/constants.py`

```python
# Backwards-compat alias
CONST_VISITOR_BACKENDS = CONST_BACKEND
```

Expressions code and tests that reference `CONST_VISITOR_BACKENDS` continue to work unchanged.

#### Re-export shim: `dataframes/constants.py`

Replace the 7 enum definitions with re-exports from core:

```python
from mountainash.core.constants import (
    CONST_BACKEND as CONST_DATAFRAME_FRAMEWORK,
    CONST_BACKEND as CONST_DATAFRAME_BACKEND,
    CONST_BACKEND_SYSTEM as CONST_EXPRESSION_TYPE,
    CONST_BACKEND_SYSTEM as CONST_JOIN_BACKEND_TYPE,
    CONST_DATAFRAME_TYPE,
    CONST_IBIS_INMEMORY_BACKEND,
)
from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
```

Any external code importing from `mountainash.dataframes.constants` still works.

#### Re-export shim: `dataframes/core/constants.py`

Import from core, keep the dataframes-specific groupings:

```python
from mountainash.core.constants import (
    CONST_BACKEND as Backend,
    CONST_BACKEND_SYSTEM as DataFrameSystemBackend,
    backend_to_system,
)

# Dataframes-specific groupings (stay here)
NARWHALS_WRAPPABLE_BACKENDS = frozenset({...})
LAZY_BACKENDS = frozenset({...})
EXPRESSION_BACKENDS = frozenset({...})
```

#### Re-export shim: `dataframes/core/dataframe_system/constants.py`

```python
from mountainash.core.constants import CONST_BACKEND_SYSTEM as CONST_DATAFRAME_BACKEND
BACKEND_DETECTION_ORDER = [...]
```

#### Fix: `expressions/constants.py`

Import from core instead of defining its own copy:

```python
from mountainash.core.constants import CONST_BACKEND as CONST_VISITOR_BACKENDS
from mountainash.core.constants import CONST_LOGIC_TYPES, CONST_EXPRESSION_NODE_TYPES
# ... rest of expression-specific enums stay here
```

### Broken import fix

`schema/schema_utils.py` line 16:
```python
# Before (broken — schema/constants.py doesn't exist)
from .constants import CONST_DATAFRAME_FRAMEWORK

# After
from mountainash.core.constants import CONST_BACKEND as CONST_DATAFRAME_FRAMEWORK
```

### Duplicate fix

Remove `CONST_PYTHON_DATAFORMAT` from `dataframes/constants.py`. Canonical definition stays in `pydata/constants.py`. The re-export shim in `dataframes/constants.py` imports from pydata.

### What stays where

| Location | Contains |
|----------|----------|
| `core/constants.py` | `CONST_BACKEND`, `CONST_BACKEND_SYSTEM`, `CONST_DATAFRAME_TYPE`, `CONST_IBIS_INMEMORY_BACKEND`, `backend_to_system()`, `CONST_VISITOR_BACKENDS` (alias), plus all existing expression operator enums |
| `dataframes/constants.py` | Re-export shim only |
| `dataframes/core/constants.py` | Re-exports from core + `NARWHALS_WRAPPABLE_BACKENDS`, `LAZY_BACKENDS`, `EXPRESSION_BACKENDS`, `InputType` |
| `dataframes/core/dataframe_system/constants.py` | Re-export + `BACKEND_DETECTION_ORDER` |
| `expressions/constants.py` | Re-exports from core + expression-specific operator enums |
| `pydata/constants.py` | `CONST_PYTHON_DATAFORMAT` (canonical, unchanged) |

## Consumer import updates

All files that import old enum names need updating. The re-export shims mean most imports still resolve, but we should update internal code to use canonical paths:

| Old Import | New Import |
|------------|-----------|
| `from mountainash.core.constants import CONST_VISITOR_BACKENDS` | Works (alias) |
| `from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK` | Works (shim), prefer `CONST_BACKEND` |
| `from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE` | Works (shim), prefer `from mountainash.core.constants` |
| `from mountainash.dataframes.core.constants import Backend` | Works (shim), prefer `CONST_BACKEND` |
| `from mountainash.dataframes.core.dataframe_system.constants import CONST_DATAFRAME_BACKEND` | Works (shim) |
| `from .constants import CONST_DATAFRAME_FRAMEWORK` (schema) | **Broken** — must fix |

Internal code (inside `src/mountainash/`) should be updated to import from `mountainash.core.constants` directly. External code can continue using old paths via shims.

## Tests

### Regression

All existing 2939+ tests continue to pass. The StrEnum values match the old string values, and re-export shims preserve all old import paths.

### New tests

**`tests/core/test_unified_constants.py`:**

1. `CONST_BACKEND` is a `StrEnum` with 5 members
2. `CONST_BACKEND.POLARS == "polars"` (string compatibility for registry lookups)
3. `CONST_BACKEND_SYSTEM` is a `StrEnum` with 3 members
4. `backend_to_system()` maps all 5 backends correctly
5. `CONST_VISITOR_BACKENDS is CONST_BACKEND` (alias identity)
6. Old import paths via shims resolve to the same enum classes (e.g., `from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE` gives same class as `from mountainash.core.constants import CONST_DATAFRAME_TYPE`)

## Scope

**In scope:**
- Create unified enums in `core/constants.py`
- Create re-export shims in `dataframes/constants.py`, `dataframes/core/constants.py`, `dataframes/core/dataframe_system/constants.py`
- Update `expressions/constants.py` to import from core
- Fix broken `schema/schema_utils.py` import
- Remove `CONST_PYTHON_DATAFORMAT` duplicate from `dataframes/constants.py`
- Update all internal imports to use canonical paths
- Add constant unification tests

**Out of scope:**
- Renaming `CONST_VISITOR_BACKENDS` references in expressions code (alias handles it)
- Changing expression backend registration to use `CONST_BACKEND_SYSTEM` (future alignment work)
- Unifying type aliases (Layer 2.4)
