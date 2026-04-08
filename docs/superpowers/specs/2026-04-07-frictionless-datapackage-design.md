# Frictionless Data Package Support

**Date:** 2026-04-07
**Status:** Design / approved for planning
**Scope:** First-class support for the Frictionless Data Package standard — descriptor round-trip, multi-resource materialization, and a Relation DAG orchestrator. Continues mountainash's Frictionless alignment work. Explicitly excludes dbt compatibility.

## Motivation

mountainash already implements the Frictionless **Table Schema** spec via `TypeSpec`/`FieldSpec` and round-trips single-table descriptors via `typespec/frictionless.py`. This design extends that foundation to the **multi-resource container** layer of the standard:

- A `DataPackage` is a coherent collection of `DataResource`s with package-level metadata and a `datapackage.json` descriptor.
- A `DataResource` describes one tabular file (or multi-file group, or inline data, or non-tabular asset) plus its schema, dialect, format, and locator.
- Resources may declare `foreignKeys` referencing fields on other resources within the same package.

The companion deliverable is a **Relation DAG** — a thin orchestrator that lets named relations reference each other via `dag.ref(name)` so that a DataPackage descriptor can be loaded, materialized through the storage facade, conformed to its declared schemas, and queried as one coherent dataset.

This design intentionally **does not** pursue dbt compatibility. A prior investigation (`docs/superpowers/specs/2026-04-04-dbt-datapackage-relation-dag-design.md`) covered that path; the present design extracts only the DataPackage and Relation DAG layers from it and discards the dbt SQL compiler.

## What already exists (reused, not rebuilt)

| Capability | Lives in | What it does |
|---|---|---|
| Single-table Frictionless round-trip | `typespec/frictionless.py` | `typespec_from_frictionless` / `typespec_to_frictionless` for one Table Schema |
| TypeSpec / FieldSpec / ForeignKey | `typespec/spec.py` | Schema metadata model |
| Conform compiler | `conform/` | `ma.conform(spec).apply(df)` — TypeSpec → relation operations |
| Pydata ingress | `pydata/ingress/` | Python collections (list/dict/tuple/dataclass/pydantic) → Polars DataFrame |
| Relation AST + visitor | `relations/core/` | 10 node types, `UnifiedRelationVisitor` composing with `UnifiedExpressionVisitor` |
| Backend relation systems | `relations/backends/relation_systems/` | Polars / Narwhals / Ibis implementations |
| Storage facade | `mountainash-utils-files` (`storage_facade/`, `storage_backends/`) | Local / MinIO / R2 / S3 / S3express read/write/list/copy/delete protocols |

The new code is glue + a small metadata layer + one new node type. Nothing in `expressions/`, `conform/`, or `pydata/` changes.

## Architecture overview

```
                    ┌────────────────────────────┐
       NEW          │  typespec.datapackage      │  DataPackage / DataResource / TableDialect
                    │  (Pydantic, round-trip)    │
                    └──────────────┬─────────────┘
                                   │
       NEW          ┌──────────────▼─────────────┐
                    │  relations.dag             │  RelationDAG, ResourceRef
                    │  (orchestrator, not AST)   │  dependency_edges + constraint_edges, .collect()
                    └──────────────┬─────────────┘
                                   │
       MINIMAL ADD  ┌──────────────▼─────────────┐
                    │  relations.core            │  +RefRelNode, +ResourceReadRelNode
                    │  +UnifiedRelationVisitor   │  +ref_resolver kwarg
                    │  +per-backend visit methods│
                    └──────────────┬─────────────┘
                                   │
       REUSED       typespec.frictionless · conform · pydata.ingress · relations · mountainash-utils-files
```

## Design

### 1. New types (`src/mountainash/typespec/datapackage.py`)

#### `TableDialect`

Pydantic dataclass mirroring the Frictionless Table Dialect spec. Fields (all optional, all spec-compliant defaults):

- `delimiter`, `lineTerminator`, `quoteChar`, `doubleQuote`, `escapeChar`, `nullSequence`, `skipInitialSpace`
- `header`, `headerRows`, `headerJoin`, `commentChar`, `caseSensitiveHeader`
- `csvddfVersion` (preserved on round-trip)

Round-trip: `TableDialect.from_descriptor(d: dict)` / `.to_descriptor() -> dict`. At materialization time the dialect is translated to `pl.read_csv` keyword arguments by the `ResourceReadRelNode` visit method.

#### `DataResource`

Wraps a `TypeSpec` with resource-level metadata. Pydantic dataclass.

