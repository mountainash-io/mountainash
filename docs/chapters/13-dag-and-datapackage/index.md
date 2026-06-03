---
title: DAG and DataPackage
description: Multi-resource orchestration with RelationDAG, named relations, dependency and constraint edges, topological collection, Frictionless DataPackage integration, and FK integrity checking.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 13: DAG and DataPackage

## Summary

Multi-resource orchestration with RelationDAG, named relations, dag.ref, dependency and constraint edges, two-edge graph model, topological collection, dag.collect, ref_resolver, Frictionless DataPackage/DataResource/TableDialect integration, from_descriptor, to_relation_dag, resource overrides, dag.add, to_package, FK integrity checking, and validate_match.

## Concepts Covered

- RelationDAG
- Named Relations
- dag.ref Method
- Dependency Edges
- Constraint Edges
- Two-Edge Graph Model
- Topological Collection
- dag.collect Method
- ref_resolver Parameter
- DataPackage
- DataResource
- TableDialect
- from_descriptor Method
- to_relation_dag Method
- Resource Overrides
- dag.add Method
- to_package Method
- FK Integrity Check
- validate_match Function

## Prerequisites

- [Chapter 1. Foundation Concepts](../01-foundations/)
- [Chapter 9. Type System and Schema](../09-type-system-and-schema/)
- [Chapter 10. Relation API Core Operations](../10-relation-api-core/)
- [Chapter 11. Relation API Advanced Features](../11-relation-api-advanced/)

---

## Introduction

Previous chapters introduced the Relation API for building and executing single data transformations. Real-world data processing, however, rarely involves one table in isolation. An analytics pipeline might load customers, orders, and products from separate files, join them together, compute aggregates, and check referential integrity across the results. Managing the compilation order, resolving cross-references, and ensuring foreign key consistency by hand becomes brittle as the number of datasets grows.

The **RelationDAG** solves this problem. It is a thin orchestrator that holds a collection of named relations, automatically tracks how they depend on each other, and compiles them in the correct topological order. Combined with Frictionless Data's **DataPackage** format for describing multi-resource datasets, the DAG provides a complete lifecycle for multi-table data: load descriptors, build relations, compile with cross-references resolved, validate foreign keys, and export the result back to a portable descriptor.

## RelationDAG

A **RelationDAG** is a container that stores named relations and the edges between them. It is not a new visitor stack or an alternative execution engine. Instead, it wraps the existing relation AST and visitor infrastructure, adding just enough bookkeeping to handle multi-resource scenarios.

```python
from mountainash.relations.dag import RelationDAG

dag = RelationDAG()
```

Internally, the DAG maintains four data structures:

- **relations**: A dictionary mapping string names to Relation objects
- **assets**: A dictionary mapping names to non-tabular resource references (images, documents)
- **dependency_edges**: A set of \( (\text{upstream}, \text{downstream}) \) tuples recording data flow
- **constraint_edges**: A set of \( (\text{parent}, \text{child}) \) tuples recording foreign key relationships

The separation between dependency and constraint edges is a deliberate design choice covered later in this chapter under the Two-Edge Graph Model.

## Named Relations

A **named relation** is simply a Relation object that has been registered in the DAG under a string key. The name serves as the relation's identity for cross-referencing, output naming, and DataPackage export.

```python
import mountainash as ma

customers = ma.relation(customers_df)
orders = ma.relation(orders_df)

dag.add("customers", customers)
dag.add("orders", orders)
```

Names must be unique within a single DAG. Attempting to add a relation with a name that already exists raises a `ValueError`. This prevents accidental overwrites that would silently invalidate downstream references.

#### Diagram: RelationDAG Container Structure

<iframe src="../../sims/dag-container-structure/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>RelationDAG Container Structure</summary>
Type: Diagram | **sim-id:** dag-container-structure<br/> | **Library:** vis-network<br/> | **Status:** Specified
Shows the four internal data structures of RelationDAG (relations dict, assets dict, dependency_edges set, constraint_edges set) and how named relations connect to them. Learning objective: Understand the internal organization of the DAG container. Bloom level: Understand. Interactions: Hover over nodes to see descriptions, click edges to highlight paths.
</details>

