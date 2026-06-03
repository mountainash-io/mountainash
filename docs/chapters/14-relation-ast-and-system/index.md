---
title: Relation AST and System Architecture
description: Relational AST node types aligned with Substrait, the UnifiedRelationVisitor, visitor composition, visit registries, optimisation registries, RelationSystem base, and pipeline-integrated nodes.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 14: Relation AST and System Architecture

## Summary

Relation AST node types (Read, Project, Filter, Aggregate, Join, Fetch, Sort, Set, Extension, Source, Ref, ResourceRead), relation protocols, UnifiedRelationVisitor, visitor composition, RelationVisitRegistry, OptimisationRegistry, Relation System Base, ExtensionRelOperation, and pipeline-integrated AST nodes (ParamsRelNode, PipelineStepRelNode).

## Concepts Covered

- RelationNode Base
- ReadRelNode
- ProjectRelNode
- FilterRelNode
- AggregateRelNode
- JoinRelNode
- FetchRelNode
- SortRelNode
- SetRelNode
- ExtensionRelNode
- SourceRelNode
- RefRelNode
- ResourceReadRelNode
- Relation Protocols
- UnifiedRelationVisitor
- Visitor Composition
- RelationVisitRegistry
- OptimisationRegistry
- Relation System Base
- ExtensionRelOperation
- ParamsRelNode
- PipelineStepRelNode

## Prerequisites

- [Chapter 1. Foundation Concepts](../01-foundations/)
- [Chapter 7. Expression Function Registry and Compilation](../07-expression-function-registry/)
- [Chapter 8. Expression Backends](../08-expression-backends/)
- [Chapter 10. Relation API Core Operations](../10-relation-api-core/)
- [Chapter 11. Relation API Advanced Features](../11-relation-api-advanced/)
- [Chapter 12. Pipeline Framework](../12-pipeline-framework/)
- [Chapter 13. DAG and DataPackage](../13-dag-and-datapackage/)

---

## Introduction

Chapters 10 and 11 covered the Relation API from the user's perspective -- calling `.filter()`, `.join()`, `.select()` and other methods on Relation objects. Under the hood, each of these method calls creates an AST node that describes *what* to do without specifying *how* to do it. This chapter opens the hood and examines the relational AST node types, the visitor that compiles them into backend-native operations, and the system architecture that ties everything together.

The design mirrors the expression layer (Chapters 6-8): a set of immutable Pydantic-based AST nodes, a visitor that dispatches to per-backend system implementations, and registries that allow extension without modifying core code. The key difference is that relation nodes form a *tree* of relational algebra operations (filter, project, join, aggregate) rather than a tree of scalar computations.

## RelationNode Base

**RelationNode** is the abstract base class for all relational AST nodes. It inherits from both Pydantic's `BaseModel` and Python's `ABC`, giving it immutable serialization semantics and an enforced interface contract.

```python
class RelationNode(BaseModel, ABC):
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    def children(self) -> tuple[Any, ...]:
        """Return structural child relation nodes."""
        ...

    @abstractmethod
    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        ...
```

Three properties define the base class:

- **Frozen model**: All nodes are immutable once created. This guarantees that an AST tree, once built, cannot be mutated by compilation or optimization passes. A new tree must be constructed instead.
- **children() method**: Returns the node's structural children by inspecting the `input`, `left`, `right`, and `inputs` attributes. This is used for tree traversal in the DAG (Chapter 13) and by introspection tools.
- **accept() method**: The abstract method that enables the Visitor Pattern. Each concrete node type implements this to call the appropriate visitor method.

The node type hierarchy splits into two categories: **Substrait-aligned nodes** that correspond to standard relational algebra operations, and **Mountainash extension nodes** that handle framework-specific concerns.

#### Diagram: Relation Node Type Hierarchy

<iframe src="../../sims/relation-node-hierarchy/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Relation Node Type Hierarchy</summary>
Type: Tree Diagram | **sim-id:** relation-node-hierarchy<br/> | **Library:** vis-network<br/> | **Status:** Specified
Shows RelationNode as the root with two branches: Substrait-aligned nodes (Read, Project, Filter, Aggregate, Join, Fetch, Sort, Set) and Mountainash extension nodes (Extension, Source, Ref, ResourceRead, Conform, ParamsRelNode, PipelineStepRelNode). Color-coded by category. Learning objective: Classify all relation node types by origin. Bloom level: Remember. Interactions: Click nodes to expand details, hover for description tooltips.
</details>

