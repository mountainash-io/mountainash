# Unified Mountainash Package — Design Spec

## Goal

Unify four closely related packages (`mountainash-expressions`, `mountainash-dataframes`, `mountainash-schema`, `mountainash-pydata`) into a single `mountainash` package with optional modules, extracting shared infrastructure into a common core.

## Context

### Current State

Four separate git repositories under `mountainash-io/mountainash/`:

| Package | Purpose | Maturity | Last Active |
|---------|---------|----------|-------------|
| `mountainash-expressions` | Column-level ops (scalar functions, ternary logic) | Mature, 2849+ tests, wiring audit | March 2026 |
| `mountainash-dataframes` | Table-level ops (join, select, filter, cast, introspect) | Stale, architecturally behind | Nov 2025 |
| `mountainash-schema` | Schema definition, type mapping, column transforms | Beta, 5 backends | Nov 2025 |
| `mountainash-pydata` | Python data ingress/egress | Beta, egress incomplete | Nov 2025 |

### Problems

1. **Duplicated infrastructure** — Backend detection, type aliases, constants, registration decorators, and factory patterns are reimplemented in each package with slight variations.
2. **Architectural drift** — Expressions uses Substrait-aligned protocols with a wiring audit; the others use older factory/strategy patterns without the same rigour.
3. **Tight coupling** — Dataframes needs expressions for filtering. Schema supports expression-based transforms. Pydata feeds into dataframes. They are not independent.
4. **Maintenance burden** — Four CI pipelines, four release processes, four version matrices for a single maintainer. Three of the four have stalled.

### Why a Single Package

- **One backend registry, one detection path** — no duplicated plumbing
- **One wiring audit** — covers all modules
- **One release process** — reduces maintenance overhead
- **Optional modules** — users install only what they need
- **Shared core** — genuine infrastructure sharing, not just co-location

### Why NOT Merge Backend Implementations

Substrait separates expressions from relations. Every DataFrame library separates `Expr` from `DataFrame`. Column ops and table ops are different abstraction levels. Each module owns its backends and protocols — core provides only the shared plumbing.

## Target Architecture

### Package Identity

**Package name:** `mountainash`
**Import:** `import mountainash as ma`

**Install surface:**

| Install | Contents |
|---------|----------|
| `pip install mountainash` | Core + expressions (current default use case) |
| `pip install mountainash[dataframes]` | + table operations |
| `pip install mountainash[schema]` | + schema management |
| `pip install mountainash[pydata]` | + Python data ingress/egress |
| `pip install mountainash[all]` | Everything |

Expressions are NOT optional — they are the primary use case and a dependency of dataframes' filter operations.

### Directory Structure

```
src/mountainash/
├── __init__.py                          # Public API: col, lit, when, table, etc.
├── __version__.py
│
├── core/                                # SHARED INFRASTRUCTURE
│   ├── constants.py                     # CONST_BACKEND enum (POLARS, IBIS, NARWHALS)
│   ├── types.py                         # SupportedDataFrames, SupportedExpressions, TypeGuards
│   ├── detection.py                     # 3-tier backend detection (exact -> pattern -> log)
│   ├── registration.py                  # @register decorator machinery
│   └── lazy_imports.py                  # Shared lazy import utilities
│
├── expressions/                         # COLUMN-LEVEL OPS
│   ├── __init__.py                      # Expression-specific exports
│   ├── nodes/                           # 7-node AST (unchanged)
│   │   └── substrait/
│   ├── function_keys/                   # FKEY enums (unchanged)
│   │   └── enums.py
│   ├── function_mapping/                # Registry + definitions (unchanged)
│   ├── protocols/                       # ExpressionSystem protocols (unchanged)
│   │   ├── substrait/
│   │   └── extensions_mountainash/
│   ├── api/                             # Expression API builders (unchanged)
│   │   ├── api_base.py
│   │   ├── boolean.py
│   │   ├── entrypoints.py
│   │   └── api_builders/
│   │       ├── substrait/
│   │       └── extensions_mountainash/
│   └── backends/                        # Expression backends (unchanged)
│       ├── polars/
│       ├── ibis/
│       └── narwhals/
│
├── dataframes/                          # TABLE-LEVEL OPS (Phase 2)
│   ├── __init__.py
│   ├── protocols/                       # DataFrameSystem protocols
│   │   ├── cast.py
│   │   ├── introspect.py
│   │   ├── select.py
│   │   ├── join.py
│   │   ├── filter.py
│   │   ├── row.py
│   │   └── lazy.py
│   ├── api/                             # TableBuilder fluent API
│   │   ├── table_builder.py
│   │   └── namespaces/
│   └── backends/                        # DataFrame backends
│       ├── polars/
│       ├── ibis/
│       └── narwhals/
│
├── schema/                              # SCHEMA MANAGEMENT (Phase 3)
│   ├── __init__.py
│   ├── config/                          # SchemaConfig, UniversalType, validators
│   ├── transform/                       # Schema transform strategies
│   └── backends/
│       ├── polars/
│       ├── ibis/
│       └── narwhals/
│
└── pydata/                              # PYTHON DATA INGRESS/EGRESS (Phase 4)
    ├── __init__.py
    ├── ingress/                          # Python -> DataFrame (10 handlers)
    └── egress/                           # DataFrame -> Python
```

### What Moves to Core

**Backend constants** (currently duplicated):
- `mountainash_expressions.core.constants.CONST_VISITOR_BACKENDS`
- `mountainash_dataframes.core.dataframe_system.constants.CONST_DATAFRAME_BACKEND`

Becomes: `mountainash.core.constants.CONST_BACKEND`

