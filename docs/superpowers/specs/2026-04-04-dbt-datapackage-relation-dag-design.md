# dbt Integration via Frictionless Data Packages and Relation DAG

**Date:** 2026-04-04
**Status:** Feasibility study / design
**Scope:** Three interconnected capabilities — Frictionless Data Package support, Relation DAG, dbt SQL compilation

## Motivation

mountainash already implements the Frictionless Table Schema specification via TypeSpec/FieldSpec, including partial foreign key support. This design extends that foundation in three directions:

1. **Frictionless Data Packages** — the multi-resource container spec, enabling mountainash to describe and round-trip entire datasets (not just single tables)
2. **Relation DAG** — named, interconnected Relations with dependency edges, bridging the gap between Data Packages and mountainash's relational algebra
3. **dbt SQL compilation** — generating dbt projects from a Relation DAG, targeting SQL models via the existing Ibis backend

The key insight: **foreignKeys in a Data Package are dependency edges in a DAG**, and a **Relation DAG is a dbt project waiting to be compiled**.

```
datapackage.json --> DataPackage --> Relation DAG --> dbt project (SQL models)
                                        ^
                         Python code (ma.relation...)
```

## Background Research

### PySpark (out of scope)

PySpark is already partially supported through two existing paths:
- **Ibis backend** — Ibis has a PySpark backend, and mountainash already recognizes `ibis.backends.pyspark.Backend` in `factories.py`
- **Narwhals backend** — Narwhals supports PySpark as a lazy-only backend

Validation testing is warranted but no new backend design is needed.

### dbt Python Models (rejected)

dbt Python models run remotely on the data platform (Snowflake Snowpark, Databricks PySpark, BigQuery BigFrames). This means any library used inside a Python model must be installed in the warehouse's Python environment. mountainash as a warehouse dependency is impractical — too many transitive dependencies, too little control over the runtime environment. Only 3 platforms support Python models, and only `table`/`incremental` materializations are available.

### dbt SQL Models (chosen approach)

SQL models are dbt's native format. They work with all dbt adapters (~11+), all materializations, and have no warehouse dependencies beyond the SQL engine itself. mountainash's existing Ibis backend can produce SQL strings via `ibis.to_sql(dialect=...)`, making SQL generation a natural extension of the current architecture.

### dbt-ibis Bridge (prior art)