## dag.add Method

The `dag.add()` method registers a named relation and automatically discovers its upstream dependencies. When you call `add("enriched_orders", some_relation)`, the DAG walks the relation's internal AST tree looking for `RefRelNode` instances. Each ref found generates a dependency edge from the referenced name to the newly added name.

The walk uses a recursive traversal function that examines each node's structural children (accessed via the `input`, `left`, `right`, and `inputs` attributes). When it encounters a `RefRelNode`, it records the referenced name:

```python
# Internal traversal (simplified)
def walk_refs(node):
    found = set()
    if isinstance(node, RefRelNode):
        found.add(node.name)
    for child in node.children():
        found |= walk_refs(child)
    return found
```

This automatic edge discovery means you never need to declare dependencies manually. The DAG infers them from the structure of the relation you are adding.

## dag.ref Method

The `dag.ref()` method creates a **reference relation** -- a lightweight placeholder that points to another named relation in the DAG. Under the hood, it constructs a `RefRelNode` leaf node wrapped in a standard Relation object:

```python
# Create a reference to the "customers" relation
cust_ref = dag.ref("customers")

# Chain operations on the reference like any relation
active_customers = cust_ref.filter(ma.col("status").eq(ma.lit("active")))

# When added to the DAG, the dependency edge is auto-discovered
dag.add("active_customers", active_customers)
# dependency_edges now contains: ("customers", "active_customers")
```

Refs are critical because they enable composition without requiring the referenced data to be materialized yet. At build time, the ref is just a named pointer. At collect time, the DAG resolves refs by looking up the compiled result in a cache.

The `dag.source()` convenience method combines `add()` and `ref()` in a single call. It registers source data under a name and immediately returns a ref for downstream use:

```python
cust_ref = dag.source("customers", customers_df)
# Equivalent to:
#   dag.add("customers", ma.relation(customers_df))
#   cust_ref = dag.ref("customers")
```

## Dependency Edges

**Dependency edges** represent data flow between relations. Each edge is a tuple \( (\text{upstream}, \text{downstream}) \) meaning "downstream needs the compiled result of upstream before it can be compiled." These edges are created automatically when `dag.add()` discovers `RefRelNode` instances in the relation tree.

Consider a three-table pipeline where enriched orders depend on both customers and orders:

```python
cust = dag.source("customers", customers_df)
orders = dag.source("orders", orders_df)

enriched = cust.join(dag.ref("orders"), on=["customer_id"], how="left")
dag.add("enriched", enriched)
```

After this code runs, the DAG contains two dependency edges: `("customers", "enriched")` and `("orders", "enriched")`. The DAG uses these edges to determine compilation order.

## Constraint Edges

**Constraint edges** represent foreign key relationships between tables. Unlike dependency edges, they do not affect compilation order. A constraint edge \( (\text{parent}, \text{child}) \) means "the child table's foreign key column(s) should reference values in the parent table's primary key column(s)."

Constraint edges are populated in two scenarios:

1. When a DataPackage with `foreignKeys` schema metadata is converted to a DAG via `to_relation_dag()`
2. When manually added by user code: `dag.constraint_edges.add(("customers", "orders"))`

The DAG's validation methods use constraint edges to check referential integrity, but the compilation engine ignores them entirely. This means you can validate FK relationships without requiring the parent table to be an input to the child table's relation tree.

#### Diagram: Two-Edge Graph Model

<iframe src="../../sims/two-edge-graph-model/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Two-Edge Graph Model</summary>
Type: Interactive Diagram | **sim-id:** two-edge-graph-model<br/> | **Library:** vis-network<br/> | **Status:** Specified
Visualizes a sample DAG with three tables (customers, orders, order_items) showing dependency edges (solid arrows, blue) and constraint edges (dashed arrows, orange) as distinct overlays. Toggle checkboxes switch edge types on/off. Learning objective: Distinguish dependency edges from constraint edges. Bloom level: Analyze. Interactions: Toggle dependency/constraint visibility, drag nodes, hover for edge type labels.
</details>

