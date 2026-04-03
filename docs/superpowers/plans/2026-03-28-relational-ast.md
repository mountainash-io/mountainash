# Relational AST Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `mountainash.relations` — a Substrait-aligned relational AST with Polars/Narwhals-aligned API, three backends, and cross-type join support.

**Architecture:** Immutable Pydantic relational nodes form a plan tree. A `Relation` fluent API builds the tree. Terminal operations (`.collect()`, `.to_polars()`, etc.) trigger a `UnifiedRelationVisitor` that walks the tree, compiles embedded expression ASTs via the existing expression visitor, and calls backend-specific `RelationSystem` methods. Three backends: Polars (native), Narwhals (pandas/PyArrow), Ibis (SQL).

**Tech Stack:** Python 3.11+, Pydantic v2, Polars, Narwhals, Ibis, pytest

**Spec:** `docs/superpowers/specs/2026-03-28-relational-ast-design.md`

**Principles (MUST READ before implementation):** Located in `../mountainash-central/01.principles/mountainash-expresions/`:
- `a.architecture/substrait-first-design.md` — Substrait naming, physical separation
- `a.architecture/minimal-ast.md` — Minimal node types, no business logic in nodes
- `a.architecture/three-layer-separation.md` — Protocol → API → Backend, zero upward imports
- `c.api-design/build-then-compile.md` — Build AST first, compile later
- `f.extension-model/backend-composition.md` — Multiple inheritance, composition class body=pass
- `g.development-practices/file-organisation.md` — Mirror structure, naming prefixes
- `g.development-practices/naming-conventions.md` — File prefix conventions

---

## Dependency Graph

```
Task 1 (Enums) ──→ Task 2 (Nodes) ──→ Task 3 (Protocols) ──→ Task 4 (Visitor) ──→ Task 5 (Relation API)
                                                                    │
                                                     ┌──────────────┼──────────────┐
                                                     ▼              ▼              ▼
                                               Task 6         Task 8         Task 10
                                            (Polars BE)    (Narwhals BE)    (Ibis BE)
                                                     │              │              │
                                                     ▼              ▼              ▼
                                               Task 7         Task 9         Task 11
                                           (Polars tests)  (Narwhals tests) (Ibis tests)
                                                     │              │              │
                                                     └──────────────┼──────────────┘
                                                                    ▼
                                                              Task 12
                                                       (Cross-type + Pipeline)
                                                                    │
                                                                    ▼
                                                              Task 13
                                                         (Wiring Audit + Exports)
```

Tasks 6, 8, 10 can run in parallel. Tasks 7, 9, 11 can run in parallel.

---

## Task 1: Foundation — Enums & Supporting Types

**Files:**
- Modify: `src/mountainash/core/constants.py`
- Create: `src/mountainash/relations/__init__.py`
- Create: `src/mountainash/relations/core/__init__.py`
- Create: `src/mountainash/relations/core/relation_nodes/__init__.py`
- Test: `tests/relations/__init__.py`
- Test: `tests/relations/test_rel_enums.py`

- [ ] **Step 1: Write test for relational enums**

```python
# tests/relations/__init__.py
# (empty)

# tests/relations/test_rel_enums.py
"""Tests for relational AST enums and supporting types."""

import pytest
from enum import Enum, StrEnum

from mountainash.core.constants import (
    ProjectOperation,
    JoinType,
    ExecutionTarget,
    SetType,
    ExtensionRelOperation,
    SortField,
)


class TestProjectOperation:
    def test_members(self):
        assert ProjectOperation.SELECT is not None
        assert ProjectOperation.WITH_COLUMNS is not None
        assert ProjectOperation.DROP is not None
        assert ProjectOperation.RENAME is not None

    def test_member_count(self):
        assert len(ProjectOperation) == 4


class TestJoinType:
    def test_is_strenum(self):
        assert issubclass(JoinType, StrEnum)

    def test_string_values(self):
        assert JoinType.INNER == "inner"
        assert JoinType.LEFT == "left"
        assert JoinType.RIGHT == "right"
        assert JoinType.OUTER == "outer"
        assert JoinType.SEMI == "semi"
        assert JoinType.ANTI == "anti"
        assert JoinType.CROSS == "cross"
        assert JoinType.ASOF == "asof"

    def test_member_count(self):
        assert len(JoinType) == 8


class TestExecutionTarget:
    def test_members(self):
        assert ExecutionTarget.LEFT is not None
        assert ExecutionTarget.RIGHT is not None

    def test_member_count(self):
        assert len(ExecutionTarget) == 2


class TestSetType:
    def test_members(self):
        assert SetType.UNION_ALL is not None
        assert SetType.UNION_DISTINCT is not None


class TestExtensionRelOperation:
    def test_members(self):
        assert ExtensionRelOperation.DROP_NULLS is not None
        assert ExtensionRelOperation.WITH_ROW_INDEX is not None
        assert ExtensionRelOperation.EXPLODE is not None
        assert ExtensionRelOperation.SAMPLE is not None
        assert ExtensionRelOperation.UNPIVOT is not None
        assert ExtensionRelOperation.PIVOT is not None
        assert ExtensionRelOperation.TOP_K is not None

    def test_member_count(self):
        assert len(ExtensionRelOperation) == 7


class TestSortField:
    def test_creation(self):
        sf = SortField(column="age")
        assert sf.column == "age"
        assert sf.descending is False
        assert sf.nulls_last is True

    def test_descending(self):
        sf = SortField(column="age", descending=True)
        assert sf.descending is True

    def test_frozen(self):
        sf = SortField(column="age")
        with pytest.raises(AttributeError):
            sf.column = "name"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/relations/test_rel_enums.py -v`
Expected: FAIL — `ImportError: cannot import name 'ProjectOperation' from 'mountainash.core.constants'`

- [ ] **Step 3: Add relational enums to core constants**

Add to `src/mountainash/core/constants.py` (after existing enums):

```python
# --- Relational AST Enums ---

class ProjectOperation(Enum):
    """Variants of the Substrait ProjectRel."""
    SELECT = auto()
    WITH_COLUMNS = auto()
    DROP = auto()
    RENAME = auto()


class JoinType(StrEnum):
    """Join types aligned with Substrait JoinRel."""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    OUTER = "outer"
    SEMI = "semi"
    ANTI = "anti"
    CROSS = "cross"
    ASOF = "asof"


class ExecutionTarget(Enum):
    """Which side of a join to execute on."""
    LEFT = auto()
    RIGHT = auto()


class SetType(Enum):
    """Substrait SetRel operation types."""
    UNION_ALL = auto()
    UNION_DISTINCT = auto()


class ExtensionRelOperation(Enum):
    """Mountainash extension relation operations (not in Substrait)."""
    DROP_NULLS = auto()
    WITH_ROW_INDEX = auto()
    EXPLODE = auto()
    SAMPLE = auto()
    UNPIVOT = auto()
    PIVOT = auto()
    TOP_K = auto()
```

Add `SortField` as a frozen dataclass in the same file:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SortField:
    """A single sort specification."""
    column: str
    descending: bool = False
    nulls_last: bool = True
```

- [ ] **Step 4: Create empty package directories**

```bash
mkdir -p src/mountainash/relations/core/relation_nodes/substrait
mkdir -p src/mountainash/relations/core/relation_nodes/extensions_mountainash
mkdir -p src/mountainash/relations/core/relation_protocols/relation_systems/substrait
mkdir -p src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash
mkdir -p src/mountainash/relations/core/relation_api
mkdir -p src/mountainash/relations/core/unified_visitor
mkdir -p src/mountainash/relations/backends/relation_systems/polars/substrait
mkdir -p src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash
mkdir -p src/mountainash/relations/backends/relation_systems/ibis/substrait
mkdir -p src/mountainash/relations/backends/relation_systems/ibis/extensions_mountainash
mkdir -p src/mountainash/relations/backends/relation_systems/narwhals/substrait
mkdir -p src/mountainash/relations/backends/relation_systems/narwhals/extensions_mountainash
mkdir -p tests/relations
```

Create `__init__.py` files in every new directory. These are all empty files:

```bash
touch src/mountainash/relations/__init__.py
touch src/mountainash/relations/core/__init__.py
touch src/mountainash/relations/core/relation_nodes/__init__.py
touch src/mountainash/relations/core/relation_nodes/substrait/__init__.py
touch src/mountainash/relations/core/relation_nodes/extensions_mountainash/__init__.py
touch src/mountainash/relations/core/relation_protocols/__init__.py
touch src/mountainash/relations/core/relation_protocols/relation_systems/__init__.py
touch src/mountainash/relations/core/relation_protocols/relation_systems/substrait/__init__.py
touch src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/__init__.py
touch src/mountainash/relations/core/relation_api/__init__.py
touch src/mountainash/relations/core/unified_visitor/__init__.py
touch src/mountainash/relations/backends/__init__.py
touch src/mountainash/relations/backends/relation_systems/__init__.py
touch src/mountainash/relations/backends/relation_systems/polars/__init__.py
touch src/mountainash/relations/backends/relation_systems/polars/substrait/__init__.py
touch src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash/__init__.py
touch src/mountainash/relations/backends/relation_systems/ibis/__init__.py
touch src/mountainash/relations/backends/relation_systems/ibis/substrait/__init__.py
touch src/mountainash/relations/backends/relation_systems/ibis/extensions_mountainash/__init__.py
touch src/mountainash/relations/backends/relation_systems/narwhals/__init__.py
touch src/mountainash/relations/backends/relation_systems/narwhals/substrait/__init__.py
touch src/mountainash/relations/backends/relation_systems/narwhals/extensions_mountainash/__init__.py
touch tests/relations/__init__.py
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `hatch run test:test-target tests/relations/test_rel_enums.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/core/constants.py src/mountainash/relations/ tests/relations/
git commit -m "feat(relations): add relational enums, SortField, and package skeleton"
```

---

## Task 2: Relational Node Types

