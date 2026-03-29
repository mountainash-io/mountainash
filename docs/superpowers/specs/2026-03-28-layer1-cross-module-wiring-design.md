# Layer 1: Cross-Module Wiring — Design Spec

## Goal

Fix 56+ broken cross-module imports across schema and pydata so all four modules actually work together, not just import at the top level.

## Problem

Schema and pydata were ported from separate packages that depended on `mountainash_dataframes`. The migration script rewrote `mountainash_dataframes.X` → `mountainash.dataframes.X`, but three paths don't exist in the ported dataframes:

| Broken Path | References | Issue |
|---|---|---|
| `mountainash.dataframes.factories` | 4 files | **Missing entirely** — `BaseStrategyFactory`, `DataFrameTypeFactoryMixin` weren't ported |
| `mountainash.dataframes.runtime_imports` | 16 files (26 refs) | Module doesn't exist at that path |
| `mountainash.dataframes.typing` | 24 files (28 refs) | Old flat path, should be `mountainash.dataframes.core.typing` |

## Solution

### Fix 1: Create `mountainash/core/factories.py`

Copy `BaseStrategyFactory` and `DataFrameTypeFactoryMixin` from the old dataframes source at `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-dataframes/src/mountainash_dataframes/factories/` into `mountainash/core/factories.py`.

These are generic infrastructure classes (dual-generic factory pattern, 3-tier type detection) used by dataframes, schema, and pydata. Core is the right home.

Update internal imports within these classes to reference `mountainash.core` and `mountainash.dataframes` paths.

### Fix 2: Create `mountainash/core/lazy_imports.py`

Copy the runtime import helpers (`import_polars()`, `import_pandas()`, `import_narwhals()`, `import_ibis()`, `import_pyarrow()`, `import_pydantic()`) into `mountainash/core/lazy_imports.py`.

Source: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-dataframes/src/mountainash_dataframes/runtime_imports.py`

These are backend-agnostic utilities used by all modules.

### Fix 3: Mass rewrite broken imports

Script rewrites all references in schema and pydata:
- `mountainash.dataframes.factories` → `mountainash.core.factories`
- `mountainash.dataframes.runtime_imports` → `mountainash.core.lazy_imports`
- `mountainash.dataframes.typing` → `mountainash.dataframes.core.typing`

Also rewrite any references in expressions `runtime_imports.py` (if it exists there).

### Fix 4: Remove try/except guards

The schema `transform/__init__.py` currently wraps imports in try/except because they were broken. Remove the guards once imports work.

## Tests

### Expanded smoke tests

**Schema (`tests/schema/test_schema_smoke.py`):**
- `SchemaTransformFactory` can detect a Polars backend
- A rename transform applied to a Polars DataFrame produces correct column names
- A cast transform (string → int) works on a Polars DataFrame

**Pydata (`tests/pydata/test_pydata_smoke.py`):**
- `PydataIngressFactory` converts a dict to a Polars DataFrame
- `PydataIngressFactory` converts a list of dicts to a Polars DataFrame

**End-to-end (`tests/integration/test_pipeline.py`):**
- Python dict → Polars DataFrame via pydata → expression filter via `ma.table().filter(ma.col())` → verify result

### Regression

All existing 2939 tests continue to pass.

## Scope

**In scope:**
- Create `mountainash/core/factories.py` (from old dataframes source)
- Create `mountainash/core/lazy_imports.py` (from old dataframes source)
- Rewrite 56+ broken imports in schema and pydata
- Remove try/except guards in schema transform init
- Expand smoke tests for schema transforms and pydata ingress
- Add end-to-end pipeline test

**Out of scope:**
- Refactoring dataframes to use core factories (it has its own factory — leave it)
- Refactoring expressions to use core lazy_imports (it has its own runtime_imports — leave it)
- Comprehensive test suites for schema or pydata (Layer 5)
