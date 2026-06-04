---
title: Foundation Concepts
description: External prerequisite knowledge for understanding mountainash, including Python type hints, protocol classes, Pydantic models, DataFrames, supported backend libraries, and core design patterns.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 1: Foundation Concepts

## Summary

External prerequisite knowledge including Python type hints, protocol classes, Pydantic models, DataFrames, supported libraries (Polars, pandas, Arrow), SQL databases, and core design patterns (lazy evaluation, method chaining, visitor pattern, DAGs).

## Concepts Covered

- Python Type Hints
- Protocol Classes
- Pydantic Models
- DataFrames
- Polars Library
- Pandas Library
- Apache Arrow
- SQL Databases
- Lazy Evaluation
- Method Chaining
- Visitor Pattern
- Directed Acyclic Graph

## Prerequisites

None (this is the first chapter).

---

## Introduction

Mountainash is a cross-backend data expression and relational pipeline library that operates across multiple DataFrame engines. Before exploring mountainash itself, you need a firm grasp of the external concepts it draws upon. This chapter covers twelve foundational ideas that mountainash assumes you already understand, organized from simple to complex.

We begin with Python's type system, which provides the structural backbone for the entire library. We then examine the DataFrame abstraction and the specific backend libraries mountainash supports. Finally, we explore four design patterns that recur throughout the architecture: lazy evaluation, method chaining, the visitor pattern, and directed acyclic graphs.

<!-- concept:1 -->
## Python Type Hints

Python type hints are annotations that describe the expected types of variables, function parameters, and return values. Introduced in PEP 484 and expanded in subsequent proposals, type hints do not affect runtime behavior by default but provide valuable information to static analysis tools, editors, and documentation generators.

Mountainash uses type hints extensively throughout its codebase. Every public method signature declares parameter types and return types, enabling IDE autocompletion and catching type errors before runtime. The following code illustrates the basic syntax.

```python
from typing import Optional, Union

def process_column(name: str, dtype: Optional[str] = None) -> list[str]:
    """Process a column name with an optional data type."""
    result = [name]
    if dtype is not None:
        result.append(dtype)
    return result
```

Modern Python (3.10+) also supports union types with the pipe operator (`str | None` instead of `Optional[str]`), and mountainash uses both forms depending on context. The `TypeVar` mechanism enables generic classes that preserve type information through method chains.

| Feature | Syntax | Purpose |
|---------|--------|---------|
| Basic annotation | `x: int` | Declare variable type |
| Optional | `Optional[str]` | Value or None |
| Union | `Union[str, int]` | Multiple possible types |
| Generics | `list[str]` | Container with item type |
| TypeVar | `T = TypeVar("T")` | Generic type parameter |
| Callable | `Callable[[int], str]` | Function signature |

<!-- concept:2 -->
## Protocol Classes

A protocol class defines a structural interface that any class can satisfy without explicit inheritance. This is Python's formalization of "duck typing" into the type system, introduced in PEP 544. If a class has the right methods with the right signatures, it satisfies the protocol, regardless of its class hierarchy.

Mountainash uses protocol classes as the primary mechanism for defining contracts between architectural layers. The expression system, relation system, and backend implementations all communicate through protocols rather than concrete base classes.

```python
from typing import Protocol, Any

class ExpressionSystemProtocol(Protocol):
    """Any class with these methods satisfies this protocol."""

    def compile_field_reference(self, node: Any) -> Any: ...
    def compile_literal(self, node: Any) -> Any: ...
    def compile_scalar_function(self, node: Any) -> Any: ...
```

The advantage of protocols over abstract base classes is decoupling. A backend implementation does not need to import or inherit from a central class to participate in the system. This enables mountainash to add new backends without modifying existing code.

- **Structural subtyping**: No `class MySystem(ExpressionSystemProtocol)` required
- **Static checking**: mypy and pyright verify protocol conformance at analysis time
- **Runtime checking**: `isinstance()` works with `@runtime_checkable` protocols
- **Composition**: A class can satisfy multiple protocols simultaneously

<!-- concept:3 -->
## Pydantic Models

Pydantic is a data validation and settings management library that uses Python type annotations to define data models. When you create a Pydantic `BaseModel` subclass, each field's type annotation becomes a validation rule applied at instantiation time.