**Files:**
- Create: `src/mountainash/relations/core/relation_nodes/reln_base.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_read.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_project.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_filter.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_sort.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_fetch.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_join.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_aggregate.py`
- Create: `src/mountainash/relations/core/relation_nodes/substrait/reln_set.py`
- Create: `src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_ma_util.py`
- Test: `tests/relations/test_rel_nodes.py`

- [ ] **Step 1: Write tests for all node types**

```python
# tests/relations/test_rel_nodes.py
"""Tests for relational AST node types."""

import pytest
from pydantic import ValidationError

from mountainash.core.constants import (
    ProjectOperation,
    JoinType,
    ExecutionTarget,
    SetType,
    ExtensionRelOperation,
    SortField,
)
from mountainash.relations.core.relation_nodes import (
    RelationNode,
    ReadRelNode,
    ProjectRelNode,
    FilterRelNode,
    SortRelNode,
    FetchRelNode,
    JoinRelNode,
    AggregateRelNode,
    SetRelNode,
    ExtensionRelNode,
)


class TestReadRelNode:
    def test_creation(self):
        node = ReadRelNode(dataframe="placeholder_df")
        assert node.dataframe == "placeholder_df"

    def test_accept(self):
        class MockVisitor:
            def visit_read_rel(self, node):
                return "visited_read"

        node = ReadRelNode(dataframe="df")
        assert node.accept(MockVisitor()) == "visited_read"

    def test_is_relation_node(self):
        node = ReadRelNode(dataframe="df")
        assert isinstance(node, RelationNode)


class TestProjectRelNode:
    def test_select(self):
        read = ReadRelNode(dataframe="df")
        node = ProjectRelNode(
            input=read,
            expressions=[],
            operation=ProjectOperation.SELECT,
        )
        assert node.operation == ProjectOperation.SELECT
        assert node.rename_mapping is None

    def test_rename(self):
        read = ReadRelNode(dataframe="df")
        node = ProjectRelNode(
            input=read,
            expressions=[],
            operation=ProjectOperation.RENAME,
            rename_mapping={"old": "new"},
        )
        assert node.rename_mapping == {"old": "new"}

    def test_accept(self):
        class MockVisitor:
            def visit_project_rel(self, node):
                return "visited_project"

        read = ReadRelNode(dataframe="df")
        node = ProjectRelNode(input=read, expressions=[], operation=ProjectOperation.SELECT)
        assert node.accept(MockVisitor()) == "visited_project"


class TestFilterRelNode:
    def test_creation(self):
        read = ReadRelNode(dataframe="df")
        node = FilterRelNode(input=read, predicate="some_predicate")
        assert node.predicate == "some_predicate"

    def test_accept(self):
        class MockVisitor:
            def visit_filter_rel(self, node):
                return "visited_filter"

        read = ReadRelNode(dataframe="df")
        node = FilterRelNode(input=read, predicate="pred")
        assert node.accept(MockVisitor()) == "visited_filter"


class TestSortRelNode:
    def test_creation(self):
        read = ReadRelNode(dataframe="df")
        fields = [SortField(column="age", descending=True)]
        node = SortRelNode(input=read, sort_fields=fields)
        assert len(node.sort_fields) == 1
        assert node.sort_fields[0].column == "age"
        assert node.sort_fields[0].descending is True

    def test_accept(self):
        class MockVisitor:
            def visit_sort_rel(self, node):
                return "visited_sort"

        read = ReadRelNode(dataframe="df")
        node = SortRelNode(input=read, sort_fields=[SortField(column="x")])
        assert node.accept(MockVisitor()) == "visited_sort"


class TestFetchRelNode:
    def test_head(self):
        read = ReadRelNode(dataframe="df")
        node = FetchRelNode(input=read, count=10)
        assert node.offset == 0
        assert node.count == 10
        assert node.from_end is False

    def test_tail(self):
        read = ReadRelNode(dataframe="df")
        node = FetchRelNode(input=read, count=5, from_end=True)
        assert node.from_end is True

    def test_slice(self):
        read = ReadRelNode(dataframe="df")
        node = FetchRelNode(input=read, offset=10, count=20)
        assert node.offset == 10
        assert node.count == 20

    def test_accept(self):
        class MockVisitor:
            def visit_fetch_rel(self, node):
                return "visited_fetch"

        read = ReadRelNode(dataframe="df")
        node = FetchRelNode(input=read, count=5)
        assert node.accept(MockVisitor()) == "visited_fetch"


class TestJoinRelNode:
    def test_inner_join(self):
        left = ReadRelNode(dataframe="left_df")
        right = ReadRelNode(dataframe="right_df")
        node = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.INNER,
            on=["id"],
        )
        assert node.join_type == JoinType.INNER
        assert node.on == ["id"]
        assert node.suffix == "_right"
        assert node.execute_on is None

    def test_asof_join(self):
        left = ReadRelNode(dataframe="left_df")
        right = ReadRelNode(dataframe="right_df")
        node = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.ASOF,
            on=["timestamp"],
            strategy="backward",
        )
        assert node.join_type == JoinType.ASOF
        assert node.strategy == "backward"

    def test_execute_on(self):
        left = ReadRelNode(dataframe="left_df")
        right = ReadRelNode(dataframe="right_df")
        node = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.LEFT,
            on=["id"],
            execute_on=ExecutionTarget.LEFT,
        )
        assert node.execute_on == ExecutionTarget.LEFT

    def test_accept(self):
        class MockVisitor:
            def visit_join_rel(self, node):
                return "visited_join"

        left = ReadRelNode(dataframe="l")
        right = ReadRelNode(dataframe="r")
        node = JoinRelNode(left=left, right=right, join_type=JoinType.INNER, on=["id"])
        assert node.accept(MockVisitor()) == "visited_join"


class TestAggregateRelNode:
    def test_group_by_agg(self):
        read = ReadRelNode(dataframe="df")
        node = AggregateRelNode(
            input=read,
            keys=["category"],
            measures=["sum_expr", "mean_expr"],
        )
        assert node.keys == ["category"]
        assert len(node.measures) == 2

    def test_distinct(self):
        read = ReadRelNode(dataframe="df")
        node = AggregateRelNode(input=read, keys=["id", "name"], measures=[])
        assert node.measures == []

    def test_accept(self):
        class MockVisitor:
            def visit_aggregate_rel(self, node):
                return "visited_aggregate"

        read = ReadRelNode(dataframe="df")
        node = AggregateRelNode(input=read, keys=["x"], measures=[])
        assert node.accept(MockVisitor()) == "visited_aggregate"


class TestSetRelNode:
    def test_union_all(self):
        r1 = ReadRelNode(dataframe="df1")
        r2 = ReadRelNode(dataframe="df2")
        node = SetRelNode(inputs=[r1, r2], set_type=SetType.UNION_ALL)
        assert len(node.inputs) == 2
        assert node.set_type == SetType.UNION_ALL

    def test_accept(self):
        class MockVisitor:
            def visit_set_rel(self, node):
                return "visited_set"

        r1 = ReadRelNode(dataframe="df1")
        node = SetRelNode(inputs=[r1], set_type=SetType.UNION_ALL)
        assert node.accept(MockVisitor()) == "visited_set"


class TestExtensionRelNode:
    def test_drop_nulls(self):
        read = ReadRelNode(dataframe="df")
        node = ExtensionRelNode(
            input=read,
            operation=ExtensionRelOperation.DROP_NULLS,
            options={"subset": ["a", "b"]},
        )
        assert node.operation == ExtensionRelOperation.DROP_NULLS
        assert node.options["subset"] == ["a", "b"]

    def test_sample(self):
        read = ReadRelNode(dataframe="df")
        node = ExtensionRelNode(
            input=read,
            operation=ExtensionRelOperation.SAMPLE,
            options={"n": 100},
        )
        assert node.options["n"] == 100

    def test_accept(self):
        class MockVisitor:
            def visit_extension_rel(self, node):
                return "visited_extension"

        read = ReadRelNode(dataframe="df")
        node = ExtensionRelNode(input=read, operation=ExtensionRelOperation.EXPLODE, options={"columns": ["tags"]})
        assert node.accept(MockVisitor()) == "visited_extension"


class TestNodeChaining:
    """Test that nodes can be composed into plan trees."""

    def test_filter_then_sort(self):
        read = ReadRelNode(dataframe="df")
        filtered = FilterRelNode(input=read, predicate="age > 30")
        sorted_node = SortRelNode(input=filtered, sort_fields=[SortField(column="name")])
        assert isinstance(sorted_node.input, FilterRelNode)
        assert isinstance(sorted_node.input.input, ReadRelNode)

    def test_deep_chain(self):
        """filter → sort → head → project"""
        read = ReadRelNode(dataframe="df")
        filtered = FilterRelNode(input=read, predicate="pred")
        sorted_node = SortRelNode(input=filtered, sort_fields=[SortField(column="x")])
        fetched = FetchRelNode(input=sorted_node, count=10)
        projected = ProjectRelNode(input=fetched, expressions=[], operation=ProjectOperation.SELECT)
        # Walk up the chain
        assert isinstance(projected.input, FetchRelNode)
        assert isinstance(projected.input.input, SortRelNode)
        assert isinstance(projected.input.input.input, FilterRelNode)
        assert isinstance(projected.input.input.input.input, ReadRelNode)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/relations/test_rel_nodes.py -v`
Expected: FAIL — `ImportError: cannot import name 'RelationNode'`

- [ ] **Step 3: Implement RelationNode base**

```python
# src/mountainash/relations/core/relation_nodes/reln_base.py
"""Base class for relational AST nodes.

Mirrors the expression node pattern from mountainash.expressions.
All relational nodes are immutable Pydantic models with visitor dispatch.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class RelationNode(BaseModel, ABC):
    """Abstract base for all relational AST nodes.

    Each subclass maps to a Substrait logical relation:
    - ReadRelNode → Read
    - ProjectRelNode → Project
    - FilterRelNode → Filter
    - SortRelNode → Sort
    - FetchRelNode → Fetch
    - JoinRelNode → Join
    - AggregateRelNode → Aggregate
    - SetRelNode → Set
    - ExtensionRelNode → Mountainash extension
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    @abstractmethod
    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        ...
```

