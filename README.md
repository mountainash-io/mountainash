# mountainash

> **Pre-release status:** Work happens on `develop`. `main` is the release line. There is no supported PyPI distribution. APIs can change without notice.

## Strategic purpose

mountainash provides one semantic layer for tabular work. You build expressions, relational plans, schemas, conformance steps, validation checks, data contracts, and pipelines without binding the build phase to one execution engine.

The package keeps the semantic model separate from backend code. It uses a small AST and typed contracts at the center, then lowers those structures to the selected backend at a terminal operation. This gives applications one place to define data behavior while native plans remain available.

## Source development

Install Python 3.10 or later and Hatch. Start from the `develop` branch:

```bash
git clone https://github.com/mountainash-io/mountainash.git
cd mountainash
git switch develop
hatch shell
```

The Hatch environments define the project commands. Common local commands are:

```bash
hatch run test:test-quick
hatch run ruff:check
hatch run mypy:check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch rules, pull requests, and coding standards. See [TESTING.md](TESTING.md) for test tiers and backend test commands.

## Quick examples

Expressions remain backend-agnostic when added to a relation. A relation terminal compiles each expression for its source backend. Ternary expressions make `UNKNOWN` filter behavior explicit.

```python
import mountainash as ma
import polars as pl

df = pl.DataFrame({"name": ["Ada", "Lin", "Sam"], "age": [37, 22, None]})
# Boolean comparison: the null age remains null and does not pass the filter.
older_than_30 = ma.col("age").gt(30)

filtered = ma.relation(df).filter(older_than_30).to_polars()

# Ternary comparison: the null age becomes the explicit UNKNOWN value.
age_over_30 = ma.t_col("age").t_gt(30)

# Booleanizers define whether UNKNOWN passes a relation filter.
definitely_over_30 = ma.relation(df).filter(age_over_30.t_is_true()).to_polars()
possibly_over_30 = ma.relation(df).filter(age_over_30.t_maybe_true()).to_polars()

definitely_over_30.to_dicts()
# [{"name": "Ada", "age": 37}]

possibly_over_30.to_dicts()
# [{"name": "Ada", "age": 37}, {"name": "Sam", "age": None}]
```

Relations build a plan and execute it at a terminal. Python data is a supported relation source.

```python
import mountainash as ma
plan = (
    ma.relation(
        [
            {"name": "Ada", "age": 37},
            {"name": "Lin", "age": 22},
        ]
    )
    .filter(ma.col("age").gt(25))
    .sort("name")
)

result = plan.to_polars()
```

`Relation.conform` attaches a backend-agnostic TypeSpec to a plan. The transformation runs when the plan compiles.

```python
import mountainash as ma
spec = ma.typespec({"name": "string", "age": "integer"})

