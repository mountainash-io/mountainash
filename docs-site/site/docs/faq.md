---
title: FAQ
---

# FAQ

Short answers to common questions about mountainash. Each answer links to the section that covers it in full.

## Getting started

### What does mountainash do?

mountainash runs tabular data logic, written once as expressions and relation plans with a Polars-style API, on Polars, on the libraries Narwhals reaches (pandas, PyArrow, Dask, DuckDB) and on SQL engines through Ibis. The logic stays a backend-agnostic tree until a terminal call compiles it for the engine that owns the data. Schemas, conformance, data contracts and validation build on the same expressions and relations. See [One logic, many engines](chapters/01-what-mountainash-does/index.md#one-logic-many-engines).

### Which Python version and which extra do I need?

Python 3.12 or later. The base install runs plans on Polars and, through Narwhals, on PyArrow. Add `pandas` for pandas frames, `ibis` plus an Ibis driver such as `ibis-framework[duckdb]` for SQL engines (you install the database driver separately), `files` for reading CSV and Parquet resources, `http` for `https://` resources, and `s3`, `gcs`, `azure` or `sftp` for those storage services. Install Dask and DuckDB yourself to use them as Narwhals providers; no extra declares them. The `dbos` extra installs a package that the current source leaves unused. See [Base install and extras](chapters/02-installation-and-package-surface/index.md#base-install-and-extras).

### Why does `pip install mountainash` not find the package?

mountainash and its sibling packages have no public PyPI release yet. Work from a source checkout with the Hatch environments, which install the sibling packages from local checkouts beside it. See [Base install and extras](chapters/02-installation-and-package-surface/index.md#base-install-and-extras) and [Contributing and testing](chapters/23-contributing-and-testing/index.md).

### How do I choose which backend runs my code?

The data you pass picks the backend. `ma.relation(df)` and `expr.compile(df)` detect the family and dialect from the object's type: a Polars frame runs on Polars, a pandas or PyArrow object runs through Narwhals, and an Ibis table runs as SQL on its connection. See [Backend detection](chapters/02-installation-and-package-surface/index.md#backend-detection). To place a step somewhere else, use `execute_on=` on a join or `collect(target=...)`, described in [Execution targets and locations](chapters/09-execution-targets-and-capabilities/index.md#execution-targets-and-locations).

### Does `import mountainash` import Polars, pandas or Ibis?

No. The package root loads only dtypes, the error root, schema and DataPackage models, value classification and the version. The expression, relation and DAG names load their subpackages on first access, and those subpackages register whichever backends are importable. A script that only reads schemas runs with no dataframe library imported. See [The top-level namespace](chapters/02-installation-and-package-surface/index.md#the-top-level-namespace).

### How closely does the API follow Polars?

Names, parameters and chaining follow Polars. mountainash covers a subset of Polars, and a few behaviours differ:

- `with_columns` takes positional expressions only; name a column with `.alias()`.
- `ma.when(...).then("A")` produces the string `"A"`, not the column `A`.
- `remove()` drops rows where the predicate is null.
- `ma.sum_horizontal()` does not skip nulls.
- `sort` has no `nulls_last` parameter; the backend decides null placement.

See [One logic, many engines](chapters/01-what-mountainash-does/index.md#one-logic-many-engines), [Columns, literals and conditions](chapters/04-building-expressions/index.md#columns-literals-and-conditions) and [Filtering, selecting and sorting](chapters/07-relations/index.md#filtering-selecting-and-sorting).

## Expressions and relations

### Why does `relation.filter()` reject my ternary expression?

Relation methods compile ternary expressions as they are, so a `t_` expression reaches the engine as an integer column of -1, 0 and 1, and the engine rejects it as a filter predicate. `expr.compile(df)` is the one path that booleanizes automatically. Name the policy explicitly with a booleanizer method:

```python
import polars as pl
import mountainash as ma

scores = pl.DataFrame({"score": [80, -99999, None]})
passed = ma.t_col("score", unknown={-99999, None}).t_gt(70)

try:
    ma.relation(scores).filter(passed).to_polars()
except Exception as exc:
    print(type(exc).__name__, exc)

print(ma.relation(scores).filter(passed.t_is_true()).to_dicts())
print(ma.relation(scores).filter(passed.t_maybe_true()).to_dicts())
```

```text
ComputeError filter predicate must be of type `Boolean`, got `i32`
[{'score': 80}]
[{'score': 80}, {'score': -99999}, {'score': None}]
```

`t_is_true` keeps only definite matches; `t_maybe_true` also keeps rows whose answer is unknown. See [Booleanization](chapters/06-ternary-logic/index.md#booleanization).

### Why are my ternary results wrong when I use a boolean column?

Automatic conversion between boolean and ternary values applies to operation results. A bare column reference keeps its storage value, so a boolean column used directly as a ternary operand reads `false` as UNKNOWN. Convert the column first with `.to_ternary()`, or compare it (`ma.col("active").eq(True)`). See [Booleanization](chapters/06-ternary-logic/index.md#booleanization).

### What is the difference between `ma.col` and `ma.t_col`?

Both reference a column, and any expression can start a ternary chain. `ma.t_col(name, unknown={...})` also declares sentinel values that count as UNKNOWN in ternary comparisons. The set replaces the default: once `unknown=` is given, null is UNKNOWN only when `None` is in the set. See [Ternary columns and sentinels](chapters/06-ternary-logic/index.md#ternary-columns-and-sentinels).

### Why does `(a > 1) and (b > 2)` give the wrong answer without an error?

Python's `and`, `or` and `not` call `bool()` on the expression object, which is always true, so `a and b` evaluates to `b` alone. Use `&`, `|` and `~`, with each comparison in parentheses. See [Operators](chapters/04-building-expressions/index.md#operators).

### How do I use a Polars or Ibis function that mountainash does not offer?

Wrap the native expression with `ma.native(...)` and give it an `.alias()`. The expression then runs on that backend only, and an Ibis value must already be bound to the table. Use a portable operation whenever one exists. See [Escaping to native expressions](chapters/04-building-expressions/index.md#escaping-to-native-expressions).

### Why does `collect()` on a DuckDB table not return rows?

`collect()` returns the engine's native result. For an Ibis source, that result is an Ibis `Table` still bound to its connection. `to_polars()`, `to_pandas()`, `to_dicts()` and the other egress terminals execute the query and fetch rows. See [Collect and terminals](chapters/08-collecting-results/index.md#collect-and-terminals).

### Can I join a pandas frame to a Polars or DuckDB relation?

Yes. The right side of a join can come from any supported library, a dict or a list of dicts. The join runs where the left input lives, the plan transfers the right side there at execution, and `explain()` shows the transfer. Pass `execute_on="right"` to run the join on the right operand's engine. See [Joins](chapters/07-relations/index.md#joins) and [Operand transfer and owned copies](chapters/09-execution-targets-and-capabilities/index.md#operand-transfer-and-owned-copies).

### Why is `relation.columns` empty, or `schema` full of unknown types?

Some plans need execution to describe themselves. A pivot's columns depend on the data, a plan that transfers an operand between engines learns its types once the source runs, and a third-party relation node has no schema contract. Read an empty list as unknown. `collect_schema()` raises `IncompleteSchemaError` in these cases, and `collect_schema(allow_execution=True)` runs the plan to get the answer. See [Schema and columns](chapters/07-relations/index.md#schema-and-columns) and [Schema inference and resolution](chapters/09-execution-targets-and-capabilities/index.md#schema-inference-and-resolution).

### Why does `ma.relation("orders.csv")` fail?

`ma.relation` takes no file paths. Read files and DataPackage resources through `ma.ResourceRef(resource).relation()` or a `RelationDAG` built with `DataPackage.to_relation_dag()`. See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects) and [Resources and DataPackage](chapters/14-relationdag/index.md#resources-and-datapackage).

## Backends, execution and limits

### Why does a bare DuckDB relation or Dask frame fail at the terminal?

Backend detection classifies both as Narwhals sources. The Narwhals read wraps a bare native object eagerly, and these lazy-only providers reject that with Narwhals' own `TypeError`. Wrap them with `narwhals.from_native` first:

```python
import duckdb
import narwhals as nw
import mountainash as ma

rel = duckdb.sql("select 1 as id, 25 as amount union all select 2, 40")
try:
    ma.relation(rel).to_dicts()
except TypeError as exc:
    print(exc)
print(ma.relation(nw.from_native(rel)).filter(ma.col("amount") > 30).to_dicts())
```

```text
Cannot only use `series_only=True` or `eager_only=False` with DuckDBPyRelation
[{'id': 2, 'amount': 40}]
```

See [Narwhals and its providers](chapters/21-backends/index.md#narwhals-and-its-providers). To run SQL inside DuckDB itself, use an Ibis DuckDB connection.

### Why does `ma.relation(ibis.memtable(...))` raise `UnresolvedExecutionLocationError`?

An in-memory Ibis table has no connection to run on. It can borrow the connection of a peer input in a join or set operation; alone, it has no execution location. Create tables through a connection (`con.create_table(...)`), or import Arrow data with `ma.from_arrow(table, target=con)`. See [Execution targets and locations](chapters/09-execution-targets-and-capabilities/index.md#execution-targets-and-locations).

### How do I make a plan run inside my database?

Start the relation from an Ibis table bound to that connection. Every step then compiles to SQL on that connection, and `explain()` shows the query mountainash sends:

```python
import ibis
import polars as pl
import mountainash as ma

con = ibis.duckdb.connect()
orders = con.create_table("orders", pl.DataFrame({"id": [1, 2, 3], "amount": [25.0, 40.0, 15.5]}).to_arrow())

plan = ma.relation(orders).filter(ma.col("amount") > 20).select("id", "amount")
print(type(plan.collect()).__name__)
print(plan.explain())
print(plan.to_dicts())
```

```text
Table
SELECT
  *
FROM "memory"."main"."orders" AS "t0"
WHERE
  "t0"."amount" > 20
[{'id': 1, 'amount': 25.0}, {'id': 2, 'amount': 40.0}]
```

`ma.from_arrow(table, target=con)` moves local data in, and `collect(target=con)` collects a local plan into the connection. A join anchored on the database table pulls a local right side into it. See [Execution targets and locations](chapters/09-execution-targets-and-capabilities/index.md#execution-targets-and-locations), [Relations from Arrow](chapters/07-relations/index.md#relations-from-arrow) and [Ibis and SQL dialects](chapters/21-backends/index.md#ibis-and-sql-dialects).

### Why did an operation raise `BackendCapabilityError`?

The backend and dialect the call runs on cannot honour it, and mountainash raises this error in place of a result that would differ. The message starts with the family in brackets and may add `Workaround:` and `Upstream ref:` lines. When the refusal comes from a capability declaration, `function_key` names the operation and `limitation` holds the declaration:

```python
import ibis
import polars as pl
import mountainash as ma
from mountainash.exceptions import BackendCapabilityError

con = ibis.duckdb.connect()
numbers = con.create_table("numbers", pl.DataFrame({"n": range(100)}).to_arrow())
sampled = ma.relation(numbers).sample(n=5, seed=7)
try:
    sampled.to_dicts()
except BackendCapabilityError as exc:
    print(exc)
    print(exc.function_key, exc.limitation.dialect, exc.limitation.param)
```

```text
[ibis] Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported.
RKEY_MOUNTAINASH_REL.SAMPLE ibis-duckdb seed
```

See [Capability errors and capability_policy](chapters/09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy), and check the dialect in the [Support matrix](chapters/16-backend-support-and-limits/index.md#support-matrix).

### Can I switch a capability refusal off?

Declared refusals, yes. `ma.capability_policy(ma.CapabilityPolicy.trusted())` turns protection off inside a `with` block, and a `CapabilityPolicy` can narrow protection to selected issue classes. Relaxing it gives up what the declaration protected: under `trusted()` the seeded sample above runs, and its result is no longer reproducible. The policy leaves refusals raised by the backend implementation itself in place: on Ibis, `product()` still raises `BackendCapabilityError` under `trusted()`, with `limitation` set to `None`, and pandas through Narwhals still refuses a column as a `str.contains` pattern. See [Capability errors and capability_policy](chapters/09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy) and [Expression AST nodes](chapters/18-expression-compilation/index.md#expression-ast-nodes).

### Where can I see what each backend supports?

[Backend support and known limits](chapters/16-backend-support-and-limits/index.md) lists every declared refusal by dialect, the dialects that run the cross-backend test suite, and the catalogued divergences. A dialect with no record for an operation has unknown coverage. Point-of-use warnings in each chapter cover the limits that affect correct use.

### Why does the same plan give different numbers on Polars and DuckDB?

A few operations follow each engine's native rules where the cross-backend tests accept either result: `round()` tie-breaking, the sign of `%`, and float to integer casts (Polars truncates, DuckDB rounds). Where exact rounding matters, cast to `DecimalDtype` with an explicit `rounding=` mode. [Known divergences](chapters/16-backend-support-and-limits/index.md#known-divergences) lists the other value-changing divergences. See [Operators](chapters/04-building-expressions/index.md#operators) and [Casting, cast safety and nulls](chapters/04-building-expressions/index.md#casting-cast-safety-and-nulls).

### Why are snapshots or `from_arrow` refused on MySQL, SingleStoreDB or Exasol?

Both create a temporary table that mountainash owns on the connection, and those dialects declare owned temporary tables unsupported. Snapshots of an Ibis plan also need one bound connection with no open transaction. See [Explain, fingerprint and snapshots](chapters/08-collecting-results/index.md#explain-fingerprint-and-snapshots) and [Materialization scopes and checkpoints](chapters/09-execution-targets-and-capabilities/index.md#materialization-scopes-and-checkpoints).

### Why does `fingerprint()` fail on a pandas source?

`fingerprint()` reads results in bounded batches and supports Polars sources and DuckDB through Ibis only; other backends raise `BackendCapabilityError`. See [Explain, fingerprint and snapshots](chapters/08-collecting-results/index.md#explain-fingerprint-and-snapshots).

## Schemas, conform and validation

### Why does `ma.table_schema({"id": "int"})` raise `UnknownDtypeError`?

`ma.table_schema` takes Frictionless type names (`integer`, `number`, `string`, `date` and so on) and parses them strictly. Use `"integer"`, or declare the field with a canonical dtype through `ma.FieldDefinition(dtype=...)`. See [TableSchema and fields](chapters/10-table-schemas-and-datapackage/index.md#tableschema-and-fields) and [Canonical dtypes](chapters/03-dtypes/index.md#canonical-dtypes).

### Why did `fields_match` passed to `ma.table_schema` have no effect?

`ma.table_schema` passes through only `title`, `description` and `primary_key`, and currently drops any other keyword silently. Set the attribute on the result (`schema.fields_match = "open"`) or build a `ma.TableSchema` directly. Likewise, give `FieldDefinition(type=...)` a `UniversalType` member in place of a string. See [TableSchema and fields](chapters/10-table-schemas-and-datapackage/index.md#tableschema-and-fields).

### Why does conform raise an engine error instead of a mountainash error?

Under the default `data_type="coerce"` policy, a value that fails conversion fails inside the engine while the plan runs, and the engine raises its own exception: a `PolarsError` on Polars, `ValueError` on pandas, `ConversionException` on DuckDB. When you expect bad values, choose `discard_value` (the value becomes null) or `discard_row` (conform drops the row):

```python
import polars as pl
import mountainash as ma
from mountainash.typespec import UniversalType

raw = pl.DataFrame({"qty": ["1", "2", "x"]})
spec = ma.TableSchema(fields={"qty": ma.FieldDefinition(type=UniversalType.INTEGER)})
try:
    ma.relation(raw).conform(spec).to_polars()
except pl.exceptions.PolarsError as exc:
    print(type(exc).__name__)
print(ma.relation(raw).conform(spec, contract={"data_type": "discard_value"}).to_dicts())
print(ma.relation(raw).conform(spec, contract={"data_type": "discard_row"}).to_dicts())
```

```text
InvalidOperationError
[{'qty': 1}, {'qty': 2}, {'qty': None}]
[{'qty': 1}, {'qty': 2}]
```

`discard_value` and `discard_row` need a cast that returns null on failure. Narwhals backends (pandas, PyArrow and the rest) lack one, and Ibis on SQLite cannot compile it. See [Conform errors](chapters/11-conforming-data/index.md#conform-errors) and [ConformContract dimensions and presets](chapters/11-conforming-data/index.md#conformcontract-dimensions-and-presets).

### Why does conform raise `ExactFieldsMismatchError` when my data has an extra column?

The default `fields_match` is `exact`: source columns must match the declared fields in count, names and order. Choose another preset (`subset` drops extras, `partial` drops extras and skips missing fields, `open` keeps extras) or pass a `contract=`. See [ConformContract dimensions and presets](chapters/11-conforming-data/index.md#conformcontract-dimensions-and-presets).

### Why does `collect()` raise `LogicalTerminalRequired` after conform?

The schema declares an `array` or `object` field whose source is JSON text. A final step outside the engine parses those values, so a native terminal would return the raw JSON text. Use a logical terminal such as `to_polars()`, `to_dicts()` or validation. See [Transform stages](chapters/11-conforming-data/index.md#transform-stages) and [Collect and terminals](chapters/08-collecting-results/index.md#collect-and-terminals).

### Why does conform ask me for a rounding mode on a decimal field?

Converting a non-decimal source to a decimal field needs an explicit rounding mode, and conform raises `DecimalConversionRequiredError` until you give one. Set `rounding=` (`half_to_even`, `half_away_from_zero` or `to_zero`) on the `FieldDefinition`. Import the error from `mountainash.conform.errors`. See [Conform errors](chapters/11-conforming-data/index.md#conform-errors).

### How do I see what conform changed?

`relation.assess_drift()` reports every divergence between schema and source from the plan alone, and `collect_with_drift()` runs the plan and returns the frame with one `ConformDrift` report per conform step. The reports compare types in the canonical vocabulary, so their content is the same on every backend. See [Drift reporting](chapters/11-conforming-data/index.md#drift-reporting).

### Does conform check constraints such as `minimum` or `unique`?

No. Conform reshapes data and converts it to the declared types. Validation checks constraints, through a [data contract](chapters/12-data-contracts/index.md#declaring-a-contract) or the [validation engine](chapters/13-validation/index.md). `custom_cast` belongs to Python data conversion with a target schema, and conform skips it. See [Relation conform](chapters/11-conforming-data/index.md#relation-conform) and [Custom semantic types](chapters/10-table-schemas-and-datapackage/index.md#custom-semantic-types).

### Why does my validator report every check as `error`?

A `Validator` conforms the data to the contract before any check runs, so every check shares a conform failure. The most common cause is an undeclared column under the default `fields_match="exact"`. Declare the column, or relax `fields_match` on the contract's schema (`"open"` keeps undeclared columns). See [Validator and validation plans](chapters/12-data-contracts/index.md#validator-and-validation-plans).

### How do I make a rule ignore null values?

Give the rule `booleanizer="t_maybe_true"`. Unknown outcomes then count as passing, and only rows that definitely break the rule fail. This works for any rule, membership tests included, and the report still keeps the pass, fail and unknown counts separate. See [Rules and guarded rules](chapters/12-data-contracts/index.md#rules-and-guarded-rules).

### Why does a pandas source count null rows as failures rather than unknown?

pandas stores a missing number as NaN, and a comparison with NaN evaluates to false, where a null would give unknown. A boolean row check therefore counts those rows as `fail`, and `t_maybe_true` cannot exempt them. See [Running checks](chapters/13-validation/index.md#running-checks).

### Why does validation raise `IdentityInvalidError`?

Validation checks a natural key or primary key before any rule runs, and null keys or duplicate key tuples break it. Fix the key, or pass `allow_imperfect_key=True` to run anyway: `identity_diagnostics` records the problem and `primary_key_unique` reports it. See [Declaring a contract](chapters/12-data-contracts/index.md#declaring-a-contract) and [Results, row identity and failure cases](chapters/13-validation/index.md#results-row-identity-and-failure-cases).

### Why does every row fail my GeoJSON field checks?

A field declared with `type=UniversalType.GEOJSON` currently conforms to JSON text, and its compiled checks then fail on every non-null row. Validate GeoJSON with a `ValueRule` over a column that already holds GeoJSON objects, and keep the `geojson` type off that column in the contract. See [Check IR and rule kinds](chapters/13-validation/index.md#check-ir-and-rule-kinds).

### Is `mountainash.validation` a stable API?

It is semi-public and evolving. Its exports serve data contracts, DAG validation and direct use, and the module has yet to mark which names are stable. Other features build on the result model and the check types. See [Validation](chapters/13-validation/index.md).

## Multi-table work and pipelines

### Should I use a `RelationDAG`, a `ValidationPlan` or a pipeline?

Use a `RelationDAG` for several named relations that refer to each other, a DataPackage round trip, or validating tables together with the foreign keys between them. Use a `ValidationPlan` to validate independent tables one after another with a shared context. Use a pipeline for units that run in dependency order with checkpoints, incremental sources and sinks; a `DagUnit` runs a DAG inside one. See [RelationDAG](chapters/14-relationdag/index.md), [Validator and validation plans](chapters/12-data-contracts/index.md#validator-and-validation-plans) and [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units).

### Why does a foreign key not change what a DAG collect runs?

Foreign keys become constraint edges, which describe the data. Dependency edges, which come from `dag.ref(...)` references, alone decide what a collect runs and in what order. Collecting `orders` reads `orders` alone, even when it has a foreign key to `customers`. See [The graph kernel](chapters/14-relationdag/index.md#the-graph-kernel).

### How do I check foreign keys across tables?

Call `dag.validate(specs)` with a `TableSchema` or data contract per relation. It checks each table, generates foreign-key checks from the DAG's constraints and the specs, and reports orphan child rows in `fk_result`. Validating a foreign key to another resource on a single relation raises `RelationDAGRequired`. See [Validating a DAG](chapters/14-relationdag/index.md#validating-a-dag) and [Foreign keys](chapters/13-validation/index.md#foreign-keys).

### Why does reading a CSV resource raise `MissingFilesDependency`?

The backend scans local CSV and Parquet files natively when it can represent their dialect. `mountainash-files` parses remote paths, compressed files, other formats and less common dialect options, and the `files` extra installs it (as do `ibis` and the storage extras). See [Resources and DataPackage](chapters/14-relationdag/index.md#resources-and-datapackage) and [Where mountainash sits](chapters/02-installation-and-package-surface/index.md#where-mountainash-sits).

### Why is a remote schema reference refused with `LocationNotAllowed`?

Descriptor references resolve under the package root, and remote references need explicit permission. Pass a `mountainash-transport` location policy that allows the scheme (`policy=`), or your own `DescriptorResolver` (`resolver=`). `mountainash-transport` raises `LocationNotAllowed`, and the class sits outside the `MountainashError` hierarchy. See [DataPackage, resources and dialects](chapters/10-table-schemas-and-datapackage/index.md#datapackage-resources-and-dialects).

### Why was my pipeline unit reused when I changed its code?

The runner reuses a unit when its identity matches a completed, retained result. The default identity covers the class name, version, parameters and upstream identities; the unit's code and constructor arguments sit outside it. Bump `version`, or override `identity()` to include configuration; `force=True` reruns everything. A `DagUnit` includes a digest of its template, so editing the template is enough. See [Pipelines and units](chapters/15-pipelines/index.md#pipelines-and-units) and [Values, identity and checkpoints](chapters/15-pipelines/index.md#values-identity-and-checkpoints).

### Where is the exception from a failed pipeline unit?

The runner records the unit as `failed`, skips everything downstream of it, and logs the exception with its traceback to the `mountainash.pipelines.runtime.runner` logger. The exception stays out of the `RunResult`. Errors raised while planning, such as `IncompatibleResume`, propagate from `run()`. See [Running a pipeline](chapters/15-pipelines/index.md#running-a-pipeline) and [Pipeline errors](chapters/15-pipelines/index.md#pipeline-errors).

### Is the pipelines API stable?

It is evolving. `Runner.run()` is the main entry point; `Runner.plan()` and `Runner.execute()` are public and lightly specified, and names may change between releases. Everything lives in `mountainash.pipelines`. See [Pipelines](chapters/15-pipelines/index.md).

## Troubleshooting errors

### How do I catch any mountainash error?

Catch `ma.MountainashError`. Every error the package raises deliberately derives from it, including errors that `mountainash.exceptions` has yet to re-export. Many also inherit a built-in exception (`UnknownDtypeError` is a `ValueError`), so existing `except ValueError` code keeps working. Three cases sit outside the hierarchy: backend detection raises a plain `ValueError`, engine errors during execution keep the engine's type, and `LocationNotAllowed` comes from `mountainash-transport`. See [Errors](chapters/02-installation-and-package-surface/index.md#errors).

### Why can't I import an error from `mountainash.exceptions`?

The facade re-exports a subset of the typed errors so far. Import these from their owning modules:

| Errors | Module |
|---|---|
| `UnresolvedExecutionLocationError`, `ConflictingExecutionTargetError`, `MaterializationScopeClosedError`, `CompileRequiresExecutionError`, `UnsupportedRelationTransportError`, `UnregisteredRelationNodeError` | `mountainash.relations.core.errors` |
| `UnknownRelationRef`, `MissingFilesDependency`, `ResourceSchemaCastError` | `mountainash.relations.dag.errors` |
| `PipelineError` and the other pipeline errors | `mountainash.pipelines` or `mountainash.pipelines.errors` |
| `DecimalConversionRequiredError` | `mountainash.conform.errors` |
| `CycleError`, `DuplicateNodeError`, `UnknownNodeError` (not `MountainashError` subclasses) | `mountainash.graph` |

All except the graph errors are `MountainashError` subclasses:

```python
import ibis
import mountainash as ma
from mountainash.relations.core.errors import UnresolvedExecutionLocationError

try:
    ma.relation(ibis.memtable({"id": [1, 2]})).to_dicts()
except UnresolvedExecutionLocationError as exc:
    print(isinstance(exc, ma.MountainashError), exc)
```

```text
True Selected execution location at root has unresolved Ibis binding: ibis (unresolved binding)
```

See [Errors](chapters/02-installation-and-package-surface/index.md#errors) and [Typed error conventions](chapters/23-contributing-and-testing/index.md#typed-error-conventions).

### What does "Cannot identify backend for type" mean?

The object passed to `expr.compile()` belongs to no supported dataframe or table family; a plain dict is the usual case. Pass a dataframe, or use `ma.relation(data)`, which converts Python data to Polars first. Detection also rejects a Narwhals frame that wraps an Ibis table; pass the Ibis table itself. See [Backend detection](chapters/02-installation-and-package-surface/index.md#backend-detection) and [Relations from Python data](chapters/07-relations/index.md#relations-from-python-data).

### Why does `compile()` raise `CompileRequiresExecutionError`?

The plan needs data moved between engines before it compiles, so a native plan exists only after something executes. Use a materialising terminal such as `collect()` or `to_polars()`. See [Collect and terminals](chapters/08-collecting-results/index.md#collect-and-terminals).

### Why does a snapshot raise `MaterializationScopeClosedError`?

`ma.materialization_scope()` releases its snapshots when the scope exits. Use `scope.detach(rel)` for any snapshot that must outlive the scope. See [Materialization scopes and checkpoints](chapters/09-execution-targets-and-capabilities/index.md#materialization-scopes-and-checkpoints).

### Why does `UnknownRelationRef` appear only when I collect?

A `dag.ref(name)` has to exist only when something is collected, so you can add relations in any order. Compiling a reference to a name that was never added raises the error. See [Building a DAG](chapters/14-relationdag/index.md#building-a-dag).

## Extending and contributing

### How do I add a new expression operation?

Six steps, one layer each: a function key, the protocol methods, the API builder method, an implementation in every backend, the function-mapping entry, and cross-backend, argument-channel and AST tests. A missing step surfaces as a failing alignment test or a dispatch error. See [Adding an expression operation](chapters/22-extending-mountainash/index.md#adding-an-expression-operation) and [Three-layer separation](chapters/17-architecture/index.md#three-layer-separation).

### Can I add a relational operation without changing mountainash?

Yes. Subclass `RelationNode`, register a visit handler for it with `RelationVisitRegistry.register(...)`, and wrap the node in a `Relation`. Built-in node types are protected. Such a plan has no schema contract, so use `collect_schema(allow_execution=True)` for its schema. See [Custom relation nodes](chapters/22-extending-mountainash/index.md#custom-relation-nodes). A built-in operation is a package change, described in [Adding a relation operation](chapters/22-extending-mountainash/index.md#adding-a-relation-operation).

### How do I record that a backend cannot do something?

Declare it as data in a capability segment module under the backend's `capabilities/` directory, and keep it out of backend-detection code in builders. Information can be family-wide; executable gates belong to a concrete dialect. Bootstrap discovers the module, so it needs no registration call. See [Declaring capability segments](chapters/22-extending-mountainash/index.md#declaring-capability-segments) and [Declaring a new segment](chapters/20-capability-spine/index.md#declaring-a-new-segment).

### How should I mark a test that fails on one backend?

Keep the backend in the parametrisation and declare the failure strictly, for that backend only, with a reason: a refusal assertion for a gated call, `expect_call_failure` for a wrong result or native error, or a strict per-backend `xfail` parameter. Never skip, drop the backend, or use a blanket or non-strict expected failure. See [Known divergences and per-backend xfail](chapters/23-contributing-and-testing/index.md#known-divergences-and-per-backend-xfail).

### How do I run the tests?

Run tests by target during development with `hatch run test:test-target-quick <path>` (or `test-target` for coverage), naming the files a change touches. The full suite runs every test against eight backends and belongs to CI and a single pre-merge gate. See [Cross-backend testing](chapters/23-contributing-and-testing/index.md#cross-backend-testing).

### Why does a new protocol method fail `test_protocol_alignment.py`?

The alignment tests discover protocols, methods and keys by introspection and fail on any method missing from a layer: a key, a registry mapping or an implementation in each backend. Finish the wiring, or list the method in `KNOWN_ASPIRATIONAL` with a reason and a date. See [Protocols as contracts](chapters/17-architecture/index.md#protocols-as-contracts).

### Can I register my own value validator?

No. `ValueValidatorKey` is a closed vocabulary, and adding a key is a package change. For a reusable check of your own, write a function that returns a `RowRule`, `ScalarRule` or `RelationRule`; a `RelationRule` covers anything the relation API can express and runs on every backend. See [Ingress handlers, units and rules](chapters/22-extending-mountainash/index.md#ingress-handlers-units-and-rules).

### Which extension points work at run time without a source checkout?

Relation nodes with visit handlers, optimisation passes, schema codecs, custom semantic types, pipeline units, sources, sinks and checkpoint stores, data-contract rules and validation checks. New operations, backends, capability declarations, type targets, ingress handlers and value validators are package changes. See [Extending mountainash](chapters/22-extending-mountainash/index.md).
