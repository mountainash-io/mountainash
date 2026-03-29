# Relational AST Design Spec

**Status:** APPROVED
**Created:** 2026-03-28
**Scope:** New `mountainash.relations` module — Substrait-aligned relational AST with Polars/Narwhals-aligned public API

## Overview

Build a relational algebra layer that mirrors the expressions architecture: immutable AST nodes, three-layer separation (protocol → API → backend), unified visitor, deferred compilation. Replaces the current eager-execution `TableBuilder` with a plan-tree model where operations build a DAG of relational nodes, and terminal operations trigger visitor-based compilation to native backend operations.

### Design Drivers

- **Substrait alignment**: Each relational node maps to a Substrait logical relation (SortRel, FilterRel, ProjectRel, AggregateRel, JoinRel, FetchRel, SetRel)
- **Expressions parity**: Same architectural pattern — build-then-compile, function registry, visitor dispatch, backend composition
- **Polars/Narwhals API alignment**: Method names and signatures match Polars/Narwhals conventions
- **Cross-type joins**: Joins accept any supported Python data type (Polars, pandas, PyArrow, Ibis, Narwhals, dict, list of dicts)
- **Backend delegation**: No optimizer in mountainash — the visitor delegates to backend implementations which use their own native optimizers (Polars query planner, Ibis SQL compiler, etc.)

---

## 1. Relational Node Types

10 node types, each mapping to a Substrait logical relation. All are immutable Pydantic BaseModel subclasses with `accept(visitor)`.

### Substrait-Aligned Nodes

```python
class RelationNode(BaseModel):
    """Abstract base for all relational AST nodes."""
    def accept(self, visitor): ...

class ReadRelNode(RelationNode):
    """Leaf node: wraps a native DataFrame."""
    dataframe: Any

class ProjectRelNode(RelationNode):
    """Select, with_columns, drop, rename. Maps to Substrait ProjectRel."""
    input: RelationNode
    expressions: list[ExpressionNode]
    operation: ProjectOperation        # Enum: SELECT, WITH_COLUMNS, DROP, RENAME
    rename_mapping: dict[str, str] | None = None

class FilterRelNode(RelationNode):
    """Filter rows by predicate. Maps to Substrait FilterRel."""
    input: RelationNode
    predicate: ExpressionNode | Any    # ExpressionNode or native backend expression

class SortRelNode(RelationNode):
    """Sort by fields. Maps to Substrait SortRel."""
    input: RelationNode
    sort_fields: list[SortField]       # Dataclass: column, descending, nulls_last

class FetchRelNode(RelationNode):
    """Head, tail, slice. Maps to Substrait FetchRel."""
    input: RelationNode
    offset: int = 0
    count: int | None = None
    from_end: bool = False

class JoinRelNode(RelationNode):
    """All join types. Maps to Substrait JoinRel."""
    left: RelationNode
    right: RelationNode
    join_type: JoinType                # Enum: INNER, LEFT, RIGHT, OUTER, SEMI, ANTI, CROSS, ASOF
    on: list[str] | None = None
    left_on: list[str] | None = None
    right_on: list[str] | None = None
    suffix: str = "_right"
    strategy: str | None = None        # Asof: backward, forward, nearest
    tolerance: Any | None = None
    execute_on: ExecutionTarget | None = None  # Enum: LEFT, RIGHT, None=auto-detect

class AggregateRelNode(RelationNode):
    """Group-by + aggregate, or distinct. Maps to Substrait AggregateRel."""
    input: RelationNode
    keys: list[str | ExpressionNode]
    measures: list[ExpressionNode]     # Empty = DISTINCT

class SetRelNode(RelationNode):
    """Union/concat. Maps to Substrait SetRel."""
    inputs: list[RelationNode]
    set_type: SetType                  # Enum: UNION_ALL, UNION_DISTINCT
```

### Mountainash Extension Node

```python
class ExtensionRelNode(RelationNode):
    """Non-Substrait operations: drop_nulls, with_row_index, explode, sample, unpivot, pivot, top_k."""
    input: RelationNode
    operation: ExtensionRelOperation   # Enum for specific operation
    options: dict[str, Any] = {}       # Operation-specific parameters
```

