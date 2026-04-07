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


## Design Principles (MANDATORY)

**You MUST read the relevant principle documents before:**
- Making any architectural decision
- Adding or modifying operations, protocols, or function keys
- Changing backend implementations
- Modifying the extension model or naming conventions
- Resolving design tensions or trade-offs

This is not advisory. Do not rely on summaries, memory, or assumptions — read the actual principle document.

**Principles location:**
`/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/`

See [PRINCIPLES.md](../mountainash-central/01.principles/mountainash-expressions/PRINCIPLES.md) for governance: statuses, category precedence, how to add new principles.

### a. Architecture

| Document | Status | Summary |
|----------|--------|---------|
| substrait-first-design.md | ENFORCED | All operations align with Substrait specification; custom ops in separate extension namespace |
| minimal-ast.md | ENFORCED | Only 7 node types; ScalarFunctionNode handles 90% of operations via function key ENUMs |
| three-layer-separation.md | ENFORCED | Protocol → API Builder → Backend; each layer has a single responsibility |
| unified-visitor.md | ADOPTED | Single visitor dispatches all node types via function registry lookup |
| relational-ast.md | ENFORCED | 10 relational node types mapping to Substrait logical relations; ExtensionRelNode for non-Substrait ops |
| relation-visitor-composition.md | ENFORCED | Relation visitor composes with expression visitor for embedded expression compilation |
| wiring-matrix.md | ADOPTED | Every operation must be wired through all six architecture layers |
| unified-package-roadmap.md | ADOPTED | Prioritized roadmap: wiring → shared infra → operations → alignment → release |

### b. Type System

| Document | Status | Summary |
|----------|--------|---------|
| function-key-enums.md | ENFORCED | Every operation has an ENUM key (FKEY_* prefix); type-safe dispatch and registry lookup |
| protocol-as-contract.md | ENFORCED | Protocol classes are the source of truth for what a backend must implement |
| expression-type-generics.md | ENFORCED | Protocols are generic over ExpressionT; backends bind concrete types; Ibis uses domain-specific types |
| node-type-design.md | ADOPTED | Pydantic-based nodes carry metadata but no logic beyond accept() |
| typespec-metadata-standard.md | ADOPTED | TypeSpec is the serializable Frictionless-aligned type specification; FieldSpec carries standard + custom types; ForeignKey/ForeignKeyReference for cross-table relationships; enum_weights for weighted enums |

### c. API Design

| Document | Status | Summary |
|----------|--------|---------|
| build-then-compile.md | ENFORCED | Expressions build a backend-agnostic AST; .compile(df) detects backend and produces native expressions |
| build-then-collect.md | ENFORCED | Relations build a backend-agnostic plan tree; .collect()/.to_polars() triggers visitor compilation |
| build-then-conform.md | ENFORCED | ma.conform({...}).apply(df) compiles TypeSpec to relation operations; replaces old schema backend strategies |
| fluent-builder-pattern.md | ENFORCED | Method chaining via __getattr__ dispatch; explicit namespaces via descriptors |
| operator-overloading.md | ENFORCED | Python operators map to named methods; reversed operators supported |
| short-aliases.md | ENFORCED | All aliases live in extension builders; Substrait builders contain only canonical names |

### d. Ternary Logic

| Document | Status | Summary |
|----------|--------|---------|
| three-valued-semantics.md | ENFORCED | TRUE=1, UNKNOWN=0, FALSE=-1; sentinel integer values, not NULL propagation |
| booleanization.md | ENFORCED | Ternary expressions auto-booleanize at compile time; six built-in booleanizers |
| sentinel-values.md | ADOPTED | t_col(name, unknown={...}) treats custom values as UNKNOWN |
| bidirectional-coercion.md | ADOPTED | Boolean↔ternary coercion happens automatically at the API builder level |

### e. Cross-Backend

| Document | Status | Summary |
|----------|--------|---------|
| backend-detection.md | ENFORCED | Automatic backend detection from DataFrame type; registered via decorator |
| consistency-guarantees.md | ENFORCED | Same expression must produce same logical result across all backends |
| known-divergences.md | ADOPTED | SQLite integer division, modulo sign semantics, Ibis type inference gaps, expression argument limitations tracked via `KNOWN_EXPR_LIMITATIONS` registries |
| cross-type-joins.md | ADOPTED | Joins accept any data type; automatic coercion at visit time; execute_on for explicit control |
| arguments-vs-options.md | ENFORCED | Arguments are visited expressions; options are raw literals; universally-literal params MUST be options; `_call_with_expr_support` + `KNOWN_EXPR_LIMITATIONS` registry enriches errors when backends reject expressions |

### f. Extension Model