result = ma.relation({"name": ["Ada"], "age": ["37"]}).conform(spec).collect()
```

Use `.compile()` for the backend-native result. Lazy backends return an unexecuted plan, but eager backends can return materialized data. Use `.collect()` when you require eager materialization. Use `.to_polars()`, `.to_pandas()`, `.to_dict()`, or `.to_dicts()` when you need a specific output form.

## Architecture and execution model

The build phase creates AST or IR nodes. Expression builders create expression nodes. Relation methods return new relations around relation nodes. Operation nodes hold semantic operations. Relation leaves hold source data, and `ma.native()` can embed a backend-native expression.

At a terminal operation, mountainash:

1. Detects the backend family and, when available, its dialect from the input type or relation leaf.
2. Resolves the operation key through the expression or relation registry.
3. Looks up capability facts for the backend, dialect, parameter, and option values. Declared capability limits can stop a call at build or materialization time.
4. Walks the AST with unified expression and relation visitors. The selected native compiler lowers each node into backend operations.
5. Returns the backend-native result from `.compile()`, or forces materialization through `.collect()` and the output terminals.

The same flow applies to expressions and relations. An expression uses `.compile(dataframe)` because the caller owns the frame. A relation uses `.compile()` and `.collect()` because the relation owns its plan and result.

```text
build                    resolve                    lower                 execute
ma.col("age").gt(30)  -> backend and dialect  -> native expression   -> caller's frame
ma.relation(data)     -> capability facts     -> native plan         -> collect or sink
```

Backend systems register with the expression and relation registries. This keeps backend selection out of API builders and makes capability differences explicit.

## Top-level package map

| Module | Responsibility and boundary |
|---|---|
| `core` | Shared types, canonical dtypes, backend detection, registries, capability facts, and common errors. It supplies infrastructure used by other modules rather than a user-facing query API. |
| `expressions` | Fluent expression builders and the backend-agnostic expression AST. Its boundary ends at native expression compilation through registered expression systems. |
| `relations` | Fluent relational plans, relation nodes, joins, aggregates, schema inference, and `RelationDAG`. Its boundary ends at native plan compilation and materialization. |
| `typespec` | Typed, serializable schemas with universal types, field constraints, keys, and Frictionless descriptor and dialect models. It describes data and does not execute transforms. |
| `conform` | Structural schema conformance and drift reporting. It turns a TypeSpec into relation and expression work. Value-level checks belong to `validation`. |
| `validation` | Backend-agnostic value checks, identities, runners, diagnostics, and validation results. Checks compile through existing visitors instead of embedding backend code. |
| `datacontracts` | Data contract declarations and compilation from TypeSpec. It maps constraints to checks and provides contract validation plans and results. |
| `pydata` | Ingress from Python collections and models, plus egress to Python data. It owns conversion at the Python boundary, not relational semantics. |
| `graph` | General graph algorithms such as topological order, ancestor discovery, and parallel layers. Relation-specific dependency and constraint edges remain in `relations`. |
| `pipelines` | Pipeline sources, steps, fluent builders, parameters, and relation integration. It connects pipeline execution to relations without replacing the relation AST. |
| `exceptions` | Public error facade for typed errors raised by core, expressions, relations, typespec, conformance, validation, and pipelines. |

## Backend matrix

Mountainash has three compiler systems. All backend implementations supported by Ibis or Narwhals are available through one of these paths. Capability coverage still differs by operation and dialect.

| Input or backend identity | Compiler path | Current boundary |
|---|---|---|
| Polars | Native expression and relation compilers | Polars is the core execution path. Relations compile to Polars plans and materialize to Polars frames. |
| Narwhals | Narwhals expression and relation systems | Frame backends that Mountainash can wrap through Narwhals can use this compiler path. Narwhals-wrapped Ibis tables are not accepted. Unwrap them and use the Ibis path directly. Mountainash capability verification is not yet exhaustive across Narwhals dialects. |
| Ibis | Ibis expression and relation compilers | Every backend supported by Ibis can use this compiler path. Explicit dialect facts and focused tests currently cover `ibis-duckdb`, `ibis-polars`, and `ibis-sqlite`. Other dialects are not yet fully characterized. |

Pandas and PyArrow route frame inputs through Narwhals and have no independent compiler registrations. Polars, Narwhals, and PyArrow are required project dependencies. Pandas and Ibis are optional extras, but the Hatch test and mypy environments install both.

## Standards and extensions

### [Substrait](https://substrait.io/)

Substrait is the alignment target for expression and relation semantics. Standard operations use the Substrait namespaces and keys where the specification provides a match. Mountainash-specific operations live in separate extension namespaces, such as ternary logic, conformance, and other utility operations.

mountainash does not currently provide native Substrait serialization. The alignment gives the AST a shared vocabulary and a future interoperability path. It does not mean that every plan can be exported as a Substrait message today.

### [Frictionless Data Package and Table Schema v2](https://datapackage.org/standard/data-package/)

`typespec` models the typed operational schema. It maps universal types, field properties, constraints, keys, missing values, and Mountainash extensions to the Frictionless Table Schema shape.

`DataPackage`, `DataResource`, and `TableDialect` represent Frictionless Data Package descriptors. The descriptor boundary can preserve raw schema and dialect mappings, resolve local references through descriptor context, and convert a resource schema to a `TypeSpec`. Standard properties stay in their standard locations. Mountainash-specific properties use the `x-mountainash` namespace.

This support covers the current descriptor, Table Schema, and TypeSpec mapping code. Frictionless v2 also defines separate conformance, validation, and resource-reader boundaries. Those boundaries are not all complete, so this README does not describe v2 support as a complete implementation.

## Roadmap

This roadmap is capability-based and has no fixed dates. The order can change when work on `develop` exposes an upstream difference or a deeper dependency.

### Complete the remaining Frictionless v2 boundaries

Finish the v2 conformance, validation, and resource-reader boundaries. This includes cross-backend nested-type materialization, consistent conformance policy, and the review of `x-mountainash` extensions.

### Close cross-backend correctness gaps

Complete conformance and validation across Polars, Narwhals, and Ibis. Expand capability facts and dialect tests across every Ibis and Narwhals backend. Complete backend bridging and the remaining coverage guards, and add public relation field-reference introspection.

### Make plans portable

Add Substrait plan serialization, pipeline serialization, stronger resource and ingestion integration, and durable read and write paths.

### Expand execution targets and expression systems

Add DataFusion as a first-class execution target. Evaluate compiler systems for PySpark and Snowpark. Further SQL and distributed engines can use the existing Ibis route. After Substrait serialization lands, Substrait consumers can become additional execution targets.

### Pass the release gate

Publish a supported distribution only when installation, dependency resolution, API stability, support documentation, and release automation describe the same tested package.

## Development and contribution links

- [Technical feature guides](https://github.com/mountainash-io/mountainash/tree/develop/docs/website/features-technical)
- [Data Package reference](https://github.com/mountainash-io/mountainash/blob/develop/docs/reference/datapackage.md)
- [Contributing](CONTRIBUTING.md)
- [Testing](TESTING.md)
- [Security policy](SECURITY.md)

## License

mountainash is released under the [MIT License](LICENSE).