### Supporting Enums

```python
class ProjectOperation(Enum):
    SELECT = auto()
    WITH_COLUMNS = auto()
    DROP = auto()
    RENAME = auto()

class JoinType(StrEnum):
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    OUTER = "outer"
    SEMI = "semi"
    ANTI = "anti"
    CROSS = "cross"
    ASOF = "asof"

class ExecutionTarget(Enum):
    LEFT = auto()
    RIGHT = auto()

class SetType(Enum):
    UNION_ALL = auto()
    UNION_DISTINCT = auto()

class ExtensionRelOperation(Enum):
    DROP_NULLS = auto()
    WITH_ROW_INDEX = auto()
    EXPLODE = auto()
    SAMPLE = auto()
    UNPIVOT = auto()
    PIVOT = auto()
    TOP_K = auto()

@dataclass(frozen=True)
class SortField:
    column: str
    descending: bool = False
    nulls_last: bool = True
```

---

## 2. Three-Layer Separation

### Layer 1: Protocols

One protocol per Substrait relation type. Methods operate on native types (`Any`).

```
relations/core/relation_protocols/relation_systems/
    substrait/
        prtcl_relsys_read.py          # SubstraitReadRelationSystemProtocol
        prtcl_relsys_project.py       # SubstraitProjectRelationSystemProtocol
        prtcl_relsys_filter.py        # SubstraitFilterRelationSystemProtocol
        prtcl_relsys_sort.py          # SubstraitSortRelationSystemProtocol
        prtcl_relsys_fetch.py         # SubstraitFetchRelationSystemProtocol
        prtcl_relsys_join.py          # SubstraitJoinRelationSystemProtocol
        prtcl_relsys_aggregate.py     # SubstraitAggregateRelationSystemProtocol
        prtcl_relsys_set.py           # SubstraitSetRelationSystemProtocol
    extensions_mountainash/
        prtcl_relsys_ext_ma_util.py   # MountainashExtensionRelationSystemProtocol
```

Example protocol:

```python
class SubstraitJoinRelationSystemProtocol(Protocol):
    def join(self, left: Any, right: Any, *, join_type: JoinType,
             on: list[str] | None, left_on: list[str] | None,
             right_on: list[str] | None, suffix: str) -> Any: ...
    def join_asof(self, left: Any, right: Any, *, on: str,
                  by: list[str] | None, strategy: str,
                  tolerance: Any | None) -> Any: ...
```

### Layer 2: API (Relation class)

```
relations/core/relation_api/
    relation.py                       # Relation (public fluent API)
    relation_base.py                  # Base with _compile_and_execute()
    grouped_relation.py               # GroupedRelation (from group_by())
```

Each method constructs a relational node and returns a new `Relation`:

```python
class Relation:
    _node: RelationNode

    def filter(self, *predicates) -> Relation:
        combined = _combine_predicates(predicates)
        return Relation(FilterRelNode(input=self._node, predicate=combined))

    def sort(self, *by, descending=False) -> Relation:
        fields = _normalize_sort_fields(by, descending)
        return Relation(SortRelNode(input=self._node, sort_fields=fields))

    def group_by(self, *keys) -> GroupedRelation:
        return GroupedRelation(self._node, keys)

    def collect(self) -> Any:
        return self._compile_and_execute()
```

### Layer 3: Backends

Per-backend RelationSystem composed via multiple inheritance:

```
relations/backends/relation_systems/
    polars/
        __init__.py                   # PolarsRelationSystem (composition, body=pass)
        base.py                       # PolarsBaseRelationSystem
        substrait/
            relsys_pl_read.py
            relsys_pl_project.py
            relsys_pl_filter.py
            relsys_pl_sort.py
            relsys_pl_fetch.py
            relsys_pl_join.py
            relsys_pl_aggregate.py
            relsys_pl_set.py
        extensions_mountainash/
            relsys_pl_ext_ma_util.py
    ibis/  (identical structure, relsys_ib_*)
    narwhals/  (identical structure, relsys_nw_*)
```