The [dbt-ibis](https://github.com/binste/dbt-ibis) project (low-velocity, ~500 lines) demonstrates a proven pattern:
- Create unbound `ibis.table()` objects with sentinel table names (e.g., `__ibd_ref__stg_orders__rid__`)
- Build Ibis expressions using these unbound tables
- Compile to SQL via `ibis.to_sql(expr, dialect=...)`
- Regex-replace sentinel names with dbt Jinja: `{{ ref('stg_orders') }}`

This pattern is directly applicable to mountainash's dbt compiler.

### Frictionless Data Package Spec

A Data Package (`datapackage.json`) is a container of Data Resources with package-level metadata. Key structural mapping:

| Frictionless | mountainash (today) | mountainash (proposed) |
|---|---|---|
| Data Package | *No equivalent* | DataPackage class |
| Data Resource | *No equivalent* | DataResource class |
| Table Schema | TypeSpec + FieldSpec | Unchanged |
| foreignKeys | ForeignKey + ForeignKeyReference | Dependency edges in DAG |
| primaryKey | FieldConstraints | Unchanged |
| missingValues | sentinel values / `t_col(unknown={...})` | Unchanged |

foreignKeys are the critical link — they declare that one resource's field references another resource's field, which is exactly a dependency edge in a transformation DAG.

## Design

### Layer 1: DataResource and DataPackage (Frictionless Metadata)

Two new classes in `src/mountainash/typespec/`, aligned with the Frictionless spec. No `frictionless-py` dependency — mountainash implements the spec directly, consistent with the existing TypeSpec approach.

**DataResource** — wraps a TypeSpec with resource-level metadata:
- `name: str` (required, unique within package)
- `path: Optional[Union[str, List[str]]]` (file path or URL to data)
- `schema: TypeSpec` (the table schema — already exists)
- `title: Optional[str]`, `description: Optional[str]` (metadata)
- `format: Optional[str]`, `mediatype: Optional[str]` (data format)

**DataPackage** — container of DataResources:
- `name: Optional[str]`, `title: Optional[str]`, `description: Optional[str]`
- `resources: List[DataResource]` (required, at least one)
- `version: Optional[str]`, `licenses: Optional[List[dict]]`
- `sources: Optional[List[dict]]`, `contributors: Optional[List[dict]]`

**Round-trip serialization:**
- `DataPackage.from_descriptor(data: dict | str | Path)` — reads `datapackage.json`
- `DataPackage.to_descriptor() -> dict` — writes `datapackage.json`
- Delegates to existing `TypeSpec.from_frictionless()` / `TypeSpec.to_frictionless()` for schema handling

**Validation:**
- Resource names must be unique within a package
- foreignKey `resource` references must resolve to existing resource names

### Layer 2: Relation DAG

Today, Relations are anonymous and standalone. This layer adds named, interconnected Relations with dependency tracking.

**Named Relations** — Relations gain an optional `name` property:
```python
r = ma.relation(df, name="stg_orders")
```

**RelationDAG** — a container of named Relations with dependency edges:
- `relations: Dict[str, Relation]` — named relations keyed by name
- `edges` — dependency edges (derived from foreignKeys or from `dag.ref()` usage)
- `topological_order() -> List[str]` — execution order respecting dependencies
- Validation: all `dag.ref()` targets and foreignKey references resolve to existing relations

**`dag.ref(name)`** — the key primitive. Returns a Relation that declares a dependency on another named relation in the DAG. Analogous to `dbt.ref()`. Under the hood, creates a ReadRelNode with a named reference rather than a concrete DataFrame.

**Two entry points for building a DAG:**

From a DataPackage:
```python
package = ma.DataPackage.from_descriptor("datapackage.json")
dag = package.to_relation_dag(data_sources={
    "customers": customers_df,
    "orders": orders_df,
})
# foreignKeys become dependency edges
# TypeSpec applied via ma.conform() per resource
```

From Python code:
```python
dag = ma.RelationDAG()
dag.add("stg_customers", ma.relation(customers_df).conform(customer_spec))
dag.add("stg_orders", ma.relation(orders_df).conform(order_spec))
dag.add("active_orders",
    dag.ref("stg_orders")
        .filter(ma.col("status").eq("active"))
        .join(dag.ref("stg_customers"), on="customer_id"))
```

**Reverse direction:**
- `RelationDAG.to_package() -> DataPackage` — exports as Frictionless descriptor
- Each named Relation's TypeSpec becomes a DataResource schema
- Dependency edges become foreignKeys

### Layer 3: dbt SQL Compiler

Takes a RelationDAG and generates a dbt project with SQL models. The compiler only understands Relations — it has no knowledge of Frictionless.

**Compilation pipeline per relation:**

1. For each `dag.ref()` dependency, create an unbound `ibis.table(schema, name="__ma_ref__<name>__")` with a sentinel table name. Schema is derived from the referenced relation's TypeSpec (or inferred).
2. Compile the Relation through the existing Ibis visitor -> `ir.Table`
3. Call `ibis.to_sql(table, dialect=target_dialect)` -> SQL string
4. Regex-replace sentinels: `"__ma_ref__X__"` -> `{{ ref('X') }}`
5. Similarly for sources: `"__ma_source__<schema>__<table>__"` -> `{{ source('<schema>', '<table>') }}`
6. Write `.sql` model file

**What gets generated:**

```
output_dir/
├── dbt_project.yml           # Project config (name, version, profile)
└── models/
    ├── stg_customers.sql     # SQL model per relation
    ├── stg_orders.sql
    ├── active_orders.sql
    └── schema.yml            # Contracts + tests for all models
```

**Generated SQL model example:**
```sql
-- models/active_orders.sql  (generated by mountainash)
SELECT
  t0.order_id,
  t0.customer_id,
  t0.amount
FROM {{ ref('stg_orders') }} AS t0
INNER JOIN {{ ref('stg_customers') }} AS t1
  ON t0.customer_id = t1.customer_id
WHERE t0.status = 'active'
```

**YAML contract + test generation from TypeSpec:**

```yaml
# models/schema.yml  (generated by mountainash)
models:
  - name: stg_orders
    config:
      materialized: table
    columns:
      - name: order_id
        data_type: integer
        tests: [not_null, unique]
      - name: customer_id
        data_type: integer
        tests: [not_null]
      - name: status
        data_type: varchar
        tests:
          - accepted_values: {values: ["active", "cancelled", "pending"]}
```

**TypeSpec -> dbt test mapping:**

| TypeSpec / FieldConstraints | dbt test |
|---|---|
| `primaryKey` | `not_null` + `unique` |
| `constraints.required = True` | `not_null` |
| `constraints.unique = True` | `unique` |
| `constraints.enum` | `accepted_values` |
| `foreignKey` | `relationships` (dbt's built-in FK test) |

**Ternary logic in SQL:** mountainash's three-valued semantics (TRUE=1, UNKNOWN=0, FALSE=-1) compile to CASE WHEN expressions via the Ibis backend. Booleanizers (e.g., `is_true`) become `CASE WHEN x = 1 THEN TRUE ELSE FALSE END`. This works in all SQL dialects.

**Dialect mapping (dbt adapter -> Ibis SQL dialect):**

| dbt adapter | Ibis dialect |
|---|---|
| postgres | postgres |
| snowflake | snowflake |
| bigquery | bigquery |
| duckdb | duckdb |
| redshift | postgres |
| databricks | spark |
| trino | trino |

**API:**
```python
ma.dbt.compile(dag, output_dir="./my_dbt_project", dialect="snowflake", project_name="analytics")
```

## Scope Boundaries

### In scope

**Frictionless layer:**
- DataResource + DataPackage classes
- `datapackage.json` round-trip serialization
- Builds on existing TypeSpec/FieldSpec/ForeignKey

**Relation DAG:**
- Named Relations with `name` property
- RelationDAG container with `dag.add()` and `dag.ref()`
- Topological sort from dependency edges
- DAG from DataPackage (foreignKeys -> edges)
- DAG from Python code (incremental building)
- DAG to DataPackage (reverse direction)

**dbt SQL compiler:**
- SQL model generation via Ibis backend -> `ibis.to_sql()`
- Sentinel table replacement for `{{ ref() }}` and `{{ source() }}`
- Ibis dialect selection per dbt adapter
- YAML schema generation (contracts + tests from TypeSpec)
- `dbt_project.yml` generation

### Out of scope (deferred)

- dbt Python models (warehouse dependency problem)
- dbt macro generation or custom Jinja beyond ref/source
- dbt incremental model logic (`is_incremental()` branching)
- DAG visualization
- Foreign key constraint enforcement at runtime (remains metadata only)
- DataPackage extensions/profiles beyond core spec
- Inline data in DataResource
- Multi-package cross-references (foreignKeys across package boundaries)
- dbt sources YAML generation (users declare sources manually)

## Risks

### Sentinel regex reliability

dbt-ibis proved this pattern works, but Ibis may quote or alias sentinel names differently across dialects. Needs thorough testing per dialect. Mitigation: start with 2-3 dialects (DuckDB, Snowflake, Postgres), expand from there.

### Ibis unbound table schema inference

`ibis.table()` requires a schema. For `dag.ref()` where the upstream Relation has a TypeSpec, this is straightforward (TypeSpec -> Ibis schema). For refs without TypeSpec, we need to either infer the schema from the Relation's output columns or require TypeSpec on all named relations.

### SQL feature coverage across dialects

Some mountainash operations may not have SQL equivalents in all dialects. The known-divergences principle already tracks Ibis/SQLite issues. dbt adds more dialects with their own quirks. Mitigation: lean on Ibis's existing dialect support; document mountainash-specific divergences per dialect.

### Conform in SQL

`ma.conform()` compiles TypeSpec to relation operations (cast, rename, coalesce). These should translate cleanly to SQL via the Ibis backend, but needs validation that all conform operations produce valid SQL across target dialects.

## Dependencies

- Existing Ibis backend (expressions + relations)
- Existing TypeSpec/FieldSpec/ForeignKey infrastructure
- Existing Frictionless import/export (`TypeSpec.from_frictionless()` / `.to_frictionless()`)
- `ibis.to_sql()` for SQL string generation
- `ibis.table()` for unbound table creation

No new external dependencies required.