## Two-Edge Graph Model

The deliberate separation of dependency edges from constraint edges is one of the DAG's key design decisions. Other orchestration systems typically model all relationships as a single edge type, forcing either over-compilation (compiling tables that are only needed for validation, not for data flow) or under-validation (skipping FK checks because the FK parent is not in the dependency graph).

Mountainash's two-edge model provides the following properties:

| Edge Type | Source | Affects Compilation | Affects Validation |
|-----------|--------|--------------------|--------------------|
| Dependency | Auto-discovered from RefRelNode | Yes -- determines topological order | No |
| Constraint | From foreignKeys metadata or manual | No | Yes -- drives FK integrity checks |

This means you can have a parent table that exists purely for FK validation without it being an input to any relation's data flow. Conversely, you can have data dependencies that carry no FK semantics.

## Topological Collection

When relations reference each other via `dag.ref()`, they must be compiled in dependency order. If relation B references relation A, then A must be compiled first so its result is available when B's `RefRelNode` is visited. The DAG enforces this ordering through **topological sorting** using Kahn's algorithm.

The `dag.topological_order()` method returns relation names in an order where every relation appears after all its upstream dependencies. If a cycle is detected (A depends on B depends on A), it raises a `ValueError`.

```python
dag = RelationDAG()
a = dag.source("raw", raw_df)
b = a.filter(ma.col("active").eq(ma.lit(True)))
dag.add("filtered", b)
c = dag.ref("filtered").select(ma.col("id"), ma.col("name"))
dag.add("projected", c)

print(dag.topological_order())
# ['raw', 'filtered', 'projected']
```

When a `target` argument is provided, only the ancestors of that target (and the target itself) are included. This enables selective compilation -- collecting a single output without compiling unrelated branches of the DAG.

## dag.collect Method

The `dag.collect()` method is the primary compilation entrypoint. Given a target relation name, it performs a topological walk of that relation's dependency tree, compiling each upstream relation in order and caching the results. The final compiled result for the target is returned.

```python
# Compile "enriched" and all its dependencies
result = dag.collect("enriched")
# result is a Polars LazyFrame (or other backend-native object)
```

The compilation process works as follows:

1. Compute the topological order for the target's dependency subgraph
2. Create a per-call cache dictionary
3. Create a `ref_resolver` closure that looks up names in the cache
4. Instantiate a `UnifiedRelationVisitor` with the resolver attached
5. For each upstream relation in topological order, compile its AST via `node.accept(visitor)` and store the result in the cache
6. Compile the target relation's AST (whose `RefRelNode` leaves now resolve from the cache) and return the result

The backend is auto-detected from the first `ReadRelNode` encountered in the dependency tree. You can override this with the `backend` parameter: `dag.collect("enriched", backend="polars")`.

## ref_resolver Parameter

The **ref_resolver** is a callable with the signature `(name: str) -> Any` that the `UnifiedRelationVisitor` calls when it encounters a `RefRelNode`. If no resolver is provided and a `RefRelNode` is visited, the visitor raises a `RelationDAGRequired` error.

During `dag.collect()`, the resolver is a closure over the per-call cache:

```python
cache = {}

def resolver(name: str):
    return cache[name]

visitor = UnifiedRelationVisitor(
    relation_system,
    expression_visitor=expr_visitor,
    ref_resolver=resolver,
)
```

Because the cache is populated in topological order before the target is compiled, every ref the target (or its intermediaries) might reference is guaranteed to be in the cache when the resolver is called. This is the mechanism that makes cross-relation references work.

#### Diagram: Topological Compilation Flow