---

## 3. Visitor & Compilation

### UnifiedRelationVisitor

Single visitor dispatches all node types. Holds a reference to the expression visitor for compiling embedded expressions.

```python
class UnifiedRelationVisitor:
    def __init__(self, relation_system, expression_visitor):
        self.backend = relation_system
        self.expr_visitor = expression_visitor

    def visit(self, node: RelationNode) -> Any:
        return node.accept(self)

    def visit_read_rel(self, node: ReadRelNode) -> Any:
        return self.backend.read(node.dataframe)

    def visit_filter_rel(self, node: FilterRelNode) -> Any:
        relation = self.visit(node.input)
        predicate = self._compile_expression(node.predicate, relation)
        return self.backend.filter(relation, predicate)

    def visit_sort_rel(self, node: SortRelNode) -> Any:
        relation = self.visit(node.input)
        return self.backend.sort(relation, node.sort_fields)

    def visit_project_rel(self, node: ProjectRelNode) -> Any:
        relation = self.visit(node.input)
        compiled_exprs = [self._compile_expression(e, relation) for e in node.expressions]
        match node.operation:
            case ProjectOperation.SELECT:
                return self.backend.project_select(relation, compiled_exprs)
            case ProjectOperation.WITH_COLUMNS:
                return self.backend.project_with_columns(relation, compiled_exprs)
            case ProjectOperation.DROP:
                return self.backend.project_drop(relation, compiled_exprs)
            case ProjectOperation.RENAME:
                return self.backend.project_rename(relation, node.rename_mapping)

    def visit_join_rel(self, node: JoinRelNode) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        # Cross-type coercion based on execute_on
        left, right = self._coerce_join_inputs(left, right, node.execute_on)
        if node.join_type == JoinType.ASOF:
            return self.backend.join_asof(left, right, ...)
        return self.backend.join(left, right, join_type=node.join_type, ...)

    def visit_aggregate_rel(self, node: AggregateRelNode) -> Any:
        relation = self.visit(node.input)
        compiled_measures = [self._compile_expression(m, relation) for m in node.measures]
        if not compiled_measures:
            return self.backend.distinct(relation, node.keys)
        return self.backend.aggregate(relation, node.keys, compiled_measures)

    def visit_fetch_rel(self, node: FetchRelNode) -> Any:
        relation = self.visit(node.input)
        if node.from_end:
            return self.backend.fetch_from_end(relation, node.count)
        return self.backend.fetch(relation, node.offset, node.count)

    def visit_set_rel(self, node: SetRelNode) -> Any:
        relations = [self.visit(inp) for inp in node.inputs]
        return self.backend.union_all(relations)

    def visit_extension_rel(self, node: ExtensionRelNode) -> Any:
        relation = self.visit(node.input)
        method = getattr(self.backend, node.operation.name.lower())
        return method(relation, **node.options)

    def _compile_expression(self, expr_node, relation) -> Any:
        if isinstance(expr_node, ExpressionNode):
            return self.expr_visitor.visit(expr_node)
        return expr_node  # Native expressions pass through
```

### Compilation Entry Point

```python
class Relation:
    def _compile_and_execute(self) -> Any:
        backend = self._detect_backend()
        relation_system = get_relation_system(backend)
        expression_system = get_expression_system(backend)
        expr_visitor = UnifiedExpressionVisitor(expression_system)
        visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
        return visitor.visit(self._node)

    def _detect_backend(self) -> CONST_BACKEND:
        leaf = self._find_leaf_read_node()
        return identify_backend(leaf.dataframe)
```

### Backend Read — Lazy by Default

| Backend | `read(df)` returns |
|---------|-------------------|
| Polars | `df.lazy()` if eager, pass-through if LazyFrame |
| Ibis | Pass-through (already deferred) |
| Narwhals | `nw.from_native(df)` — eager |

Terminal operations handle final materialization.

---

## 4. Public API

### Entry Points

```python
import mountainash as ma

r = ma.relation(df)                  # Any supported DataFrame
ma.concat([r1, r2])                  # Module-level concat
```