## ReadRelNode

A **ReadRelNode** is the leaf node representing a data source scan. It holds a reference to the actual data object (a Polars DataFrame, Polars LazyFrame, Ibis table expression, or similar) and has no child relation nodes. Every relational plan tree must have at least one ReadRelNode (or another leaf type) at its bottom.

```python
class ReadRelNode(RelationNode):
    dataframe: Any  # The source data object

    def accept(self, visitor):
        return visitor.visit_read_rel(self)
```

When the visitor encounters a ReadRelNode, it calls the backend's `read()` method, which wraps the raw data object in whatever form the backend needs for subsequent operations. For the Polars backend, this typically converts an eager DataFrame to a LazyFrame.

## ProjectRelNode

A **ProjectRelNode** represents column-level transformations: selecting columns, adding computed columns, dropping columns, or renaming columns. The `operation` field determines which variant applies.

The four project operation types are defined by the `ProjectOperation` enum:

| Operation | Description | Relation API Method |
|-----------|-------------|-------------------|
| SELECT | Keep only specified columns/expressions | `.select()` |
| WITH_COLUMNS | Add or replace columns while keeping existing ones | `.with_columns()` |
| DROP | Remove specified columns | `.drop()` |
| RENAME | Rename columns using a mapping | `.rename()` |

```python
class ProjectRelNode(RelationNode):
    input: RelationNode           # Child relation
    expressions: list[Any]        # Column expressions
    operation: ProjectOperation   # SELECT, WITH_COLUMNS, DROP, RENAME
    rename_mapping: dict | None   # Only for RENAME
```

The `expressions` list contains either `ExpressionNode` AST objects (from the expression layer) or `BaseExpressionAPI` wrappers. The visitor's `compile_expression()` method handles both cases, extracting the underlying node if needed.

## FilterRelNode

A **FilterRelNode** applies a boolean predicate to filter rows. It holds a single `predicate` expression that evaluates to a boolean series. Only rows where the predicate is true are retained.

```python
class FilterRelNode(RelationNode):
    input: RelationNode  # Child relation
    predicate: Any       # Boolean expression
```

When the Relation API's `.filter()` method receives multiple predicates, they are combined with logical AND before constructing the node. The visitor compiles the predicate expression through the expression visitor, then passes it to the backend's `filter()` method.

## AggregateRelNode

An **AggregateRelNode** represents group-by aggregation. It contains grouping keys and aggregate measure expressions. When the measures list is empty, the node represents a distinct operation (deduplicate by the key columns).

```python
class AggregateRelNode(RelationNode):
    input: RelationNode   # Child relation
    keys: list[Any]       # Grouping expressions
    measures: list[Any]   # Aggregate expressions (sum, mean, count, etc.)
```

The visitor dispatches to either `backend.aggregate()` or `backend.distinct()` depending on whether measures are present. This dual purpose avoids needing a separate DeduplicateRelNode while remaining aligned with Substrait's AggregateRel semantics.

## JoinRelNode

A **JoinRelNode** combines two relation subtrees. It is the only standard node with two children (`left` and `right`) rather than a single `input`. The node carries all the parameters needed to describe the join:

```python
class JoinRelNode(RelationNode):
    left: RelationNode              # Left relation
    right: RelationNode             # Right relation
    join_type: JoinType             # INNER, LEFT, RIGHT, FULL, CROSS, SEMI, ANTI, ASOF
    on: list[str] | None            # Shared key columns
    left_on: list[str] | None       # Left-side key columns
    right_on: list[str] | None      # Right-side key columns
    suffix: str = "_right"          # Disambiguating suffix
    strategy: str | None            # Asof join strategy
    tolerance: Any                  # Asof join tolerance
    execute_on: ExecutionTarget | None  # Which side to execute on
```

