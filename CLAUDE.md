# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Code Intelligence

Prefer LSP over Grep/Glob/Read for code navigation:
- `goToDefinition` / `goToImplementation` to jump to source
- `findReferences` to see all usages across the codebase
- `workspaceSymbol` to find where something is defined
- `documentSymbol` to list all symbols in a file
- `hover` for type info without reading the file
- `incomingCalls` / `outgoingCalls` for call hierarchy

Before renaming or changing a function signature, use
`findReferences` to find all call sites first.

Use Grep/Glob only for text/pattern searches (comments,
strings, config values) where LSP doesn't help.

After writing or editing code, check LSP diagnostics before
moving on. Fix any type errors or missing imports immediately.


## Superpowers Specs & Plans Location

Save all superpowers specs and plans to the **mountainash-central** repo, not this repo:

- **Specs:** `mountainash-central/04.planning/mountainash/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
- **Plans:** `mountainash-central/04.planning/mountainash/superpowers/plans/YYYY-MM-DD-<topic>.md`

Never save specs or plans under `docs/superpowers/` in this repo. The central repo is the single source of truth for all planning documents.


## Design Principles (MANDATORY)

**You MUST read the relevant principle documents before:**
- Making any architectural decision
- Adding or modifying operations, protocols, or function keys
- Changing backend implementations
- Modifying the extension model or naming conventions
- Resolving design tensions or trade-offs

This is not advisory. Do not rely on summaries, memory, or assumptions — read the actual principle document.

**Principles location:**
`/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash/`

See [PRINCIPLES.md](../mountainash-central/01.principles/mountainash/PRINCIPLES.md) for governance: statuses, category precedence, how to add new principles.

Each category has `core/` (cross-cutting) and module-specific subdirectories. See each category's INDEX.md for details and the root README.md for a by-module view.

### a. Architecture

| Document | Scope | Status | Summary |
|----------|-------|--------|---------|
| substrait-first-design.md | core | ENFORCED | All operations align with Substrait specification; custom ops in separate extension namespace |
| three-layer-separation.md | core | ENFORCED | Protocol → API Builder → Backend; each layer has a single responsibility |
| minimal-ast.md | expressions | ENFORCED | 9 expression node types; ScalarFunctionNode handles 90% of operations via function key ENUMs |
| unified-visitor.md | expressions | ADOPTED | Single visitor dispatches all expression node types via function registry lookup |
| wiring-matrix.md | expressions | ADOPTED | Every expression operation must be wired through all six architecture layers |
| relational-ast.md | relations | ENFORCED | 10 core Substrait-aligned relation nodes plus Mountainash extension leaf nodes |
| relation-visitor-composition.md | relations | ENFORCED | Relation visitor composes with expression visitor for embedded expression compilation |
| relation-dag-orchestrator.md | dag | ADOPTED | RelationDAG is a thin orchestrator over the existing visitor (+1 ref_resolver param, +2 leaf nodes) |
| two-edge-graph-model.md | dag | ENFORCED | RelationDAG keeps `dependency_edges` and `constraint_edges` sharply separate |

### b. Type System

| Document | Scope | Status | Summary |
|----------|-------|--------|---------|
| protocol-as-contract.md | core | ENFORCED | Protocol classes are the source of truth for what a backend must implement |
| function-key-enums.md | expressions | ENFORCED | Every operation has an ENUM key (FKEY_* prefix); type-safe dispatch and registry lookup |
| expression-type-generics.md | expressions | ENFORCED | Protocols are generic over ExpressionT; backends bind concrete types |
| node-type-design.md | expressions | ADOPTED | Pydantic-based nodes carry metadata but no logic beyond accept() |
| three-valued-semantics.md | expressions | ENFORCED | TRUE=1, UNKNOWN=0, FALSE=-1; sentinel integer values, not NULL propagation |
| booleanization.md | expressions | ENFORCED | Ternary expressions auto-booleanize at compile time; six built-in booleanizers |
| sentinel-values.md | expressions | ADOPTED | t_col(name, unknown={...}) treats custom values as UNKNOWN |
| bidirectional-coercion.md | expressions | ADOPTED | Boolean↔ternary coercion happens automatically at the API builder level |
| typespec-metadata-standard.md | typespec | ADOPTED | TypeSpec is the serializable Frictionless-aligned type specification |
| lossless-frictionless-storage.md | typespec | ADOPTED | `DataResource.table_schema` stores raw Frictionless schema dicts; conversion to TypeSpec is lazy |
| frictionless-structural-fidelity.md | typespec | ENFORCED | TypeSpec mirrors Frictionless Table Schema structurally; flat fields, no custom submodels |

### c. API Design

| Document | Scope | Status | Summary |
|----------|-------|--------|---------|
| fluent-builder-pattern.md | core | ENFORCED | Method chaining via __getattr__ dispatch; explicit namespaces via descriptors |
| polars-api-substrait-ast.md | core | ADOPTED | Public API mirrors Polars conventions; internal AST stays Substrait-aligned; API builder is the translation boundary |
| build-then-compile.md | expressions | ENFORCED | Expressions build a backend-agnostic AST; .compile(df) detects backend and produces native expressions |
| operator-overloading.md | expressions | ENFORCED | Python operators map to named methods; reversed operators supported |
| short-aliases.md | expressions | ENFORCED | All aliases live in extension builders; Substrait builders contain only canonical names |
| free-function-entrypoints.md | expressions | ADOPTED | `entrypoints.py` conventions: when to use free functions vs fluent methods |
| build-then-collect.md | relations | ENFORCED | Relations build a backend-agnostic plan tree; .collect()/.to_polars() triggers visitor compilation |
| scalar-terminal-composition.md | relations | ADOPTED | Scalar terminals on `Relation` are thin compositions over aggregate expression functions |
| build-then-conform.md | conform | ENFORCED | ma.relation(df).conform(spec).to_polars() — conform is a Relation method producing ProjectRelNode; cross-backend automatic |

### d. Cross-Backend

| Document | Scope | Status | Summary |
|----------|-------|--------|---------|
| backend-detection.md | core | ENFORCED | Automatic backend detection from DataFrame type; registered via decorator |
| consistency-guarantees.md | core | ENFORCED | Same expression/relation must produce same logical result across all backends |
| known-divergences.md | core | ADOPTED | Backend-specific quirks tracked via `KNOWN_EXPR_LIMITATIONS` registries and xfail markers |
| upstream-fix-monitoring.md | core | ADOPTED | Link upstream issues, monitor changelogs, reconciliation audit for xfails |
| arguments-vs-options.md | expressions | ENFORCED | Arguments are visited expressions; options are raw literals; universally-literal params MUST be options |
| cross-type-joins.md | relations | ADOPTED | Joins accept any data type; automatic coercion at visit time |

### e. Extension Model

| Document | Scope | Status | Summary |
|----------|-------|--------|---------|
| substrait-vs-mountainash.md | core | ENFORCED | Physical directory separation at every layer; FKEY_SUBSTRAIT_* vs FKEY_MOUNTAINASH_* enums |
| adding-operations.md | core | ADOPTED | Six-step process: enum → protocol → API builder → all backends → function mapping → tests |
| backend-composition.md | core | ENFORCED | Each backend composes all protocol implementations via multiple inheritance |

### f. Development Practices

| Document | Status | Summary |
|----------|--------|---------|
| naming-conventions.md | ENFORCED | File prefixes (exn_, prtcl_, api_bldr_, expsys_), backend prefixes (pl_, ib_, nw_) |
| testing-philosophy.md | ENFORCED | Cross-backend parametrized tests; xfail for known quirks; never skip or disable |
| cross-backend-test-coverage.md | ENFORCED | Every new expression test must be cross-backend parametrized; Polars-only tests require explicit justification |
| file-organisation.md | ADOPTED | 5-module package structure (expressions, relations, typespec, conform, pydata); expressions use three-layer mirror |
| import-conventions.md | ENFORCED | Four import categories; lazy_loader for __init__.py, lazy_imports for runtime optional backends |
| closed-by-default-verification.md | ADOPTED | Verification systems must fail on undiscovered items, not silently skip |

### h. Backlog

See [BACKLOG_INDEX.md](../mountainash-central/01.principles/mountainash/h.backlog/BACKLOG_INDEX.md) for prioritized items. Items organized into `active/`, `deferred/`, and `archive/` subdirectories.

### i. Competitor Analysis

| Document | Status | Summary |
|----------|--------|---------|
| competitive-positioning.md | ADOPTED | Market landscape, strengths/weaknesses, positioning as "abstract data products" |

### j. Research

| Document | Status | Summary |
|----------|--------|---------|
| introspection-driven-verification-patterns.md | REFERENCE | Prior art: 9 patterns for protocol/reflection-based test completeness |
| r-ast-expression-architecture-comparison.md | REFERENCE | R's dplyr/data.table AST vs Python expression systems |
| unified-package-roadmap.md | REFERENCE | Historical roadmap from the unified package migration |


## Package Structure

```
src/mountainash/
├── __init__.py                  # Top-level re-exports (col, lit, when, relation, typespec, etc.)
├── core/                        # Shared infrastructure (constants, types, enums, factories, io)
│   └── dtypes/                 # Canonical type system: MountainashDtype canon, TypeTarget,
│                               #   DtypeRegistry (schema/cast uses), parse_dtype/parse_cast_target,
│                               #   NativeDtype, cast-safety table, 6 lazy per-target modules
├── expressions/                 # Expression AST (mature, ~25k lines, ~2850 tests)
│   ├── core/                   # Nodes, protocols, API builders, function keys
│   └── backends/               # Polars, Ibis, Narwhals ExpressionSystem implementations
├── relations/                   # Relational AST (~60 files, 290 tests)
│   ├── core/
│   │   ├── relation_nodes/     # 10 Substrait-aligned + extension node types (reln_*)
│   │   │   ├── substrait/      # Substrait-aligned nodes
│   │   │   └── extensions_mountainash/  # SourceRelNode, RefRelNode, ResourceReadRelNode, util ops
│   │   ├── relation_protocols/ # 9 protocol files + RelationSystem base (prtcl_relsys_*)
│   │   ├── relation_api/       # Relation fluent API, GroupedRelation
│   │   └── unified_visitor/    # UnifiedRelationVisitor (with optional ref_resolver kwarg)
│   ├── dag/                    # RelationDAG orchestrator (pure orchestration, no file I/O)
│   │   ├── dag.py              # RelationDAG, dependency_edges, constraint_edges, collect()
│   │   ├── resource_ref.py     # ResourceRef wrapper (tabular + non-tabular)
│   │   └── errors.py           # RelationDAGRequired, MissingResourceSchema, UnsupportedResourceFormat
│   └── backends/
│       └── relation_systems/   # Polars (relsys_pl_*), Narwhals (relsys_nw_*), Ibis (relsys_ib_*)
├── typespec/                    # Type metadata — serializable Frictionless-aligned specs
│   ├── spec.py                 # TypeSpec, FieldSpec, FieldConstraints
│   ├── universal_types.py      # UniversalType enum + bidirectional boundary map to MountainashDtype
│   │                           #   (to_canonical/from_canonical/parse_universal) — Frictionless boundary only
│   ├── frictionless.py         # Frictionless Table Schema import/export
│   ├── datapackage.py          # TableDialect, DataResource, DataPackage (multi-resource container)
│   ├── extraction.py           # Extract TypeSpec from DataFrames/dataclasses/Pydantic via core.dtypes registry
│   ├── validation.py           # Validate DataFrames against a TypeSpec
│   ├── converters.py           # TypeSpec -> backend schemas via core.dtypes registry
│   └── custom_types.py         # CustomTypeRegistry, semantic type converters
├── conform/                     # Shared helper for TypeSpec conformance
│   └── expressions.py          # _build_conform_exprs — used by Relation.conform() and DAG visitor
└── pydata/                      # Python data ingress/egress with three-tier hybrid conversion
    ├── ingress/                # Python data -> Polars DataFrame (11 handlers)
    └── egress/                 # DataFrame -> Python collections (tuples, dicts, dataclasses, Pydantic)