### Chainable Operations (return Relation)

```python
# ProjectRel
r.select("a", "b", ma.col("c") * 2)
r.with_columns(ma.col("a") + 1, (ma.col("b") * 2).alias("double_b"))
r.drop("x", "y")
r.rename({"old": "new"})

# FilterRel
r.filter(ma.col("age") > 30)
r.filter(ma.col("age") > 30, ma.col("score") >= 85)  # Multiple = AND

# SortRel
r.sort("age")
r.sort("age", descending=True)
r.sort("group", "age", descending=[False, True])

# FetchRel
r.head(10)
r.tail(5)
r.slice(offset=10, length=20)

# JoinRel (any data type accepted for 'other')
r.join(other_relation, on="id")
r.join(pandas_df, on="id", how="left")
r.join(dict_data, on="id", how="left", execute_on=ExecutionTarget.LEFT)
r.join_asof(other, on="timestamp", by="ticker", strategy="backward")

# AggregateRel
r.group_by("category").agg(
    ma.col("price").mean().alias("avg_price"),
    ma.col("quantity").sum().alias("total_qty"),
)
r.unique("id", "name")
r.unique(subset=["id"], keep="first")

# SetRel
ma.concat([r1, r2])

# ExtensionRel
r.drop_nulls()
r.drop_nulls(subset=["a", "b"])
r.with_row_index(name="idx")
r.explode("tags")
r.sample(n=100)
r.sample(fraction=0.1)
r.unpivot(on=["q1", "q2", "q3"], index="student", variable_name="quarter", value_name="score")
r.pivot(on="quarter", index="student", values="score")
r.top_k(5, by="score")
r.pipe(my_custom_function)
```

### GroupedRelation

```python
class GroupedRelation:
    _node: RelationNode
    _keys: list[str | ExpressionNode]

    def agg(self, *expressions) -> Relation:
        return Relation(AggregateRelNode(input=self._node, keys=self._keys, measures=list(expressions)))
```

### Terminal Operations

```python
r.collect()          # Native type (same as input)
r.to_polars()        # pl.DataFrame
r.to_pandas()        # pd.DataFrame
r.to_pyarrow()       # pa.Table
r.to_ibis()          # ibis.Table
r.to_narwhals()      # nw.DataFrame
r.to_dict()          # dict[str, list]
r.to_dicts()         # list[dict]
```

### Introspection

```python
r.columns             # list[str] — inferred from plan
r.schema              # dict[str, dtype] — inferred from plan
r.shape               # (rows, cols) — triggers compilation
```

---

## 5. Cross-Type Join Handling

### At Build Time

```python
class Relation:
    def join(self, other, *, on=None, left_on=None, right_on=None,
             how="inner", suffix="_right", execute_on=None) -> Relation:
        right_node = self._to_relation_node(other)
        node = JoinRelNode(
            left=self._node, right=right_node,
            join_type=JoinType(how), on=_normalize_columns(on),
            left_on=_normalize_columns(left_on), right_on=_normalize_columns(right_on),
            suffix=suffix, execute_on=execute_on,
        )
        return Relation(node)

    def _to_relation_node(self, other) -> RelationNode:
        if isinstance(other, Relation):
            return other._node
        return ReadRelNode(dataframe=other)
```

### At Compile Time

The visitor coerces the non-target side to match the execution backend. Uses the same conversion logic as existing DataFrameSystem casts (extract and reuse).

---

## 6. File Organisation