- **Required:** `name: str` (unique within package; must be lowercase + alphanumeric + `.-_`)
- **Required (exactly one):** `path: str | list[str]` *or* `data: Any` (inline). Validated on construction.
- **Tabular fields:** `type: Literal["table"] | None`, `dialect: TableDialect | None`, `schema: TypeSpec | None`, `format: str | None`, `mediatype: str | None`, `encoding: str | None`
- **General fields:** `title`, `description`, `bytes`, `hash`, `sources`, `licenses`
- **Round-trip safety:** `extras: dict[str, Any]` preserves any unknown properties found in the descriptor.

Schema serialization delegates to existing `typespec_from_frictionless` / `typespec_to_frictionless`.

#### `DataPackage`

Container of resources plus package-level metadata. Pydantic dataclass.

- **Required:** `resources: list[DataResource]` (≥1 element, names unique)
- **SHOULD have:** `name`, `id`, `licenses`, `$schema` (preserved as observed; new packages default to `2.0`)
- **Optional:** `title`, `description`, `homepage`, `version`, `created`, `keywords`, `contributors`, `sources`, `image`
- **Round-trip safety:** `extras: dict[str, Any]`

**Construction validation:**
- Resource names must be unique within the package.
- Each resource must declare exactly one of `path | data`.
- Every `foreignKey.reference.resource` value must resolve to an existing resource name in the package (or `""` for self-reference, per spec).

**Round-trip API:**
```python
pkg = DataPackage.from_descriptor("datapackage.json")  # path | dict | str
pkg = DataPackage.from_descriptor(open("datapackage.json").read())
descriptor: dict = pkg.to_descriptor()
pkg.write("datapackage.json")
```

Resource-level `sources` / `licenses` are **preserved as-observed** (not expanded from the package level on read). This ensures byte-equivalent round-trip when the user does not mutate the package.

### 2. New AST nodes (`src/mountainash/relations/core/relation_nodes/extension/`)

Both nodes are mountainash extensions (`FKEY_MOUNTAINASH_RELATION_*`), not Substrait — `ref` and `resource_read` are not part of the Substrait spec.

#### `ResourceReadRelNode`

Carries a full `DataResource` and an optional output `TypeSpec`.

At visit time, the per-backend `visit_resource_read_rel` implementation:

1. If `resource.data` is set (inline): hand the value to `pydata.ingress` to produce a Polars DataFrame.
2. Else (`resource.path` is set): resolve the path through the storage facade (`mountainash-utils-files`). For multi-file `path: [...]`, read each, then vertical-concat (the spec mandates same dialect/schema/structure across files).
3. Dispatch to a reader by `format` / `mediatype`:
   - CSV → `pl.read_csv` with `TableDialect` kwargs translated
   - JSON → `pl.read_json`
   - Parquet → `pl.read_parquet`
4. If `resource.schema` is present, apply `ma.conform(schema)` to the loaded frame.
5. Return the backend-native object (e.g. `pl.LazyFrame`).

If `format`/`mediatype` cannot be resolved or no reader is registered, raise `UnsupportedResourceFormat` with the resource name and observed format.

#### `RefRelNode`

Carries `name: str` and an optional `output_schema: TypeSpec`. The schema is populated when the upstream relation has a known TypeSpec (e.g. came from a `DataResource` with a schema).

At visit time the per-backend `visit_ref_rel` implementation calls `ctx.ref_resolver(node.name)`. If no `ref_resolver` is on the visit context, raise `RelationDAGRequired` — i.e. a relation containing a `RefRelNode` cannot be compiled standalone, only inside a `RelationDAG.collect()`.

Both nodes go through the full six-layer wiring matrix per `wiring-matrix.md` (enum → protocol → builder → 3 backends → function map → tests).

### 3. `RelationDAG` (`src/mountainash/relations/dag/`)

Thin orchestrator. Not a Relation, not an AST node, not visitable. A graph **of** relation trees that share the existing visitor infrastructure.

```python
class RelationDAG:
    relations: dict[str, Relation]               # named tabular relations
    assets:    dict[str, ResourceRef]            # non-tabular wrappers (read_bytes only)
    dependency_edges: set[tuple[str, str]]       # derived from RefRelNode walking
    constraint_edges: set[tuple[str, str]]       # derived from foreignKeys

    def add(self, name: str, relation: Relation) -> None: ...
    def ref(self, name: str) -> Relation: ...    # produces a Relation wrapping a RefRelNode
    def topological_order(self, target: str | None = None) -> list[str]: ...
    def collect(self, name: str, *, backend: Backend | None = None) -> Any: ...
    def to_package(self) -> DataPackage: ...

    @classmethod
    def from_package(
        cls,
        pkg: DataPackage,
        overrides: dict[str, Any] | None = None,
    ) -> RelationDAG: ...
```

