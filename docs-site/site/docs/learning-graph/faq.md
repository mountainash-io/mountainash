# Mountainash Frequently Asked Questions

Total questions: 72

## Getting Started

### What is mountainash and what problem does it solve?

Mountainash is a cross-backend data expression and relational pipeline library for Python. It solves the problem of backend lock-in: when you write data transformations directly against Polars, pandas, or SQL, your logic is tied to that specific engine. Mountainash provides a unified Python API that compiles to native operations across Polars, pandas (via Narwhals), and SQL databases (via Ibis), so you can write your transformation logic once and run it on any supported backend.

Unlike thin compatibility layers, mountainash provides a full Substrait-aligned abstract syntax tree (AST), three-valued ternary logic, schema-first data quality via TypeSpec, and declarative pipeline orchestration — enabling "abstract data products" that behave consistently across backends.

### What backends does mountainash support?

Mountainash supports three backends:

1. **Polars** — compiled via `PolarsExpressionSystem` and `PolarsRelationSystem`, targeting Polars LazyFrames for deferred execution.
2. **Narwhals** — compiled via `NarwhalsExpressionSystem` and `NarwhalsRelationSystem`, providing portability across pandas and other Narwhals-compatible DataFrame libraries.
3. **Ibis** — compiled via `IbisExpressionSystem` and `IbisRelationSystem`, targeting SQL databases through Ibis's SQL compilation.

Each backend implements the same protocol contracts, ensuring that expressions and relations produce equivalent results regardless of which engine executes them.

### What are the prerequisites for using mountainash?

You should have:

- **Intermediate Python** — comfort with classes, decorators, type hints, and protocol classes.
- **DataFrame experience** — familiarity with at least one DataFrame library such as Polars or pandas.
- **Basic SQL knowledge** — understanding of SELECT, JOIN, GROUP BY, and WHERE clauses.
- **DAG concepts** — a basic understanding of directed acyclic graphs and topological ordering, which underpin the RelationDAG orchestrator and pipeline framework.

You do not need deep knowledge of Polars internals, Ibis internals, or database administration.

### How do I create my first expression in mountainash?

Use the `col()` and `lit()` factory functions to build expressions via method chaining:

```python
from mountainash import col, lit

# Reference a column and apply operations
expr = col("price") * lit(1.1)  # 10% markup

# Boolean expression with comparison
filter_expr = col("age") >= lit(18)

# String namespace operation
name_expr = col("name").str.to_uppercase()
```

Expressions are not executed immediately — they build an AST (abstract syntax tree) that is later compiled to native backend operations when you call a terminal method like `.collect()` or `.to_polars()`.

### How do I create my first relation in mountainash?

Use the `relation()` factory to wrap a DataFrame and chain relational operations:

```python
from mountainash import relation, col, lit

# Wrap a Polars DataFrame
rel = relation(df)

# Build a query pipeline
result = (
    rel
    .filter(col("status") == lit("active"))
    .select(col("name"), col("email"), col("created_at"))
    .sort(col("created_at").desc())
    .head(10)
    .collect()
)
```

The `relation()` factory auto-detects the backend from the input data. The chain of operations builds a relational AST, and `.collect()` compiles and executes it on the detected backend.

### What is the difference between expressions and relations?

**Expressions** represent column-level computations — arithmetic, comparisons, string transforms, aggregations, and window functions. They are built with `col()`, `lit()`, and `when()`, and produce an expression AST (e.g., `ScalarFunctionNode`, `FieldReferenceNode`).

**Relations** represent table-level operations — filter, sort, join, group_by, select, and set operations. They are built with the `relation()` factory and the `Relation` class, producing a relational AST (e.g., `FilterRelNode`, `JoinRelNode`).

Expressions are used *within* relations. For example, `rel.filter(col("x") > lit(5))` uses an expression (`col("x") > lit(5)`) inside a relational operation (`.filter()`). Expressions define *what to compute*; relations define *how to combine, filter, and shape data*.

### How does backend detection work?

The Backend Detection system (concept 16) automatically identifies which backend to use based on the input data type. When you call `relation(df)`, mountainash inspects `df` using DataFrame Type Guards — functions that check whether the input is a Polars DataFrame/LazyFrame, a pandas DataFrame, an Ibis table, or another supported type.

The detection maps to the `Backend` enum (POLARS, NARWHALS, IBIS), which selects the appropriate expression and relation system implementations. This means you never need to manually specify the backend — it is inferred from your data.

### What is the build-then-compile pattern?

The build-then-compile pattern is the core architectural principle of mountainash. When you chain operations like `col("x") + lit(1)` or `rel.filter(...)`, you are *building* an abstract syntax tree (AST), not executing anything. The AST is a pure data structure (Pydantic models) that represents your intent.

When you call a terminal operation — `.collect()` for relations, or when an expression is used inside a relation that gets collected — the AST is *compiled* to native backend operations by the Unified Expression Visitor or UnifiedRelationVisitor. This two-phase design enables backend portability: the same AST compiles to different native code depending on the target backend.

### Can I use mountainash with existing Polars or pandas code?

Yes. Mountainash is designed to interoperate with existing code. You can:

- Wrap an existing Polars DataFrame or LazyFrame with `relation(df)` and chain mountainash operations.
- Convert results back to native DataFrames with `.to_polars()` or `.to_pandas()`.
- Use the `native()` function to embed a backend-native expression directly when mountainash does not yet support a particular operation.

This means you can adopt mountainash incrementally — wrapping specific transformations in mountainash while keeping the rest of your pipeline in native code.

### What is the three-layer architecture?

Mountainash follows a three-layer architecture: **Protocol, API Builder, Backend**.

