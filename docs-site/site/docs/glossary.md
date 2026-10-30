# Glossary

Definitions of the public classes, functions, parameters and domain terms used across this documentation. Each entry links to the section that explains the term in full.

## A

### Abstract syntax tree (AST)

A tree of nodes that records a computation as data, with each operation as a node and its inputs as children. Expressions and relations hold an AST that names what to compute and leaves out how any engine computes it.

See [Lazy plans and the AST](chapters/01-what-mountainash-does/index.md#lazy-plans-and-the-ast).

### Aggregate expression

An expression that reduces many rows to one value, such as `sum`, `mean`, `count` or `n_unique`, or the free functions `ma.count_records`, `ma.corr`, `ma.median` and `ma.quantile`. It is evaluated per group in `group_by(...).agg(...)` or broadcast to rows with `over`.

See [Aggregates](chapters/05-namespaces-aggregates-and-windows/index.md#aggregates).

### `always_true`, `always_false`, `always_unknown`

Constant ternary expressions that produce 1, -1 and 0 on every row. They act as defaults in conditional chains and as neutral starting values when a variable number of ternary conditions is combined.

See [Ternary columns and sentinels](chapters/06-ternary-logic/index.md#ternary-columns-and-sentinels).

### API builder

A class in the API builder layer that holds the public methods for one operation category and turns each call into AST nodes keyed by function keys. Builders supply the flat methods and namespaces of an expression object; they never touch a backend.

See [API builders and expression systems](chapters/17-architecture/index.md#api-builders-and-expression-systems).

### Arguments and options

The two parameter channels of a function node. Arguments are child nodes that the visitor compiles into native expressions; options are raw Python values passed unchanged to the backend. A parameter that every backend needs as a literal is an option.

See [Expression AST nodes](chapters/18-expression-compilation/index.md#expression-ast-nodes).

### Arrow exchange

The use of Apache Arrow tables as the common format for moving data between backend families. Each relation system can export a native value to a `pyarrow.Table` and import one, which operand transfer, `ma.from_arrow` and `to_pyarrow()` rely on.

See [Arrow import and export](chapters/21-backends/index.md#arrow-import-and-export).

### As-of join

A join, built with `join_asof`, that matches each left row to the nearest right row on an ordered key rather than an equal one. `strategy` picks the backward, forward or nearest match, `by` requires equal group values and `tolerance` limits the distance.

See [Joins](chapters/07-relations/index.md#joins).

## B

### Backend capability declaration

A recorded statement about what a backend family or dialect supports, restricts or does differently for one operation or parameter. Most declarations are descriptive information; a smaller set are executable policies that gate calls, enrich native errors or protect results.

See [Backend capabilities, families and dialects](chapters/09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

### Backend detection

The selection of a backend family from the Python type of the dataframe or table passed to `ma.relation` or `compile`. Polars objects map to Polars, Ibis tables to Ibis, and anything Narwhals accepts to Narwhals; there is no backend argument.

See [Backend detection](chapters/02-installation-and-package-surface/index.md#backend-detection).

### Backend family

One of the three APIs mountainash compiles plans to: Polars, Narwhals or Ibis. Each family has one expression system and one relation system, and reaches one or more engines, which are distinguished as dialects.

See [Backend capabilities, families and dialects](chapters/09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

### Backend identity

The pair of backend family and dialect that selects which capability declarations apply to a call. It is derived from the execution location of the call, not from the original source; a dialect of `None` means only family-wide declarations apply.

See [Backend capabilities, families and dialects](chapters/09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

### Backend registration

The process by which a backend's composed expression system and relation system are recorded in keyed registries under the family name, through the `@register_expression_system` and `@register_relation_system` decorators. Ibis registers only when its extra is installed.

See [Composition and registration](chapters/21-backends/index.md#composition-and-registration).

### `BackendCapabilityError`

The `MountainashError` raised when a capability declaration refuses a call, or when a declaration explains a native failure. It names the backend and operation, and carries the declaration as `limitation`, including any workaround and upstream reference.

See [Capability errors and capability_policy](chapters/09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy).

### `BaseDataContract`

The base class for data contracts declared as Python classes. Class attributes holding a `FieldDefinition` become the contract's fields in declaration order, inherited fields included, and a nested `Config` class holds contract-level settings such as `natural_key`.

See [Declaring a contract](chapters/12-data-contracts/index.md#declaring-a-contract).

### Boolean-ternary coercion

The automatic conversion applied when boolean and ternary expressions meet. A boolean passed to a ternary operator is wrapped with `to_ternary()`, and a ternary passed to a boolean operator is wrapped with `t_is_true()`, while the expression is being built.

See [Booleanization](chapters/06-ternary-logic/index.md#booleanization).

### Booleanizer

A rule that maps a ternary result (1, 0, -1) to a boolean. Six are built in, such as `t_is_true` (the default) and `t_maybe_true`. `compile()` applies one to ternary expressions; relation methods do not, so filters need an explicit booleanizer.

See [Booleanization](chapters/06-ternary-logic/index.md#booleanization).

```python
import polars as pl
import mountainash as ma

df = pl.DataFrame({"score": [80, None, 50]})
check = ma.t_col("score").t_gt(70)
print(df.select(
    raw=check.compile(df, booleanizer=None),
    is_true=check.compile(df),
    maybe_true=check.compile(df, booleanizer="t_maybe_true"),
))
```

```text
shape: (3, 3)
┌─────┬─────────┬────────────┐
│ raw ┆ is_true ┆ maybe_true │
│ --- ┆ ---     ┆ ---        │
│ i32 ┆ bool    ┆ bool       │
╞═════╪═════════╪════════════╡
│ 1   ┆ true    ┆ true       │
│ 0   ┆ false   ┆ true       │
│ -1  ┆ false   ┆ false      │
└─────┴─────────┴────────────┘
```

### Bound call

An operation applied to specific arguments at a specific location, represented as `BoundCall` with the operation key, backend, dialect, the binding of every protocol parameter and the set of parameters the caller supplied. Capability gates evaluate bound calls.

See [Bound calls and value classes](chapters/20-capability-spine/index.md#bound-calls-and-value-classes).

### Build then compile

The rule that building an expression or relation creates a backend-agnostic AST without data or a backend, and a separate compile step, triggered by `compile(df)` or a terminal, detects the backend and produces native expressions or plans.

See [Lazy plans and the AST](chapters/01-what-mountainash-does/index.md#lazy-plans-and-the-ast).

## C

### Canonical dtype

A member of `ma.MountainashDtype`, the package's backend-neutral type vocabulary with short Substrait-style names such as `i64`, `fp64`, `string` and `timestamp`. Schemas, casts and conversions to every type target are expressed in it.

See [Canonical dtypes](chapters/03-dtypes/index.md#canonical-dtypes).

### Capability bootstrap

The loading step that discovers every capability segment module, binds each to the scope declared beside it, validates it and publishes the result to `CapabilityRegistry` as one immutable generation.

See [Bootstrap and the registry](chapters/20-capability-spine/index.md#bootstrap-and-the-registry).

### Capability gate

An executable capability policy whose consumer is `gate`: it refuses a bound call with `BackendCapabilityError` before the backend lowers or runs it. Gates are checked during preflight and during compilation, against the canonical node.

See [Gates and preflight](chapters/20-capability-spine/index.md#gates-and-preflight).

### Capability information

A descriptive capability record (`CapabilityInformation`) giving a support level at the native or public layer, a message and an optional workaround and upstream issue. It has no executable consumer, so it never changes what runs.

See [Information and policy](chapters/20-capability-spine/index.md#information-and-policy).

### `capability_policy`

A context manager, `ma.capability_policy(policy)`, that sets how capability declarations are enforced inside its block. A `ma.CapabilityPolicy` selects issue classes for protection, error enrichment and disclosure, and which protection mechanisms (gate, materialization) act. The default is `CapabilityPolicy.checked()`.

See [Capability errors and capability_policy](chapters/09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy).

### Capability policy rule

An executable capability record (`CapabilityPolicyRule`) that names a consumer (gate, immediate error, materialization error or result protection) and an action (block, permit, enrich or detect non-null to null). It is declared under a concrete dialect only.

See [Information and policy](chapters/20-capability-spine/index.md#information-and-policy).

### Capability scope

The reach of a capability segment, declared in the `_scope.py` file beside it: family-wide, covering every dialect of a backend family and holding information only, or one named dialect, which may also hold executable policies.

See [Segments and scopes](chapters/20-capability-spine/index.md#segments-and-scopes).

### Capability segment

A Python module exporting a `SEGMENT` constant of type `CapabilitySegment` that holds the information records, policy rules and change records for one domain. Its file path encodes the backend family, scope, operation origin and domain.

See [Segments and scopes](chapters/20-capability-spine/index.md#segments-and-scopes).

### Capability spine

The internal pipeline that carries capability declarations from segment modules through bootstrap and the registry to their consumers: preflight, compile-time gates, error enrichment, result protection and the coverage report. It never implements an operation.

See [Information and policy](chapters/20-capability-spine/index.md#information-and-policy).

### `CapabilityRegistry`

The class-level registry that holds the current published generation of capability records and answers lookups, such as `capability_for` for one cell's policy and `violations_for` for every gate a bound call breaks.

See [Bootstrap and the registry](chapters/20-capability-spine/index.md#bootstrap-and-the-registry).

### Cast safety

A classification of a conversion between two canonical dtypes as safe (no information can be lost) or unsafe, answered from a fixed table by `is_safe_cast` and `classify_cast`. It is separate from whether a particular cast succeeds.

See [Casting, cast safety and nulls](chapters/04-building-expressions/index.md#casting-cast-safety-and-nulls).

### Check IR

The intermediate representation of validation checks: frozen dataclasses (`RowRule`, `ScalarRule`, `RelationRule`, `ValueRule`, `ForeignKeyRule` and the reserved `DistributionRule`) that each declare what to test, with an id and a severity, but not how to run it.

See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### Check summary

One row of `ValidationResult.check_summaries`, the frame form of a `CheckSummary` record, giving a check's id, kind, severity, status (`passed`, `failed`, `error` or `skipped`) and its pass, fail and unknown counts.

See [Results, row identity and failure cases](chapters/13-validation/index.md#results-row-identity-and-failure-cases).

### Checkpoint (materialization scope)

A completed stage of an iterative computation marked with `scope.checkpoint(rel, replaces=...)`. Under the scope's `ma.CheckpointPolicy` the stage is copied, cutting the plan so later stages build on the stored result instead of a growing chain.

See [Materialization scopes and checkpoints](chapters/09-execution-targets-and-capabilities/index.md#materialization-scopes-and-checkpoints).

### Checkpoint (pipeline)

A store that records, per pipeline unit, the results produced under each identity together with source progress, so that a later run reuses unchanged units and resumes sources. `MemoryCheckpoint` and `FileCheckpoint` are the built-in stores.

See [Values, identity and checkpoints](chapters/15-pipelines/index.md#values-identity-and-checkpoints).

### `coalesce`, `greatest`, `least`

Free functions that combine two or more expressions row by row: `ma.coalesce` returns the first non-null value, and `ma.greatest` and `ma.least` return the largest and smallest value, ignoring nulls.

See [Combining columns](chapters/04-building-expressions/index.md#combining-columns).

### `col`

The function `ma.col(name)` that builds an expression referencing one column by name. The name is checked only when the expression is compiled against data; `"*"` and anchored regular expressions pass through to the backend as selectors.

See [Columns, literals and conditions](chapters/04-building-expressions/index.md#columns-literals-and-conditions).

### `collect_with_drift`

A relation terminal that executes the plan and returns a `ConformCollection` holding the native result frame, one drift report per conform step in plan order and the effective schema of the output.

See [Drift reporting](chapters/11-conforming-data/index.md#drift-reporting).

### Compilation reuse

The guarantee that, within one terminal call, a relation object appearing several times in a plan is compiled and transferred once. Reuse is by object identity, and nothing is cached across terminal calls.

See [Compilation reuse](chapters/09-execution-targets-and-capabilities/index.md#compilation-reuse).

### `compile` (expression)

The method `expr.compile(df)` that turns an expression into the native expression of the backend detected from `df`, applying the default booleanizer to ternary results unless `booleanizer=` says otherwise.

See [Compiling an expression](chapters/04-building-expressions/index.md#compiling-an-expression).

### `concat`

The function `ma.concat(relations, distinct=False)` that stacks relations with the same columns, like SQL `UNION ALL`, or `UNION` with `distinct=True`. Inputs may come from different libraries; the first input decides where the result runs.

See [Combining relations](chapters/07-relations/index.md#combining-relations).

### `conform`

The relation method `relation.conform(schema)` that adds a deferred step reconciling a source with a `TableSchema`: renaming, reading lexical values, casting and handling extra or missing columns under a conform contract, once the source shape is known at the terminal.

See [Relation conform](chapters/11-conforming-data/index.md#relation-conform).

### Conform contract

The policy (`ConformContract`) that tells conform how to treat each divergence between schema and data, along four dimensions: `extra_columns`, `missing_columns`, `data_type` and `keys`. It is resolved from the `fields_match` preset, the schema's `contract` and the `contract=` argument.

See [ConformContract dimensions and presets](chapters/11-conforming-data/index.md#conformcontract-dimensions-and-presets).

### Conform error

An error derived from `ConformError` that reports a conform step the contract does not allow, such as an `exact` field mismatch, missing or extra columns or a frozen type change (`SchemaDriftError`). Most are raised at the terminal.

See [Conform errors](chapters/11-conforming-data/index.md#conform-errors).

### Constraint edge

A graph edge that records a relationship between the data of two nodes, such as a foreign key, with optional metadata. Constraint edges never affect execution order; `RelationDAG` uses them to generate foreign-key checks.

See [The graph kernel](chapters/14-relationdag/index.md#the-graph-kernel).

### Cross-backend test

A test parametrised over every backend in `tests/fixtures/backend_registry.py` that asserts the same result for each, so that a behaviour is checked once for all families and dialects rather than per backend.

See [Cross-backend testing](chapters/23-contributing-and-testing/index.md#cross-backend-testing).

### Cross-family DAG collection

The collection of a `RelationDAG` whose named relations live in different backends. A relation combining them runs in the backend of its anchor (its first input), and each foreign dependency is materialized in its own backend and transferred.

See [Collecting a DAG](chapters/14-relationdag/index.md#collecting-a-dag).

### Cross-type join

A join whose right side comes from a different library from the left: another relation, a native frame, a dict or a list of dicts. The left side decides where the join runs, and the right side is transferred there at execution time.

See [Joins](chapters/07-relations/index.md#joins).

### Custom semantic type

A named value converter registered in `CustomTypeRegistry` for values that need logic beyond a cast, such as NaN handling or token parsing. A field opts in with `custom_cast="name"`; `safe_float`, `safe_int`, `xml_string` and `rich_boolean` are built in.

See [Custom semantic types](chapters/10-table-schemas-and-datapackage/index.md#custom-semantic-types).

## D

### DAG materialization session

The per-call context in which `RelationDAG` collects or validates. It compiles each named relation at most once, caches the result for every consumer and caches each cross-backend conversion once per destination.

See [Collecting a DAG](chapters/14-relationdag/index.md#collecting-a-dag).

### `DAGRelation`

The relation returned by `dag.ref(name)`: a reference to another named relation in a `RelationDAG` whose chained methods keep the DAG binding, so its terminals compile through the DAG and resolve references.

See [Building a DAG](chapters/14-relationdag/index.md#building-a-dag).

### `DagUnit`

A pipeline unit that runs one target relation of a `RelationDAG` template, binding the template's named inputs to the values of upstream units.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### Data contract

A declaration of a table's fields (as `FieldDefinition` values) together with the validation checks those fields imply and any extra rules. A contract only declares; the validation engine casts the data to the declared types and runs the checks.

See [Declaring a contract](chapters/12-data-contracts/index.md#declaring-a-contract).

### `datacontract`

The function `ma.datacontract(source)` that builds a data contract class from an existing schema: a `TableSchema`, a simple dict, a Frictionless descriptor or path, or a Pydantic model class.

See [Declaring a contract](chapters/12-data-contracts/index.md#declaring-a-contract).

### `DataPackage`

The model of a Frictionless Data Package: an ordered tuple of named `DataResource` entries plus package properties, read with `from_path`, `from_json` or `from_descriptor` and written with `write` or `to_descriptor`.

See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects).

### `DataResource`

One named resource in a `DataPackage`: a pointer to data (a `path` or inline `data`) with an optional table schema and dialect, each given inline or as a reference to another JSON document.

See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects).

### Dependency edge

A graph edge stating that one node needs another node's output. Dependency edges alone determine topological order and execution layers; in a `RelationDAG` they come from the `dag.ref` references inside each relation.

See [The graph kernel](chapters/14-relationdag/index.md#the-graph-kernel).

### Descriptor reference

A schema or dialect given as a string in a Data Package descriptor, naming another JSON document. It is resolved against the package's base URI when `to_table_schema()` or `to_dialect()` runs, confined to the package root unless remote access is allowed.

See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects).

### `DescriptorWriteMode`

The enum that selects how a Data Package descriptor is written: `PRESERVE` keeps the descriptor as authored, with references unchanged, and `CANONICAL` writes the normalised v2 form with `$schema` profile URLs.

See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects).

### Dialect

The specific engine behind a backend family, such as `narwhals-pandas`, `narwhals-duckdb` or `ibis-postgres`. Dialect-scoped capability declarations add to the family-wide ones; `KNOWN_DIALECTS` lists the names declarations may target.

See [Backend capabilities, families and dialects](chapters/09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

### `DistributionRule`

A reserved check class in the validation check IR for distribution and statistical checks. It is not implemented, and constructing one raises; dataset-level conditions expressible as one aggregate are written as `ScalarRule`.

See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### Drift

The set of divergences a conform step found between the declared schema and the actual source, with the action the contract took for each, reported as `ConformDrift`: extra and missing columns, type mismatches and related entries.

See [Drift reporting](chapters/11-conforming-data/index.md#drift-reporting).

### Dtype parsing

The conversion of user input into a canonical dtype by `parse_dtype()`, which accepts enum members, Python types and alias strings, or into a cast target by `parse_cast_target()`, which also accepts parameterized descriptors and native dtypes.

See [Parsing dtypes](chapters/03-dtypes/index.md#parsing-dtypes).

## E

### Egress

The conversion of a relation's result into a chosen output form through a terminal: a frame of a named library (`to_polars`, `to_pandas`, `to_pyarrow`), Python collections (`to_dicts`, `to_tuples`), dataclasses, Pydantic models or indexed structures.

See [Egress formats](chapters/08-collecting-results/index.md#egress-formats).

### `element`

The function `ma.element()` that builds an expression referring to the current list element inside the per-element expression passed to `list.filter(...)` or `list.agg(...)` on a list column.

See [Names, structs and lists](chapters/05-namespaces-aggregates-and-windows/index.md#names-structs-and-lists).

### Empty policy

The `EmptyPolicy` setting of a pipeline unit that decides what an output with no rows means: `WARN` (the default) logs a warning, `FAIL` raises `EmptyUnitOutput` and `SILENT` skips the check.

See [Running a pipeline](chapters/15-pipelines/index.md#running-a-pipeline).

### Execution location

The place a relation node runs, resolved from the plan without reading rows: a backend family, a dialect, an evaluation form (eager, lazy or deferred) and a binding, such as an Ibis connection. Sources sit where their data lives.

See [Execution targets and locations](chapters/09-execution-targets-and-capabilities/index.md#execution-targets-and-locations).

### Execution target

An explicit request for where work runs: `execute_on=` on a join chooses which input it runs at, and `target=` on `collect()` chooses where the plan's root runs. Without one, placement follows the data.

See [Execution targets and locations](chapters/09-execution-targets-and-capabilities/index.md#execution-targets-and-locations).

### `explain`

A relation method that returns a description of the compiled plan without executing it: the engine's query plan or SQL, or, when the plan crosses locations, the relation tree with each node's location and each transfer.

See [Explain, fingerprint and snapshots](chapters/08-collecting-results/index.md#explain-fingerprint-and-snapshots).

### Expression AST node

An immutable Pydantic model that holds one element of an expression tree, such as `ScalarFunctionNode`, `FieldReferenceNode` or `LiteralNode`, and only an `accept(visitor)` method. New scalar operations add function keys, not node classes.

See [Expression AST nodes](chapters/18-expression-compilation/index.md#expression-ast-nodes).

### Expression namespace

An attribute of an expression, such as `.str`, `.dt`, `.list`, `.struct`, `.name`, `.cat` or `.geo`, that groups operations for one kind of data and returns new expressions, so calls chain across namespaces.

See [Namespaces](chapters/05-namespaces-aggregates-and-windows/index.md#namespaces).

### Expression object

The value returned by expression entry points such as `ma.col`, an instance of `ma.BaseExpressionAPI` (concretely `BooleanExpressionAPI`). It wraps one AST node and holds no data and no backend.

See [Expression objects](chapters/04-building-expressions/index.md#expression-objects).

### Expression system

A backend's implementation of every expression-system protocol, composed by multiple inheritance into one class such as `PolarsExpressionSystem`, and called by the visitor to produce native expressions.

See [API builders and expression systems](chapters/17-architecture/index.md#api-builders-and-expression-systems).

## F

### Failure case

One row of `ValidationResult.failure_cases`, describing a failing or unknown outcome of one check for one row or diagnostic, with the check id, outcome, field and value where known, message and row identity columns.

See [Results, row identity and failure cases](chapters/13-validation/index.md#results-row-identity-and-failure-cases).

### `FieldDefinition`

An immutable, unnamed declaration of one table field: its type (`type`, `dtype`, `format`), constraints, lexical reading rules and conform behaviour. A `TableSchema` maps names to field definitions.

See [TableSchema and fields](chapters/10-table-schemas-and-datapackage/index.md#tableschema-and-fields).

### `fields_match`

The `TableSchema` setting naming a Frictionless preset (`exact`, `equal`, `subset`, `superset`, `partial` or the mountainash `open`) that fixes the conform contract's column dimensions and any structural guard. The default is `exact`.

See [ConformContract dimensions and presets](chapters/11-conforming-data/index.md#conformcontract-dimensions-and-presets).

### `filter`

The relation method that keeps rows where every given boolean predicate is true, dropping rows where a predicate is null. Ternary predicates must be booleanized explicitly first.

See [Filtering, selecting and sorting](chapters/07-relations/index.md#filtering-selecting-and-sorting).

### `fingerprint`

A relation method that summarises content as a small Polars frame of hashes per value column, keyed by a declared logical key, so that two relations in different engines can be compared without moving their data.

See [Explain, fingerprint and snapshots](chapters/08-collecting-results/index.md#explain-fingerprint-and-snapshots).

### Foreign key

A schema declaration (`ForeignKey` with a `ForeignKeyReference`) that the values of some fields must appear in fields of a referenced table. Declaring one checks no data; `RelationDAG` records it as a constraint edge.

See [Foreign keys](chapters/10-table-schemas-and-datapackage/index.md#foreign-keys).

### `ForeignKeyRule`

The validation check that every child key appears among the parent's keys, comparing canonical logical key values rather than running a backend join. A child key with a null component is not an orphan by default (SQL `MATCH SIMPLE`).

See [Foreign keys](chapters/13-validation/index.md#foreign-keys).

### Frictionless Table Schema

The Frictionless Data standard for describing a table's fields, types and constraints as JSON. `TableSchema.to_frictionless()` and `from_frictionless()` write and read it, keeping mountainash-only settings under an `x-mountainash` key.

See [Frictionless descriptors](chapters/10-table-schemas-and-datapackage/index.md#frictionless-descriptors).

### `from_arrow`

The function `ma.from_arrow(table, target=None)` that imports a PyArrow table immediately and returns a relation over the copy, in Polars by default or as an owned temporary table on a given Ibis connection.

See [Relations from Arrow](chapters/07-relations/index.md#relations-from-arrow).

### Function key

An enum member (`FKEY_*`) that identifies one expression operation, such as `FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT`. It is the operation's identity from node construction through registry lookup, capability lookup and backend dispatch.

See [Function keys](chapters/18-expression-compilation/index.md#function-keys).

```python
import mountainash as ma
from mountainash.expressions.introspect import walk

expr = ma.col("qty").fill_null(0) > 3
for node in walk(expr):
    print(type(node).__name__, getattr(node, "function_key", None))
```

```text
ScalarFunctionNode FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT
ScalarFunctionNode FKEY_MOUNTAINASH_NULL.FILL_NULL
FieldReferenceNode None
LiteralNode None
LiteralNode None
```

### Function registry

The registry (`ExpressionFunctionRegistry`) that maps each function key to an `ExpressionFunctionDef` describing the protocol method to call and its parameters. The expression visitor dispatches only through it.

See [The function registry](chapters/18-expression-compilation/index.md#the-function-registry).

## G

### Gate then lower

The ordering rule that an operation stays as its canonical AST node until capability gates have inspected it, and only then is lowered into backend primitives, so a refusal names the operation the user wrote.

See [The unified expression visitor](chapters/18-expression-compilation/index.md#the-unified-expression-visitor).

### Graph kernel

The small graph container `Graph` in `mountainash.graph`, shared by `RelationDAG` and pipelines. It stores named nodes with separate dependency and constraint edge sets and provides ordering, layering and ancestry, but never executes anything.

See [The graph kernel](chapters/14-relationdag/index.md#the-graph-kernel).

### `group_by`

The relation method that returns a `GroupedRelation`; its `agg(*expressions)` produces one row per distinct key combination, with the key columns followed by one column per named aggregate. Group order is not defined.

See [Grouping and reshaping](chapters/07-relations/index.md#grouping-and-reshaping).

### `guarded`

A helper, `guarded(precondition, test)`, that builds a conditional rule expression: rows where the precondition is false pass, and the test applies to the rest. It returns the ordinary expression `precondition.not_() | test`.

See [Writing custom rules](chapters/12-data-contracts/index.md#writing-custom-rules).

## H

### Horizontal function

A free function that combines several expressions within each row, following Polars naming: `ma.max_horizontal`, `ma.min_horizontal`, `ma.all_horizontal`, `ma.any_horizontal` and `ma.sum_horizontal`. Each needs at least two arguments.

See [Horizontal functions](chapters/05-namespaces-aggregates-and-windows/index.md#horizontal-functions).

## I

### Ibis family

The backend family that compiles expressions to deferred Ibis expressions and relations to Ibis tables, run as SQL by the bound connection. It is installed with the `ibis` extra and covers each SQL engine as an `ibis-` dialect.

See [Ibis and SQL dialects](chapters/21-backends/index.md#ibis-and-sql-dialects).

### Identity (pipeline)

A digest (`Identity`) of everything that determines a pipeline unit's output: its version, parameters and upstream identities. Checkpoints key results by identity, so an unchanged identity lets a run reuse the stored result.

See [Values, identity and checkpoints](chapters/15-pipelines/index.md#values-identity-and-checkpoints).

### Ingress

The conversion of Python data (dicts, lists of records, dataclasses, Pydantic models, tuples and similar) into a Polars frame, chosen by input shape. `ma.relation` uses it for Python inputs; `ma.PydataIngress` exposes it with schemas.

See [Relations from Python data](chapters/07-relations/index.md#relations-from-python-data).

### `is_in`

The expression method that tests whether each value appears in a fixed set of members, with `is_not_in` as its complement. It never coerces types, and a null value is reported as neither in nor not in the set.

See [Membership](chapters/05-namespaces-aggregates-and-windows/index.md#membership).

## J

### `join`

The relation method that combines two relations on key columns with `how` set to `inner`, `left`, `right`, `outer`, `semi`, `anti` or `cross`. Overlapping right column names receive `suffix`, and `execute_on` chooses which side it runs at.

See [Joins](chapters/07-relations/index.md#joins).

## K

### Keyed registry

The shared registry primitive `KeyedRegistry` in `mountainash.core.registries`: a dictionary with decorator registration, optional lazy initialisation and validation and a duplicate-key check, used for backend systems, visit handlers, optimisation passes and schema adapters.

See [The function registry](chapters/18-expression-compilation/index.md#the-function-registry).

### Known divergence

A recorded case where the same expression or relation fails or gives a different result on some backend. It is declared in capability records or tests instead of hidden, and becomes a gate where a declaration refuses the call.

See [Known divergences](chapters/16-backend-support-and-limits/index.md#known-divergences).

## L

### Lazy evaluation

Describing work first and executing it later as one unit. mountainash relations record operations without touching data, and run only when a terminal is called, which lets the engine optimise the whole plan.

See [Lazy plans and the AST](chapters/01-what-mountainash-does/index.md#lazy-plans-and-the-ast).

### Lazy top-level import

The loading strategy of `import mountainash as ma`, which imports no dataframe backend. Expression, relation, DAG and capability names are attached with `lazy_loader` and import their subpackage, which registers available backends, on first access.

See [The top-level namespace](chapters/02-installation-and-package-surface/index.md#the-top-level-namespace).

### `lit`

The function `ma.lit(value)` that builds an expression for a constant, optionally typed with `dtype=`. Plain Python values next to operators and methods are wrapped automatically, so it is needed mainly when the constant comes first or stands alone.

See [Columns, literals and conditions](chapters/04-building-expressions/index.md#columns-literals-and-conditions).

### Logical terminal

A terminal that builds its output through the final resolution step for conformed structured fields, such as `to_polars()`. Native terminals (`collect()`, `collect_with_drift()`) raise `LogicalTerminalRequired` when a plan contains fields that need that step.

See [Collect and terminals](chapters/08-collecting-results/index.md#collect-and-terminals).

## M

### `materialization_scope`

A context manager, `ma.materialization_scope()`, that owns the snapshots and checkpoint copies taken through it and releases them when it closes; `scope.detach(rel)` lets copies outlive the scope.

See [Materialization scopes and checkpoints](chapters/09-execution-targets-and-capabilities/index.md#materialization-scopes-and-checkpoints).

### Missing values

Text sentinels, declared with `missing_values` on a schema or field, that stand for null in lexical data such as CSV. They are compared as strings before type conversion and may carry a reason through `LabeledValue`.

See [Missing values and temporals](chapters/10-table-schemas-and-datapackage/index.md#missing-values-and-temporals).

### `MountainashError`

The root class of every error mountainash raises deliberately, exported as `ma.MountainashError`. Domains with several errors have their own base, and many classes also inherit a matching built-in exception such as `ValueError`.

See [Errors](chapters/02-installation-and-package-surface/index.md#errors).

### `mountainash.exceptions`

The module that re-exports typed error classes from the modules that own them, following the `polars.exceptions` convention. Some errors, including pipeline and execution-location errors, are imported from their owning modules instead.

See [Errors](chapters/02-installation-and-package-surface/index.md#errors).

## N

### Narwhals family

The backend family that compiles to Narwhals expressions and frames, so one implementation serves pandas, PyArrow, Dask, DuckDB and Polars through Narwhals. `collect()` returns the native result of the provider underneath.

See [Narwhals and its providers](chapters/21-backends/index.md#narwhals-and-its-providers).

### Narwhals provider

The native library underneath a Narwhals frame, used as its dialect: `narwhals-pandas`, `narwhals-pyarrow`, `narwhals-polars`, `narwhals-lazy`, `narwhals-duckdb` or `narwhals-dask`. DuckDB and Dask are lazy-only providers.

See [Narwhals and its providers](chapters/21-backends/index.md#narwhals-and-its-providers).

### `native`

The function `ma.native(expr)` that wraps a backend-native expression so it can be combined with portable operations. It passes through unchanged, so the containing expression runs only on that backend and needs an explicit alias.

See [Escaping to native expressions](chapters/04-building-expressions/index.md#escaping-to-native-expressions).

### Native schema conversion

The conversion of a `TableSchema` into a library's own schema object, such as a Polars schema or PyArrow schema, through the dtype registry. Each field resolves to `backend_type`, then `dtype`, then the canonical mapping of `type`.

See [Extracting and converting schemas](chapters/10-table-schemas-and-datapackage/index.md#extracting-and-converting-schemas).

### Native type adapter

A stateless class, one per type target, that translates canonical dtypes to and from that library's native types and carries Arrow transport behaviour. The set of targets is closed, so adding one is a package change.

See [Type and schema adapters](chapters/22-extending-mountainash/index.md#type-and-schema-adapters).

## O

### Operand transfer

The movement of a subtree's result from its own execution location to the location of the operation that consumes it, planned before execution and shown in `explain()`. Data crosses families as an Arrow table.

See [Operand transfer and owned copies](chapters/09-execution-targets-and-capabilities/index.md#operand-transfer-and-owned-copies).

### Operand type resolution

The compile-time lookup of the types of an operation's operands from the native input's schema metadata, without executing data, for operations and capability rules that declare they need those types.

See [The unified expression visitor](chapters/18-expression-compilation/index.md#the-unified-expression-visitor).

### Optimisation pass

A transform registered by another package with `register_optimisation(node_type, transform_fn)` and applied to relation trees containing that node type before preparation. mountainash itself ships none and leaves optimisation to the engines.

See [Optimisation passes](chapters/19-relation-compilation/index.md#optimisation-passes).

### Output name

The column name an expression produces in `select` or `with_columns`, derived from the expression tree the same way on every backend: a column keeps its name, an operation takes its first operand's name, and `.alias()` or `.name` overrides it.

See [Output names](chapters/04-building-expressions/index.md#output-names).

### `over`

The expression method `.over(*partition_by, order_by=...)` that evaluates an expression within groups of rows while keeping every row, like a SQL window. It broadcasts aggregates and orders cumulative, offset and ranking functions.

See [Windows with over](chapters/05-namespaces-aggregates-and-windows/index.md#windows-with-over).

### Owned copy

An independent native value that mountainash created and is responsible for cleaning up, such as a snapshot, checkpoint copy or durable transfer result. On an Ibis connection it is a `ma_owned_` table dropped once unreachable.

See [Operand transfer and owned copies](chapters/09-execution-targets-and-capabilities/index.md#operand-transfer-and-owned-copies).

## P

### Parameter axis

A `ParamAxis(names, values)` declaring one dimension of pipeline parameters to iterate over; `expand_axes(*axes)` yields the Cartesian product as parameter dictionaries, each run and checkpointed separately.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### Parameterized dtype

A frozen descriptor for a canonical type that needs parameters, such as `DecimalDtype(precision, scale)`, `TimestampDtype`, `TimeDtype`, `DurationDtype`, `ListDtype` or `StructDtype`. Unstated parameters are `SchemaTypeStatus.UNKNOWN`.

See [Canonical dtypes](chapters/03-dtypes/index.md#canonical-dtypes).

### Per-backend xfail

The testing convention that a backend failing a cross-backend test stays in the parametrisation and is marked as a strict expected failure for that backend only, with a reason naming the cause.

See [Known divergences and per-backend xfail](chapters/23-contributing-and-testing/index.md#known-divergences-and-per-backend-xfail).

### Pipeline

A named graph of units (`Pipeline`) in which each unit declares the units it depends on. A `Runner` plans and executes it with checkpoints, retries and parameter sets. The pipeline surface is still evolving.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### `pivot` and `unpivot`

Relation methods that reshape data: `pivot` turns the distinct values of one column into new columns (long to wide), and `unpivot`, alias `melt`, turns columns into variable and value rows (wide to long).

See [Grouping and reshaping](chapters/07-relations/index.md#grouping-and-reshaping).

### Polars family

The backend family that compiles to native Polars, with the single dialect `polars`. It is a base dependency and the reference backend for cross-backend tests; its relation system works on `LazyFrame`.

See [Polars](chapters/21-backends/index.md#polars).

### Polars-style API

The convention that mountainash's public method names, parameters and chaining follow Polars, so `ma.col`, `ma.lit`, `ma.when` and relation methods such as `filter` and `with_columns` read like their Polars counterparts.

See [One logic, many engines](chapters/01-what-mountainash-does/index.md#one-logic-many-engines).

### Preflight

The check that runs capability gates over a whole relation plan after execution locations are resolved and before any source is read or any data is transferred. Gates that need compiler metadata are left to compilation.

See [Gates and preflight](chapters/20-capability-spine/index.md#gates-and-preflight).

### Protocol

A `typing.Protocol` class listing the methods, with exact signatures, that one operation domain requires of an API builder or a backend system. Every backend must implement each protocol method and add no undeclared operations.

See [Protocols as contracts](chapters/17-architecture/index.md#protocols-as-contracts).

### Protocol alignment test

A test that discovers protocols and their implementations by introspection and fails when a method, key or parameter is missing or mismatched in any backend, unless it is listed as a known gap with a reason.

See [Cross-backend testing](chapters/23-contributing-and-testing/index.md#cross-backend-testing).

### `PythonUnit`

A pipeline unit that runs a Python function, receiving one argument per dependency and a run context; the `@unit` decorator creates one. The function's return value becomes the unit's value.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

## R

### Relation

A `Relation` object holding a tree of relational operations over one or more sources. Each chainable method returns a new relation with one more node, reading and compiling nothing until a terminal is called.

See [Relation objects](chapters/07-relations/index.md#relation-objects).

### `relation`

The function `ma.relation(data)` that creates a relation from a Polars, Narwhals-supported or Ibis object, or from Python data. The argument's type decides where the plan runs.

See [Relation objects](chapters/07-relations/index.md#relation-objects).

### Relation AST node

A Pydantic model, defined under `relations/core/relation_nodes/`, holding one relational operation, its children and its embedded expressions, with a dispatch key. Node kinds follow Substrait relation types plus mountainash extensions.

See [Relation AST nodes](chapters/19-relation-compilation/index.md#relation-ast-nodes).

### Relation operation key

An enum member of `RKEY_SUBSTRAIT_REL` or `RKEY_MOUNTAINASH_REL` that identifies one relational operation, playing the role function keys play for expressions. `RelationOperationRegistry` maps each key to its definition.

See [Relation operation keys and registry](chapters/19-relation-compilation/index.md#relation-operation-keys-and-registry).

### Relation system

A backend family's class implementing every relational operation on native objects, composed from mixins that satisfy nine relation-system protocols (eight Substrait relation kinds plus mountainash extensions).

See [Relation systems](chapters/19-relation-compilation/index.md#relation-systems).

### `RelationDAG`

A named collection of relations, created with `ma.RelationDAG()`, in which relations refer to each other with `dag.ref(name)`. It records dependency and constraint edges, collects named relations in topological order and validates tables and foreign keys together.

See [Building a DAG](chapters/14-relationdag/index.md#building-a-dag).

### `RelationRule`

A validation check whose `plan` function receives the relation under test and returns the rows that break the rule, so any join, group or window the relation API supports can express the check.

See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### Resource read

The deferred reading of a Data Package resource when a resource relation is collected: inline data becomes an in-memory frame, local CSV or Parquet is scanned natively, and other sources go through `mountainash-transport`.

See [Resources and DataPackage](chapters/14-relationdag/index.md#resources-and-datapackage).

### `ResourceRef`

A wrapper, `ma.ResourceRef`, around one `DataResource` that reports whether the resource is tabular and reads it: `relation()` for a tabular resource and `read_bytes()` for raw content.

See [Resources and DataPackage](chapters/14-relationdag/index.md#resources-and-datapackage).

### Retry configuration

The `RetryConfig` passed to a pipeline `Runner` that retries a failing unit up to `max_attempts` times with exponential backoff. Exceptions derived from `NonRetryable` are never retried.

See [Running a pipeline](chapters/15-pipelines/index.md#running-a-pipeline).

### Row identity

The rule, `RowIdentity`, for how a validation failure case points back to its source row: `keyed` by a natural or primary key, `row_number` by position as a diagnostic ordinal, or `none` (the default).

See [Results, row identity and failure cases](chapters/13-validation/index.md#results-row-identity-and-failure-cases).

### `RowRule`

A validation check that evaluates a boolean or ternary expression once per row and counts passes, failures and unknowns, with optional `mostly` threshold, booleanizer, message and fields copied into failure cases.

See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### `Rule`

A frozen, named mountainash expression that should hold for a dataset, used in data contracts for conditions beyond single-field constraints. `RuleRegistry` groups rules; `id`, `booleanizer`, `mostly` and `severity` control how each is checked.

See [Rules and guarded rules](chapters/12-data-contracts/index.md#rules-and-guarded-rules).

### `Runner`

The pipeline executor, `Runner(pipeline, checkpoint=None, workers=1, retry=None)`. `plan()` orders units and computes identities without running anything; `execute()` runs layers, reusing checkpointed results; `run()` does both.

See [Running a pipeline](chapters/15-pipelines/index.md#running-a-pipeline).

## S

### Scalar terminal

A relation terminal that returns one Python value: `item(column, row)` for one cell, `count_rows()`, or an aggregate over a whole column such as `sum`, `avg`, `min` or `max`.

See [Scalar terminals](chapters/08-collecting-results/index.md#scalar-terminals).

### `ScalarRule`

A validation check whose aggregate expression reduces the whole dataset to one boolean verdict. A null result counts as not passing.

See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### Schema adapter and codec

The two extension contracts for schemas: a `NativeSchemaAdapter` reads and encodes a `TableSchema` for one native library, and a `SchemaCodec` decodes and encodes a complete schema in one interchange format such as Frictionless.

See [Type and schema adapters](chapters/22-extending-mountainash/index.md#type-and-schema-adapters).

### Schema comparison

The comparison of two table schemas by `compare_specs`, returning a `SpecDiff` of missing fields, extra fields and type changes, and the check of a dataframe against a schema by `validate_match` and `assert_match`.

See [Extracting and converting schemas](chapters/10-table-schemas-and-datapackage/index.md#extracting-and-converting-schemas).

### Schema extraction

The derivation of a `TableSchema` from an existing shape: a dataframe of any supported backend (`extract_from_dataframe`), a dataclass (`extract_from_dataclass`) or a Pydantic model (`extract_from_pydantic`).

See [Extracting and converting schemas](chapters/10-table-schemas-and-datapackage/index.md#extracting-and-converting-schemas).

### Schema inference

The determination of a relation's output columns and types, through `rel.schema`, from the plan, source schemas and native metadata without executing the plan. Types that cannot be established are `SchemaTypeStatus.UNKNOWN`.

See [Schema inference and resolution](chapters/09-execution-targets-and-capabilities/index.md#schema-inference-and-resolution).

### `select` and `with_columns`

Relation methods for projecting columns: `select` returns only the listed columns and expressions, and `with_columns` keeps every column and adds or replaces the listed ones. `with_columns` takes positional expressions named with `.alias()`.

See [Filtering, selecting and sorting](chapters/07-relations/index.md#filtering-selecting-and-sorting).

### Selector

The part of a capability record that narrows it within a parameter: an exact option value, a predicate over the bindings of a bound call, or a value class that matches a family of option strings.

See [Bound calls and value classes](chapters/20-capability-spine/index.md#bound-calls-and-value-classes).

### Sentinel

A value declared with `ma.t_col(name, unknown={...})` that ternary comparisons on that column treat as UNKNOWN. The set replaces the default, so null counts as UNKNOWN only when `None` is included.

See [Ternary columns and sentinels](chapters/06-ternary-logic/index.md#ternary-columns-and-sentinels).

### Severity

The closed classification of a validation check as `"blocking"` (the default) or `"warning"`. A failed warning check keeps its status in summaries but does not make the result fail; a check that errors always blocks.

See [How the runner executes checks](chapters/13-validation/index.md#how-the-runner-executes-checks).

### Sink unit

A pipeline unit, subclassing `SinkUnit`, that writes its single upstream value to an external destination and returns a `LocatorReference` (a locator and a record count) instead of the data. `ParquetDirectorySink` and `IbisTableSink` are built in.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### Snapshot

A relation over an independent native copy of a plan's result, taken now with `snapshot()`. Later changes to the source do not reach it; on a database the copy is a temporary table that mountainash owns.

See [Explain, fingerprint and snapshots](chapters/08-collecting-results/index.md#explain-fingerprint-and-snapshots).

### Source unit

A pipeline unit that fetches data from outside the pipeline, possibly incrementally, returning a `SourceResult` with the value, its partition coverage and a resume cursor. `CallableSource` wraps a fetch function.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### Structured field transport

The way conform carries a field declared `array` or `object`: native lists and structs are converted in place, JSON text is decoded at the end, and unknown types are carried opaquely, chosen from the source type alone.

See [Transform stages](chapters/11-conforming-data/index.md#transform-stages).

### Substrait

An open specification for relational query plans and their scalar, aggregate and window functions. The mountainash AST follows its model: relation nodes match Substrait relation types and standard operations carry `FKEY_SUBSTRAIT_*` keys.

See [Lazy plans and the AST](chapters/01-what-mountainash-does/index.md#lazy-plans-and-the-ast).

### Substrait and mountainash extensions

The split of operations by origin at every layer: `FKEY_SUBSTRAIT_*` keys and `substrait/` directories for operations Substrait defines, and `FKEY_MOUNTAINASH_*` keys and `extensions_mountainash/` directories for operations it does not, such as ternary logic.

See [Function keys](chapters/18-expression-compilation/index.md#function-keys).

### Support matrix

The generated reference table that crosses registered operations with backend families and dialects, built from the capability catalogue, while keeping implementation discovery, information records and policies apart.

See [Support matrix](chapters/16-backend-support-and-limits/index.md#support-matrix).

## T

### `t_col`

The function `ma.t_col(name, unknown=...)` that builds a column reference for ternary work and optionally declares sentinel values that every ternary comparison on the column treats as UNKNOWN.

See [Ternary columns and sentinels](chapters/06-ternary-logic/index.md#ternary-columns-and-sentinels).

### `table_schema`

The shortcut `ma.table_schema(columns, **metadata)` that builds a `TableSchema` from a `{name: type_string}` dictionary of Frictionless type names, the same as `TableSchema.from_simple_dict`.

See [TableSchema and fields](chapters/10-table-schemas-and-datapackage/index.md#tableschema-and-fields).

### Table schema semantic validation

The checking of a `TableSchema` declaration without data by `validate_table_schema_semantics`, returning `TableSchemaIssue` records for problems such as keys naming undeclared fields or constraints unsuited to a field type.

See [Table schema semantic validation](chapters/13-validation/index.md#table-schema-semantic-validation).

### `TableDialect`

The model of a Frictionless Table Dialect, `ma.TableDialect`, describing how a delimited, structured, spreadsheet or database source is laid out, such as delimiter, quote character, header rows and sheet name.

See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects).

### `TableSchema`

The model of a table's structure: an ordered mapping from column name to `FieldDefinition`, plus table-level settings such as primary key, foreign keys, missing values and `fields_match`. It reads and writes Frictionless Table Schema.

See [TableSchema and fields](chapters/10-table-schemas-and-datapackage/index.md#tableschema-and-fields).

### Terminal

A relation method that executes the plan and returns a result, such as `collect()`, `to_polars()`, `to_dicts()` or `item()`. Building never executes; each terminal call runs the plan again.

See [Collect and terminals](chapters/08-collecting-results/index.md#collect-and-terminals).

### Ternary comparison

A comparison method (`t_eq`, `t_ne`, `t_gt`, `t_ge`, `t_lt`, `t_le`, `t_is_in`, `t_is_not_in`) that returns 1 where it holds, -1 where it does not and 0 where either side is null or a declared sentinel.

See [Ternary comparisons and logic](chapters/06-ternary-logic/index.md#ternary-comparisons-and-logic).

### Ternary logical operator

A method (`t_and`, `t_or`, `t_not`, `t_xor`, `t_xor_parity`) that combines ternary values. With TRUE=1, UNKNOWN=0 and FALSE=-1, AND is the minimum of its inputs, OR the maximum and NOT flips the sign.

See [Ternary comparisons and logic](chapters/06-ternary-logic/index.md#ternary-comparisons-and-logic).

### Three-layer separation

The internal architecture in which protocols declare required methods, API builders turn user calls into AST nodes, and backend systems compile nodes into native objects. Each layer has one responsibility and its own kind of knowledge.

See [Three-layer separation](chapters/17-architecture/index.md#three-layer-separation).

### Three-valued logic

A logic with an explicit third outcome, UNKNOWN, beside TRUE and FALSE, so missing data is not silently treated as false. mountainash encodes ternary results as integers: TRUE is 1, UNKNOWN is 0 and FALSE is -1.

See [Three-valued logic](chapters/01-what-mountainash-does/index.md#three-valued-logic).

### `today` and `now`

Functions, `ma.today()` and `ma.now()`, that produce the current date and timestamp as a constant column. The value is taken at compile time; on Ibis, `now()` uses the database server's clock.

See [Columns, literals and conditions](chapters/04-building-expressions/index.md#columns-literals-and-conditions).

### `TypeTarget`

The enum naming each library whose types the canonical dtypes map to and from: `polars`, `pandas`, `pyarrow`, `ibis`, `narwhals` and `python`. Type targets are conversion destinations, distinct from execution backends.

See [Native type targets](chapters/03-dtypes/index.md#native-type-targets).

## U

### Unified expression visitor

The single class, `UnifiedExpressionVisitor`, that compiles every expression node type for one backend by looking up function keys in the function registry, applying capability gates and calling the backend expression system.

See [The unified expression visitor](chapters/18-expression-compilation/index.md#the-unified-expression-visitor).

### Unified relation visitor

The class, `UnifiedRelationVisitor`, that turns a relation node tree into a native plan by calling a relation system, composing with a unified expression visitor for the expressions embedded in each node.

See [The unified relation visitor](chapters/19-relation-compilation/index.md#the-unified-relation-visitor).

### Unit

An object satisfying the pipeline `Unit` protocol: a name, a version, input names, an identity computed from inputs and parameters, a `run(upstream, ctx)` method and a lifecycle that tells the runner how to plan, run and commit it.

See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### Universal type

A member of `UniversalType`, the Frictionless field type list (`integer`, `number`, `date`, `year` and others). `to_canonical` and `from_canonical` map between universal types and canonical dtypes at the Frictionless boundary.

See [Frictionless descriptors](chapters/10-table-schemas-and-datapackage/index.md#frictionless-descriptors).

## V

### `ValidationPlan`

A sequence of named validation steps, each a validator with its data, run in order with a shared context. `execute()` returns a `PlanResult`; `fail_fast=True` stops after the first step that does not pass.

See [Validator and validation plans](chapters/12-data-contracts/index.md#validator-and-validation-plans).

### `ValidationResult`

The outcome of a validation run: `passes`, the contract and validator names, `check_summaries` and `failure_cases` as Polars frames on every backend, and the row identity used.

See [Results, row identity and failure cases](chapters/13-validation/index.md#results-row-identity-and-failure-cases).

### `ValidationRunner`

The engine that runs a list of validation checks against one relation or native dataframe with `validate_relation`, returning a `ValidationResult` without raising for failing or erroring checks.

See [Running checks](chapters/13-validation/index.md#running-checks).

### `Validator`

A reusable validation step that binds a data contract, an optional rule registry, an optional natural key and optional data preparation. `validate(data)` resolves row identity, conforms the data and runs the checks.

See [Validator and validation plans](chapters/12-data-contracts/index.md#validator-and-validation-plans).

### Value class

A named family of option strings (`ValueClass`) recognised by a fixed predicate, used by capability selectors to match an unbounded set of values with one record. The built-in classes cover IANA time zone names, Polars offset strings and duration multipliers.

See [Bound calls and value classes](chapters/20-capability-spine/index.md#bound-calls-and-value-classes).

### Value classification

The identification of a scalar's kind without coercing it: `ma.value_kind(value)` returns a `ma.ValueKind` (`ABSENT`, `BOOLEAN`, `INTEGER`, `FLOAT`, `TEXT` or `UNSUPPORTED`), checking exact types so `True` is never read as 1.

See [Value classification](chapters/02-installation-and-package-surface/index.md#value-classification).

### Value (pipeline)

The object (`Value`) passed between pipeline units: a payload, the producing unit's identity, a kind (`RECORDS`, `TABULAR`, `REFERENCE` or `OPAQUE`), a backend location for frames and an optional partition coverage.

See [Values, identity and checkpoints](chapters/15-pipelines/index.md#values-identity-and-checkpoints).

### `ValueRule`

A validation check that applies a named logical value validator, such as an allowed-value set or a JSON Schema, to one or more fields per row, counting passes, failures and unknowns.

See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### Visit handler

A function registered in `RelationVisitRegistry` for a custom `RelationNode` subclass. The relation visitor calls it before any operation-key lookup, so packages outside mountainash can add relation nodes without changing the package.

See [Custom relation nodes](chapters/22-extending-mountainash/index.md#custom-relation-nodes).

## W

### `when`

The function `ma.when(condition).then(value)` that starts a conditional expression; further `when`/`then` pairs add branches tested in order and `.otherwise(value)` completes it. Plain values in `then` are literals, not column names.

See [Columns, literals and conditions](chapters/04-building-expressions/index.md#columns-literals-and-conditions).