**Type aliases** (currently duplicated):
- `mountainash_expressions.types.SupportedExpressions`
- `mountainash_dataframes.core.typing.dataframes.SupportedDataFrames`
- `mountainash_dataframes.core.typing.expressions.SupportedExpressions`

All move to: `mountainash.core.types`

**Backend detection** (currently duplicated):
- Expressions: `ExpressionSystemFactory` with type-based dispatch
- Dataframes: `DataFrameTypeFactoryMixin` with 3-tier detection
- Schema: `CastSchemaFactory` with similar detection

Becomes: `mountainash.core.detection` using the 3-tier approach (exact match, pattern match, log unknown)

**Registration decorator** (currently duplicated):
- Expressions: `@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)`
- Dataframes: `@register_dataframe_system(CONST_DATAFRAME_BACKEND.POLARS)`

Becomes: shared machinery in `mountainash.core.registration` that each module's decorator delegates to.

**What does NOT move to core:**
- Function keys, AST nodes — expression-specific
- Protocols — each module owns its own
- API builders — each module owns its own
- Backend implementations — each module owns its own
- SchemaConfig, UniversalType — schema-specific
- Ingress/egress handlers — pydata-specific

**Boundary principle:** Core provides the plumbing, modules provide the logic.

### Public API

```python
import mountainash as ma

# Expressions (always available - current API unchanged)
ma.col("age").gt(30)
ma.lit(42)
ma.when(ma.col("x").gt(0)).then(ma.lit("pos")).otherwise(ma.lit("neg"))
ma.coalesce(ma.col("a"), ma.col("b"))
ma.t_col("score", unknown={-99999})

# Dataframes (requires [dataframes])
ma.table(df).select("id", "name").filter(ma.col("age").gt(30))
ma.table(df).join(other_df, on="id", how="left")
ma.table(df).to_pandas()

# Schema (requires [schema])
ma.SchemaConfig(columns={...})

# Pydata (requires [pydata])
ma.ingress([{"id": 1, "name": "Alice"}])
```

## Migration Path

### Phase 1: Restructure (this spec's implementation scope)

Work happens in the existing `mountainash-expressions` git repo. The repo directory is NOT renamed (that can happen later) — only the Python package inside it changes.

1. Rename the Python package from `mountainash_expressions` to `mountainash` (i.e., `src/mountainash_expressions/` becomes `src/mountainash/`)
2. Move expression-specific code into `src/mountainash/expressions/`
3. Extract shared infrastructure into `src/mountainash/core/`
4. Create `src/mountainash/__init__.py` exporting the current public API
5. Update all internal imports throughout the codebase
6. Create `src/mountainash_expressions/` as a backwards-compat shim package
7. All 2849+ existing tests pass with both import paths
8. Update `pyproject.toml` package name to `mountainash`

```python
# mountainash_expressions/__init__.py
import warnings
warnings.warn(
    "mountainash-expressions is deprecated. Use 'import mountainash as ma' instead.",
    DeprecationWarning,
    stacklevel=2,
)
from mountainash.expressions import *
from mountainash.expressions.api.entrypoints import col, lit, when, coalesce, greatest, least, native, t_col
```

### Phase 2: Port Dataframes (separate spec)

- Port `mountainash-dataframes` table operations into `mountainash/dataframes/`
- Bring architecture up to expressions standard (Substrait-informed protocols, wiring audit)
- Publish backwards-compat `mountainash-dataframes` shim

### Phase 3: Port Schema (separate spec)

- Port `mountainash-schema` into `mountainash/schema/`
- Align type system with `mountainash.core.types`
- Publish backwards-compat shim

### Phase 4: Port Pydata (separate spec)

- Port `mountainash-pydata` into `mountainash/pydata/`
- Publish backwards-compat shim

### Phase 5: Deprecation

- Old shim packages emit `DeprecationWarning` on import
- Remove shims in a major version bump

## Phase 1 Deliverables

### What Phase 1 Creates

- New `mountainash` package with `pyproject.toml` (optional deps for `[dataframes]`, `[schema]`, `[pydata]`, `[all]`)
- `mountainash/core/` with extracted shared infrastructure (constants, types, detection, registration)
- `mountainash/expressions/` containing all current expression code, restructured to import from core
- `mountainash/__init__.py` exporting the current public API
- Empty `mountainash/dataframes/__init__.py`, `mountainash/schema/__init__.py`, `mountainash/pydata/__init__.py` stubs with `ImportError` guards for optional dependencies
- Updated `pyproject.toml` with package rename and optional dependency groups
- All existing tests passing under new import structure

### What Phase 1 Preserves

- All 2849+ existing tests
- All existing import paths (via `mountainash_expressions` backwards-compat shim)
- All expression architecture internals (protocols, function keys, AST nodes, backends)
- Git history (this is a rename + restructure, not a new repo)

### What Phase 1 Does NOT Include

- Porting dataframes, schema, or pydata code
- Any new features or operations
- Renaming internal classes or protocols
- Changing the expression architecture
- Publishing to PyPI (that's a release decision, not a code decision)

## Scope Boundaries

**In scope (full design):**
- Target architecture for all four modules
- Core extraction specification
- Migration path (5 phases)
- Backwards compatibility strategy

**In scope (Phase 1 implementation):**
- Package restructure
- Core extraction
- Expression migration
- Backwards-compat shim
- Test preservation

**Out of scope:**
- Dataframes architecture redesign (Phase 2 spec)
- Schema alignment (Phase 3 spec)
- Pydata completion (Phase 4 spec)
- PyPI publication strategy
- CI/CD pipeline design
- Substrait relational alignment decision (deferred to Phase 2)