1. **Protocol layer** — defines contracts (Python Protocol classes) that specify what operations must be supported. `Expression System Protocols` and `Relation Protocols` declare the interface without implementation.
2. **API Builder layer** — provides the fluent user-facing API (`col()`, `lit()`, `relation()`, `.filter()`, `.join()`) that builds AST nodes. This layer is backend-agnostic.
3. **Backend layer** — implements the protocols for each specific engine (Polars, Narwhals, Ibis), compiling AST nodes to native operations.

This separation ensures that adding a new backend requires implementing protocols without changing the API or AST layers.

### How do I install mountainash?

Mountainash is a Python package installable via pip or uv:

```bash
uv pip install mountainash
```

The core package has minimal dependencies. Backend-specific dependencies (Polars, pandas, Ibis) are optional — mountainash uses a Lazy Import System that defers importing backend libraries until they are actually needed. This means you only need to install the backends you intend to use.

### What version of Python does mountainash require?

Mountainash requires Python 3.10 or later. It makes extensive use of modern Python features including type hints with generics, Protocol classes for structural subtyping, dataclasses, and Pydantic v2 models for AST node definitions. The type hint usage is not just for documentation — it is integral to the expression type generics system and the protocol-based backend contracts.

## Core Concepts

### What are function keys and how does the function registry work?

Function keys are enum values that uniquely identify every operation in mountainash. They follow two naming conventions:

- **FKEY_SUBSTRAIT_*** — operations aligned with the Substrait specification (e.g., `FKEY_SUBSTRAIT_ADD`, `FKEY_SUBSTRAIT_EQUAL`).
- **FKEY_MOUNTAINASH_*** — mountainash extension operations not in Substrait (e.g., custom string or datetime functions).

The `ExpressionFunctionRegistry` maps each function key to an `ExpressionFunctionDef` that declares the operation's arity, argument types, and compilation metadata. When the Unified Expression Visitor encounters a `ScalarFunctionNode`, it performs a Function Registry Lookup to find the function key, then dispatches to the correct backend compile function. This registry-driven design means adding a new operation requires registering it once rather than modifying visitor code.

### What are the seven expression AST node types?

The expression AST consists of seven node types, all subclassing `ExpressionNode Base`:

1. **ScalarFunctionNode** — represents function calls (arithmetic, comparison, string ops) with a function key and arguments.
2. **FieldReferenceNode** — references a column by name (produced by `col()`).
3. **LiteralNode** — represents a literal value (produced by `lit()`).
4. **CastNode** — represents a type cast operation.
5. **IfThenNode** — represents conditional logic (produced by `when()`).
6. **SingularOrListNode** — wraps a single value or list of values for operations like `is_in()`.
7. **WindowFunctionNode** — represents windowed aggregations with a `WindowSpec` and `WindowBound`.

All nodes are Pydantic models, making them serializable and inspectable.

### What are the ten relational node types?

The relational AST includes ten core node types plus four extension types:

**Core (Substrait-aligned):**
1. **ReadRelNode** — reads from a data source (DataFrame).
2. **ProjectRelNode** — selects/projects columns.
3. **FilterRelNode** — filters rows by a boolean expression.
4. **AggregateRelNode** — groups and aggregates.
5. **JoinRelNode** — joins two relations.
6. **FetchRelNode** — limits rows (head/offset).
7. **SortRelNode** — sorts by one or more expressions.
8. **SetRelNode** — union, intersect, or difference operations.

**Extension types:**
9. **ExtensionRelNode** — for custom relational operations.
10. **SourceRelNode** — pipeline source references.
11. **RefRelNode** — DAG relation references.
12. **ResourceReadRelNode** — DataPackage resource reads.

### How does the Unified Expression Visitor compile AST nodes?

The Unified Expression Visitor implements the Visitor Pattern: it traverses the expression AST recursively, dispatching each node type to a type-specific handler. For `ScalarFunctionNode`, it uses Function Registry Lookup to find the function key's `ExpressionFunctionDef`, then calls the backend-specific compile function (e.g., `polars_compile_add` for Polars).

The visitor is "unified" because a single visitor class handles all node types and delegates to the correct backend via protocol-based composition. Each backend (Polars, Narwhals, Ibis) provides compile files organized by category — Substrait Compile Files for standard operations and Extension Compile Files for mountainash extensions. The visitor resolves the right compile function at runtime through the function registry, making the system extensible without modifying the visitor itself.

### What is the difference between arguments and options in expression functions?

In mountainash's `ExpressionFunctionDef`, parameters are classified as either **arguments** or **options**:

- **Arguments** are positional expression inputs — they are other expressions that participate in the computation. For example, in `add(a, b)`, both `a` and `b` are arguments (expression AST nodes).
- **Options** are non-expression configuration values — strings, integers, or enums that modify behavior. For example, a rounding function might take a precision option as an integer.

This distinction matters because arguments are compiled recursively by the visitor (they are AST subtrees), while options are passed through as literal values to the backend compile function. Getting this classification wrong leads to compilation errors.

### How do namespaces work in the expression API?

Namespaces group related operations under a dotted accessor on the expression API. Mountainash provides five namespaces:

- **`.str`** (String Namespace) — string operations like `.str.to_uppercase()`, `.str.contains()`.
- **`.dt`** (Datetime Namespace) — datetime operations like `.dt.year()`, `.dt.truncate()`.
- **`.struct`** (Struct Namespace) — struct field access.
- **`.list`** (List Namespace) — list/array operations.
- **`.name`** (Name Namespace) — column renaming operations like `.name.prefix()`.

Namespaces are implemented via `NamespaceDescriptor`, a Python descriptor that returns a namespace-specific API object when accessed. This keeps the main expression API uncluttered while providing discoverability through dot-completion.

### What is TypeSpec and how does it relate to Frictionless Table Schema?