```

For detailed file organisation see principle: `f.development-practices/file-organisation.md`


## Dependencies

**IMPORTANT:** Using **local Ibis fork** with Polars calendar interval fix:

```toml
ibis-framework = { path = "/home/nathanielramm/git/ibis", extras = ["pandas", "sqlite", "duckdb"] }
```

All other dependencies are in `pyproject.toml`.

**Workspace dependency for DataPackage I/O:** `mountainash-utils-files` (sibling package, optional `storage` extra) provides `StorageFacade` used by `core/io.py` to load remote `DataResource` paths. `core.io.is_remote()` delegates to the facade's scheme registry for auto-detection; `core.io.facade_read_bytes()` calls `StorageFacade.from_path()`. Local paths bypass the facade and use Polars directly. The import is lazy so a local-only test run never touches `mountainash_utils_files`.


## Development Commands

```bash
# Testing
hatch run test:test                  # Full suite with coverage
hatch run test:test-quick            # Fast iteration (no coverage)
hatch run test:test-target <path>    # Specific file or test
hatch run test:test-target-quick <path>  # Specific, no coverage

# Linting & type checking
hatch run ruff:check                 # Check for issues
hatch run ruff:fix                   # Auto-fix issues
hatch run mypy:check                 # Type safety validation

# Building
hatch build