The `execute_on` field (covered in Chapter 15) controls cross-backend join execution. The visitor handles asof joins as a special case, routing them to `backend.join_asof()` with the appropriate strategy and tolerance parameters.

## FetchRelNode

A **FetchRelNode** implements limit and offset operations for result pagination. It also supports tail operations via the `from_end` flag, which the visitor routes to a separate `fetch_from_end()` backend method.

```python
class FetchRelNode(RelationNode):
    input: RelationNode
    offset: int = 0          # Rows to skip
    count: int | None = None  # Max rows to return
    from_end: bool = False    # Tail operation flag
```

The `.head(n)`, `.tail(n)`, `.slice(offset, length)`, `.limit(n)`, `.first()`, and `.last()` Relation API methods all produce FetchRelNode instances with different parameter combinations.

## SortRelNode

A **SortRelNode** orders rows by one or more sort specifications. Each specification is a `SortField` constant that captures the column name and sort direction (ascending or descending).

```python
class SortRelNode(RelationNode):
    input: RelationNode
    sort_fields: list[SortField]
```

## SetRelNode

A **SetRelNode** combines multiple relation subtrees using set operations. Unlike JoinRelNode which combines two relations horizontally (adding columns), SetRelNode combines them vertically (stacking rows). It uses a list of `inputs` rather than `left`/`right`.

```python
class SetRelNode(RelationNode):
    inputs: list[RelationNode]  # Relations to combine
    set_type: SetType           # UNION_ALL, UNION_DISTINCT
```

The `concat()` function and set operation methods on Relation produce SetRelNode instances. The visitor compiles each input relation, then passes the list to `backend.union_all()`.

#### Diagram: Relation AST Tree Example

<iframe src="../../sims/relation-ast-example/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Relation AST Tree Example</summary>
Type: Interactive Tree | **sim-id:** relation-ast-example<br/> | **Library:** vis-network<br/> | **Status:** Specified
Displays a sample relational AST tree for the query: `relation(df).filter(col("age") > 18).select(col("name"), col("email")).head(10)`. Shows ReadRelNode at the leaf, FilterRelNode above it, ProjectRelNode above that, and FetchRelNode at the root. Each node shows its type and key attributes. Learning objective: Read and interpret a relational AST. Bloom level: Analyze. Interactions: Click nodes to expand their attributes, hover edges to see data flow direction.
</details>

## ExtensionRelNode

An **ExtensionRelNode** handles operations that are common in DataFrame APIs but not part of the Substrait specification. These include `drop_nulls`, `with_row_index`, `explode`, `unnest`, and other practical utilities.

```python
class ExtensionRelNode(RelationNode):
    input: RelationNode
    operation: ExtensionRelOperation  # Enum of extension operations
    options: dict[str, Any] = {}      # Operation-specific configuration
```

The `ExtensionRelOperation` enum catalogues all supported extension operations. The visitor dispatches these by looking up a method on the backend system whose name matches the operation's lowercase enum name. For example, `ExtensionRelOperation.UNNEST` calls `backend.unnest(relation, **options)`.

This design means adding a new extension operation requires only:

1. Adding a member to the `ExtensionRelOperation` enum
2. Implementing the corresponding method on each backend's extension mixin

No changes to the visitor or node hierarchy are needed.

## SourceRelNode

A **SourceRelNode** is a leaf node that holds raw Python data (list of dictionaries, dict of lists, dataclasses, Pydantic models) for deferred conversion to a DataFrame. Unlike ReadRelNode, which expects a pre-existing DataFrame, SourceRelNode accepts Python-native data structures.

```python
class SourceRelNode(RelationNode):
    data: Any                              # Raw Python data
    detected_format: CONST_PYTHON_DATAFORMAT  # Auto-detected format
```

At visit time, the handler invokes `PydataIngress.convert()` to transform the Python data into a Polars DataFrame, then passes it to `backend.read()`. This deferred conversion means the data is not copied or transformed until the relation is actually compiled.

## RefRelNode

A **RefRelNode** is the leaf node used by `dag.ref()` to create cross-references between named relations in a RelationDAG. It carries the name of the referenced relation and an optional output schema for type checking.

```python
class RefRelNode(RelationNode):
    name: str                    # Name of the referenced relation
    output_schema: Any | None    # Optional schema for validation
```