**`ResourceRef`** is the unified iteration wrapper: every resource (tabular or non-tabular) becomes a `ResourceRef`, exposing `.read_bytes()` always and `.relation()` only when the resource is tabular.

**Two edge sets, sharply distinct:**
- `dependency_edges` are derived by walking each named relation's tree for `RefRelNode` instances. They drive `topological_order()` and `collect()` execution order. They are the *only* thing that controls evaluation.
- `constraint_edges` are derived from `TypeSpec` foreignKeys at construction time. They are metadata only — used by validation tools, never by `collect()`. There is intentionally no `dag.edges` accessor that conflates the two.

**`collect(name)` algorithm:**
1. Compute topological order over `dependency_edges` reachable from `name`.
2. Initialize `cache: dict[str, Any] = {}`.
3. Build `ref_resolver = lambda n: cache[n]`.
4. For each upstream `u` in topological order: walk its relation tree with `UnifiedRelationVisitor(backend, ref_resolver=ref_resolver)`, store the result as `cache[u]`.
5. Compile `name` itself the same way and return the backend-native result.

Caching is per-`collect()` call. Cross-call memoization is out of scope (see § Out of scope).

### 4. Visitor changes

`UnifiedRelationVisitor.__init__` gains:

```python
def __init__(self, backend, *, ref_resolver: Callable[[str], Any] | None = None):
```

Default `None` keeps standalone Relation behaviour unchanged. A `RefRelNode` encountered without a resolver raises `RelationDAGRequired`.

Each `relation_system_*` (Polars, Narwhals, Ibis) gains exactly two new visit methods:

- `visit_ref_rel(node, ctx)` — `return ctx.ref_resolver(node.name)`
- `visit_resource_read_rel(node, ctx)` — invokes the storage facade, dispatches to the format-specific reader, applies conform if a schema is present, returns the backend-native object

No new protocols. No new visitor class. No special-casing — same wiring as any other op.

### 5. API surface

```python
import mountainash as ma

# --- Read a descriptor from disk -----------------------------------
pkg = ma.DataPackage.from_descriptor("datapackage.json")
dag = pkg.to_relation_dag()
df  = dag.collect("orders").to_polars()             # storage facade + conform run automatically

# Override one resource (testing, swap of trusted/untrusted source)
dag = pkg.to_relation_dag(overrides={"orders": orders_df_in_memory})

# Build extra named relations on top of package resources
dag.add(
    "active_orders",
    dag.ref("orders")
        .filter(ma.col("status").eq("active"))
        .join(dag.ref("customers"), on="customer_id"),
)
active = dag.collect("active_orders").to_polars()

# --- Pure Python, no descriptor at all ----------------------------
dag = ma.RelationDAG()
dag.add("stg_orders", ma.relation(orders_df).conform(order_spec))
dag.add("stg_cust",   ma.relation(cust_df).conform(cust_spec))
pkg = dag.to_package()
pkg.write("./out/datapackage.json")
```

Top-level re-exports added to `mountainash/__init__.py`:
- `DataPackage`, `DataResource`, `TableDialect`
- `RelationDAG`, `ResourceRef`

### 6. Round-trip semantics

- **Resource `sources` / `licenses` inheritance:** preserved as-observed (not expanded from the package on read). A descriptor read in and written back out is byte-equivalent unless the user explicitly mutates fields.
- **Unknown properties:** preserved via `extras: dict` at both Package and Resource level. Round-trips losslessly.
- **`$schema` profile version:** preserved as observed (`1.0` or `2.0`); new packages default to `2.0`.
- **Foreign keys:** live on `TypeSpec` (existing), become `constraint_edges` in the DAG, round-trip back into the descriptor unchanged.
- **`to_package()` from a Python-built DAG:** each named Relation must have an output TypeSpec — either declared via `.conform(spec)` or inferable from a `ResourceReadRelNode` source. Otherwise raises `MissingResourceSchema` listing the offending relation names.

### 7. Implementation phases