# Upstream issue reconciliation
python scripts/audit_upstream_issues.py --skip-github                          # Local cross-reference only
python scripts/audit_upstream_issues.py --report-file scripts/outputs/reconciliation-report.md  # Full audit with GitHub checks
python scripts/validate_upstream_registry.py                                   # Validate YAML schema

# Drift guard xfail report
python scripts/report_drift_guards.py                                                     # Terminal summary
python scripts/report_drift_guards.py --report-file scripts/outputs/drift-guards-report.md  # Save to file
```


## Import Paths

```python
# Public API (both work identically)
import mountainash as ma                    # Canonical
from mountainash import col, lit, coalesce, greatest, least, when, native, t_col

# Relations API
from mountainash import relation, concat    # or ma.relation(df), ma.concat([r1, r2])

# Data Package + Relation DAG (Frictionless integration)
from mountainash import (
    DataPackage, DataResource, TableDialect,    # Frictionless metadata types
    RelationDAG, ResourceRef,                    # DAG orchestrator + resource wrapper
)

# Constants (shared core)
from mountainash.core.constants import (
    CONST_BACKEND, CONST_BACKEND_SYSTEM,    # Backend detection + routing enums
    ProjectOperation, JoinType, SetType,     # Relational AST enums
    SortField, ExecutionTarget,              # Relational supporting types
)