RefRelNode cannot be compiled standalone. When the visitor encounters one, it looks up the registered handler in the `RelationVisitRegistry`, which calls `visitor.ref_resolver(node.name)`. If no ref_resolver was provided, a `RelationDAGRequired` error is raised, directing the user to compile via `dag.collect()` instead of calling `relation.to_polars()` directly.

## ResourceReadRelNode

A **ResourceReadRelNode** is a leaf node that carries a Frictionless `DataResource` object. It bridges the DataPackage metadata layer with the relation execution layer. When the DAG calls `to_relation_dag()`, each tabular resource is wrapped in a ResourceReadRelNode.

```python
class ResourceReadRelNode(RelationNode):
    resource: DataResource  # Frictionless DataResource
```

The visit handler for this node performs two steps:

1. Call `backend.read_resource(resource)` to load the data via the storage facade
2. If the resource has a `table_schema`, apply conformance transforms via `visitor.apply_conform()`

This two-step approach means the schema is not just metadata -- it actively drives type coercion and column ordering when the data is loaded.

## Relation Protocols

**Relation protocols** define the interface contracts that the Relation API, the visitor, and the backend systems must satisfy. They are implemented as Python Protocol classes (structural typing), allowing any class that implements the required methods to satisfy the protocol without explicit inheritance.

The protocol hierarchy includes:

- **RelationAPIProtocol**: Defines the user-facing API surface (`.select()`, `.filter()`, `.join()`, etc.)
- **SubstraitReadRelationSystemProtocol**: Backend must implement `read()`
- **SubstraitProjectRelationSystemProtocol**: Backend must implement `project_select()`, `project_with_columns()`, etc.
- **SubstraitFilterRelationSystemProtocol**: Backend must implement `filter()`
- **SubstraitJoinRelationSystemProtocol**: Backend must implement `join()`, `join_asof()`
- **SubstraitAggregateRelationSystemProtocol**: Backend must implement `aggregate()`, `distinct()`
- And one protocol for each Substrait-aligned operation type

These protocols serve as compile-time documentation and enable static type checkers to verify that backend implementations are complete.

## UnifiedRelationVisitor

The **UnifiedRelationVisitor** is the compiler that walks a relational AST tree and produces backend-native results. It is "unified" because a single visitor class handles all backends -- the backend-specific behavior comes from the `RelationSystem` instance injected at construction time.

```python
class UnifiedRelationVisitor:
    def __init__(
        self,
        relation_system,
        expression_visitor,
        *,
        ref_resolver=None,
    ):
        self.backend = relation_system
        self.expr_visitor = expression_visitor
        self.ref_resolver = ref_resolver
```

The visitor implements named `visit_*` methods for each Substrait-aligned node type:

- `visit_read_rel()` -- Calls `backend.read()`
- `visit_project_rel()` -- Dispatches to `project_select()`, `project_with_columns()`, etc.
- `visit_filter_rel()` -- Compiles the predicate, calls `backend.filter()`
- `visit_sort_rel()` -- Calls `backend.sort()`
- `visit_fetch_rel()` -- Routes to `backend.fetch()` or `backend.fetch_from_end()`
- `visit_join_rel()` -- Handles cross-type coercion, routes asof joins separately
- `visit_aggregate_rel()` -- Routes to `backend.aggregate()` or `backend.distinct()`
- `visit_set_rel()` -- Calls `backend.union_all()`
- `visit_extension_rel()` -- Dispatches via operation name lookup

For extension nodes (Source, Ref, ResourceRead, Conform), the visitor delegates to the `RelationVisitRegistry`.

#### Diagram: Visitor Compilation Flow

<iframe src="../../sims/relation-visitor-flow/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Visitor Compilation Flow</summary>
Type: Sequence Diagram | **sim-id:** relation-visitor-flow<br/> | **Library:** vis-network<br/> | **Status:** Specified
Shows the compilation of a Filter-then-Select query: UnifiedRelationVisitor receives the ProjectRelNode root, recurses into FilterRelNode, recurses into ReadRelNode, then unwinds calling backend.read(), backend.filter(), backend.project_select(). Expression visitor calls shown as sub-sequences. Learning objective: Trace the recursive compilation through the visitor. Bloom level: Apply. Interactions: Step through the sequence with forward/back controls, highlight current stack frame.
</details>