```
src/mountainash/
├── core/
│   └── constants.py                          # Add: ProjectOperation, JoinType, SetType, etc.
│
├── relations/                                # NEW module
│   ├── __init__.py                           # Exports: relation(), concat()
│   │
│   ├── core/
│   │   ├── relation_nodes/
│   │   │   ├── __init__.py
│   │   │   ├── reln_base.py
│   │   │   ├── substrait/
│   │   │   │   ├── reln_read.py
│   │   │   │   ├── reln_project.py
│   │   │   │   ├── reln_filter.py
│   │   │   │   ├── reln_sort.py
│   │   │   │   ├── reln_fetch.py
│   │   │   │   ├── reln_join.py
│   │   │   │   ├── reln_aggregate.py
│   │   │   │   └── reln_set.py
│   │   │   └── extensions_mountainash/
│   │   │       └── reln_ext_ma_util.py
│   │   │
│   │   ├── relation_protocols/
│   │   │   └── relation_systems/
│   │   │       ├── substrait/
│   │   │       │   ├── prtcl_relsys_read.py
│   │   │       │   ├── prtcl_relsys_project.py
│   │   │       │   ├── prtcl_relsys_filter.py
│   │   │       │   ├── prtcl_relsys_sort.py
│   │   │       │   ├── prtcl_relsys_fetch.py
│   │   │       │   ├── prtcl_relsys_join.py
│   │   │       │   ├── prtcl_relsys_aggregate.py
│   │   │       │   └── prtcl_relsys_set.py
│   │   │       └── extensions_mountainash/
│   │   │           └── prtcl_relsys_ext_ma_util.py
│   │   │
│   │   ├── relation_api/
│   │   │   ├── relation.py
│   │   │   ├── relation_base.py
│   │   │   └── grouped_relation.py
│   │   │
│   │   └── unified_visitor/
│   │       └── relation_visitor.py
│   │
│   └── backends/
│       └── relation_systems/
│           ├── polars/
│           │   ├── __init__.py
│           │   ├── base.py
│           │   ├── substrait/
│           │   │   ├── relsys_pl_read.py
│           │   │   ├── relsys_pl_project.py
│           │   │   ├── relsys_pl_filter.py
│           │   │   ├── relsys_pl_sort.py
│           │   │   ├── relsys_pl_fetch.py
│           │   │   ├── relsys_pl_join.py
│           │   │   ├── relsys_pl_aggregate.py
│           │   │   └── relsys_pl_set.py
│           │   └── extensions_mountainash/
│           │       └── relsys_pl_ext_ma_util.py
│           ├── ibis/
│           │   └── (identical structure, relsys_ib_*)
│           └── narwhals/
│               └── (identical structure, relsys_nw_*)
```

Naming conventions:

| Layer | Prefix | Example |
|-------|--------|---------|
| Relation nodes | `reln_` | `reln_filter.py` |
| Relation protocols | `prtcl_relsys_` | `prtcl_relsys_filter.py` |
| Polars backend | `relsys_pl_` | `relsys_pl_filter.py` |
| Ibis backend | `relsys_ib_` | `relsys_ib_filter.py` |
| Narwhals backend | `relsys_nw_` | `relsys_nw_filter.py` |
| Extension nodes | `reln_ext_ma_` | `reln_ext_ma_util.py` |
| Extension protocols | `prtcl_relsys_ext_ma_` | `prtcl_relsys_ext_ma_util.py` |
| Extension backends | `relsys_*_ext_ma_` | `relsys_pl_ext_ma_util.py` |

---

## 7. Wiring Matrix

Every operation must be wired through all layers:

| Operation | Node | Protocol | Polars | Ibis | Narwhals |
|-----------|------|----------|--------|------|----------|
| select | ProjectRelNode(SELECT) | `project_select` | relsys_pl_project | relsys_ib_project | relsys_nw_project |
| with_columns | ProjectRelNode(WITH_COLUMNS) | `project_with_columns` | " | " | " |
| drop | ProjectRelNode(DROP) | `project_drop` | " | " | " |
| rename | ProjectRelNode(RENAME) | `project_rename` | " | " | " |
| filter | FilterRelNode | `filter` | relsys_pl_filter | relsys_ib_filter | relsys_nw_filter |
| sort | SortRelNode | `sort` | relsys_pl_sort | relsys_ib_sort | relsys_nw_sort |
| head | FetchRelNode | `fetch` | relsys_pl_fetch | relsys_ib_fetch | relsys_nw_fetch |
| tail | FetchRelNode(from_end) | `fetch_from_end` | " | " | " |
| slice | FetchRelNode | `fetch` | " | " | " |
| join (7 types) | JoinRelNode | `join` | relsys_pl_join | relsys_ib_join | relsys_nw_join |
| join_asof | JoinRelNode(ASOF) | `join_asof` | " | " | " |
| group_by+agg | AggregateRelNode | `aggregate` | relsys_pl_aggregate | relsys_ib_aggregate | relsys_nw_aggregate |
| unique | AggregateRelNode(empty) | `distinct` | " | " | " |
| concat | SetRelNode(UNION_ALL) | `union_all` | relsys_pl_set | relsys_ib_set | relsys_nw_set |
| drop_nulls | ExtensionRelNode | `drop_nulls` | relsys_pl_ext_ma_util | relsys_ib_ext_ma_util | relsys_nw_ext_ma_util |
| with_row_index | ExtensionRelNode | `with_row_index` | " | " | " |
| explode | ExtensionRelNode | `explode` | " | " | " |
| sample | ExtensionRelNode | `sample` | " | " | " |
| unpivot | ExtensionRelNode | `unpivot` | " | " | " |
| pivot | ExtensionRelNode | `pivot` | " | " | " |
| top_k | ExtensionRelNode | `top_k` | " | " | " |

---

## 8. Testing Strategy

### Test Structure

```
tests/relations/
    conftest.py                       # Fixtures: DataFrames for all backends
    test_rel_nodes.py                 # Node construction, immutability
    test_rel_project.py               # select, with_columns, drop, rename
    test_rel_filter.py                # filter with mountainash exprs, native exprs, multiple
    test_rel_sort.py                  # Single, multi, descending, nulls
    test_rel_fetch.py                 # head, tail, slice
    test_rel_join.py                  # All 7 join types
    test_rel_aggregate.py             # group_by+agg, unique/distinct
    test_rel_set.py                   # concat
    test_rel_ext_util.py              # drop_nulls, with_row_index, explode, sample, etc.
    test_rel_pipeline.py              # Multi-operation chains
    test_rel_cross_type_join.py       # Joins across different backend types
    test_rel_wiring_audit.py          # Automated: every protocol method has backend impl
```

### Cross-Backend Parametrization

```python
RELATION_BACKENDS = ["polars", "ibis_duckdb", "ibis_sqlite", "narwhals_pandas", "narwhals_pyarrow"]

@pytest.fixture(params=RELATION_BACKENDS)
def sample_relation(request):
    """Returns ma.relation(df) where df is the requested backend type."""
    ...
```

### Wiring Audit

```python
class TestRelationWiringAudit:
    def test_no_orphan_protocol_methods(self): ...
    def test_all_node_types_handled_by_visitor(self): ...
    def test_all_operations_have_tests(self): ...
```

### Known Divergences

Use xfail for backend-specific limitations:

```python
@pytest.mark.xfail(condition=backend == "ibis_sqlite", reason="SQLite lacks ASOF joins")
```

---

## 9. Migration & Coexistence

### Dependency Graph

```
mountainash.core ← mountainash.expressions ← mountainash.relations
                 ← mountainash.dataframes  (independent, untouched)
```

### Migration Phases

1. **Parallel systems** — both `ma.table(df)` and `ma.relation(df)` work independently
2. **Test migration** — port overlapping dataframes tests to relations test suite
3. **Deprecate** — `ma.table()` emits DeprecationWarning, points to `ma.relation()`
4. **Remove** — delete `mountainash.dataframes` once all client code migrated

### Reuse vs Rebuild

| Component | Decision |
|-----------|----------|
| `mountainash.core.constants` | Reuse — add relational enums |
| `mountainash.core.types` | Reuse |
| Backend detection | Reuse — `identify_backend()` |
| Expression AST nodes | Reuse — embedded in relational nodes |
| Expression visitor | Reuse — composed inside relation visitor |
| ExpressionSystem backends | Reuse — expression compilation unchanged |
| DataFrameSystem protocols | Rebuild as RelationSystem protocols |
| DataFrameSystem backends | Rebuild as RelationSystem backends |
| TableBuilder | Rebuild as Relation class |
| Cross-type coercion | Extract from DataFrameSystem casts, reuse |