Mountainash uses Pydantic models in two critical areas. First, the expression AST nodes are all Pydantic `BaseModel` subclasses, configured as frozen (immutable) objects. Second, the type specification system (TypeSpec, FieldSpec) and data package integration use Pydantic for schema definition and validation.

```python
from pydantic import BaseModel, ConfigDict

class ExpressionNode(BaseModel):
    """An immutable AST node backed by Pydantic validation."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    function_key: str
    arguments: list[Any] = []
```

Key Pydantic features used in mountainash include:

- **Frozen models**: `ConfigDict(frozen=True)` makes instances immutable after creation
- **Model validation**: Type coercion and constraint checking at construction time
- **Serialization**: `model_dump()` and `model_validate()` for dict round-tripping
- **Computed fields**: Properties derived from validated data
- **Aliases**: Field names that differ between Python and external formats

<!-- concept:4 -->
## DataFrames

A DataFrame is a two-dimensional, size-mutable, tabular data structure with labeled columns. Each column holds homogeneously-typed data, while the overall table can contain columns of different types. DataFrames are the dominant abstraction for structured data manipulation in the Python data ecosystem.

Mountainash treats DataFrames as the primary input and output medium. You feed DataFrames into the system, express transformations using mountainash's backend-agnostic API, and receive DataFrames back. The library supports DataFrames from multiple backend libraries, each with different performance characteristics and capabilities.

#### Diagram: DataFrame Structure and Backend Mapping
<iframe src="../../sims/dataframe-backend-mapping/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>DataFrame Structure and Backend Mapping</summary>
Type: diagram
**sim-id:** dataframe-backend-mapping<br/>
**Library:** vis-network<br/>
**Status:** Specified

A network diagram showing how a single logical DataFrame concept maps to concrete implementations across backends. Central node labeled "DataFrame" connects to four backend nodes (Polars DataFrame, Polars LazyFrame, pandas DataFrame, PyArrow Table, Ibis Table). Each backend node shows a tooltip on hover with key characteristics (in-memory vs lazy, row-oriented vs columnar). Clicking a backend node highlights its connections. Color scheme: central node in SteelBlue, backend nodes in their taxonomy colors from the learning graph. Learning objective: Understand that mountainash abstracts over multiple concrete DataFrame types (Bloom: Understand).
</details>

The key distinction mountainash cares about is whether a DataFrame is **eager** (data is materialized in memory) or **lazy** (transformations are recorded as a plan and executed only when results are requested).

<!-- concept:5 -->
## Polars Library

Polars is a high-performance DataFrame library written in Rust with Python bindings. It provides both eager and lazy execution modes, columnar memory layout based on Apache Arrow, and a rich expression API.

Mountainash designates Polars as its primary backend. The Polars expression system receives the most comprehensive support, and Polars LazyFrame operations map most naturally to mountainash's relational AST. When you call `relation(polars_df)`, the library routes through the `PolarsRelationSystem` and `PolarsExpressionSystem` backends.

```python
import polars as pl

# Eager DataFrame
df = pl.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})

# Lazy DataFrame (no computation yet)
lf = df.lazy().filter(pl.col("age") > 28).select("name")

# Collect triggers execution
result = lf.collect()
```

Polars operates on Apache Arrow arrays internally, enabling zero-copy interoperability with other Arrow-based tools. Its lazy mode constructs a query plan that the Polars optimizer can rewrite before execution.

<!-- concept:6 -->
## Pandas Library

Pandas is the most widely adopted DataFrame library in Python. It provides an eager, row-indexed DataFrame with extensive I/O support, statistical functions, and integration with the broader scientific Python ecosystem.

In mountainash, pandas DataFrames are routed through the Narwhals adapter layer. Rather than implementing a separate pandas expression system, mountainash wraps pandas DataFrames with Narwhals to provide a Polars-compatible API surface. This means pandas users get access to mountainash features without learning a new API, although performance characteristics differ from native Polars execution.