- [ ] **Step 4: Implement all Substrait-aligned nodes**

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_read.py
"""Read relation node — leaf of the plan tree."""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode


class ReadRelNode(RelationNode):
    """Wraps a native DataFrame as the entry point of a relational plan."""

    dataframe: Any

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_read_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_project.py
"""Project relation node — select, with_columns, drop, rename."""

from __future__ import annotations
from typing import Any, Optional

from ..reln_base import RelationNode
from mountainash.core.constants import ProjectOperation


class ProjectRelNode(RelationNode):
    """Maps to Substrait ProjectRel. Handles select, with_columns, drop, rename."""

    input: RelationNode
    expressions: list[Any]
    operation: ProjectOperation
    rename_mapping: Optional[dict[str, str]] = None

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_project_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_filter.py
"""Filter relation node — row filtering by predicate."""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode


class FilterRelNode(RelationNode):
    """Maps to Substrait FilterRel."""

    input: RelationNode
    predicate: Any  # ExpressionNode or native backend expression

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_filter_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_sort.py
"""Sort relation node."""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode
from mountainash.core.constants import SortField


class SortRelNode(RelationNode):
    """Maps to Substrait SortRel."""

    input: RelationNode
    sort_fields: list[SortField]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_sort_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_fetch.py
"""Fetch relation node — head, tail, slice."""

from __future__ import annotations
from typing import Any, Optional

from ..reln_base import RelationNode


class FetchRelNode(RelationNode):
    """Maps to Substrait FetchRel."""

    input: RelationNode
    offset: int = 0
    count: Optional[int] = None
    from_end: bool = False

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_fetch_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_join.py
"""Join relation node — all join types including asof."""

from __future__ import annotations
from typing import Any, Optional

from ..reln_base import RelationNode
from mountainash.core.constants import JoinType, ExecutionTarget


class JoinRelNode(RelationNode):
    """Maps to Substrait JoinRel."""

    left: RelationNode
    right: RelationNode
    join_type: JoinType
    on: Optional[list[str]] = None
    left_on: Optional[list[str]] = None
    right_on: Optional[list[str]] = None
    suffix: str = "_right"
    strategy: Optional[str] = None
    tolerance: Any = None
    execute_on: Optional[ExecutionTarget] = None

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_join_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_aggregate.py
"""Aggregate relation node — group_by+agg, distinct."""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode


class AggregateRelNode(RelationNode):
    """Maps to Substrait AggregateRel. Empty measures = DISTINCT."""

    input: RelationNode
    keys: list[Any]  # str column names or ExpressionNode
    measures: list[Any]  # ExpressionNode or native expressions

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_aggregate_rel(self)
```

```python
# src/mountainash/relations/core/relation_nodes/substrait/reln_set.py
"""Set relation node — union, concat."""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode
from mountainash.core.constants import SetType


class SetRelNode(RelationNode):
    """Maps to Substrait SetRel."""

    inputs: list[RelationNode]
    set_type: SetType

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_set_rel(self)
```

- [ ] **Step 5: Implement extension node**

```python
# src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_ma_util.py
"""Extension relation node — non-Substrait operations."""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode
from mountainash.core.constants import ExtensionRelOperation


class ExtensionRelNode(RelationNode):
    """Mountainash extension operations not in Substrait spec."""

    input: RelationNode
    operation: ExtensionRelOperation
    options: dict[str, Any] = {}

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_extension_rel(self)
```

- [ ] **Step 6: Update `__init__.py` re-exports**

```python
# src/mountainash/relations/core/relation_nodes/substrait/__init__.py
from .reln_read import ReadRelNode
from .reln_project import ProjectRelNode
from .reln_filter import FilterRelNode
from .reln_sort import SortRelNode
from .reln_fetch import FetchRelNode
from .reln_join import JoinRelNode
from .reln_aggregate import AggregateRelNode
from .reln_set import SetRelNode

__all__ = [
    "ReadRelNode",
    "ProjectRelNode",
    "FilterRelNode",
    "SortRelNode",
    "FetchRelNode",
    "JoinRelNode",
    "AggregateRelNode",
    "SetRelNode",
]
```

```python
# src/mountainash/relations/core/relation_nodes/extensions_mountainash/__init__.py
from .reln_ext_ma_util import ExtensionRelNode

__all__ = ["ExtensionRelNode"]
```

```python
# src/mountainash/relations/core/relation_nodes/__init__.py
from .reln_base import RelationNode
from .substrait import (
    ReadRelNode,
    ProjectRelNode,
    FilterRelNode,
    SortRelNode,
    FetchRelNode,
    JoinRelNode,
    AggregateRelNode,
    SetRelNode,
)
from .extensions_mountainash import ExtensionRelNode

__all__ = [
    "RelationNode",
    "ReadRelNode",
    "ProjectRelNode",
    "FilterRelNode",
    "SortRelNode",
    "FetchRelNode",
    "JoinRelNode",
    "AggregateRelNode",
    "SetRelNode",
    "ExtensionRelNode",
]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `hatch run test:test-target tests/relations/test_rel_nodes.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/relations/core/relation_nodes/ tests/relations/test_rel_nodes.py
git commit -m "feat(relations): add 10 relational AST node types"
```

---

## Task 3: Protocols

**Files:**
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_read.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_project.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_filter.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_sort.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_fetch.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_join.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_aggregate.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_set.py`
- Create: `src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/prtcl_relsys_ext_ma_util.py`
- Create: `src/mountainash/relations/core/relation_protocols/relsys_base.py`
- Test: `tests/relations/test_rel_protocols.py`

- [ ] **Step 1: Write tests that verify protocol structure**

```python
# tests/relations/test_rel_protocols.py
"""Tests for relational system protocol definitions."""

import inspect
import pytest

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
)
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)
from mountainash.relations.core.relation_protocols.relsys_base import RelationSystem


class TestProtocolMethods:
    """Verify each protocol defines expected methods."""

    def test_read_protocol(self):
        assert hasattr(SubstraitReadRelationSystemProtocol, "read")

    def test_project_protocol(self):
        for method in ["project_select", "project_with_columns", "project_drop", "project_rename"]:
            assert hasattr(SubstraitProjectRelationSystemProtocol, method), f"Missing: {method}"

    def test_filter_protocol(self):
        assert hasattr(SubstraitFilterRelationSystemProtocol, "filter")

    def test_sort_protocol(self):
        assert hasattr(SubstraitSortRelationSystemProtocol, "sort")

    def test_fetch_protocol(self):
        for method in ["fetch", "fetch_from_end"]:
            assert hasattr(SubstraitFetchRelationSystemProtocol, method), f"Missing: {method}"

    def test_join_protocol(self):
        for method in ["join", "join_asof"]:
            assert hasattr(SubstraitJoinRelationSystemProtocol, method), f"Missing: {method}"

    def test_aggregate_protocol(self):
        for method in ["aggregate", "distinct"]:
            assert hasattr(SubstraitAggregateRelationSystemProtocol, method), f"Missing: {method}"

    def test_set_protocol(self):
        assert hasattr(SubstraitSetRelationSystemProtocol, "union_all")

    def test_extension_protocol(self):
        for method in ["drop_nulls", "with_row_index", "explode", "sample", "unpivot", "pivot", "top_k"]:
            assert hasattr(MountainashExtensionRelationSystemProtocol, method), f"Missing: {method}"


class TestRelationSystemBase:
    """Verify the base class composes all protocols."""

    def test_inherits_all_substrait_protocols(self):
        assert issubclass(RelationSystem, SubstraitReadRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitProjectRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitFilterRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitSortRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitFetchRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitJoinRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitAggregateRelationSystemProtocol)
        assert issubclass(RelationSystem, SubstraitSetRelationSystemProtocol)

    def test_inherits_extension_protocol(self):
        assert issubclass(RelationSystem, MountainashExtensionRelationSystemProtocol)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/relations/test_rel_protocols.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement all protocol files**

Each protocol is a `Protocol` class with abstract method signatures. The methods take and return `Any` — backends fill in native types. Here are all 9 files:

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_read.py
"""Protocol for read relation operations."""

from __future__ import annotations
from typing import Any, Protocol