<iframe src="../../sims/dag-topological-compile/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Topological Compilation Flow</summary>
Type: Step-through Animation | **sim-id:** dag-topological-compile<br/> | **Library:** vis-network<br/> | **Status:** Specified
Animated walk-through of dag.collect("enriched") for a three-table DAG. Each step highlights the current node being compiled, shows the cache state, and illustrates ref_resolver lookups. Learning objective: Trace the compilation sequence through a DAG. Bloom level: Apply. Interactions: Step forward/backward buttons, cache state panel updates on each step.
</details>

## DataPackage

A **DataPackage** is a Pydantic model representing the Frictionless Data Package specification. It serves as a portable, JSON-serializable descriptor for a collection of data resources. In mountainash, DataPackage is the bridge between external dataset definitions and the internal RelationDAG.

The DataPackage model contains:

- **resources**: A list of `DataResource` objects (at least one required)
- **name**, **title**, **description**: Optional metadata
- **licenses**, **contributors**, **sources**: Provenance metadata
- **version**, **created**: Versioning information

Resource names must be unique within a package. Foreign key references are validated at construction time -- if a resource's schema references a resource name that does not exist in the package, a `ValueError` is raised immediately.

```python
from mountainash.typespec.datapackage import DataPackage

pkg = DataPackage.from_descriptor("datapackage.json")
print(pkg.resources[0].name)       # 'customers'
print(len(pkg.resources))          # 3
```

## DataResource

A **DataResource** is a Pydantic model representing one data source within a DataPackage. Each resource must have exactly one of `path` (file location) or `data` (inline data). The resource carries schema information, format hints, and dialect configuration.

Key fields include:

- **name**: Unique identifier within the package
- **path**: File path or URL to the data (mutually exclusive with data)
- **data**: Inline data (mutually exclusive with path)
- **table_schema**: The Frictionless Table Schema (aliased as "schema" in JSON)
- **dialect**: A `TableDialect` object for CSV parsing configuration
- **format**: File format hint ("csv", "json", "parquet")

The `from_descriptor()` class method handles the conversion from raw JSON dictionaries, automatically parsing nested objects like dialect and separating known fields from extras:

```python
from mountainash.typespec.datapackage import DataResource

raw = {
    "name": "orders",
    "path": "data/orders.csv",
    "format": "csv",
    "schema": {"fields": [{"name": "id", "type": "integer"}]},
    "custom_key": "preserved"
}
resource = DataResource.from_descriptor(raw)
# resource.extras == {"custom_key": "preserved"}
```

## TableDialect

A **TableDialect** specifies CSV parsing parameters following the Frictionless specification. It controls how raw CSV bytes are interpreted: field delimiters, quote characters, null sequences, header handling, and comment characters.

```python
from mountainash.typespec.datapackage import TableDialect

dialect = TableDialect(
    delimiter="\t",
    quote_char='"',
    null_sequence="NA",
    header=True,
    comment_char="#"
)
```

The dialect integrates with Polars through the `to_polars_read_csv_kwargs()` method, which translates Frictionless field names to Polars parameter names. Fields that Polars does not support are silently dropped:

| Frictionless Field | Polars Parameter |
|-------------------|-----------------|
| delimiter | separator |
| header | has_header |
| quote_char | quote_char |
| escape_char | eol_char |
| comment_char | comment_prefix |
| null_sequence | null_values |

## from_descriptor Method

Both `DataPackage` and `DataResource` provide a `from_descriptor()` class method for constructing instances from raw dictionaries or file paths. This is the primary entry point for loading external Frictionless descriptors.

For `DataPackage`, the method accepts three input types:

1. A Python dictionary (parsed JSON)
2. A string path to a JSON file on disk
3. A `pathlib.Path` object pointing to a JSON file

```python
# From a file path
pkg = DataPackage.from_descriptor("path/to/datapackage.json")

# From a dictionary
pkg = DataPackage.from_descriptor({
    "resources": [
        {"name": "data", "path": "data.csv", "schema": {...}}
    ]
})
```

The method separates known Frictionless fields from extension fields, storing the latter in an `extras` dictionary. This enables lossless round-tripping -- custom fields survive `from_descriptor()` followed by `to_descriptor()`.

## to_relation_dag Method