`TypeSpec` is mountainash's universal type metadata container. It describes a table's schema as a list of `FieldSpec` objects, each specifying a column's name, `UniversalType` (an enum of logical types like STRING, INTEGER, DATE), and optional `FieldConstraints` (nullable, unique, enum values, min/max).

TypeSpec is aligned with the Frictionless Table Schema standard, meaning you can convert between TypeSpec and Frictionless schemas without loss. This alignment enables interoperability with the broader Frictionless data ecosystem, including DataPackage descriptors used by the RelationDAG.

TypeSpec is backend-agnostic — the Type Bridge and Backend Type Mapping convert between UniversalType values and backend-specific types (Polars dtypes, pandas dtypes, Arrow schemas) when needed.

### What does the conform() operation do?

`Relation.conform()` applies a TypeSpec schema to a relation, transforming it to match the specified column names, types, and constraints. It handles:

- **Column selection** — only columns listed in the TypeSpec are retained.
- **Column ordering** — columns are reordered to match the TypeSpec.
- **Type casting** — columns are cast to the UniversalType specified in each FieldSpec.
- **Constraint enforcement** — nullable, unique, and other constraints can be validated.

This is central to mountainash's "schema-first data quality" approach: you define the expected shape of your data as a TypeSpec, then use `.conform()` to ensure any input data matches that shape before further processing. It works identically across all three backends.

### What is the difference between dependency edges and constraint edges in RelationDAG?

RelationDAG uses a Two-Edge Graph Model to track two distinct types of relationships:

- **Dependency edges** represent data flow — relation B depends on relation A because B reads from A's output. These edges determine execution order via topological sorting.
- **Constraint edges** represent integrity constraints — typically foreign key relationships where relation B's FK column must reference valid values in relation A. These edges enable FK Integrity Checks but do not require A to be computed before B (the data may already exist).

This separation allows the DAG to model both "must compute A before B" (dependency) and "A and B have a referential relationship" (constraint) without conflating the two.

### How does topological collection work in RelationDAG?

When you call `dag.collect()`, the RelationDAG performs topological sorting on the dependency edges to determine the correct execution order. Relations with no dependencies are collected first, then relations whose dependencies have been satisfied, and so on.

The `ref_resolver` parameter controls how `RefRelNode` references are resolved — it maps relation names to their computed results during collection, enabling one relation to reference another's output. This ensures that when relation B depends on relation A, A's result is available when B is compiled and executed.

The Topological Collection process respects only dependency edges, not constraint edges, so referential integrity checks are separate from execution ordering.

### What is the PipelineBuilder and how do pipelines work?

`PipelineBuilder` provides a declarative API for constructing multi-step data pipelines. You define steps using the `@step` decorator and sources using the `@source` function:

```python
from mountainash.pipeline import PipelineBuilder, step, source

pipeline = PipelineBuilder()

@pipeline.source("raw_data")
def load_data():
    return relation(df)

@pipeline.step("cleaned", depends_on=["raw_data"])
def clean(ctx):
    return ctx.inputs["raw_data"].filter(col("valid") == lit(True))
```

The builder constructs a `PipelineSpec` — a serializable description of steps, dependencies, and parameters. The `SimplePipelineRunner` executes the spec by topologically sorting steps and running them in order, passing `StepContext` and producing `StepResult` objects.

### How does parameter binding work in pipelines?

Pipeline parameter binding uses `ParamSpec` — a Pydantic model that declares typed parameters for a pipeline step. When a step calls `relation.params(param_spec)`, it creates a `ParamsRelNode` in the AST that references the parameters.

At execution time, the `fold_params` function substitutes concrete values into the AST, replacing `ParamsRelNode` references with actual values. This enables reusable pipeline steps that can be parameterized differently across runs — for example, a date-range filter where the start and end dates are parameters bound at runtime.

### What is the DataPackage integration?

Mountainash integrates with the Frictionless DataPackage standard for describing multi-resource datasets. A DataPackage descriptor (JSON/YAML) declares resources (tables), their schemas, file paths, dialects, and relationships (foreign keys).

The `from_descriptor()` method parses a DataPackage descriptor into `DataPackage` and `DataResource` objects. The `to_relation_dag()` method converts these into a `RelationDAG`, automatically creating `ResourceReadRelNode` entries for each resource and wiring up dependency and constraint edges based on foreign key references.

This means you can describe a multi-table dataset in a standard DataPackage format and mountainash will build the execution graph automatically.

### What is ternary logic and why does mountainash use it?

Mountainash implements three-valued (ternary) logic with values TRUE, FALSE, and UNKNOWN, rather than the two-valued TRUE/FALSE of standard Python booleans. This aligns with SQL's three-valued logic where NULL propagates through boolean operations.

However, mountainash's ternary logic differs from SQL NULL propagation in specific ways — it uses sentinel integers for the three states and supports auto-booleanization (converting UNKNOWN to FALSE when a definite boolean is required, such as in filter operations). This design makes NULL handling explicit and predictable across backends, avoiding subtle differences in how Polars, pandas, and SQL treat NULL in boolean contexts.

### What is the Substrait specification and how does mountainash align with it?

Substrait is an open standard for describing data compute operations in a language-agnostic way. Mountainash aligns its expression and relation node types with Substrait's type system:

- Expression function keys prefixed with `FKEY_SUBSTRAIT_*` correspond to Substrait-defined functions.
- Relational node types (ReadRel, ProjectRel, FilterRel, AggregateRel, JoinRel, FetchRel, SortRel, SetRel) follow Substrait's relational algebra naming.

This alignment provides a well-defined vocabulary for operations and makes mountainash's AST conceptually interoperable with other Substrait-aligned systems. Operations that go beyond Substrait's scope use the `FKEY_MOUNTAINASH_*` prefix and `ExtensionRelNode` type.

### How does schema extraction work?