1. **TypeSpec audit + `TableDialect`.** Audit `typespec/frictionless.py` for any missing `FieldSpec` round-trip gaps (call-out from earlier — foreignKey support was partial). Add `TableDialect` with descriptor round-trip and Polars kwarg translation.
2. **`DataResource` + `DataPackage`.** Pydantic dataclasses, descriptor round-trip via existing single-table converter, construction validation, `extras` preservation, full unit test coverage including real descriptors from `github.com/datasets/`.
3. **`RefRelNode` + `ResourceReadRelNode`.** Wired through all three backends per the six-layer wiring matrix. Tests cover CSV / JSON / Parquet / inline / multi-file `path: []`.
4. **`RelationDAG`.** Orchestrator + `add()` + `ref()` + `topological_order()` + `collect()` + per-call caching + `RelationDAGRequired` error path.
5. **Bidirectional bridge.** `DataPackage.to_relation_dag(overrides=...)` and `RelationDAG.to_package()` with `MissingResourceSchema` validation.
6. **End-to-end tests.** Real descriptors from `github.com/datasets/` (e.g. `gdp`, `country-codes`) as fixtures, round-trip + collect + back-to-descriptor.

## Scope

### In scope

- `DataPackage`, `DataResource`, `TableDialect` types with full descriptor round-trip
- Storage-facade-backed materialization for CSV / JSON / Parquet + inline `data:` + multi-file `path: [...]`
- `RefRelNode` and `ResourceReadRelNode` with full wiring matrix coverage across Polars / Narwhals / Ibis
- `RelationDAG` orchestrator with `dependency_edges` and `constraint_edges`, `collect()`, `to_package()`, `from_package()`, `overrides=`
- Construction validation: unique names, FK references resolve, `path` xor `data`
- Non-tabular resources represented as `ResourceRef` exposing `read_bytes()`
- Top-level `mountainash` re-exports

### Out of scope (deferred)

- DAG visualization (graphviz, mermaid, etc.)
- Foreign-key constraint *enforcement* at runtime — `constraint_edges` are metadata only
- Multi-package cross-references (foreignKeys spanning package boundaries)
- DataPackage profiles or extensions beyond the core spec
- **Any dbt SQL generation** — explicitly excluded; covered (and rejected) by the prior 2026-04-04 spec
- Excel / SQL / GeoJSON / NDJSON readers — start with CSV / JSON / Parquet / inline; rest are follow-on tickets
- Hash verification of `bytes` / `hash` resource fields
- Cross-`collect()` caching policy for remote `path` resources — the storage facade handles fetch; no smart cache layer here

## Risks

### Storage facade backend coverage for HTTPS

`mountainash-utils-files` already covers local, MinIO, R2, S3, and S3express. The Frictionless spec allows `path` to be a fully qualified `https://` URL pointing at a public dataset. We need to verify that HTTPS paths route correctly through the facade. **Mitigation:** thin local HTTPS adapter if the facade doesn't already handle it.

### Conform composition with lazy frames

`ma.conform()` was designed against eager Polars `DataFrame`s. The relation visitor now produces `pl.LazyFrame` from `ResourceReadRelNode`, so we need to confirm `conform()` composes cleanly with lazy frames through the relation pipeline. **Mitigation:** if not, materialize at the read boundary inside `visit_resource_read_rel` before applying conform — measurable performance cost, not a correctness issue.

### Round-trip fidelity against real descriptors

Frictionless allows arbitrary unknown properties; the `extras` escape hatch covers known cases but real-world packages from `github.com/datasets/` may surface edge cases (nested unknown objects, profile-specific extensions, comments-in-JSON-equivalents). **Mitigation:** pull 5–10 real descriptors as test fixtures during phase 2; iterate `extras` handling against them.

### TypeSpec ↔ Frictionless gaps

Existing `typespec/frictionless.py` may not round-trip every standard `Field` property cleanly — foreignKey support was previously called out as partial. **Mitigation:** the phase-1 audit pass is explicitly there to close this before package-level work begins. Without a clean Field round-trip, package-level round-trip is impossible.

### Two-graph confusion

`dependency_edges` vs `constraint_edges` is a sharp semantic distinction users may miss. Conflating them would corrupt either execution order or constraint validation. **Mitigation:** clear naming, separate accessors, no shortcut accessor that hides which is which, prominent docs example showing the difference.

## Dependencies

- Existing `typespec/frictionless.py` (single-table converter)
- Existing `conform/` compiler
- Existing `pydata/ingress/` handlers
- Existing `relations/` AST and `UnifiedRelationVisitor`
- `mountainash-utils-files` `storage_facade` (already a sibling package in the workspace)
- Polars (`pl.read_csv`, `pl.read_json`, `pl.read_parquet`, `pl.LazyFrame`)

No new external dependencies required.