class SubstraitReadRelationSystemProtocol(Protocol):
    """Read: convert native DataFrame to backend's working format."""

    def read(self, dataframe: Any, /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_project.py
"""Protocol for project relation operations."""

from __future__ import annotations
from typing import Any, Optional, Protocol


class SubstraitProjectRelationSystemProtocol(Protocol):
    """Project: select, with_columns, drop, rename."""

    def project_select(self, relation: Any, columns: list[Any], /) -> Any: ...

    def project_with_columns(self, relation: Any, expressions: list[Any], /) -> Any: ...

    def project_drop(self, relation: Any, columns: list[Any], /) -> Any: ...

    def project_rename(self, relation: Any, mapping: dict[str, str], /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_filter.py
"""Protocol for filter relation operations."""

from __future__ import annotations
from typing import Any, Protocol


class SubstraitFilterRelationSystemProtocol(Protocol):
    """Filter: eliminate rows based on predicate."""

    def filter(self, relation: Any, predicate: Any, /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_sort.py
"""Protocol for sort relation operations."""

from __future__ import annotations
from typing import Any, Protocol

from mountainash.core.constants import SortField


class SubstraitSortRelationSystemProtocol(Protocol):
    """Sort: reorder rows by sort fields."""

    def sort(self, relation: Any, sort_fields: list[SortField], /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_fetch.py
"""Protocol for fetch relation operations."""

from __future__ import annotations
from typing import Any, Optional, Protocol


class SubstraitFetchRelationSystemProtocol(Protocol):
    """Fetch: offset/limit (head, tail, slice)."""

    def fetch(self, relation: Any, offset: int, count: Optional[int], /) -> Any: ...

    def fetch_from_end(self, relation: Any, count: int, /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_join.py
"""Protocol for join relation operations."""

from __future__ import annotations
from typing import Any, Optional, Protocol

from mountainash.core.constants import JoinType


class SubstraitJoinRelationSystemProtocol(Protocol):
    """Join: combine two relations."""

    def join(
        self,
        left: Any,
        right: Any,
        *,
        join_type: JoinType,
        on: Optional[list[str]],
        left_on: Optional[list[str]],
        right_on: Optional[list[str]],
        suffix: str,
    ) -> Any: ...

    def join_asof(
        self,
        left: Any,
        right: Any,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_aggregate.py
"""Protocol for aggregate relation operations."""

from __future__ import annotations
from typing import Any, Protocol


class SubstraitAggregateRelationSystemProtocol(Protocol):
    """Aggregate: group_by+agg, distinct."""

    def aggregate(self, relation: Any, keys: list[Any], measures: list[Any], /) -> Any: ...

    def distinct(self, relation: Any, columns: list[Any], /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/prtcl_relsys_set.py
"""Protocol for set relation operations."""

from __future__ import annotations
from typing import Any, Protocol


class SubstraitSetRelationSystemProtocol(Protocol):
    """Set: union, concat."""

    def union_all(self, relations: list[Any], /) -> Any: ...
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/prtcl_relsys_ext_ma_util.py
"""Protocol for Mountainash extension relation operations."""

from __future__ import annotations
from typing import Any, Optional, Protocol


class MountainashExtensionRelationSystemProtocol(Protocol):
    """Non-Substrait operations."""

    def drop_nulls(self, relation: Any, /, *, subset: Optional[list[str]] = None) -> Any: ...

    def with_row_index(self, relation: Any, /, *, name: str = "index") -> Any: ...

    def explode(self, relation: Any, /, *, columns: list[str]) -> Any: ...

    def sample(self, relation: Any, /, *, n: Optional[int] = None, fraction: Optional[float] = None) -> Any: ...

    def unpivot(
        self,
        relation: Any,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> Any: ...

    def pivot(
        self,
        relation: Any,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> Any: ...

    def top_k(self, relation: Any, /, *, k: int, by: str, descending: bool = True) -> Any: ...
```

- [ ] **Step 4: Add `__init__.py` re-exports for protocols**

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/substrait/__init__.py
from .prtcl_relsys_read import SubstraitReadRelationSystemProtocol
from .prtcl_relsys_project import SubstraitProjectRelationSystemProtocol
from .prtcl_relsys_filter import SubstraitFilterRelationSystemProtocol
from .prtcl_relsys_sort import SubstraitSortRelationSystemProtocol
from .prtcl_relsys_fetch import SubstraitFetchRelationSystemProtocol
from .prtcl_relsys_join import SubstraitJoinRelationSystemProtocol
from .prtcl_relsys_aggregate import SubstraitAggregateRelationSystemProtocol
from .prtcl_relsys_set import SubstraitSetRelationSystemProtocol

__all__ = [
    "SubstraitReadRelationSystemProtocol",
    "SubstraitProjectRelationSystemProtocol",
    "SubstraitFilterRelationSystemProtocol",
    "SubstraitSortRelationSystemProtocol",
    "SubstraitFetchRelationSystemProtocol",
    "SubstraitJoinRelationSystemProtocol",
    "SubstraitAggregateRelationSystemProtocol",
    "SubstraitSetRelationSystemProtocol",
]
```

```python
# src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/__init__.py
from .prtcl_relsys_ext_ma_util import MountainashExtensionRelationSystemProtocol

__all__ = ["MountainashExtensionRelationSystemProtocol"]
```

- [ ] **Step 5: Implement RelationSystem base class with registry**

```python
# src/mountainash/relations/core/relation_protocols/relsys_base.py
"""Base RelationSystem class and registry.

Mirrors the expression system pattern from mountainash.expressions.
"""

from __future__ import annotations
from abc import abstractmethod
from typing import Any, Dict, Type, TYPE_CHECKING

from mountainash.core.constants import CONST_BACKEND

from .relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
)
from .relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)


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
    """Abstract base composing all relation protocol interfaces."""

    @property
    @abstractmethod
    def backend_type(self) -> CONST_BACKEND:
        """Return the backend type constant for this RelationSystem."""
        ...


# Registry
_relation_system_registry: Dict[str, Type[RelationSystem]] = {}


def register_relation_system(backend: CONST_BACKEND):
    """Decorator for registering RelationSystem classes."""
    def decorator(cls: Type[RelationSystem]) -> Type[RelationSystem]:
        _relation_system_registry[backend.value] = cls
        return cls
    return decorator


def get_relation_system(backend: CONST_BACKEND) -> Type[RelationSystem]:
    """Get the RelationSystem class for a backend."""
    if backend.value not in _relation_system_registry:
        raise KeyError(
            f"No RelationSystem registered for backend '{backend.value}'. "
            f"Registered: {list(_relation_system_registry.keys())}"
        )
    return _relation_system_registry[backend.value]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `hatch run test:test-target tests/relations/test_rel_protocols.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/relations/core/relation_protocols/ tests/relations/test_rel_protocols.py
git commit -m "feat(relations): add 9 relation system protocols and base registry"
```

---

## Task 4: Unified Relation Visitor

**Files:**
- Create: `src/mountainash/relations/core/unified_visitor/relation_visitor.py`
- Test: `tests/relations/test_rel_visitor.py`

- [ ] **Step 1: Write visitor tests with mock backends**

```python
# tests/relations/test_rel_visitor.py
"""Tests for the UnifiedRelationVisitor."""

import pytest

from mountainash.core.constants import (
    ProjectOperation,
    JoinType,
    SetType,
    SortField,
    ExtensionRelOperation,
)
from mountainash.relations.core.relation_nodes import (
    ReadRelNode,
    ProjectRelNode,
    FilterRelNode,
    SortRelNode,
    FetchRelNode,
    JoinRelNode,
    AggregateRelNode,
    SetRelNode,
    ExtensionRelNode,
)
from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor


class MockRelationSystem:
    """Minimal mock that records calls."""

    def __init__(self):
        self.calls = []

    def read(self, dataframe):
        self.calls.append(("read", dataframe))
        return f"read({dataframe})"

    def project_select(self, relation, columns):
        self.calls.append(("project_select", relation, columns))
        return f"select({relation})"

    def project_with_columns(self, relation, expressions):
        self.calls.append(("project_with_columns", relation, expressions))
        return f"with_columns({relation})"

    def project_drop(self, relation, columns):
        self.calls.append(("project_drop", relation, columns))
        return f"drop({relation})"

    def project_rename(self, relation, mapping):
        self.calls.append(("project_rename", relation, mapping))
        return f"rename({relation})"

    def filter(self, relation, predicate):
        self.calls.append(("filter", relation, predicate))
        return f"filter({relation})"

    def sort(self, relation, sort_fields):
        self.calls.append(("sort", relation, sort_fields))
        return f"sort({relation})"

    def fetch(self, relation, offset, count):
        self.calls.append(("fetch", relation, offset, count))
        return f"fetch({relation})"

    def fetch_from_end(self, relation, count):
        self.calls.append(("fetch_from_end", relation, count))
        return f"fetch_end({relation})"

    def join(self, left, right, *, join_type, on, left_on, right_on, suffix):
        self.calls.append(("join", left, right))
        return f"join({left},{right})"

    def join_asof(self, left, right, *, on, by, strategy, tolerance):
        self.calls.append(("join_asof", left, right))
        return f"asof({left},{right})"

    def aggregate(self, relation, keys, measures):
        self.calls.append(("aggregate", relation, keys, measures))
        return f"agg({relation})"

    def distinct(self, relation, columns):
        self.calls.append(("distinct", relation, columns))
        return f"distinct({relation})"

    def union_all(self, relations):
        self.calls.append(("union_all", relations))
        return f"union({relations})"

    def drop_nulls(self, relation, *, subset=None):
        self.calls.append(("drop_nulls", relation))
        return f"drop_nulls({relation})"

    def with_row_index(self, relation, *, name="index"):
        self.calls.append(("with_row_index", relation))
        return f"row_idx({relation})"

    def explode(self, relation, *, columns):
        self.calls.append(("explode", relation))
        return f"explode({relation})"

    def sample(self, relation, *, n=None, fraction=None):
        self.calls.append(("sample", relation))
        return f"sample({relation})"

    def unpivot(self, relation, *, on, index=None, variable_name="variable", value_name="value"):
        self.calls.append(("unpivot", relation))
        return f"unpivot({relation})"

    def pivot(self, relation, *, on, index=None, values=None, aggregate_function="first"):
        self.calls.append(("pivot", relation))
        return f"pivot({relation})"

    def top_k(self, relation, *, k, by, descending=True):
        self.calls.append(("top_k", relation))
        return f"top_k({relation})"


class MockExpressionVisitor:
    """Mock that returns expressions unchanged."""

    def visit(self, node):
        return f"compiled({node})"


@pytest.fixture
def visitor():
    backend = MockRelationSystem()
    expr_visitor = MockExpressionVisitor()
    return UnifiedRelationVisitor(backend, expr_visitor), backend


class TestVisitorReadRel:
    def test_read(self, visitor):
        v, backend = visitor
        node = ReadRelNode(dataframe="my_df")
        result = v.visit(node)
        assert result == "read(my_df)"
        assert backend.calls[0][0] == "read"


class TestVisitorFilterRel:
    def test_filter(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = FilterRelNode(input=read, predicate="native_pred")
        result = v.visit(node)
        assert "filter" in result
        assert backend.calls[0][0] == "read"
        assert backend.calls[1][0] == "filter"


class TestVisitorSortRel:
    def test_sort(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        fields = [SortField(column="age", descending=True)]
        node = SortRelNode(input=read, sort_fields=fields)
        result = v.visit(node)
        assert "sort" in result


class TestVisitorFetchRel:
    def test_head(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = FetchRelNode(input=read, count=10)
        result = v.visit(node)
        assert "fetch" in result

    def test_tail(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = FetchRelNode(input=read, count=5, from_end=True)
        result = v.visit(node)
        assert "fetch_end" in result


class TestVisitorJoinRel:
    def test_inner_join(self, visitor):
        v, backend = visitor
        left = ReadRelNode(dataframe="left")
        right = ReadRelNode(dataframe="right")
        node = JoinRelNode(left=left, right=right, join_type=JoinType.INNER, on=["id"])
        result = v.visit(node)
        assert "join" in result

    def test_asof_join(self, visitor):
        v, backend = visitor
        left = ReadRelNode(dataframe="left")
        right = ReadRelNode(dataframe="right")
        node = JoinRelNode(
            left=left, right=right, join_type=JoinType.ASOF,
            on=["ts"], strategy="backward",
        )
        result = v.visit(node)
        assert "asof" in result


class TestVisitorAggregateRel:
    def test_aggregate(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = AggregateRelNode(input=read, keys=["cat"], measures=["sum_expr"])
        result = v.visit(node)
        assert "agg" in result

    def test_distinct(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = AggregateRelNode(input=read, keys=["id"], measures=[])
        result = v.visit(node)
        assert "distinct" in result


class TestVisitorSetRel:
    def test_union(self, visitor):
        v, backend = visitor
        r1 = ReadRelNode(dataframe="df1")
        r2 = ReadRelNode(dataframe="df2")
        node = SetRelNode(inputs=[r1, r2], set_type=SetType.UNION_ALL)
        result = v.visit(node)
        assert "union" in result


class TestVisitorExtensionRel:
    def test_drop_nulls(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = ExtensionRelNode(input=read, operation=ExtensionRelOperation.DROP_NULLS, options={"subset": ["a"]})
        result = v.visit(node)
        assert "drop_nulls" in result

    def test_sample(self, visitor):
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        node = ExtensionRelNode(input=read, operation=ExtensionRelOperation.SAMPLE, options={"n": 10})
        result = v.visit(node)
        assert "sample" in result


class TestVisitorChainedPlan:
    def test_filter_sort_head(self, visitor):
        """read → filter → sort → head"""
        v, backend = visitor
        read = ReadRelNode(dataframe="df")
        filtered = FilterRelNode(input=read, predicate="pred")
        sorted_node = SortRelNode(input=filtered, sort_fields=[SortField(column="x")])
        fetched = FetchRelNode(input=sorted_node, count=10)
        result = v.visit(fetched)
        call_ops = [c[0] for c in backend.calls]
        assert call_ops == ["read", "filter", "sort", "fetch"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/relations/test_rel_visitor.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement UnifiedRelationVisitor**

```python
# src/mountainash/relations/core/unified_visitor/relation_visitor.py
"""Unified relation visitor for relational AST nodes.

Walks the relational plan tree and calls backend RelationSystem methods.
Delegates expression compilation to the expression visitor.
"""

from __future__ import annotations
from typing import Any

from mountainash.core.constants import JoinType, ProjectOperation
from mountainash.expressions.core.expression_nodes import ExpressionNode

from ..relation_nodes import (
    RelationNode,
    ReadRelNode,
    ProjectRelNode,
    FilterRelNode,
    SortRelNode,
    FetchRelNode,
    JoinRelNode,
    AggregateRelNode,
    SetRelNode,
    ExtensionRelNode,
)


class UnifiedRelationVisitor:
    """Walks a relational AST and produces backend-native results.

    Composes with the expression visitor to compile embedded expression ASTs.
    """

    def __init__(self, relation_system: Any, expression_visitor: Any) -> None:
        self.backend = relation_system
        self.expr_visitor = expression_visitor

    def visit(self, node: RelationNode) -> Any:
        return node.accept(self)

    def visit_read_rel(self, node: ReadRelNode) -> Any:
        return self.backend.read(node.dataframe)

    def visit_project_rel(self, node: ProjectRelNode) -> Any:
        relation = self.visit(node.input)
        compiled_exprs = [self._compile_expression(e) for e in node.expressions]
        match node.operation:
            case ProjectOperation.SELECT:
                return self.backend.project_select(relation, compiled_exprs)
            case ProjectOperation.WITH_COLUMNS:
                return self.backend.project_with_columns(relation, compiled_exprs)
            case ProjectOperation.DROP:
                return self.backend.project_drop(relation, compiled_exprs)
            case ProjectOperation.RENAME:
                return self.backend.project_rename(relation, node.rename_mapping)

    def visit_filter_rel(self, node: FilterRelNode) -> Any:
        relation = self.visit(node.input)
        predicate = self._compile_expression(node.predicate)
        return self.backend.filter(relation, predicate)

    def visit_sort_rel(self, node: SortRelNode) -> Any:
        relation = self.visit(node.input)
        return self.backend.sort(relation, node.sort_fields)

    def visit_fetch_rel(self, node: FetchRelNode) -> Any:
        relation = self.visit(node.input)
        if node.from_end:
            return self.backend.fetch_from_end(relation, node.count)
        return self.backend.fetch(relation, node.offset, node.count)

    def visit_join_rel(self, node: JoinRelNode) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.join_type == JoinType.ASOF:
            return self.backend.join_asof(
                left, right,
                on=node.on[0] if node.on else node.left_on[0],
                by=None,
                strategy=node.strategy or "backward",
                tolerance=node.tolerance,
            )
        return self.backend.join(
            left, right,
            join_type=node.join_type,
            on=node.on,
            left_on=node.left_on,
            right_on=node.right_on,
            suffix=node.suffix,
        )

    def visit_aggregate_rel(self, node: AggregateRelNode) -> Any:
        relation = self.visit(node.input)
        if not node.measures:
            return self.backend.distinct(relation, node.keys)
        compiled_measures = [self._compile_expression(m) for m in node.measures]
        return self.backend.aggregate(relation, node.keys, compiled_measures)

    def visit_set_rel(self, node: SetRelNode) -> Any:
        relations = [self.visit(inp) for inp in node.inputs]
        return self.backend.union_all(relations)

    def visit_extension_rel(self, node: ExtensionRelNode) -> Any:
        relation = self.visit(node.input)
        method_name = node.operation.name.lower()
        method = getattr(self.backend, method_name)
        return method(relation, **node.options)

    def _compile_expression(self, expr: Any) -> Any:
        """Compile an expression AST node, or pass through native expressions."""
        if isinstance(expr, ExpressionNode):
            return self.expr_visitor.visit(expr)
        return expr
```

- [ ] **Step 4: Update `__init__.py`**

```python
# src/mountainash/relations/core/unified_visitor/__init__.py
from .relation_visitor import UnifiedRelationVisitor

__all__ = ["UnifiedRelationVisitor"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `hatch run test:test-target tests/relations/test_rel_visitor.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/relations/core/unified_visitor/ tests/relations/test_rel_visitor.py
git commit -m "feat(relations): add UnifiedRelationVisitor"
```

---

## Task 5: Relation Public API

**Files:**
- Create: `src/mountainash/relations/core/relation_api/relation_base.py`
- Create: `src/mountainash/relations/core/relation_api/relation.py`
- Create: `src/mountainash/relations/core/relation_api/grouped_relation.py`
- Modify: `src/mountainash/relations/__init__.py`
- Test: `tests/relations/test_rel_api_build.py`

This task tests only the **build phase** — that API methods produce the correct AST nodes. Backend execution is tested in Tasks 7/9/11.

- [ ] **Step 1: Write tests for API build phase**

```python
# tests/relations/test_rel_api_build.py
"""Tests that Relation API methods produce correct AST nodes.

These tests verify the build phase only — no backend execution.
"""

import pytest

from mountainash.core.constants import (
    ProjectOperation, JoinType, SetType, SortField,
    ExtensionRelOperation, ExecutionTarget,
)
from mountainash.relations import relation, concat
from mountainash.relations.core.relation_nodes import (
    ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
    FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode,
    ExtensionRelNode,
)
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_api.grouped_relation import GroupedRelation


@pytest.fixture
def r():
    """A Relation wrapping a placeholder DataFrame."""
    return relation("placeholder_df")


class TestRelationFactory:
    def test_relation_creates_read_node(self):
        r = relation("my_df")
        assert isinstance(r, Relation)
        assert isinstance(r._node, ReadRelNode)
        assert r._node.dataframe == "my_df"


class TestProjectOperations:
    def test_select_strings(self, r):
        result = r.select("a", "b")
        assert isinstance(result._node, ProjectRelNode)
        assert result._node.operation == ProjectOperation.SELECT

    def test_with_columns(self, r):
        result = r.with_columns("expr1", "expr2")
        assert isinstance(result._node, ProjectRelNode)
        assert result._node.operation == ProjectOperation.WITH_COLUMNS

    def test_drop(self, r):
        result = r.drop("x", "y")
        assert isinstance(result._node, ProjectRelNode)
        assert result._node.operation == ProjectOperation.DROP

    def test_rename(self, r):
        result = r.rename({"old": "new"})
        assert isinstance(result._node, ProjectRelNode)
        assert result._node.operation == ProjectOperation.RENAME
        assert result._node.rename_mapping == {"old": "new"}


class TestFilterOperation:
    def test_single_predicate(self, r):
        result = r.filter("pred")
        assert isinstance(result._node, FilterRelNode)
        assert result._node.predicate == "pred"

    def test_multiple_predicates_chain(self, r):
        result = r.filter("pred1", "pred2")
        # Multiple predicates should produce nested FilterRelNodes or a combined predicate
        assert isinstance(result._node, FilterRelNode)


class TestSortOperation:
    def test_single_column(self, r):
        result = r.sort("age")
        assert isinstance(result._node, SortRelNode)
        assert len(result._node.sort_fields) == 1
        assert result._node.sort_fields[0].column == "age"
        assert result._node.sort_fields[0].descending is False

    def test_descending(self, r):
        result = r.sort("age", descending=True)
        assert result._node.sort_fields[0].descending is True

    def test_multi_column(self, r):
        result = r.sort("group", "age", descending=[False, True])
        assert len(result._node.sort_fields) == 2
        assert result._node.sort_fields[0].descending is False
        assert result._node.sort_fields[1].descending is True


class TestFetchOperations:
    def test_head(self, r):
        result = r.head(10)
        assert isinstance(result._node, FetchRelNode)
        assert result._node.count == 10
        assert result._node.from_end is False

    def test_tail(self, r):
        result = r.tail(5)
        assert isinstance(result._node, FetchRelNode)
        assert result._node.count == 5
        assert result._node.from_end is True

    def test_slice(self, r):
        result = r.slice(offset=10, length=20)
        assert isinstance(result._node, FetchRelNode)
        assert result._node.offset == 10
        assert result._node.count == 20


class TestJoinOperations:
    def test_join_with_relation(self, r):
        other = relation("other_df")
        result = r.join(other, on="id")
        assert isinstance(result._node, JoinRelNode)
        assert result._node.join_type == JoinType.INNER
        assert result._node.on == ["id"]

    def test_join_with_raw_data(self, r):
        result = r.join("raw_dict_data", on="id", how="left")
        assert isinstance(result._node, JoinRelNode)
        assert result._node.join_type == JoinType.LEFT
        # Right side wraps raw data in ReadRelNode
        assert isinstance(result._node.right, ReadRelNode)

    def test_join_execute_on(self, r):
        other = relation("other_df")
        result = r.join(other, on="id", execute_on=ExecutionTarget.LEFT)
        assert result._node.execute_on == ExecutionTarget.LEFT

    def test_join_asof(self, r):
        other = relation("other_df")
        result = r.join_asof(other, on="timestamp", strategy="backward")
        assert isinstance(result._node, JoinRelNode)
        assert result._node.join_type == JoinType.ASOF
        assert result._node.strategy == "backward"


class TestAggregateOperations:
    def test_group_by_returns_grouped(self, r):
        grouped = r.group_by("category")
        assert isinstance(grouped, GroupedRelation)

    def test_group_by_agg(self, r):
        result = r.group_by("category").agg("sum_expr", "mean_expr")
        assert isinstance(result._node, AggregateRelNode)
        assert result._node.keys == ["category"]
        assert len(result._node.measures) == 2

    def test_unique(self, r):
        result = r.unique("id", "name")
        assert isinstance(result._node, AggregateRelNode)
        assert result._node.measures == []


class TestSetOperations:
    def test_concat(self):
        r1 = relation("df1")
        r2 = relation("df2")
        result = concat([r1, r2])
        assert isinstance(result._node, SetRelNode)
        assert result._node.set_type == SetType.UNION_ALL
        assert len(result._node.inputs) == 2


class TestExtensionOperations:
    def test_drop_nulls(self, r):
        result = r.drop_nulls(subset=["a"])
        assert isinstance(result._node, ExtensionRelNode)
        assert result._node.operation == ExtensionRelOperation.DROP_NULLS
        assert result._node.options["subset"] == ["a"]

    def test_with_row_index(self, r):
        result = r.with_row_index(name="idx")
        assert isinstance(result._node, ExtensionRelNode)
        assert result._node.operation == ExtensionRelOperation.WITH_ROW_INDEX

    def test_explode(self, r):
        result = r.explode("tags")
        assert isinstance(result._node, ExtensionRelNode)
        assert result._node.operation == ExtensionRelOperation.EXPLODE

    def test_sample(self, r):
        result = r.sample(n=100)
        assert isinstance(result._node, ExtensionRelNode)
        assert result._node.operation == ExtensionRelOperation.SAMPLE

    def test_top_k(self, r):
        result = r.top_k(5, by="score")
        assert isinstance(result._node, ExtensionRelNode)
        assert result._node.operation == ExtensionRelOperation.TOP_K


class TestChaining:
    def test_filter_sort_head(self, r):
        result = r.filter("pred").sort("name").head(10)
        assert isinstance(result._node, FetchRelNode)
        assert isinstance(result._node.input, SortRelNode)
        assert isinstance(result._node.input.input, FilterRelNode)
        assert isinstance(result._node.input.input.input, ReadRelNode)

    def test_pipe(self, r):
        def add_filter(rel):
            return rel.filter("custom_pred")

        result = r.pipe(add_filter)
        assert isinstance(result._node, FilterRelNode)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/relations/test_rel_api_build.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement Relation base**

```python
# src/mountainash/relations/core/relation_api/relation_base.py
"""Base for Relation with compilation machinery."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.expsys_base import (
    identify_backend,
    get_expression_system,
)
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

from ..relation_nodes import RelationNode, ReadRelNode, JoinRelNode, SetRelNode
from ..relation_protocols.relsys_base import get_relation_system
from ..unified_visitor.relation_visitor import UnifiedRelationVisitor


class RelationBase:
    """Base class providing compilation and introspection."""

    __slots__ = ("_node",)

    def __init__(self, node: RelationNode) -> None:
        self._node = node

    def _compile_and_execute(self) -> Any:
        """Detect backend, create visitors, walk the plan tree."""
        backend = self._detect_backend()
        relation_system_cls = get_relation_system(backend)
        relation_system = relation_system_cls()
        expression_system_cls = get_expression_system(backend)
        expression_system = expression_system_cls()
        expr_visitor = UnifiedExpressionVisitor(expression_system)
        visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
        return visitor.visit(self._node)

    def _detect_backend(self) -> CONST_BACKEND:
        """Find the leaf ReadRelNode and detect its backend."""
        leaf = self._find_leaf_read_node(self._node)
        return identify_backend(leaf.dataframe)

    @staticmethod
    def _find_leaf_read_node(node: RelationNode) -> ReadRelNode:
        """Walk down the tree to find the first ReadRelNode."""
        if isinstance(node, ReadRelNode):
            return node
        if isinstance(node, JoinRelNode):
            return RelationBase._find_leaf_read_node(node.left)
        if isinstance(node, SetRelNode):
            return RelationBase._find_leaf_read_node(node.inputs[0])
        if hasattr(node, "input"):
            return RelationBase._find_leaf_read_node(node.input)
        raise ValueError(f"Cannot find ReadRelNode in plan tree from {type(node).__name__}")
```

- [ ] **Step 4: Implement Relation class**

```python
# src/mountainash/relations/core/relation_api/relation.py
"""Relation — the public fluent API for relational operations."""

from __future__ import annotations
from typing import Any, Callable, Optional, Sequence, Union

from mountainash.core.constants import (
    ProjectOperation,
    JoinType,
    ExecutionTarget,
    SetType,
    SortField,
    ExtensionRelOperation,
)
from ..relation_nodes import (
    ReadRelNode,
    ProjectRelNode,
    FilterRelNode,
    SortRelNode,
    FetchRelNode,
    JoinRelNode,
    AggregateRelNode,
    SetRelNode,
    ExtensionRelNode,
    RelationNode,
)
from .relation_base import RelationBase
from .grouped_relation import GroupedRelation


class Relation(RelationBase):
    """Fluent builder for relational plans.

    Each method returns a new Relation wrapping an extended plan tree.
    Terminal operations (.collect(), .to_polars(), etc.) trigger compilation.
    """

    # --- ProjectRel ---

    def select(self, *columns: Any) -> Relation:
        exprs = list(columns)
        return Relation(ProjectRelNode(
            input=self._node, expressions=exprs, operation=ProjectOperation.SELECT,
        ))

    def with_columns(self, *expressions: Any) -> Relation:
        exprs = list(expressions)
        return Relation(ProjectRelNode(
            input=self._node, expressions=exprs, operation=ProjectOperation.WITH_COLUMNS,
        ))

    def drop(self, *columns: str) -> Relation:
        exprs = list(columns)
        return Relation(ProjectRelNode(
            input=self._node, expressions=exprs, operation=ProjectOperation.DROP,
        ))

    def rename(self, mapping: dict[str, str]) -> Relation:
        return Relation(ProjectRelNode(
            input=self._node, expressions=[], operation=ProjectOperation.RENAME,
            rename_mapping=mapping,
        ))

    # --- FilterRel ---

    def filter(self, *predicates: Any) -> Relation:
        node = self._node
        for pred in predicates:
            node = FilterRelNode(input=node, predicate=pred)
        return Relation(node)

    # --- SortRel ---

    def sort(self, *by: str, descending: Union[bool, list[bool]] = False) -> Relation:
        fields = _normalize_sort_fields(list(by), descending)
        return Relation(SortRelNode(input=self._node, sort_fields=fields))

    # --- FetchRel ---

    def head(self, n: int = 5) -> Relation:
        return Relation(FetchRelNode(input=self._node, count=n))

    def tail(self, n: int = 5) -> Relation:
        return Relation(FetchRelNode(input=self._node, count=n, from_end=True))

    def slice(self, offset: int, length: Optional[int] = None) -> Relation:
        return Relation(FetchRelNode(input=self._node, offset=offset, count=length))

    # --- JoinRel ---

    def join(
        self,
        other: Any,
        *,
        on: Optional[Union[str, list[str]]] = None,
        left_on: Optional[Union[str, list[str]]] = None,
        right_on: Optional[Union[str, list[str]]] = None,
        how: str = "inner",
        suffix: str = "_right",
        execute_on: Optional[ExecutionTarget] = None,
    ) -> Relation:
        right_node = self._to_relation_node(other)
        return Relation(JoinRelNode(
            left=self._node,
            right=right_node,
            join_type=JoinType(how),
            on=_normalize_columns(on),
            left_on=_normalize_columns(left_on),
            right_on=_normalize_columns(right_on),
            suffix=suffix,
            execute_on=execute_on,
        ))

    def join_asof(
        self,
        other: Any,
        *,
        on: str,
        by: Optional[Union[str, list[str]]] = None,
        strategy: str = "backward",
        tolerance: Any = None,
    ) -> Relation:
        right_node = self._to_relation_node(other)
        return Relation(JoinRelNode(
            left=self._node,
            right=right_node,
            join_type=JoinType.ASOF,
            on=[on],
            strategy=strategy,
            tolerance=tolerance,
        ))

    # --- AggregateRel ---

    def group_by(self, *keys: Any) -> GroupedRelation:
        return GroupedRelation(self._node, list(keys))

    def unique(self, *columns: str, subset: Optional[list[str]] = None, keep: str = "any") -> Relation:
        cols = list(columns) if columns else (subset or [])
        return Relation(AggregateRelNode(input=self._node, keys=cols, measures=[]))

    # --- ExtensionRel ---

    def drop_nulls(self, *, subset: Optional[list[str]] = None) -> Relation:
        opts: dict[str, Any] = {}
        if subset is not None:
            opts["subset"] = subset
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.DROP_NULLS, options=opts,
        ))

    def with_row_index(self, *, name: str = "index") -> Relation:
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.WITH_ROW_INDEX,
            options={"name": name},
        ))

    def explode(self, *columns: str) -> Relation:
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.EXPLODE,
            options={"columns": list(columns)},
        ))

    def sample(self, *, n: Optional[int] = None, fraction: Optional[float] = None) -> Relation:
        opts: dict[str, Any] = {}
        if n is not None:
            opts["n"] = n
        if fraction is not None:
            opts["fraction"] = fraction
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.SAMPLE, options=opts,
        ))

    def unpivot(
        self,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> Relation:
        opts: dict[str, Any] = {
            "on": on, "variable_name": variable_name, "value_name": value_name,
        }
        if index is not None:
            opts["index"] = index
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.UNPIVOT, options=opts,
        ))

    def pivot(
        self,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> Relation:
        opts: dict[str, Any] = {"on": on, "aggregate_function": aggregate_function}
        if index is not None:
            opts["index"] = index
        if values is not None:
            opts["values"] = values
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.PIVOT, options=opts,
        ))

    def top_k(self, k: int, *, by: str, descending: bool = True) -> Relation:
        return Relation(ExtensionRelNode(
            input=self._node, operation=ExtensionRelOperation.TOP_K,
            options={"k": k, "by": by, "descending": descending},
        ))

    def pipe(self, func: Callable[["Relation"], "Relation"], *args: Any, **kwargs: Any) -> Relation:
        return func(self, *args, **kwargs)

    # --- Terminal operations ---

    def collect(self) -> Any:
        return self._compile_and_execute()

    def to_polars(self) -> Any:
        result = self._compile_and_execute()
        import polars as pl
        if isinstance(result, (pl.DataFrame, pl.LazyFrame)):
            return result.collect() if isinstance(result, pl.LazyFrame) else result
        # Cross-convert via narwhals or direct methods
        return _convert_to_polars(result)

    def to_pandas(self) -> Any:
        result = self._compile_and_execute()
        return _convert_to_pandas(result)

    def to_dict(self) -> dict:
        result = self.to_polars()
        return result.to_dict(as_series=False)

    def to_dicts(self) -> list[dict]:
        result = self.to_polars()
        return result.to_dicts()

    # --- Introspection ---

    @property
    def columns(self) -> list[str]:
        # For now, compile and inspect. Schema inference can be added later.
        result = self._compile_and_execute()
        if hasattr(result, "columns"):
            cols = result.columns
            return list(cols) if not isinstance(cols, list) else cols
        raise NotImplementedError("Cannot infer columns for this backend type")

    # --- Helpers ---

    @staticmethod
    def _to_relation_node(other: Any) -> RelationNode:
        if isinstance(other, Relation):
            return other._node
        return ReadRelNode(dataframe=other)


def relation(df: Any) -> Relation:
    """Create a Relation from any supported DataFrame type."""
    return Relation(ReadRelNode(dataframe=df))


def concat(relations: list[Relation]) -> Relation:
    """Concatenate multiple Relations (UNION ALL)."""
    nodes = [r._node for r in relations]
    return Relation(SetRelNode(inputs=nodes, set_type=SetType.UNION_ALL))


# --- Utility functions ---

def _normalize_columns(cols: Optional[Union[str, list[str]]]) -> Optional[list[str]]:
    if cols is None:
        return None
    if isinstance(cols, str):
        return [cols]
    return list(cols)


def _normalize_sort_fields(columns: list[str], descending: Union[bool, list[bool]]) -> list[SortField]:
    if isinstance(descending, bool):
        return [SortField(column=c, descending=descending) for c in columns]
    if len(descending) != len(columns):
        raise ValueError(
            f"Length of descending ({len(descending)}) must match "
            f"number of columns ({len(columns)})"
        )
    return [SortField(column=c, descending=d) for c, d in zip(columns, descending)]


def _convert_to_polars(result: Any) -> Any:
    """Best-effort conversion to Polars DataFrame."""
    import polars as pl
    if hasattr(result, "to_polars"):
        return result.to_polars()
    if hasattr(result, "to_pandas"):
        return pl.from_pandas(result.to_pandas())
    raise TypeError(f"Cannot convert {type(result)} to Polars DataFrame")


def _convert_to_pandas(result: Any) -> Any:
    """Best-effort conversion to pandas DataFrame."""
    if hasattr(result, "to_pandas"):
        return result.to_pandas()
    import polars as pl
    if isinstance(result, pl.DataFrame):
        return result.to_pandas()
    raise TypeError(f"Cannot convert {type(result)} to pandas DataFrame")
```

- [ ] **Step 5: Implement GroupedRelation**

```python
# src/mountainash/relations/core/relation_api/grouped_relation.py
"""GroupedRelation — returned by Relation.group_by()."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from ..relation_nodes import AggregateRelNode, RelationNode

if TYPE_CHECKING:
    from .relation import Relation


class GroupedRelation:
    """Intermediate object holding grouping keys. Only exposes .agg()."""

    __slots__ = ("_node", "_keys")

    def __init__(self, node: RelationNode, keys: list[Any]) -> None:
        self._node = node
        self._keys = keys

    def agg(self, *expressions: Any) -> "Relation":
        from .relation import Relation
        return Relation(AggregateRelNode(
            input=self._node,
            keys=self._keys,
            measures=list(expressions),
        ))
```

- [ ] **Step 6: Update `__init__.py` files**

```python
# src/mountainash/relations/core/relation_api/__init__.py
from .relation import Relation, relation, concat
from .grouped_relation import GroupedRelation

__all__ = ["Relation", "GroupedRelation", "relation", "concat"]
```

```python
# src/mountainash/relations/__init__.py
"""Mountainash Relations — Substrait-aligned relational AST."""

from .core.relation_api import Relation, relation, concat, GroupedRelation

__all__ = ["Relation", "GroupedRelation", "relation", "concat"]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `hatch run test:test-target tests/relations/test_rel_api_build.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/relations/ tests/relations/test_rel_api_build.py
git commit -m "feat(relations): add Relation fluent API and GroupedRelation"
```

---

## Task 6: Polars Backend

**Files:**
- Create: `src/mountainash/relations/backends/relation_systems/polars/base.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_read.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_project.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_filter.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_sort.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_fetch.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_join.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_aggregate.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/substrait/relsys_pl_set.py`
- Create: `src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash/relsys_pl_ext_ma_util.py`
- Modify: `src/mountainash/relations/backends/relation_systems/polars/__init__.py`

This task implements all Polars backend methods. Each file is one protocol implementation. The composition class (`__init__.py`) inherits all of them.

Refer to the spec Section 3 for the `read` lazy-by-default pattern. Polars converts eager DataFrames to LazyFrame via `.lazy()`.

- [ ] **Step 1: Implement all Polars backend files**

The agent implementing this task should:
1. Read the protocol files from Task 3 to understand method signatures
2. Implement each method using Polars native API
3. Follow the `backend-composition.md` principle: composition class body = `pass`
4. Use `@register_relation_system(CONST_BACKEND.POLARS)` on the composition class

Key implementation details per file:

**`relsys_pl_read.py`**: `read()` calls `df.lazy()` if df is eager `pl.DataFrame`, pass-through if `pl.LazyFrame`.

**`relsys_pl_project.py`**:
- `project_select(relation, columns)`: For string columns, use `relation.select(columns)`. For expression objects, pass through.
- `project_with_columns(relation, exprs)`: `relation.with_columns(exprs)`
- `project_drop(relation, columns)`: `relation.drop(columns)`
- `project_rename(relation, mapping)`: `relation.rename(mapping)`

**`relsys_pl_filter.py`**: `relation.filter(predicate)`

**`relsys_pl_sort.py`**: Convert `SortField` list to `relation.sort(by=[...], descending=[...], nulls_last=[...])`

**`relsys_pl_fetch.py`**:
- `fetch(relation, offset, count)`: `relation.slice(offset, count)`
- `fetch_from_end(relation, count)`: `relation.tail(count)`

**`relsys_pl_join.py`**:
- `join(...)`: Map `JoinType` to Polars `how` parameter. Use `relation.join(right, on=..., how=..., suffix=...)`
- `join_asof(...)`: `relation.join_asof(right, on=..., by=..., strategy=...)`

**`relsys_pl_aggregate.py`**:
- `aggregate(relation, keys, measures)`: `relation.group_by(keys).agg(measures)`
- `distinct(relation, columns)`: `relation.unique(subset=columns)` if columns, else `relation.unique()`

**`relsys_pl_set.py`**: `pl.concat(relations)`

**`relsys_pl_ext_ma_util.py`**: Each method maps directly to the Polars equivalent (e.g., `drop_nulls`, `with_row_index`, `explode`, `sample`, `unpivot`, `pivot`, `top_k`).

**Composition `__init__.py`**:
```python
@register_relation_system(CONST_BACKEND.POLARS)
class PolarsRelationSystem(
    SubstraitPolarsReadRelationSystem,
    SubstraitPolarsProjectRelationSystem,
    SubstraitPolarsFilterRelationSystem,
    SubstraitPolarsSortRelationSystem,
    SubstraitPolarsFetchRelationSystem,
    SubstraitPolarsJoinRelationSystem,
    SubstraitPolarsAggregateRelationSystem,
    SubstraitPolarsSetRelationSystem,
    MountainashPolarsExtensionRelationSystem,
):
    pass
```

- [ ] **Step 2: Run existing tests to ensure no regressions**

Run: `hatch run test:test-target tests/relations/ -v`
Expected: Previous tests still pass. Backend not exercised yet (that's Task 7).

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/relations/backends/relation_systems/polars/
git commit -m "feat(relations): add Polars relation system backend"
```

---

## Task 7: Polars Integration Tests

**Files:**
- Create: `tests/relations/conftest.py`
- Create: `tests/relations/test_rel_polars.py`

- [ ] **Step 1: Create test fixtures and Polars integration tests**

The conftest provides sample DataFrames. Tests exercise the full pipeline: `relation(polars_df).filter(...).sort(...).to_polars()`.

Test coverage per operation:
- `select`, `with_columns`, `drop`, `rename`
- `filter` with mountainash expressions and native Polars expressions
- `sort` single/multi/descending
- `head`, `tail`, `slice`
- `join` (inner, left, anti) with Polars DataFrames
- `group_by().agg()` with mountainash aggregate expressions
- `unique`
- `drop_nulls`, `with_row_index`, `explode`, `sample`
- Pipeline chains: `filter → sort → head → to_polars()`

Each test should verify actual data output (row counts, values), not just types.

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target tests/relations/test_rel_polars.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add tests/relations/conftest.py tests/relations/test_rel_polars.py
git commit -m "test(relations): add Polars integration tests"
```

---

## Task 8: Narwhals Backend

**Files:** Same structure as Task 6 but in `narwhals/` directory with `relsys_nw_*` prefixes.

Key differences from Polars:
- `read()`: Wraps with `nw.from_native(df)` — handles pandas, PyArrow, cuDF
- Operations use Narwhals API: `nw_df.sort(...)`, `nw_df.filter(...)`, etc.
- Results need `nw.to_native()` unwrapping when returning from terminal operations
- `join_asof`: Available in Narwhals
- `pivot`: Only available on eager DataFrame, not LazyFrame
- `sample`: May require fallback for some backends

Register with `@register_relation_system(CONST_BACKEND.NARWHALS)`.

- [ ] **Step 1: Implement all Narwhals backend files**
- [ ] **Step 2: Commit**

```bash
git add src/mountainash/relations/backends/relation_systems/narwhals/
git commit -m "feat(relations): add Narwhals relation system backend"
```

---

## Task 9: Narwhals Integration Tests

**Files:**
- Create: `tests/relations/test_rel_narwhals.py`

Parametrize over pandas and PyArrow inputs. Same test coverage as Task 7.

- [ ] **Step 1: Write and run Narwhals integration tests**
- [ ] **Step 2: Commit**

```bash
git add tests/relations/test_rel_narwhals.py
git commit -m "test(relations): add Narwhals integration tests (pandas + PyArrow)"
```

---

## Task 10: Ibis Backend

**Files:** Same structure as Task 6 but in `ibis/` directory with `relsys_ib_*` prefixes.

Key differences:
- `read()`: Pass-through (Ibis tables are already deferred)
- Operations use Ibis API: `table.order_by(...)`, `table.filter(...)`, `table.mutate(...)`, `table.select(...)`
- `sort` → `order_by` in Ibis
- `with_columns` → `mutate` in Ibis
- `unique` → `distinct` in Ibis
- `join_asof`: Not available in all Ibis backends — xfail for SQLite
- `pivot`/`unpivot`: `pivot_wider`/`unpivot` in Ibis
- `sample`: Uses fraction-based sampling
- Terminal operations need `.to_polars()` or `.to_pandas()` on the Ibis result

Register with `@register_relation_system(CONST_BACKEND.IBIS)`.

- [ ] **Step 1: Implement all Ibis backend files**
- [ ] **Step 2: Commit**

```bash
git add src/mountainash/relations/backends/relation_systems/ibis/
git commit -m "feat(relations): add Ibis relation system backend"
```

---

## Task 11: Ibis Integration Tests

**Files:**
- Create: `tests/relations/test_rel_ibis.py`

Use DuckDB in-memory backend (matching existing test pattern). xfail for known limitations (SQLite ASOF, etc.).

- [ ] **Step 1: Write and run Ibis integration tests**
- [ ] **Step 2: Commit**

```bash
git add tests/relations/test_rel_ibis.py
git commit -m "test(relations): add Ibis integration tests (DuckDB)"
```

---

## Task 12: Cross-Type Joins & Pipeline Tests

**Files:**
- Create: `tests/relations/test_rel_cross_type_join.py`
- Create: `tests/relations/test_rel_pipeline.py`

- [ ] **Step 1: Write cross-type join tests**

Test joining across backend types:
- Polars left + pandas right
- Polars left + dict right
- Polars left + PyArrow right
- Verify data correctness after cross-type join

- [ ] **Step 2: Write pipeline tests**

Test multi-operation chains that exercise real-world workflows:
```python
result = (
    ma.relation(df)
    .filter(ma.col("age") > 30)
    .with_columns(ma.col("salary") * 1.1)
    .sort("name")
    .head(10)
    .to_polars()
)
```

Parametrize across backends.

- [ ] **Step 3: Run all tests**

Run: `hatch run test:test-target tests/relations/ -v`
Expected: ALL PASS (with xfails for known divergences)

- [ ] **Step 4: Commit**

```bash
git add tests/relations/test_rel_cross_type_join.py tests/relations/test_rel_pipeline.py
git commit -m "test(relations): add cross-type join and pipeline integration tests"
```

---

## Task 13: Wiring Audit & Public Exports

**Files:**
- Create: `tests/relations/test_rel_wiring_audit.py`
- Modify: `src/mountainash/__init__.py`

- [ ] **Step 1: Write wiring audit tests**

```python
# tests/relations/test_rel_wiring_audit.py
"""Automated wiring audit for relational system."""

import inspect
import pytest

from mountainash.relations.core.relation_nodes import RelationNode
from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
from mountainash.relations.core.relation_protocols.relsys_base import RelationSystem
from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
from mountainash.relations.backends.relation_systems.narwhals import NarwhalsRelationSystem
from mountainash.relations.backends.relation_systems.ibis import IbisRelationSystem


class TestVisitorCoversAllNodes:
    """Every RelationNode subclass must have a visit_* method in the visitor."""

    def test_all_node_types_handled(self):
        node_subclasses = set()
        for cls in RelationNode.__subclasses__():
            node_subclasses.add(cls.__name__)

        visitor_methods = {
            name for name in dir(UnifiedRelationVisitor)
            if name.startswith("visit_") and name != "visit"
        }

        for node_name in node_subclasses:
            # Convert CamelCase to snake_case for method name matching
            expected_method = "visit_" + _camel_to_snake(node_name.replace("Node", ""))
            assert expected_method in visitor_methods, (
                f"Visitor missing method {expected_method} for {node_name}"
            )


class TestAllBackendsImplementProtocols:
    """Every protocol method must be implemented by all 3 backends."""

    @pytest.mark.parametrize("backend_cls", [
        PolarsRelationSystem,
        NarwhalsRelationSystem,
        IbisRelationSystem,
    ])
    def test_backend_implements_all_protocol_methods(self, backend_cls):
        # Get all abstract methods from RelationSystem
        protocol_methods = set()
        for base in RelationSystem.__mro__:
            for name, method in inspect.getmembers(base):
                if not name.startswith("_") and callable(method):
                    protocol_methods.add(name)

        # Remove non-protocol items
        protocol_methods -= {"backend_type"}

        for method_name in protocol_methods:
            assert hasattr(backend_cls, method_name), (
                f"{backend_cls.__name__} missing protocol method: {method_name}"
            )


def _camel_to_snake(name: str) -> str:
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
```

- [ ] **Step 2: Add public exports to mountainash `__init__.py`**

Add to `src/mountainash/__init__.py`:

```python
from mountainash.relations import relation, concat
```

This enables:
```python
import mountainash as ma
r = ma.relation(df)
ma.concat([r1, r2])
```

- [ ] **Step 3: Run full test suite**

Run: `hatch run test:test`
Expected: All existing tests pass + all new relations tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/relations/test_rel_wiring_audit.py src/mountainash/__init__.py
git commit -m "feat(relations): add wiring audit and ma.relation() public export"
```

---

## Self-Review Checklist

1. **Spec coverage**: All 9 sections of the spec are covered:
   - S1 Node types → Task 2
   - S2 Three-layer separation → Tasks 3 (protocols), 5 (API), 6/8/10 (backends)
   - S3 Visitor → Task 4
   - S4 Public API → Task 5
   - S5 Cross-type joins → Task 12
   - S6 File organisation → enforced by file paths in each task
   - S7 Wiring matrix → Task 13
   - S8 Testing → Tasks 7, 9, 11, 12
   - S9 Migration → Task 13 (public exports); deprecation is future work

2. **Placeholder scan**: No TBDs. Tasks 8/10 (Narwhals/Ibis backends) are described with implementation guidance rather than full code — the implementing agent reads protocols + Polars example to implement.

3. **Type consistency**: `RelationNode`, `Relation`, `GroupedRelation`, `relation()`, `concat()` names are consistent across all tasks. `SortField`, `ProjectOperation`, `JoinType`, `SetType`, `ExtensionRelOperation`, `ExecutionTarget` enums match between spec, Task 1 definitions, and Task 5 usage.