Schema Extraction infers a TypeSpec from existing data structures. Mountainash supports three extraction sources:

1. **DataFrame Extraction** — inspects a Polars, pandas, or Arrow DataFrame's schema to produce a TypeSpec with column names and mapped UniversalType values.
2. **Dataclass Extraction** — inspects Python dataclass field annotations to produce a TypeSpec.
3. **Pydantic Extraction** — inspects Pydantic model field definitions (including validators and constraints) to produce a TypeSpec with FieldConstraints.

All three produce the same TypeSpec format, so you can extract a schema from any supported source and use it with `.conform()`, `validate_match()`, or schema comparison regardless of origin.

### What is visitor composition?

Visitor Composition is the technique used to combine the expression visitor and relation visitor into a single coherent compilation system. Since relational operations contain expressions (e.g., a filter's predicate), the `UnifiedRelationVisitor` must delegate to the `Unified Expression Visitor` when it encounters expression AST nodes inside relation nodes.

This composition is achieved through Backend Composition using multiple inheritance: each backend system class (e.g., `PolarsRelationSystem`) inherits from both the relation visitor and expression visitor base classes, giving it the ability to compile both relation and expression nodes. The `RelationVisitRegistry` manages this composition, ensuring the correct visitor methods are dispatched.

### What are extension operations?

Extension operations are mountainash-specific operations that go beyond the Substrait specification. They exist in both the expression and relation layers:

- **Expression extensions** use function keys with the `FKEY_MOUNTAINASH_*` prefix and are compiled via Extension Compile Files separate from the Substrait compile files.
- **Relation extensions** use `ExtensionRelNode` and are registered via `RelationVisitRegistry` with `ExtensionRelOperation` definitions.

This separation keeps the Substrait-aligned core clean while allowing mountainash to provide additional operations (like custom string functions or domain-specific relational transforms) without violating the standard alignment.

### What are the when() function and conditional expressions?

The `when()` function creates conditional (if-then-else) expressions, similar to SQL's CASE WHEN. It builds an `IfThenNode` in the expression AST:

```python
from mountainash import col, lit, when

category = when(col("age") < lit(18)).then(lit("minor"))
    .when(col("age") < lit(65)).then(lit("adult"))
    .otherwise(lit("senior"))
```

Multiple `.when().then()` clauses can be chained, with a final `.otherwise()` for the default case. Each condition must be a boolean expression (typically using `BooleanExpressionAPI`). The conditions are evaluated in order, and the first matching condition's value is returned. If no condition matches and no `.otherwise()` is provided, the result is NULL.

### How do GroupedRelation and aggregation work together?

When you call `.group_by()` on a `Relation`, it returns a `GroupedRelation` — a special intermediate object that only allows aggregation operations. You must call `.agg()` on the grouped relation to produce results:

```python
result = (
    relation(df)
    .group_by(col("department"))
    .agg(
        col("salary").mean().alias("avg_salary"),
        col("employee_id").count().alias("headcount")
    )
    .collect()
)
```

This two-step pattern (group then aggregate) mirrors SQL's GROUP BY semantics and builds an `AggregateRelNode` in the relational AST. Aggregation Functions like `.sum()`, `.mean()`, `.count()`, `.min()`, `.max()` are available on the expression API and are compiled to backend-native aggregations.

## Technical Details

### How do I add a new expression operation to mountainash?

Adding a new operation follows a six-step wiring process:

1. **Define the function key** — add a new enum value to the function key enums (FKEY_SUBSTRAIT_* or FKEY_MOUNTAINASH_*).
2. **Register the function definition** — create an `ExpressionFunctionDef` specifying arity, argument vs option classification, and register it in the `ExpressionFunctionRegistry`.
3. **Add the API method** — add a method to `BaseExpressionAPI` (or the appropriate namespace) that builds the correct `ScalarFunctionNode` with the function key.
4. **Write Polars compile function** — implement the Polars-specific compilation in the appropriate Substrait or Extension compile file.
5. **Write Narwhals compile function** — implement the Narwhals-specific compilation.
6. **Write Ibis compile function** — implement the Ibis-specific compilation.

Each compile function takes the visitor, the node, and any arguments/options, and returns the native expression for that backend.

### How does cross-backend testing work?

Mountainash uses `Cross-Backend Parametrize` to run the same test against all three backends. Tests are parameterized with the backend enum, and each test creates data in the target backend format, runs the mountainash operation, and asserts the result.

When a backend has a known limitation, the test is marked with `xfail Known Quirks` — a pytest xfail marker with a reason string documenting the specific divergence. This ensures the test suite documents known differences without failing the CI build, while still catching new regressions.

```python
@pytest.mark.parametrize("backend", [Backend.POLARS, Backend.NARWHALS, Backend.IBIS])
def test_string_upper(backend):
    # Test runs against each backend
    ...
```

### What are the known backend divergences?

Backend Divergences are documented differences in behavior across the three backends. Common categories include:

- **NULL handling** — Polars, pandas, and SQL handle NULLs differently in aggregations, comparisons, and sorting.
- **Type coercion** — implicit type promotion rules differ (e.g., integer + float behavior).
- **String operations** — regex dialect differences, collation-sensitive operations.
- **Window functions** — default frame specifications may differ between backends.

These divergences are tracked as `Known Expr Limitations` and surfaced via xfail markers in the test suite. The mountainash documentation catalogs each known divergence so users can make informed decisions about cross-backend portability.

### How does the Lazy Import System work?

The Lazy Import System defers importing backend-specific libraries until they are first used. When mountainash is imported, it does not immediately import Polars, pandas/Narwhals, or Ibis. Instead, it uses lazy import proxies that trigger the actual import only when a backend-specific code path is reached.

This provides two benefits: faster startup time (you don't pay the import cost of backends you never use) and graceful degradation (you can use mountainash with only Polars installed, without getting ImportError for Ibis or pandas).

### How does the UnifiedRelationVisitor differ from the expression visitor?

While both visitors follow the Visitor Pattern, they differ in scope and composition:

- **Unified Expression Visitor** — traverses expression AST nodes, dispatching via the Function Registry to produce a single native expression (e.g., a Polars `Expr`, an Ibis column expression).
- **UnifiedRelationVisitor** — traverses relation AST nodes, producing native table operations (e.g., a Polars LazyFrame pipeline, an Ibis SQL query). It also composes with the expression visitor to handle embedded expressions.

The relation visitor uses `RelationVisitRegistry` for dispatch (including `OptimisationRegistry` for optimization passes), while the expression visitor uses `ExpressionFunctionRegistry`. The relation visitor manages state across a multi-node query plan; the expression visitor is typically stateless within a single expression tree.

### What is the OptimisationRegistry?

The `OptimisationRegistry` extends the `RelationVisitRegistry` to support optimization passes on the relational AST. Before compilation, the registry can apply transformations to the AST — such as predicate pushdown, projection pruning, or join reordering — without changing the logical semantics.

This is separate from the backend's native optimizer (e.g., Polars' lazy optimizer or SQL query planners). The OptimisationRegistry operates at the mountainash AST level, enabling optimizations that work across all backends. Backend-specific optimizations still happen downstream when the compiled plan is executed.

### How does cross-type join handling work?

Cross-Type Joins occur when joining two relations from different backends or with different key types. Mountainash handles this through:

1. **Backend Detection** — determining the backend of each relation.
2. **Type coercion** — automatically casting join key columns to compatible types when the left and right keys differ.
3. **Join Key Coalescing** — after a join, merging the left and right key columns into a single column when they are semantically equivalent.

This is particularly relevant when relations come from different DataPackage resources that may have been loaded via different backends, ensuring that foreign-key-based joins work correctly regardless of type differences.

### What is the execute_on parameter?

The `execute_on` parameter on the `relation()` factory allows you to override automatic backend detection and force execution on a specific backend. Combined with `Execution Target`, this is useful when:

- You have data in one format but want to compile and execute on a different backend (e.g., convert a pandas DataFrame to Polars for performance).
- You are testing cross-backend behavior explicitly.
- Your pipeline mixes backends and you need to control which engine handles specific stages.

```python
# Force Polars execution even if df is a pandas DataFrame
rel = relation(df, execute_on=Backend.POLARS)
```

### How does the Factory Pattern work in mountainash?

The Factory Pattern, implemented through `BaseFactoryMixin`, provides a consistent way to create backend-specific instances from a common interface. When you call `relation(df)`, the factory:

1. Detects the backend from the input data via Backend Detection.
2. Looks up the registered backend system class (e.g., `PolarsRelationSystem`).
3. Instantiates the backend system and wraps the data.

This keeps the user API backend-agnostic — you always call `relation()`, never `PolarsRelation()` directly. The factory pattern also supports the `execute_on` parameter for manual backend override.

### What is the ref_resolver parameter in RelationDAG?

The `ref_resolver` parameter controls how `RefRelNode` references are resolved during DAG collection. When relation B references relation A via `dag.ref("A")`, a `RefRelNode` is inserted into B's AST. During `dag.collect()`, the ref_resolver maps relation names to their computed results.

The default resolver uses the DAG's own computed results — when A finishes collecting, its result is stored and used when B's `RefRelNode` is encountered. Custom ref_resolvers can override this behavior, for example to resolve references from an external cache or database rather than computing them on the fly.

### What are Foreign Key integrity checks?

FK Integrity Check validates that foreign key relationships declared in TypeSpec or DataPackage descriptors are satisfied by the actual data. A `ForeignKeyReference` specifies that column(s) in one table must reference valid values in column(s) of another table.

During or after `dag.collect()`, mountainash can verify these constraints by checking that every value in the FK column exists in the referenced table's primary key column. Violations are reported as data quality errors. This integrates with the Constraint Edges in the two-edge graph model — constraint edges declare the FK relationship, and the integrity check validates it.

### How does schema validation work?

Schema Validation compares actual data against a TypeSpec to verify conformance. The `validate_match` function checks:

- **Column presence** — all required columns exist in the data.
- **Column types** — each column's actual type matches the expected UniversalType.
- **Constraints** — nullable, unique, enum, min/max constraints on FieldSpec are satisfied.

Schema Comparison goes further, comparing two TypeSpec objects to identify differences — added columns, removed columns, type changes, constraint changes. This is useful for detecting schema drift between pipeline runs or data versions.

### How does Backend Type Mapping convert between UniversalType and native types?

The Type Bridge provides bidirectional conversion between mountainash's `UniversalType` enum and each backend's native type system. Three specialized converters handle the mapping:

- **Polars Schema Convert** — maps UniversalType to Polars dtypes (e.g., UniversalType.STRING to pl.Utf8, UniversalType.INTEGER to pl.Int64).
- **Pandas Dtypes Convert** — maps UniversalType to pandas/numpy dtypes.
- **Arrow Schema Convert** — maps UniversalType to Apache Arrow types.

The mapping is not always 1:1 — some backends have richer type systems than others. The Type Bridge handles these asymmetries by choosing sensible defaults (e.g., mapping UniversalType.INTEGER to the backend's default integer width). Custom Type Registry entries can override these defaults for specific use cases.

### How do window functions work in mountainash?

Window functions perform calculations across a set of rows related to the current row. In mountainash, they are built using the expression API with the `WindowFunctionNode`:

```python
from mountainash import col

# Running sum over a window
running_total = col("amount").sum().over(
    partition_by=[col("category")],
    order_by=[col("date")]
)
```

The `WindowSpec` defines the partitioning and ordering, while `WindowBound` specifies the frame boundaries (e.g., ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW). The `OverNode` wraps the aggregation with its window specification. Window functions are compiled per-backend, with known divergences in default frame specifications documented as Known Expr Limitations.

### What is the Backend Composition pattern using multiple inheritance?

Backend Composition uses Python's multiple inheritance to assemble a complete backend system from reusable components. Each backend class (e.g., `PolarsRelationSystem`) inherits from:

- The relation visitor base (providing relational node dispatch)
- The expression visitor base (providing expression compilation)
- Backend-specific mixins (providing Polars/Narwhals/Ibis native operations)

This composition means a single class can compile both relation and expression AST nodes, handle visitor delegation, and access backend-native APIs. The `Backend Composition` concept (concept 85) works with `Multiple Inheritance` (concept 86) to keep backend implementations modular — shared behavior lives in base classes while backend-specific overrides live in the leaf classes.

## Common Challenges

### Why does my expression work on Polars but fail on Ibis?

This is typically caused by Known Expr Limitations — operations that are supported on one backend but not (yet) on another. Common causes:

1. **Missing compile function** — the operation may not have an Ibis compile implementation yet.
2. **Type differences** — Ibis/SQL may require explicit casts that Polars handles implicitly.
3. **NULL semantics** — SQL's three-valued logic differs from Polars' null handling in edge cases.
4. **String function dialect** — regex syntax or string function names may differ.

Check the Known Expr Limitations documentation and use `xfail Known Quirks` in your tests to document expected divergences. The `native()` function can be used as a workaround to embed backend-specific code when needed.

### How do I handle NULL values consistently across backends?

NULL handling is one of the most common cross-backend challenges. Mountainash provides several tools:

- **`coalesce()`** — returns the first non-NULL value from a list of expressions.
- **Null Handling operations** — `.is_null()`, `.is_not_null()`, `.fill_null()` on the expression API.
- **Ternary logic** — mountainash's three-valued logic with auto-booleanization ensures that NULL in boolean contexts (like filters) produces consistent behavior across backends.

Be aware that aggregation functions may handle NULLs differently across backends (e.g., `sum()` of all NULLs may be 0 on one backend and NULL on another). Test null edge cases explicitly with cross-backend parametrize.

### Why is my relation not returning any results?

Common causes include:

1. **Filter too restrictive** — your filter expression eliminates all rows. Debug by collecting without the filter first.
2. **Type mismatch in comparison** — comparing a string column to an integer literal (or vice versa) may produce no matches. Use `cast()` or ensure types align.
3. **Missing collect** — you built the relation but forgot to call `.collect()`, `.to_polars()`, or `.to_pandas()`. Without a terminal operation, nothing executes.
4. **Empty source data** — the input DataFrame itself may be empty.

The build-then-collect pattern means errors may surface at collection time, not at build time. If `.collect()` raises an error, inspect the built AST to find the problematic node.

### How do I debug expression compilation errors?

When compilation fails, the error typically comes from the backend (Polars, Narwhals, or Ibis), not from mountainash itself. Debugging steps:

1. **Inspect the AST** — expressions and relations are Pydantic models, so you can print or serialize them to see the tree structure.
2. **Simplify the expression** — reduce to the smallest expression that reproduces the error.
3. **Check function key** — ensure the operation's function key is registered in the ExpressionFunctionRegistry and has a compile function for the target backend.
4. **Check arguments vs options** — verify that expression inputs are classified correctly.
5. **Test on a different backend** — if the expression works on Polars but fails on Ibis, the issue is likely in the Ibis compile function.

### Why does my join produce duplicate columns?

When joining two relations that share column names (beyond the join key), the result may contain duplicate column names. Mountainash's Join Key Coalescing handles the join key itself, merging the left and right key columns into one. However, non-key columns with the same name are retained from both sides.

To resolve this, use `.select()` after the join to choose the columns you want, or rename columns before joining using the Name Namespace (`.name.prefix()`, `.name.suffix()`).

### How do I handle schema drift between pipeline runs?

Schema drift — when the structure of input data changes between runs — can be managed with TypeSpec:

1. **Define expected schemas** — create TypeSpec objects for each data source.
2. **Use validate_match** — before processing, validate incoming data against the expected TypeSpec.
3. **Use conform** — apply `.conform()` to force data into the expected shape, which will raise errors on incompatible changes.
4. **Compare schemas** — use Schema Comparison to detect and report differences between expected and actual schemas.

For pipeline-based workflows, the PipelineBuilder's typed parameter binding via ParamSpec ensures that pipeline parameters are validated at bind time.

### What happens when a RelationDAG has circular dependencies?

A RelationDAG cannot have circular dependencies — it is a directed *acyclic* graph. If you attempt to create a cycle (A depends on B, B depends on A), the topological sorting step in `dag.collect()` will detect it and raise an error.

Design your data flow to be strictly one-directional. If two relations need to reference each other, restructure the pipeline so that one is computed first and the other reads from its result. The two-edge graph model helps here: constraint edges (like FK relationships) are allowed to form cycles because they don't affect execution order — only dependency edges must be acyclic.

### How do I use mountainash with multiple DataPackage resources?

Load a DataPackage descriptor and convert it to a RelationDAG:

```python
from mountainash.dag import DataPackage

pkg = DataPackage.from_descriptor("datapackage.json")
dag = pkg.to_relation_dag()

# Add transformations using dag.ref()
dag.add("enriched_orders",
    dag.ref("orders")
    .join(dag.ref("customers"), on="customer_id")
    .select(col("order_id"), col("customer_name"), col("total"))
)

results = dag.collect()
```

Resource Overrides let you customize how individual resources are loaded (e.g., specifying a different file path or backend). The DAG automatically wires up dependency and constraint edges based on the DataPackage's FK declarations.

### How do I handle type mismatches when combining data from different sources?

Type mismatches commonly occur when joining or concatenating relations from different sources (e.g., a CSV file where all columns are strings and a database where columns have proper types). Strategies include:

1. **Use `.conform()`** — define a TypeSpec for the target schema and apply `.conform()` to each source before combining. This ensures all sources have matching types.
2. **Use `cast()` explicitly** — cast individual columns before the join: `col("id").cast(UniversalType.INTEGER)`.
3. **Define TypeSpec in DataPackage** — when using DataPackage integration, the resource schemas define expected types, and mountainash casts automatically during `ResourceReadRelNode` processing.

Type mismatches in join keys are handled automatically by Cross-Type Joins, but non-key columns require explicit handling.

### How do I troubleshoot performance issues in mountainash pipelines?

Since mountainash compiles to native backend operations, performance is primarily determined by the backend:

1. **Profile at the backend level** — mountainash adds negligible overhead; the time is spent in Polars, pandas, or SQL execution.
2. **Use lazy evaluation** — Polars LazyFrames and Ibis deferred expressions allow the backend optimizer to work effectively.
3. **Minimize collects** — each `.collect()` materializes data. Chain operations before collecting to let the backend optimize the full plan.
4. **Check the relational AST** — inspect the compiled plan to verify that filters are applied early (predicate pushdown) and unnecessary columns are pruned.
5. **Consider the OptimisationRegistry** — mountainash's AST-level optimizations can reduce work before it reaches the backend.

## Best Practices

### When should I use mountainash vs writing native Polars/pandas code?

Use mountainash when:

- **Backend portability matters** — your code needs to run against different backends (e.g., Polars for local development, SQL for production).
- **Schema-first data quality** — you want TypeSpec-driven validation and conformance.
- **Multi-resource DAG workflows** — you have complex dependencies between data sources.
- **Team standardization** — you want a unified API regardless of individual backend preferences.

Stick with native code when:
- You need maximum performance and are locked to a single backend.
- You need backend-specific features that mountainash does not expose.
- Your transformation is simple and the overhead of abstraction is not justified.

### How should I structure TypeSpec schemas for best results?

Follow these guidelines for effective TypeSpec design:

1. **Be explicit about types** — always specify `UniversalType` rather than relying on inference.
2. **Set nullable correctly** — mark columns as non-nullable only when you are certain they never contain NULLs.
3. **Use constraints sparingly** — `FieldConstraints` (min, max, enum, unique) are powerful but add validation overhead.
4. **Align with Frictionless** — if you plan to use DataPackage integration, ensure your TypeSpec follows Frictionless Table Schema conventions.
5. **Extract from canonical sources** — use Pydantic Extraction or Dataclass Extraction to derive TypeSpec from your domain models, keeping schemas DRY.

### How should I organize relational pipelines?

For maintainable pipelines:

1. **Use meaningful relation names** in RelationDAG — names serve as documentation and reference points.
2. **Keep relation chains short** — break long chains into named intermediate relations in a DAG for readability and debuggability.
3. **Apply conform early** — validate and shape data at ingestion time, not deep in the pipeline.
4. **Use PipelineBuilder for complex workflows** — when you have parameterized, multi-step pipelines with reusable steps.
5. **Test at the relation level** — write tests that verify the output of each named relation, not just the final result.

### What is the recommended approach for cross-backend testing?

Follow these practices:

1. **Use Cross-Backend Parametrize** — parameterize every test with all three backends.
2. **Mark known divergences with xfail** — use `xfail Known Quirks` with descriptive reason strings, not `skip`.
3. **Test NULL edge cases** — NULL handling is the most common source of cross-backend differences.
4. **Test type coercion** — verify behavior with mixed types, especially in joins and comparisons.
5. **Keep a divergence catalog** — maintain a document or code comments listing all known divergences and their status.
6. **Test with realistic data** — small synthetic datasets may miss issues that emerge at scale or with specific data patterns.

### How should I decide between FKEY_SUBSTRAIT and FKEY_MOUNTAINASH prefixes?

Use `FKEY_SUBSTRAIT_*` when:
- The operation has a direct equivalent in the Substrait specification.
- The semantics match Substrait's definition exactly.
- The operation is a standard relational/analytical function.

Use `FKEY_MOUNTAINASH_*` when:
- The operation is not in the Substrait specification.
- It is a convenience function specific to mountainash's use cases.
- It extends Substrait semantics in mountainash-specific ways.

When in doubt, check the Substrait specification. If the function exists there with matching semantics, use the Substrait prefix. This keeps mountainash's AST interoperable with other Substrait-aligned tools.

### How should I handle backend-specific code in a portable pipeline?

When you need backend-specific behavior:

1. **Prefer mountainash abstractions** — use the expression and relation API as much as possible.
2. **Use native() sparingly** — the `native()` function lets you embed backend-specific expressions, but this breaks portability.
3. **Isolate backend-specific logic** — if you must use `native()`, wrap it in a function that checks the backend and provides different implementations per backend.
4. **Use xfail in tests** — if an operation is known to differ across backends, document it.
5. **Contribute back** — if you frequently need an operation that mountainash does not support, consider adding it via the six-step wiring process.

### When should I use RelationDAG vs PipelineBuilder?

Both orchestrate multi-step data workflows, but they serve different purposes:

- **RelationDAG** — best for data flow orchestration where the focus is on named data sources and their dependencies. It integrates with DataPackage, supports FK integrity checks, and uses the two-edge graph model. Use it when your workflow is primarily about connecting and transforming data sources.
- **PipelineBuilder** — best for process orchestration where the focus is on parameterized, reusable processing steps. It supports typed parameter binding via ParamSpec, step-level context and results, and declarative pipeline specs. Use it when your workflow needs runtime parameterization, step-level error handling, or pipeline specification serialization.

You can combine both: use a PipelineBuilder step that internally creates and collects a RelationDAG.

### How do I ensure data quality across the pipeline?

Layer multiple data quality mechanisms:

1. **Schema extraction** at the source — derive TypeSpec from domain models.
2. **Schema validation** at ingestion — use `validate_match()` to verify incoming data.
3. **Conformance** at transformation boundaries — apply `.conform()` at each stage.
4. **FK integrity checks** for referential data — use RelationDAG constraint edges and FK Integrity Check.
5. **Pipeline parameters** for runtime controls — use ParamSpec to enforce typed parameter values.

This multi-layer approach catches schema issues early and prevents corrupt data from propagating through the pipeline.

## Advanced Topics

### How do I implement a custom backend?

To implement a new backend, you need to:

1. **Implement Expression System Protocols** — create a class implementing the expression system protocol with compile functions for every function key in the registry.
2. **Implement Relation Protocols** — create a class implementing the relation protocol with handlers for all relation node types.
3. **Register with Backend Enum** — add a new value to the Backend enum and Backend System Enum.
4. **Implement Type Bridge** — add Backend Type Mapping for your backend's native type system to/from UniversalType.
5. **Implement Backend Composition** — use multiple inheritance to compose expression and relation visitors into a single backend system class.
6. **Add cross-backend tests** — extend parametrized tests to include the new backend.

The protocol-as-contract principle ensures that the interface is well-defined: implement all protocol methods and the backend will integrate with the rest of mountainash.

### How does the Custom Type Registry work?

The `Custom Type Registry` allows you to extend mountainash's type system with application-specific types. It uses Type Converters to define bidirectional mappings between custom logical types and the `UniversalType` enum.

For example, if your domain has a "Currency" type that maps to DECIMAL with specific precision constraints, you can register a type converter that:
- Maps "Currency" to `UniversalType.DECIMAL` with precision=10, scale=2.
- Adds default FieldConstraints (non-nullable, min=0).
- Provides custom schema extraction logic for your domain models.

The registry is lazy-loaded, so custom type definitions only need to be registered before first use.

### How do I build extension relation node types?

Extension relation nodes use `ExtensionRelNode` and `RelationVisitRegistry`:

1. **Define the operation** — create an `ExtensionRelOperation` subclass with custom fields for your operation's parameters.
2. **Register with RelationVisitRegistry** — register a visitor function that handles your custom node type.
3. **Implement per-backend** — provide compile functions for each backend, similar to expression compile functions.

Extension nodes integrate with the existing visitor composition: when the `UnifiedRelationVisitor` encounters an `ExtensionRelNode`, it looks up the registered handler in the `RelationVisitRegistry` and delegates to it.

This is useful for domain-specific operations like data masking, incremental loading, or custom join strategies that don't fit the standard relational algebra nodes.

### How does the TableDialect work in DataPackage integration?

`TableDialect` describes the physical format of a DataResource — CSV delimiter, quote character, header rows, encoding, and other format-specific settings. When mountainash reads a DataPackage resource, the TableDialect determines how the raw file is parsed into a DataFrame.

The `ResourceReadRelNode` carries the TableDialect information so that the relation visitor can configure the appropriate file reader for each backend (e.g., Polars' `read_csv` with specific separator settings, or Ibis' file reader configuration).

### What is the six-step wiring process for new operations?

The six-step wiring process is the standard procedure for adding any new operation to mountainash:

1. **Function Key** — add an enum value to the function key enums.
2. **Function Definition** — register an `ExpressionFunctionDef` in the registry.
3. **API Method** — add the fluent API method to the appropriate class or namespace.
4. **Polars Compile** — write the Polars compile function.
5. **Narwhals Compile** — write the Narwhals compile function.
6. **Ibis Compile** — write the Ibis compile function.

Each step produces a specific artifact, and skipping any step results in a compilation error for the affected backend. The process ensures end-to-end coverage: from the user-facing API through the AST to backend-specific execution.

### How do I design pipelines with runtime parameterization?

Use ParamSpec and fold_params for type-safe runtime parameterization:

```python
from mountainash.pipeline import ParamSpec
from pydantic import BaseModel

class DateRangeParams(BaseModel):
    start_date: str
    end_date: str

param_spec = ParamSpec(model=DateRangeParams)

# In a pipeline step
rel = (
    relation(df)
    .params(param_spec)
    .filter(
        (col("date") >= col("start_date")) &
        (col("date") <= col("end_date"))
    )
)

# At runtime, bind concrete values
from mountainash.pipeline import fold_params
bound = fold_params(rel, DateRangeParams(start_date="2024-01-01", end_date="2024-12-31"))
```

ParamSpec ensures type safety — the Pydantic model validates parameter values before they are bound. The `ParamsRelNode` in the AST is a placeholder that `fold_params` replaces with concrete values at execution time.

### How does mountainash compare to Ibis or Narwhals alone?

- **vs Ibis** — Ibis is SQL-focused: it provides a DataFrame-like API that compiles to SQL for various database backends. Mountainash goes further with a full Substrait-aligned AST, TypeSpec schema system, RelationDAG orchestration, ternary logic, and pipeline framework. Mountainash *uses* Ibis as one of its backends.
- **vs Narwhals** — Narwhals is a thin compatibility layer that provides a common API across DataFrame libraries (pandas, Polars, cuDF). It aims for minimal overhead. Mountainash provides a richer abstraction with AST-based compilation, schema validation, DAG workflows, and pipeline orchestration. Mountainash uses Narwhals as its pandas-ecosystem backend.

Mountainash's unique value is the combination: Substrait-aligned AST, three backends, schema-first quality, and pipeline orchestration in a single coherent library.