# Function key enums (expressions)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    KEY_SCALAR_COMPARISON, KEY_SCALAR_BOOLEAN, MOUNTAINASH_TERNARY,
)

# Expression nodes
from mountainash.expressions.core.expression_nodes.substrait import (
    ScalarFunctionNode, FieldReferenceNode, LiteralNode,
)

# Relation nodes
from mountainash.relations.core.relation_nodes import (
    ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
    FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode, ExtensionRelNode,
)
```

## Relations Architecture

The `mountainash.relations` module provides a Substrait-aligned relational AST. It mirrors the expressions architecture:

**Build phase** (backend-agnostic):
```python
r = ma.relation(df).filter(ma.col("age").gt(30)).sort("name").head(10)
# Builds: FetchRelNode → SortRelNode → FilterRelNode → ReadRelNode
```

**Compile phase** (terminal operations trigger visitor):
```python
result = r.to_polars()  # Detects backend, walks tree, calls Polars methods
```

**Key concepts:**
- 10 node types mapping to Substrait logical relations
- UnifiedRelationVisitor composes with UnifiedExpressionVisitor for embedded expressions
- 3 backends: Polars (LazyFrame-based), Narwhals (pandas/PyArrow), Ibis (SQL)
- Cross-type joins: `relation(polars_df).join(pandas_df, on="id")` — automatic coercion
- `GroupedRelation` returned by `.group_by()`, only exposes `.agg()`
- **Conform** is a relation method: `ma.relation(df).conform(spec).to_polars()` — builds a `ProjectRelNode` from TypeSpec fields, cross-backend automatic

**Spec:** `mountainash-central/04.planning/mountainash/superpowers/specs/2026-03-28-relational-ast-design.md`

### Relation DAG (Frictionless Data Package integration)

Named relations can be grouped into a `RelationDAG` that lets one relation reference another via `dag.ref(name)`. The DAG holds two distinct edge sets: `dependency_edges` (drive `collect()` execution order) and `constraint_edges` (foreign-key metadata, never executed). `dag.collect(name)` topologically walks dependencies, materialises each upstream once into a per-call cache, then compiles the target via the existing `UnifiedRelationVisitor` with a `ref_resolver` closing over that cache.

A `DataPackage` (Frictionless multi-resource container) bridges in both directions:

```python
import mountainash as ma

# Read a Frictionless descriptor → DAG → collect a resource
pkg = ma.DataPackage.from_descriptor("datapackage.json")
dag = pkg.to_relation_dag()
df  = dag.collect("orders")