## Visitor Composition

**Visitor composition** is the pattern by which the relation visitor delegates expression compilation to the expression visitor. When a relation node contains expression AST nodes (filter predicates, projection expressions, aggregation measures), the relation visitor calls `self.compile_expression()` which routes to the expression visitor:

```python
def compile_expression(self, expr):
    if isinstance(expr, ExpressionNode):
        return self.expr_visitor.visit(expr)
    if isinstance(expr, BaseExpressionAPI):
        return self.expr_visitor.visit(expr._node)
    return expr  # Native/string expressions pass through
```

This three-way dispatch handles:

1. **ExpressionNode** objects from the expression AST -- compiled directly
2. **BaseExpressionAPI** wrappers (e.g., `ma.col("x").gt(5)`) -- extract the internal node and compile
3. **Native expressions** (Polars `pl.Expr`, string column names) -- passed through unchanged to the backend

The composition ensures that the same expression compilation logic is reused whether the expression appears in a filter, a projection, or an aggregation.

## RelationVisitRegistry

The **RelationVisitRegistry** is a class-level registry that maps node types to visit handler functions. It enables extension nodes to register their compilation behavior without modifying the core `UnifiedRelationVisitor` class.

```python
class RelationVisitRegistry:
    _handlers: dict[type, RelationVisitHandler] = {}

    @classmethod
    def register(cls, node_type, handler):
        if node_type in _PROTECTED_NODE_TYPES:
            raise TypeError(...)
        cls._handlers[node_type] = handler

    @classmethod
    def get(cls, node_type):
        cls._ensure_initialized()
        return cls._handlers.get(node_type)
```

The registry distinguishes **protected node types** from registerable ones. The eight Substrait-aligned nodes (Read, Project, Filter, Sort, Fetch, Join, Aggregate, Set) plus ExtensionRelNode are protected -- their visit methods are hardcoded in the visitor and cannot be overridden via the registry. Extension nodes (Source, Ref, ResourceRead, Conform) are registered lazily on first access.

This protection prevents plugins from accidentally overriding core relational algebra semantics while still allowing new node types to be added by external packages.

Core handlers are registered lazily via `_ensure_initialized()`:

| Node Type | Handler | Behavior |
|-----------|---------|----------|
| RefRelNode | `_visit_ref_rel` | Calls `ref_resolver(name)` or raises `RelationDAGRequired` |
| ResourceReadRelNode | `_visit_resource_read_rel` | Loads data via storage facade, applies conform |
| SourceRelNode | `_visit_source_rel` | Converts Python data via PydataIngress |
| ConformRelNode | `_visit_conform_rel` | Applies schema conformance transforms |

## OptimisationRegistry

The **OptimisationRegistry** stores node-level optimization functions that run before compilation. When the Relation API builds the final AST, it checks the registry for optimizations applicable to the root node type and applies them.

The primary optimization currently registered is `fold_params`, which folds `ParamsRelNode` into the underlying `PipelineStepRelNode` to avoid an extra visitor dispatch. The registry pattern exists to support future optimizations like predicate pushdown, projection pruning, or join reordering.

Optimizations must be pure functions: they accept a node and return either the same node (no optimization applicable) or a new, optimized node. They must not mutate the input node.

## Relation System Base

The **RelationSystem** abstract base class defines the complete interface that each backend must implement. It composes all the Substrait-aligned protocol interfaces and the Mountainash extension protocol into a single class:

```python
class RelationSystem(
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    MountainashExtensionRelationSystemProtocol,
):
    @property
    @abstractmethod
    def backend_type(self) -> CONST_BACKEND: ...
```

Backend implementations are registered via the `@register_relation_system()` decorator, which associates a `CONST_BACKEND` enum value with a concrete class. The `get_relation_system()` function retrieves the registered class by backend type.

This architecture means the visitor never imports backend-specific code directly. It asks the registry for the appropriate system, and the registry returns the class that was registered for that backend. Adding a new backend requires only implementing the protocols and registering the class.