The `to_relation_dag()` method on `DataPackage` converts a package descriptor into a live `RelationDAG`. This is the primary bridge from declarative metadata to executable data pipelines.

The conversion follows these rules:

1. **Tabular resources** (those with a path and table schema) become named relations wrapping a `ResourceReadRelNode`
2. **Non-tabular resources** (images, documents) become entries in `dag.assets`
3. **Foreign keys** from the resource schemas populate `dag.constraint_edges` (not dependency_edges)
4. **Resource overrides** substitute in-memory DataFrames for specific resources

```python
pkg = DataPackage.from_descriptor("datapackage.json")

# Basic conversion
dag = pkg.to_relation_dag()

# With overrides for testing
dag = pkg.to_relation_dag(overrides={
    "customers": test_customers_df,
    "orders": test_orders_df,
})
```

The overrides parameter is particularly useful for testing, where you want to use the same DAG structure but substitute controlled test data for the file-backed resources.

## Resource Overrides

**Resource overrides** let you substitute in-memory DataFrames for file-backed resources when building a DAG from a DataPackage. When the `to_relation_dag()` method encounters a resource name that exists in the overrides dictionary, it wraps the override DataFrame in `ma.relation()` instead of creating a `ResourceReadRelNode`.

This mechanism supports several workflows:

- **Testing**: Replace production file paths with test fixtures
- **Caching**: Substitute pre-loaded DataFrames to avoid re-reading files
- **Mocking**: Provide synthetic data for resources that are unavailable

The override applies only to the named resource. All other relations in the DAG, including those that reference the overridden resource via `dag.ref()`, continue to work normally because the DAG resolves refs by name, not by the underlying node type.

#### Diagram: DataPackage to RelationDAG Conversion

<iframe src="../../sims/datapackage-to-dag/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>DataPackage to RelationDAG Conversion</summary>
Type: Flow Diagram | **sim-id:** datapackage-to-dag<br/> | **Library:** vis-network<br/> | **Status:** Specified
Shows the conversion pipeline from a DataPackage JSON descriptor through from_descriptor() to DataPackage object, then to_relation_dag() producing a RelationDAG with relations, assets, and constraint edges. Includes an override path. Learning objective: Trace the conversion from descriptor to executable DAG. Bloom level: Apply. Interactions: Click each stage to see its internal state, highlight override vs normal paths.
</details>

## to_package Method

The `to_package()` method exports a RelationDAG back to a Frictionless DataPackage descriptor, completing the round-trip. Each named relation in the DAG must have a schema that can be exported. The method supports two sources of schema information:

1. Relations backed by a `ResourceReadRelNode` reuse the original `DataResource`
2. Relations with an `output_schema` attribute use that schema to construct a new resource

If a relation has neither, the method raises a `MissingResourceSchema` error. Assets (non-tabular resources) pass through to the output package unchanged.

```python
dag = RelationDAG()
dag.add("customers", ma.relation(customers_df))
dag.add("orders", ma.relation(orders_df))

# Export to DataPackage
package = dag.to_package()
package.write("output/datapackage.json")
```

This round-trip capability means you can load a DataPackage, transform its data through a DAG, and export the results as a new DataPackage that other tools (Frictionless Framework, CKAN, OpenRefine) can consume.

## FK Integrity Check

Foreign key integrity checking validates that every non-null value in a child table's FK column(s) exists in the parent table's referenced column(s). The DAG performs this check during `dag.validate()` using the `check_fk_integrity()` function.

The check operates on materialized Polars DataFrames and follows this logic:

1. Filter out rows where any FK column is null (null FKs represent optional relationships)
2. Perform an anti-join between the child's FK columns and the parent's referenced columns
3. If any orphaned rows remain, create an `FKViolation` with the count and a sample of up to 10 orphan rows

```python
# The FKViolation dataclass captures:
@dataclass
class FKViolation:
    child_table: str       # Name of the child table
    parent_table: str      # Name of the parent table
    child_fields: list     # FK column(s) in the child
    parent_fields: list    # Referenced column(s) in the parent
    orphan_count: int      # Total number of orphaned rows
    orphan_sample: DataFrame  # Up to 10 sample orphans
```