# Override a single resource for testing
dag = pkg.to_relation_dag(overrides={"orders": local_df})

# Build extra named relations on top
dag.add(
    "active_orders",
    dag.ref("orders").filter(ma.col("status").eq("active"))
)

# Reverse direction — export the DAG back to a descriptor
pkg2 = dag.to_package()
pkg2.write("./out/datapackage.json")
```

**Architectural notes:**
- The DAG is **not** a parallel visitor stack — it adds exactly `+1` visitor parameter (`ref_resolver`) and `+2` leaf node types (`RefRelNode`, `ResourceReadRelNode`). See `a.architecture/dag/relation-dag-orchestrator.md`.
- `DataResource.table_schema` stores the **raw Frictionless schema dict** (not `TypeSpec`) so byte-equivalent round-trip is preserved against real `datapackage.json` files. Conversion to `TypeSpec` happens lazily inside the visitor when conform actually runs. See `b.type-system/typespec/lossless-frictionless-storage.md`.
- Foreign keys become `constraint_edges`, never `dependency_edges`. A `DataPackage` read from disk yields a DAG with N nodes and zero dependency edges — every resource is independently loadable. See `a.architecture/dag/two-edge-graph-model.md`.
- Conform is cross-backend since the relation-native redesign (2026-05-15). The only known limitation is Ibis coalesce type strictness when `null_fill` mixes string columns with numeric literals.

**Spec:** `mountainash-central/04.planning/mountainash/superpowers/specs/2026-04-07-frictionless-datapackage-design.md`
**Plan:** `mountainash-central/04.planning/mountainash/superpowers/plans/2026-04-07-frictionless-datapackage.md`


## Documentation Corpora

This project has 4 registered documentation corpora from [hiivmind-corpus-data](https://github.com/hiivmind/hiivmind-corpus-data), providing indexed, concept-mapped reference docs for the upstream libraries mountainash builds on.

| Corpus | Covers |
|--------|--------|
| `polars` | Polars DataFrame library — expressions, lazy evaluation, IO, types (19 concepts) |
| `ibis` | Ibis framework — deferred execution, backend portability, expression API (15 concepts) |
| `narwhals` | Narwhals — dataframe-agnostic API, expression model, cross-backend behavior (14 concepts) |
| `substrait` | Substrait spec — query plans, type system, scalar/aggregate/window functions (13 concepts) |

Each corpus has a **concept graph** (`graph.yaml`) that maps the library's domain into named concepts with relationships (depends-on, part-of, extends, see-also). A **cross-corpus registry graph** (`.hiivmind/corpus/registry-graph.yaml`) then bridges equivalent concepts across all four libraries — 66 bridges linking concepts like `polars:string-expressions` ↔ `ibis:string-expressions` ↔ `narwhals:string-expressions` ↔ `substrait:scalar-functions`, with 25 query-routing aliases so a search for "datetime expressions" returns relevant docs from all four corpora simultaneously.

This is particularly valuable for mountainash because the expression system must produce identical results across Polars, Ibis, and Narwhals backends. When implementing or debugging a cross-backend operation, the corpora let you compare how each library handles it — e.g., querying "null handling" pulls up Polars' `fill_null`/`is_null`, Ibis' coalesce/ifelse, and Narwhals' cross-backend null semantics in one search.

**Registry:** `.hiivmind/corpus/registry.yaml`
**Cross-corpus bridges:** `.hiivmind/corpus/registry-graph.yaml`

**How to query:** Use `/hiivmind-corpus navigate` to search across corpora. Queries are routed through aliases and bridges, so searching a concept in one library automatically surfaces the equivalent docs in the others.

**When to use:** Consult the corpora when you need to understand how an upstream library implements something — e.g., how Polars handles string expressions, what Substrait's scalar function spec looks like, or how Ibis compiles temporal operations.

**When NOT to use:** For mountainash's own architecture and design decisions, use the Design Principles above instead. The corpora document the *upstream libraries*, not mountainash itself.


## GitHub Operations

This project uses [hiivmind-pulse-gh](https://github.com/hiivmind/hiivmind-pulse-gh) for GitHub automation.

**Configuration Location**: `/home/nathanielramm/git/mountainash-io/mountainash/.hiivmind/github`

Use the hiivmind-pulse-gh plugin for all GitHub operations (issues, PRs, milestones, project status) to benefit from automatic context enrichment.
