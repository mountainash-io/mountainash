# Phase 3: Port Schema to Unified Package — Design Spec

## Goal

Port `mountainash-schema` into `mountainash.schema` within the unified `mountainash` package, preserving all functionality and adding basic smoke tests.

## Context

### Current State

The unified `mountainash` package now has:
- `mountainash.core` — shared constants and types
- `mountainash.expressions` — column-level ops (2842+ tests)
- `mountainash.dataframes` — table-level ops with expression integration (85+ tests)

### mountainash-schema Current State

Located at `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-schema/`:

| Metric | Value |
|--------|-------|
| Source files | 20 (~6,325 lines) |
| Absolute imports to rewrite | 22 (`mountainash_schema.`) |
| Cross-package deps on mountainash_dataframes | 36 occurrences |
| Cross-package deps on mountainash_expressions | 0 |
| Test files | **0** (empty tests directory) |
| Backends | 5 (Polars, Ibis, Narwhals, Pandas, PyArrow) |

**Key dependency:** Schema imports factory base classes, constants, type aliases, and runtime import utilities from `mountainash_dataframes`. These will be rewritten to `mountainash.dataframes`.

## What Gets Ported

### Source Structure

```
src/mountainash/schema/
├── __init__.py                          # 33 exports (SchemaConfig, UniversalType, etc.)
├── schema_utils.py                      # Utility functions (536 lines)
├── column_mapper/
│   └── __init__.py                      # Stub
├── config/                              # Core configuration (4,143 lines)
│   ├── __init__.py
│   ├── schema_config.py                 # SchemaConfig main class (1,001 lines)
│   ├── types.py                         # UniversalType enum + type mappings (708 lines)
│   ├── custom_types.py                  # TypeConverter, CustomTypeRegistry (907 lines)
│   ├── extractors.py                    # Schema extraction from dataclass/Pydantic/DataFrame (813 lines)
│   ├── converters.py                    # Convert schemas to backend formats (268 lines)
│   ├── validators.py                    # Schema validation (270 lines)
│   └── universal_schema.py              # TableSchema, SchemaField (29 lines)
└── transform/                           # Backend-specific transforms (1,550 lines)
    ├── __init__.py
    ├── cast_schema_factory.py           # Factory pattern (71 lines)
    ├── base_schema_transform_strategy.py # Base class (197 lines)
    ├── cast_schema_polars.py            # Polars (344 lines)
    ├── cast_schema_ibis.py              # Ibis (310 lines)
    ├── cast_schema_narwhals.py          # Narwhals (279 lines)
    ├── cast_schema_pandas.py            # Pandas (243 lines)
    └── cast_schema_pyarrow.py           # PyArrow (62 lines)
```

### Import Rewrites

1. **22 occurrences:** `mountainash_schema.` → `mountainash.schema.`
2. **36 occurrences:** `mountainash_dataframes.` → `mountainash.dataframes.` (cross-package dependency on factory base classes, constants, type aliases, runtime imports)
3. String references in lazy_loader and docstrings

### What Does NOT Port

- `__version__.py` (version lives at `mountainash` level)

## Public API

**No top-level exports.** Schema is a supporting module, not primary API. Access via:

```python
from mountainash.schema import SchemaConfig, UniversalType, SchemaTransformFactory
```

The `mountainash/__init__.py` is NOT modified. The schema stub `__init__.py` is replaced with the real module.

## Test Strategy

The original schema project has zero tests. Phase 3 adds basic smoke tests:

```
tests/schema/
├── __init__.py
└── test_schema_smoke.py    # 5-10 smoke tests
```

**Smoke tests cover:**
1. `SchemaConfig` can be instantiated
2. `UniversalType` enum values are accessible
3. `SchemaTransformFactory` can detect a Polars backend
4. A basic rename transform works on a Polars DataFrame
5. A basic cast transform works on a Polars DataFrame
6. Type mapping round-trip (Universal → Polars → Universal)

## Scope Boundaries

**In scope:**
- Port 20 source files into `src/mountainash/schema/`
- Rewrite 22 internal + 36 cross-package imports
- Write 5-10 smoke tests
- Verify existing expression + dataframes tests still pass

**Out of scope:**
- Architectural alignment
- Comprehensive test suite
- Backwards-compat shim for `mountainash_schema`
- Moving factory base classes to `mountainash.core`
- Top-level exports