- Pandas uses row-major memory layout (unlike Polars' columnar layout)
- All operations are eager by default (no lazy execution)
- Rich ecosystem of extensions (GeoPandas, modin, etc.)
- String-based indexing can cause subtle type mismatches

<!-- concept:7 -->
## Apache Arrow

Apache Arrow is a cross-language columnar memory format specification. It defines how tabular data should be laid out in memory for efficient analytical operations, including zero-copy reads between processes and libraries.

Mountainash relies on Arrow at multiple levels. Polars uses Arrow arrays as its internal memory format. Narwhals can wrap PyArrow tables directly. The type system maps between Arrow types and mountainash's universal types. When data crosses backend boundaries, Arrow serves as the common interchange format.

| Feature | Description |
|---------|-------------|
| Columnar format | Data stored column-by-column for vectorized operations |
| Zero-copy | Shared memory between processes without serialization |
| IPC format | Standardized file and streaming formats |
| Type system | Rich type definitions including nested and temporal types |

<!-- concept:8 -->
## SQL Databases

SQL databases store and query relational data using the Structured Query Language. They enforce schemas, support transactions, and optimize queries through cost-based planners.

Mountainash supports SQL databases through the Ibis backend. Ibis translates Python expressions into SQL queries that execute on database engines like DuckDB, PostgreSQL, SQLite, and others. When you pass an Ibis table to `relation()`, mountainash routes through the `IbisRelationSystem` and `IbisExpressionSystem`, which compile the relational AST into SQL.

!!! note "Ibis as a SQL Abstraction"
    Ibis itself is a Python expression library that generates SQL. Mountainash wraps Ibis, adding its own expression AST and relational operators on top. This means mountainash expressions compile to Ibis expressions, which then compile to SQL for the target database engine.

<!-- concept:9 -->
## Lazy Evaluation

Lazy evaluation is a strategy where expressions are not computed until their results are actually needed. Instead of executing operations immediately, the system records them as a plan or tree of operations. Execution happens only when a terminal operation explicitly requests results.

Mountainash adopts lazy evaluation as a core architectural principle. When you write `relation(df).filter(ma.col("age") > 30).select("name")`, no filtering or selection occurs. Instead, mountainash constructs an AST of relational nodes. Only when you call `.collect()`, `.to_polars()`, or another terminal operation does the system compile the AST and execute it against the backend.

This approach provides several advantages:

- **Optimization**: The full query plan is visible before execution, enabling rewrites
- **Backend independence**: The same AST can compile to Polars operations, SQL, or Narwhals calls
- **Composability**: Partial plans can be stored, extended, and reused
- **Efficiency**: Unnecessary intermediate materializations are eliminated

```python
import mountainash as ma

# No execution happens here -- only AST construction
plan = (
    ma.relation(df)
    .filter(ma.col("status") == "active")
    .select("name", "email")
    .sort("name")
)

# Execution happens here
result = plan.to_polars()
```

<!-- concept:10 -->
## Method Chaining

Method chaining is a programming pattern where each method returns the object itself (or a new instance of the same type), allowing multiple method calls to be linked in a single expression. This creates a fluent interface that reads as a sequence of transformations.

In mountainash, every relational operation returns a new `Relation` object wrapping a new AST node. The original relation is unchanged (immutability), and the chain reads top-to-bottom as a data pipeline.

```python
result = (
    ma.relation(df)
    .filter(ma.col("age") > 18)          # Returns new Relation
    .select("name", "age", "score")       # Returns new Relation
    .sort("score", descending=True)       # Returns new Relation
    .head(10)                             # Returns new Relation
    .to_polars()                          # Terminal: executes and returns DataFrame
)
```

Method chaining in mountainash differs from some implementations because it creates new objects rather than mutating state. Each `.filter()`, `.select()`, or `.sort()` call constructs a new `Relation` instance with a new AST node whose `input` points to the previous node. This produces an immutable linked list of operations.

#### Diagram: Method Chaining and AST Construction
<iframe src="../../sims/method-chaining-ast/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Method Chaining and AST Construction</summary>
Type: diagram
**sim-id:** method-chaining-ast<br/>
**Library:** vis-network<br/>
**Status:** Specified

An interactive diagram showing the correspondence between a method chain (displayed as Python code on the left) and the resulting AST tree (displayed as connected nodes on the right). Hovering over a method call highlights the corresponding AST node. Nodes are arranged vertically with the terminal operation at the top and ReadRelNode at the bottom. Each node displays its type (ReadRelNode, FilterRelNode, ProjectRelNode, SortRelNode, FetchRelNode). Clicking a node shows its properties in a tooltip. Colors follow the RLAPI taxonomy (Teal family). Learning objective: Trace how fluent method calls produce an immutable AST of relational nodes (Bloom: Analyze).
</details>

<!-- concept:11 -->
## Visitor Pattern

The visitor pattern is a behavioral design pattern that separates an algorithm from the object structure it operates on. A visitor object is passed to each node in a data structure, and each node calls the appropriate method on the visitor based on its own type. This double-dispatch mechanism allows new operations to be added without modifying the node classes.

Mountainash uses the visitor pattern as the compilation mechanism for both expressions and relations. The `UnifiedExpressionVisitor` traverses expression AST nodes and dispatches to an expression system (Polars, Narwhals, or Ibis) for compilation. The `UnifiedRelationVisitor` does the same for relational AST nodes.

```python
class ExpressionNode:
    def accept(self, visitor):
        """Each node type calls the right visitor method."""
        ...

class FieldReferenceNode(ExpressionNode):
    def accept(self, visitor):
        return visitor.visit_field_reference(self)

class LiteralNode(ExpressionNode):
    def accept(self, visitor):
        return visitor.visit_literal(self)
```

The key benefit is extensibility in two dimensions. New node types require adding one `accept` method and one visitor method per backend. New backends require implementing a new visitor (or expression system) without touching any node classes.

<!-- concept:12 -->
## Directed Acyclic Graph

A directed acyclic graph (DAG) is a graph structure where edges have direction and no cycles exist. Every path through the graph eventually terminates; you cannot follow edges and return to a node you have already visited.

Mountainash uses DAGs in two distinct contexts. First, the relational AST itself forms a DAG. Each relational operation node points to its input(s), creating a tree (a special case of a DAG) that represents the query plan. Join operations have two inputs, making the structure a true DAG rather than a simple linear chain.

Second, the `RelationDAG` class provides an explicit multi-resource orchestration layer. Named relations can reference each other via `dag.ref()`, creating dependency edges. The DAG ensures topological ordering during collection, so upstream relations are materialized before downstream consumers.

#### Diagram: DAG in Query Plans vs RelationDAG
<iframe src="../../sims/dag-dual-usage/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>DAG in Query Plans vs RelationDAG</summary>
Type: diagram
**sim-id:** dag-dual-usage<br/>
**Library:** vis-network<br/>
**Status:** Specified

A split-panel interactive diagram. The left panel shows a relational AST as a DAG: ReadRelNode nodes at the leaves, FilterRelNode and ProjectRelNode in the middle, JoinRelNode merging two branches. The right panel shows a RelationDAG with named relations (customers, orders, summary) connected by dependency edges. Both panels are interactive: clicking a node highlights its dependencies. A toggle button switches between the two views. Color scheme: left panel uses RLAST colors (DodgerBlue), right panel uses DAG colors (Orange). Learning objective: Distinguish the two levels at which DAGs appear in mountainash architecture (Bloom: Analyze).
</details>

Properties of DAGs that mountainash exploits include:

- **Topological ordering**: Nodes can be processed in dependency order
- **Parallel execution potential**: Independent branches can execute concurrently
- **Cycle detection**: Invalid circular dependencies are caught at construction time
- **Incremental computation**: Only changed subgraphs need recomputation

## Key Takeaways

- Python type hints provide the structural backbone for mountainash's API contracts, enabling static analysis and IDE support across all modules.
- Protocol classes enable mountainash's extensible architecture by defining interfaces without requiring inheritance, allowing backends to be added independently.
- Pydantic models serve as the foundation for both expression AST nodes (immutable, validated) and schema definitions (TypeSpec, FieldSpec).
- DataFrames are the universal input/output format; mountainash supports Polars, pandas, PyArrow, and Ibis tables through a unified API.
- Polars is the primary backend with native support, while pandas and PyArrow route through Narwhals, and SQL databases route through Ibis.
- Lazy evaluation means mountainash constructs AST plans rather than executing immediately, enabling optimization and backend independence.
- Method chaining creates immutable Relation objects that build a linked AST of relational operations, executed only at terminal operations.
- The visitor pattern provides the compilation mechanism: visitors traverse AST nodes and dispatch to backend-specific implementations for code generation.
