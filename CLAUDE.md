# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
| explicit-enforcement-role.md | core | ADOPTED | A field that documents must not also decide; CapabilityFact.enforcement is an explicit closed enum defaulting to the strict GATE role |
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
| conform-contract.md | conform | ADOPTED | One contract model, four policy dimensions (extra_columns/missing_columns/data_type/keys); drift report (ConformDrift) is the evaluator's dual via collect_with_drift(); single reconciler resolve_conform_output |

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
| typed-error-hierarchy.md | ADOPTED | MountainashError root; hybrid hierarchy (domain base where ≥2 errors); builtin-compat via MI; exceptions.py façade; boy-scout migration ratchet |
| closed-by-default-verification.md | ADOPTED | Verification systems must fail on undiscovered items, not silently skip |

### h. Backlog

See [BACKLOG_INDEX.md](../mountainash-central/01.principles/mountainash/h.backlog/BACKLOG_INDEX.md) for prioritized items. Items organized into `active/`, `deferred/`, and `archive/` subdirectories.

### i. Competitor Analysis

| Document | Status | Summary |
|----------|--------|---------|
| competitive-positioning.md | ADOPTED | Market landscape, strengths/weaknesses, positioning as "abstract data products" |
| declarative-vs-imperative-landscape.md | REFERENCE | Two-axis (transformation/orchestration) declarative map of the Python field; referenced matrix + per-tool deep dive vs Ibis/Substrait/Polars/dbt/SQLMesh/Dagster/Frictionless/Pandera/dlt; semantic-layer cluster (MetricFlow/Cube/BSL/Malloy) with translate-out (OSI) + integrate-up (BSL/Ibis) opportunities; mountainash subsumes Ibis+Narwhals reach behind Polars syntax; novelty = DataPackage-as-result + two-edge DAG + conform-node |
| semantic-layer-interchange-architecture.md | REFERENCE | OSI hub-and-spoke interop design: canonical SemanticModel + N adapters (not N²); hard seam = SQL-text metric ↔ AST measure (export free via Ibis/SQLGlot, import best-effort/lossy); reuses lossless-raw-storage + universal_types boundary-map + closed-by-default fidelity report; Tier-1 OSI, Tier-2 MetricFlow/BSL, long tail via OSI/Sidemantic; precedes brainstorm→spec gate |
| substrait-interoperability-ingestion.md | REFERENCE | Expands substrait-first-design's to_substrait/from_substrait future-consideration: making mountainash a Substrait consumer/producer, not just aligned; unlocks SQL ingestion (no parser), engine interop (DuckDB/Velox/DataFusion/Arrow), portable serializable plans; codec = function_anchor↔FKEY map + Rel↔node (mapping not reimpl); ExtendedExpression is the metric-import surface; producer near-free via ibis-substrait; scope-discipline risk = stay logical, not an execution engine |
| osi-specification-critique-swot.md | REFERENCE | Full OSI spec dissection (v0.1.1/v0.2.0.dev0): anatomy (datasets/relationships/fields/metrics/custom_extensions/ai_context), the dialect enum lumping 3 incompatible paradigms (SQL transpilable vs MDX OLAP vs MAQL LDM-context), "vendor-neutral envelope / vendor-specific payload" critique, SWOT, gap inventory; headline opportunity = Substrait ExtendedExpression as a neutral OSI dialect (mountainash leads, not just consumes); thoroughly referenced (MS Learn MDX, GoodData MAQL) |

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

All other dependencies are in `pyproject.toml`.

**Workspace dependency for DataPackage I/O:** `mountainash-transport` (sibling package, optional `storage` extra) provides `StorageFacade` used by `core/io.py` to load remote `DataResource` paths. `core.io.is_remote()` delegates to the facade's scheme registry for auto-detection; `core.io.facade_read_bytes()` calls `StorageFacade.from_path()`. Local paths bypass the facade and use Polars directly. The import is lazy so a local-only test run never touches `mountainash_transport`.


## Development Commands

**Run TARGETED tests only — never the full suite.** The mountainash suite is
enormous (~3000+ tests across three backends); running it per task or per review
wastes minutes and huge token/compute budgets. During development — and in every
subagent dispatch — scope tests to the file(s) the change touches with
`hatch run test:test-target-quick <path>` (or `test-target` when you need
coverage). The full `hatch run test:test` is reserved for CI and, at most, a
single pre-merge gate on the whole branch — it is never a per-task or per-review
command. If a change's blast radius is genuinely wider than one file, name the
specific affected test files/dirs, not the whole suite.

```bash
# Testing
hatch run test:test-target <path>    # Specific file or test  ← default during development
hatch run test:test-target-quick <path>  # Specific, no coverage  ← default during development

# Linting & type checking
hatch run ruff:check                 # Check for issues
hatch run ruff:fix                   # Auto-fix issues

# Building
# hatch build

# # Upstream issue reconciliation
# python scripts/audit_upstream_issues.py --skip-github                          # Local cross-reference only
# python scripts/audit_upstream_issues.py --report-file scripts/outputs/reconciliation-report.md  # Full audit with GitHub checks
# python scripts/validate_upstream_registry.py                                   # Validate YAML schema

# # Drift guard xfail report
# python scripts/report_drift_guards.py                                                     # Terminal summary
# python scripts/report_drift_guards.py --report-file scripts/outputs/drift-guards-report.md  # Save to file
```



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