The anti-join approach is efficient because it leverages Polars' native join engine rather than iterating row-by-row. For a child table with \( n \) rows and a parent table with \( m \) unique keys, the check runs in approximately \( O(n + m) \) time.

## validate_match Function

The `validate_match` function (from the type system module) checks whether a DataFrame's actual schema matches an expected TypeSpec. It is used within the DAG validation pipeline as the first phase (table-level validation) before FK checks are performed.

The full DAG validation runs in two phases:

1. **Phase 1 -- Table Validation**: For each table, materialize it via `dag.collect()`, then validate the resulting DataFrame against its TypeSpec or data contract
2. **Phase 2 -- FK Integrity**: Using the cached DataFrames from Phase 1, check all foreign key relationships defined in the specs

The result is a `DAGValidationResult` object:

```python
@dataclass
class DAGValidationResult:
    passes: bool                          # True if all checks pass
    table_results: dict[str, ValidationResult]  # Per-table results
    fk_violations: list[FKViolation]      # FK violations found
```

Two validation modes are available:

- **Full validation** (`dag.validate()`): Runs all table validations and all FK checks, collecting every failure
- **Quick validation** (`dag.validate_quick()`): Stops at the first table failure or FK violation, useful for CI pipelines where you want fast feedback

#### Diagram: Two-Phase DAG Validation

<iframe src="../../sims/dag-validation-phases/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Two-Phase DAG Validation</summary>
Type: Flow Diagram | **sim-id:** dag-validation-phases<br/> | **Library:** vis-network<br/> | **Status:** Specified
Two-column flow showing Phase 1 (table validation per resource) feeding cached DataFrames into Phase 2 (FK integrity checking across tables). Shows the fast-exit path for validate_quick. Learning objective: Understand the two-phase validation architecture. Bloom level: Analyze. Interactions: Toggle between full and quick mode to see different execution paths.
</details>

## Putting It All Together

The following example demonstrates a complete workflow from DataPackage loading through DAG execution and validation:

```python
import mountainash as ma
from mountainash.typespec.datapackage import DataPackage
from mountainash.relations.dag import RelationDAG

# Load a DataPackage descriptor
pkg = DataPackage.from_descriptor("sales/datapackage.json")

# Convert to a DAG (FK metadata becomes constraint edges)
dag = pkg.to_relation_dag()

# Build a derived relation using refs
customers = dag.ref("customers")
orders = dag.ref("orders")

summary = (
    customers
    .join(orders, on=["customer_id"], how="left")
    .group_by(ma.col("region"))
    .agg(
        ma.col("order_total").sum().alias("total_revenue"),
        ma.col("customer_id").n_unique().alias("unique_customers"),
    )
)

dag.add("regional_summary", summary)

# Compile and collect the result
result = dag.collect("regional_summary")

# Export the enriched DAG as a new DataPackage
output_pkg = dag.to_package()
output_pkg.write("output/datapackage.json")
```

## Key Takeaways

- **RelationDAG** is a thin orchestrator over named relations that tracks dependencies and compiles in topological order.
- **dag.ref()** creates lightweight reference placeholders resolved at compile time, enabling composition without premature materialization.
- **dag.add()** automatically discovers upstream dependencies by walking the AST for RefRelNode instances.
- The **two-edge graph model** separates dependency edges (compilation order) from constraint edges (FK validation), preventing over-compilation and under-validation.
- **Topological collection** via dag.collect() compiles relations in dependency order using a per-call cache and ref_resolver closure.
- **DataPackage**, **DataResource**, and **TableDialect** provide Frictionless-standard metadata models with lossless round-trip serialization.
- **to_relation_dag()** bridges from declarative descriptors to executable DAGs, with resource overrides for testing.
- **FK integrity checking** uses anti-joins for efficient orphan detection, running in a second phase after table validation.