| Document | Status | Summary |
|----------|--------|---------|
| substrait-vs-mountainash.md | ENFORCED | Physical directory separation at every layer; FKEY_SUBSTRAIT_* vs FKEY_MOUNTAINASH_* enums |
| adding-operations.md | ADOPTED | Six-step process: enum → protocol → API builder → all backends → function mapping → tests |
| backend-composition.md | ENFORCED | Each backend composes all protocol implementations via multiple inheritance |

### g. Development Practices

| Document | Status | Summary |
|----------|--------|---------|
| naming-conventions.md | ENFORCED | File prefixes (exn_, prtcl_, api_bldr_, expsys_), backend prefixes (pl_, ib_, nw_) |
| testing-philosophy.md | ENFORCED | Cross-backend parametrized tests; xfail for known quirks; never skip or disable |
| file-organisation.md | ADOPTED | 5-module package structure (expressions, relations, typespec, conform, pydata); expressions use three-layer mirror |
| import-conventions.md | ENFORCED | Four import categories; lazy_loader for __init__.py, lazy_imports for runtime optional backends, TYPE_CHECKING for annotations; ruff FA+TCH enforcement |

### h. Backlog

| Document | Summary |
|----------|---------|
| polars-alignment-deferred.md | Deferred work from Polars API alignment batches 1–7 |

### i. Competitor Analysis

| Document | Status | Summary |
|----------|--------|---------|
| competitive-positioning.md | ADOPTED | Market landscape, Socratic strengths/weaknesses, feature gaps, positioning as "abstract data products" alongside Ibis/Narwhals/Pandera |


## Package Structure

```
src/mountainash/
├── __init__.py                  # Top-level re-exports (col, lit, when, relation, conform, typespec, etc.)
├── core/                        # Shared infrastructure (constants, types, enums, factories)
├── expressions/                 # Expression AST (mature, ~25k lines, ~2850 tests)
│   ├── core/                   # Nodes, protocols, API builders, function keys
│   └── backends/               # Polars, Ibis, Narwhals ExpressionSystem implementations
├── relations/                   # Relational AST (~60 files, 290 tests)
│   ├── core/
│   │   ├── relation_nodes/     # 10 Substrait-aligned node types (reln_*)
│   │   ├── relation_protocols/ # 9 protocol files + RelationSystem base (prtcl_relsys_*)
│   │   ├── relation_api/       # Relation fluent API, GroupedRelation
│   │   └── unified_visitor/    # UnifiedRelationVisitor
│   └── backends/
│       └── relation_systems/   # Polars (relsys_pl_*), Narwhals (relsys_nw_*), Ibis (relsys_ib_*)
├── typespec/                    # Type metadata — serializable Frictionless-aligned specs
│   ├── spec.py                 # TypeSpec, FieldSpec, FieldConstraints
│   ├── universal_types.py      # UniversalType enum, backend type mappings
│   ├── type_bridge.py          # UniversalType <-> MountainashDtype interim bridge
│   ├── frictionless.py         # Frictionless Table Schema import/export
│   ├── extraction.py           # Extract TypeSpec from DataFrames, dataclasses, Pydantic
│   ├── validation.py           # Validate DataFrames against a TypeSpec
│   ├── converters.py           # UniversalType -> backend-specific types
│   └── custom_types.py         # CustomTypeRegistry, semantic type converters
├── conform/                     # Data conformance — compiles TypeSpec to relation operations
│   ├── builder.py              # ConformBuilder — user-facing DSL (ma.conform)
│   └── compiler.py             # compile_conform() — ~130 lines replacing ~1,400 lines of backend strategies
└── pydata/                      # Python data ingress/egress with three-tier hybrid conversion
    ├── ingress/                # Python data -> Polars DataFrame (11 handlers)
    └── egress/                 # DataFrame -> Python collections (tuples, dicts, dataclasses, Pydantic)
```

For detailed file organisation see principle: `g.development-practices/file-organisation.md`


## Dependencies

**IMPORTANT:** Using **local Ibis fork** with Polars calendar interval fix:

```toml
ibis-framework = { path = "/home/nathanielramm/git/ibis", extras = ["pandas", "sqlite", "duckdb"] }
```

All other dependencies are in `pyproject.toml`.


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
```


## Import Paths

```python
# Public API (both work identically)
import mountainash as ma                    # Canonical
import mountainash_expressions as ma        # Deprecated, works via shim
from mountainash import col, lit, coalesce, greatest, least, when, native, t_col

# Relations API
from mountainash import relation, concat    # or ma.relation(df), ma.concat([r1, r2])

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

**Spec:** `docs/superpowers/specs/2026-03-28-relational-ast-design.md`


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