#### Diagram: Relation System Composition

<iframe src="../../sims/relation-system-composition/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Relation System Composition</summary>
Type: Class Diagram | **sim-id:** relation-system-composition<br/> | **Library:** vis-network<br/> | **Status:** Specified
Shows the RelationSystem base class composed from 9 protocol mixins, with PolarsRelationSystem, NarwhalsRelationSystem, and IbisRelationSystem as concrete implementations. Each protocol lists its required methods. The @register_relation_system decorator and get_relation_system() lookup are shown. Learning objective: Understand how backends compose protocol implementations. Bloom level: Understand. Interactions: Click protocols to see method signatures, click backends to see which protocol implementations they inherit.
</details>

## ExtensionRelOperation

**ExtensionRelOperation** is an enum that catalogues all non-Substrait relational operations supported by mountainash. Each member corresponds to a method that backend systems must implement in their `MountainashExtensionRelationSystemProtocol` mixin.

The visitor resolves extension operations by converting the enum member's name to lowercase and looking up the corresponding method on the backend:

```python
def visit_extension_rel(self, node):
    relation = self.visit(node.input)
    method_name = node.operation.name.lower()
    method = getattr(self.backend, method_name)
    return method(relation, **node.options)
```

This convention-based dispatch means adding a new extension operation is a three-step process: add the enum member, implement the method on each backend, and the visitor automatically routes to it. No visitor modification is needed.

## ParamsRelNode

**ParamsRelNode** is a pipeline-integrated AST node that attaches runtime parameters to a relation. It wraps another relation node (typically a `PipelineStepRelNode`) and carries a dictionary of parameter values.

```python
class ParamsRelNode(RelationNode):
    input: Any                        # Wrapped relation node
    params: dict[str, Any] = {}       # Parameter values
```

The `relation.params()` method creates a ParamsRelNode wrapping the current relation's AST. At optimization time, the `fold_params()` function merges the parameter dictionary into the underlying `PipelineStepRelNode`, validating parameter names against declared `ParamSpec` objects and applying defaults for missing optional parameters.

## PipelineStepRelNode

**PipelineStepRelNode** represents a deferred pipeline step execution within the relational AST. It carries a reference to the pipeline, the step name, an executor, and bound parameters.

```python
class PipelineStepRelNode(RelationNode):
    step_name: str
    pipeline: Any
    data_key: str | None = None
    executor: Any | None = None
    param_specs: tuple[ParamSpec, ...] = ()
    bound_params: dict[str, Any] = {}
```

When the visitor encounters this node (via the registered handler), it delegates to `executor.execute()`, passing the pipeline, step name, and bound parameters. This enables pipeline steps to participate in the relational AST alongside regular operations.

The `register_pipeline_bridge()` function registers both `PipelineStepRelNode` and `ParamsRelNode` handlers in the `RelationVisitRegistry`, and `register_params_optimisation()` registers the `fold_params` optimizer in the `OptimisationRegistry`. These are called lazily when the pipeline module is first imported.

## Key Takeaways

- **RelationNode** is the immutable Pydantic base class for all relational AST nodes, enforcing frozen semantics and the Visitor Pattern via `accept()`.
- Eight **Substrait-aligned nodes** (Read, Project, Filter, Aggregate, Join, Fetch, Sort, Set) cover standard relational algebra; five **extension nodes** (Extension, Source, Ref, ResourceRead, Conform) handle framework-specific concerns.
- The **UnifiedRelationVisitor** compiles ASTs by recursively visiting nodes and delegating to the injected `RelationSystem` backend -- one visitor class serves all backends.
- **Visitor composition** delegates expression compilation to the expression visitor, handling ExpressionNode, BaseExpressionAPI, and native pass-through.
- The **RelationVisitRegistry** allows extension nodes to register handlers without modifying core code, while protecting Substrait-aligned nodes from override.
- **RelationSystem** is composed from nine protocol mixins via multiple inheritance; concrete backends register via decorator and are looked up by enum.
- **ParamsRelNode** and **PipelineStepRelNode** bridge the pipeline framework into the relational AST, with fold_params optimization merging parameters before compilation.
