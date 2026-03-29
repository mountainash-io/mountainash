# Schema & PyData Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align schema and pydata modules with the build-then-execute paradigm — extend `ma.relation()` to accept Python data (source) and emit Python data (sink), add `ma.schema()` as a deferred schema API.

**Architecture:** `ma.relation()` becomes the universal entry point. Python data input creates a `SourceRelNode` (new leaf node) whose visitor method calls existing `PydataIngressFactory` at execution time. Sink terminals on `Relation` delegate to existing egress code. `SchemaBuilder` wraps existing `SchemaConfig`/`CastSchemaFactory`/extractors/validators.

**Tech Stack:** Python 3, Pydantic (frozen BaseModel for nodes), Polars, existing mountainash.pydata and mountainash.schema internals.

**Spec:** `docs/superpowers/specs/2026-03-29-schema-pydata-alignment-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/mountainash/relations/core/relation_nodes/mountainash_extensions/reln_ext_source.py` | NEW: `SourceRelNode` — leaf node holding Python data + detected format |
| `src/mountainash/relations/core/relation_nodes/__init__.py` | MODIFY: export `SourceRelNode` |
| `src/mountainash/relations/core/unified_visitor/relation_visitor.py` | MODIFY: add `visit_source_rel()` method |
| `src/mountainash/relations/core/relation_api/relation_base.py` | MODIFY: update `_find_leaf_read_node()` to handle `SourceRelNode` |
| `src/mountainash/relations/core/relation_api/relation.py` | MODIFY: extend `relation()` factory, add sink terminals |
| `src/mountainash/schema/schema_builder.py` | NEW: `SchemaBuilder` — deferred schema API |
| `src/mountainash/__init__.py` | MODIFY: add `schema` entry point |
| `tests/alignment/test_source.py` | NEW: source tests (Python data → relation → collect) |
| `tests/alignment/test_sink.py` | NEW: sink tests (relation → Python data) |
| `tests/alignment/test_schema_builder.py` | NEW: schema builder tests |
| `tests/alignment/test_roundtrip.py` | NEW: round-trip integration tests |

---

### Task 1: SourceRelNode

**Files:**
- Create: `src/mountainash/relations/core/relation_nodes/mountainash_extensions/reln_ext_source.py`
- Modify: `src/mountainash/relations/core/relation_nodes/__init__.py`
- Test: `tests/alignment/test_source.py`

- [ ] **Step 1: Write the failing test for SourceRelNode construction**

Create `tests/alignment/__init__.py` (empty) and `tests/alignment/test_source.py`:

```python
"""Tests for SourceRelNode — Python data source for relations."""
from __future__ import annotations

import pytest

from mountainash.relations.core.relation_nodes import SourceRelNode
from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT


class TestSourceRelNodeConstruction:
    """SourceRelNode holds Python data and detected format."""

    def test_create_with_list_of_dicts(self):
        data = [{"a": 1, "b": 2}]
        node = SourceRelNode(data=data, detected_format=CONST_PYTHON_DATAFORMAT.PYLIST)
        assert node.data is data
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_create_with_dict_of_lists(self):
        data = {"a": [1, 2], "b": [3, 4]}
        node = SourceRelNode(data=data, detected_format=CONST_PYTHON_DATAFORMAT.PYDICT)
        assert node.data is data
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYDICT

    def test_accept_calls_visit_source_rel(self):
        data = [{"a": 1}]
        node = SourceRelNode(data=data, detected_format=CONST_PYTHON_DATAFORMAT.PYLIST)

        class MockVisitor:
            def visit_source_rel(self, node):
                return "visited"

        result = node.accept(MockVisitor())
        assert result == "visited"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/alignment/test_source.py::TestSourceRelNodeConstruction -v`
Expected: FAIL with `ImportError: cannot import name 'SourceRelNode'`

- [ ] **Step 3: Implement SourceRelNode**

Create `src/mountainash/relations/core/relation_nodes/mountainash_extensions/reln_ext_source.py`:

```python
"""Source relation node — holds Python data for deferred ingress.

This is a leaf node (no input relation). At execution time, the visitor
materializes the Python data into a DataFrame via PydataIngressFactory.
"""
from __future__ import annotations

from typing import Any

from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
from ..reln_base import RelationNode


class SourceRelNode(RelationNode, frozen=False, arbitrary_types_allowed=True):
    """Leaf node holding Python data for deferred conversion to DataFrame.

    Fields:
        data: The raw Python data (list of dicts, dict of lists, dataclasses, etc.)
        detected_format: The auto-detected data format from PydataIngressFactory.
    """
    data: Any
    detected_format: CONST_PYTHON_DATAFORMAT

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_source_rel(self)
```

**Note on `frozen=False`:** The node holds arbitrary Python data that may not be hashable. Pydantic's frozen mode would reject mutable data. This is the only non-frozen relation node — all others are immutable plan nodes. SourceRelNode is a leaf that holds a reference to user data, not a plan transformation.

- [ ] **Step 4: Export SourceRelNode from relation_nodes/__init__.py**

Add to `src/mountainash/relations/core/relation_nodes/__init__.py`:

```python
from .mountainash_extensions.reln_ext_source import SourceRelNode
```

And add `"SourceRelNode"` to the `__all__` list.

- [ ] **Step 5: Run test to verify it passes**

Run: `hatch run test:test-target-quick tests/alignment/test_source.py::TestSourceRelNodeConstruction -v`
Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add tests/alignment/ src/mountainash/relations/core/relation_nodes/mountainash_extensions/reln_ext_source.py src/mountainash/relations/core/relation_nodes/__init__.py
git commit -m "feat(relations): add SourceRelNode for Python data sources"
```

---

### Task 2: Visitor handling for SourceRelNode

**Files:**
- Modify: `src/mountainash/relations/core/unified_visitor/relation_visitor.py`
- Modify: `src/mountainash/relations/core/relation_api/relation_base.py`
- Test: `tests/alignment/test_source.py`

- [ ] **Step 1: Write the failing test for visitor execution**

Append to `tests/alignment/test_source.py`:

```python
import polars as pl

import mountainash as ma


class TestSourceRelVisitorExecution:
    """SourceRelNode visitor materializes Python data into a DataFrame."""

    def test_source_list_of_dicts_collects_to_polars(self):
        data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        result = ma.relation(data).collect()
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
        if isinstance(result, pl.LazyFrame):
            result = result.collect()
        assert result.shape == (2, 2)
        assert result["a"].to_list() == [1, 2]
        assert result["b"].to_list() == ["x", "y"]

    def test_source_dict_of_lists_collects_to_polars(self):
        data = {"x": [10, 20, 30], "y": ["a", "b", "c"]}
        result = ma.relation(data).to_polars()
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)
        assert result["x"].to_list() == [10, 20, 30]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/alignment/test_source.py::TestSourceRelVisitorExecution -v`
Expected: FAIL — `ma.relation(data)` currently only accepts DataFrames.

- [ ] **Step 3: Extend `relation()` factory to detect Python data**

Modify `src/mountainash/relations/core/relation_api/relation.py`. Find the `relation()` function and update it:

```python
def relation(data: Any) -> Relation:
    """Create a Relation from a DataFrame or Python data.

    For DataFrames (Polars, Pandas, Narwhals, Ibis, PyArrow), creates a
    ReadRelNode directly. For Python data (dicts, lists, dataclasses, etc.),
    creates a SourceRelNode with deferred conversion.
    """
    from mountainash.relations.core.relation_nodes import ReadRelNode, SourceRelNode

    # Try DataFrame detection first
    if _is_dataframe(data):
        return Relation(ReadRelNode(dataframe=data))

    # Python data — detect format and create SourceRelNode
    from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory
    from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

    detected = PydataIngressFactory._get_strategy_key(data)
    if detected is None:
        detected = CONST_PYTHON_DATAFORMAT.UNKNOWN

    return Relation(SourceRelNode(data=data, detected_format=detected))


def _is_dataframe(data: Any) -> bool:
    """Check if data is a recognized DataFrame type."""
    type_name = type(data).__module__ + "." + type(data).__qualname__
    # Check common DataFrame types by module
    df_modules = ("polars.", "pandas.", "narwhals.", "pyarrow.", "ibis.")
    return any(type_name.startswith(mod) for mod in df_modules)
```

- [ ] **Step 4: Add `visit_source_rel()` to the visitor**

Modify `src/mountainash/relations/core/unified_visitor/relation_visitor.py`. Add this method to `UnifiedRelationVisitor`:

```python
def visit_source_rel(self, node: Any) -> Any:
    """Visit a source node — materialize Python data into a DataFrame."""
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress

    df = PydataIngress.convert(node.data)
    return self.backend.read(df)
```

- [ ] **Step 5: Update `_find_leaf_read_node()` in RelationBase to handle SourceRelNode**

Modify `src/mountainash/relations/core/relation_api/relation_base.py`. In the `_find_leaf_read_node` static method, add handling for `SourceRelNode`:

```python
from mountainash.relations.core.relation_nodes import SourceRelNode

# At the start of _find_leaf_read_node:
if isinstance(node, SourceRelNode):
    # Source nodes don't have a backend yet — default to Polars
    # The visitor will materialize via PydataIngress (which returns Polars)
    return None
```

And update `_detect_backend()` to handle the `None` case:

```python
def _detect_backend(self) -> CONST_BACKEND:
    """Walk the plan tree to find a ReadRelNode and identify its backend."""
    leaf = self._find_leaf_read_node(self._node)
    if leaf is None:
        # SourceRelNode — PydataIngress returns Polars by default
        return CONST_BACKEND.POLARS
    return identify_backend(leaf.dataframe)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `hatch run test:test-target-quick tests/alignment/test_source.py::TestSourceRelVisitorExecution -v`
Expected: 2 PASSED

- [ ] **Step 7: Run all existing relation tests to check for regressions**

Run: `hatch run test:test-target-quick tests/relations/ -v --tb=short`
Expected: All previously passing tests still pass.

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/relations/core/relation_api/relation.py src/mountainash/relations/core/relation_api/relation_base.py src/mountainash/relations/core/unified_visitor/relation_visitor.py tests/alignment/test_source.py
git commit -m "feat(relations): extend relation() to accept Python data via SourceRelNode"
```

---

### Task 3: Source tests — transforms on Python data

**Files:**
- Test: `tests/alignment/test_source.py`

- [ ] **Step 1: Write tests for source + relation transforms**

Append to `tests/alignment/test_source.py`:

```python
class TestSourceWithTransforms:
    """Python data sourced through relation transforms."""

    def test_source_filter(self):
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 20}]
        result = ma.relation(data).filter(ma.col("age").gt(25)).to_polars()
        assert result.shape == (1, 2)
        assert result["name"].to_list() == ["Alice"]

    def test_source_sort(self):
        data = [{"x": 3}, {"x": 1}, {"x": 2}]
        result = ma.relation(data).sort("x").to_polars()
        assert result["x"].to_list() == [1, 2, 3]

    def test_source_head(self):
        data = {"val": [10, 20, 30, 40, 50]}
        result = ma.relation(data).head(3).to_polars()
        assert result.shape == (3, 1)

    def test_source_select(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        result = ma.relation(data).select("a", "c").to_polars()
        assert result.columns == ["a", "c"]

    def test_source_with_columns(self):
        data = [{"x": 10}, {"x": 20}]
        result = ma.relation(data).with_columns(
            ma.col("x").mul(2).alias("x2")
        ).to_polars()
        assert "x2" in result.columns
        assert result["x2"].to_list() == [20, 40]


class TestSourceDetectedFormat:
    """SourceRelNode exposes detected format for introspection."""

    def test_list_of_dicts_detected_as_pylist(self):
        data = [{"a": 1}]
        r = ma.relation(data)
        node = r._node
        assert isinstance(node, SourceRelNode)
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_dict_of_lists_detected_as_pydict(self):
        data = {"a": [1, 2]}
        r = ma.relation(data)
        node = r._node
        assert isinstance(node, SourceRelNode)
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYDICT
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/alignment/test_source.py -v`
Expected: All PASSED (implementation already done in Task 2)

- [ ] **Step 3: Commit**

```bash
git add tests/alignment/test_source.py
git commit -m "test(alignment): add source transform and format detection tests"
```

---

### Task 4: Sink terminal methods on Relation

**Files:**
- Modify: `src/mountainash/relations/core/relation_api/relation.py`
- Test: `tests/alignment/test_sink.py`

- [ ] **Step 1: Write the failing tests for sink terminals**

Create `tests/alignment/test_sink.py`:

```python
"""Tests for sink terminal methods on Relation."""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl
import pytest

import mountainash as ma


@dataclass
class Person:
    name: str
    age: int


@pytest.fixture
def people_df():
    return pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
    })


class TestSinkToTuples:
    """Relation.to_tuples() returns list of tuples."""

    def test_to_tuples(self, people_df):
        result = ma.relation(people_df).to_tuples()
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == ("Alice", 30)
        assert result[1] == ("Bob", 25)

    def test_to_tuples_after_filter(self, people_df):
        result = ma.relation(people_df).filter(ma.col("age").gt(28)).to_tuples()
        assert len(result) == 2


class TestSinkToDataclasses:
    """Relation.to_dataclasses() returns list of dataclass instances."""

    def test_to_dataclasses(self, people_df):
        result = ma.relation(people_df).to_dataclasses(Person)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], Person)
        assert result[0].name == "Alice"
        assert result[0].age == 30

    def test_to_dataclasses_after_sort(self, people_df):
        result = ma.relation(people_df).sort("age").to_dataclasses(Person)
        assert result[0].name == "Bob"
        assert result[2].name == "Charlie"


class TestSinkToPydantic:
    """Relation.to_pydantic() returns list of Pydantic model instances."""

    def test_to_pydantic(self, people_df):
        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        class PersonModel(BaseModel):
            name: str
            age: int

        result = ma.relation(people_df).to_pydantic(PersonModel)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], PersonModel)
        assert result[0].name == "Alice"
        assert result[0].age == 30
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target-quick tests/alignment/test_sink.py -v`
Expected: FAIL with `AttributeError: 'Relation' object has no attribute 'to_tuples'`

- [ ] **Step 3: Add sink terminal methods to Relation**

Modify `src/mountainash/relations/core/relation_api/relation.py`. Add these methods to the `Relation` class:

```python
def to_tuples(self) -> list[tuple]:
    """Execute the plan and return rows as a list of tuples."""
    df = self.to_polars()
    return df.rows()

def to_dataclasses(self, cls: type) -> list:
    """Execute the plan and return rows as a list of dataclass instances.

    Args:
        cls: The dataclass type to instantiate for each row.

    Returns:
        List of dataclass instances.
    """
    rows = self.to_dicts()
    return [cls(**row) for row in rows]

def to_pydantic(self, cls: type) -> list:
    """Execute the plan and return rows as a list of Pydantic model instances.

    Args:
        cls: The Pydantic model class to instantiate for each row.

    Returns:
        List of Pydantic model instances.
    """
    rows = self.to_dicts()
    return [cls(**row) for row in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `hatch run test:test-target-quick tests/alignment/test_sink.py -v`
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/relations/core/relation_api/relation.py tests/alignment/test_sink.py
git commit -m "feat(relations): add sink terminal methods — to_tuples, to_dataclasses, to_pydantic"
```

---

### Task 5: SchemaBuilder — definition and apply

**Files:**
- Create: `src/mountainash/schema/schema_builder.py`
- Modify: `src/mountainash/__init__.py`
- Test: `tests/alignment/test_schema_builder.py`

- [ ] **Step 1: Write failing tests for SchemaBuilder definition and apply**

Create `tests/alignment/test_schema_builder.py`:

```python
"""Tests for SchemaBuilder — deferred schema API."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "age": ["30", "25", "35"],
        "full_name": ["Alice", "Bob", "Charlie"],
        "score": [1.5, None, 3.0],
    })


class TestSchemaBuilderDefinition:
    """ma.schema() creates a deferred SchemaBuilder."""

    def test_schema_returns_schema_builder(self):
        s = ma.schema({"age": {"cast": "integer"}})
        assert hasattr(s, "apply")
        assert hasattr(s, "columns")

    def test_schema_columns_property(self):
        s = ma.schema({
            "age": {"cast": "integer"},
            "name": {"cast": "string"},
        })
        assert s.columns == ["age", "name"]

    def test_schema_transforms_property(self):
        s = ma.schema({
            "age": {"cast": "integer"},
            "name": {"rename": "full_name"},
        })
        transforms = s.transforms
        assert "age" in transforms
        assert "name" in transforms


class TestSchemaBuilderApply:
    """SchemaBuilder.apply() transforms a DataFrame."""

    def test_apply_cast_integer(self, sample_df):
        s = ma.schema({"age": {"cast": "integer"}})
        result = s.apply(sample_df)
        assert isinstance(result, pl.DataFrame)
        assert result["age"].dtype == pl.Int64

    def test_apply_rename(self, sample_df):
        s = ma.schema({"name": {"rename": "full_name"}})
        result = s.apply(sample_df)
        assert "name" in result.columns

    def test_apply_null_fill(self, sample_df):
        s = ma.schema({"score": {"null_fill": 0.0}})
        result = s.apply(sample_df)
        assert result["score"].null_count() == 0
        assert result["score"].to_list() == [1.5, 0.0, 3.0]

    def test_apply_multi_transform(self, sample_df):
        s = ma.schema({
            "age": {"cast": "integer"},
            "score": {"null_fill": 0.0},
        })
        result = s.apply(sample_df)
        assert result["age"].dtype == pl.Int64
        assert result["score"].null_count() == 0

    def test_apply_strict_missing_column_raises(self, sample_df):
        s = ma.schema({"nonexistent": {"cast": "integer"}})
        with pytest.raises(Exception):
            s.apply(sample_df, strict=True)

    def test_apply_lenient_missing_column_skips(self, sample_df):
        s = ma.schema({"nonexistent": {"cast": "integer"}})
        result = s.apply(sample_df)
        # Should not raise, just skip the missing column
        assert result.shape == sample_df.shape
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target-quick tests/alignment/test_schema_builder.py -v`
Expected: FAIL with `AttributeError: module 'mountainash' has no attribute 'schema'`

- [ ] **Step 3: Implement SchemaBuilder**

Create `src/mountainash/schema/schema_builder.py`:

```python
"""SchemaBuilder — deferred schema definition, extraction, and validation.

Wraps existing SchemaConfig + CastSchemaFactory + extractors + validators
behind a build-then-execute API.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames


class SchemaBuilder:
    """Deferred schema definition with terminal methods.

    Build phase: ma.schema({...}) creates a SchemaBuilder holding the spec.
    Execute phase: .apply(df) constructs SchemaConfig, detects backend, transforms.

    Also provides class methods for extraction and validation.
    """

    def __init__(self, spec: Dict[str, Dict[str, Any]]) -> None:
        self._spec = spec

    @property
    def columns(self) -> list[str]:
        """Column names defined in this schema."""
        return list(self._spec.keys())

    @property
    def transforms(self) -> Dict[str, Dict[str, Any]]:
        """Summary of planned transforms per column."""
        return dict(self._spec)

    def apply(
        self,
        df: SupportedDataFrames,
        *,
        strict: bool = False,
    ) -> SupportedDataFrames:
        """Apply this schema transform to a DataFrame.

        Args:
            df: The DataFrame to transform.
            strict: If True, raise on missing columns. If False, skip them.

        Returns:
            Transformed DataFrame (same backend type as input).
        """
        from mountainash.schema.config import SchemaConfig
        from mountainash.schema.transform import CastSchemaFactory

        config = SchemaConfig(columns=self._spec, strict=strict)
        strategy = CastSchemaFactory.get_strategy(df)
        return strategy.apply(df, config)

    @classmethod
    def extract(cls, source: Any) -> SchemaBuilder:
        """Extract a schema from a DataFrame, dataclass, or Pydantic model.

        Args:
            source: A DataFrame, dataclass type, or Pydantic model type.

        Returns:
            SchemaBuilder with extracted column definitions.
        """
        from mountainash.schema.config.extractors import (
            extract_schema_from_dataframe,
            from_dataclass,
        )
        from mountainash.schema.config.universal_schema import TableSchema

        # Dataclass or Pydantic model (it's a type, not an instance)
        if isinstance(source, type):
            import dataclasses
            if dataclasses.is_dataclass(source):
                table_schema = from_dataclass(source)
                return cls._from_table_schema(table_schema)
            # Try Pydantic
            if hasattr(source, "__pydantic_core_schema__") or hasattr(source, "__fields__"):
                from mountainash.schema.config.extractors import from_pydantic
                table_schema = from_pydantic(source)
                return cls._from_table_schema(table_schema)

        # DataFrame instance
        table_schema = extract_schema_from_dataframe(source)
        return cls._from_table_schema(table_schema)

    @classmethod
    def _from_table_schema(cls, table_schema: Any) -> SchemaBuilder:
        """Convert a TableSchema to a SchemaBuilder spec."""
        spec = {}
        for field in table_schema.fields:
            field_spec: Dict[str, Any] = {}
            if field.type:
                field_spec["cast"] = field.type
            spec[field.name] = field_spec
        return cls(spec)

    def validate(self, df: SupportedDataFrames) -> Any:
        """Validate a DataFrame against this schema.

        Args:
            df: The DataFrame to validate.

        Returns:
            ValidationResult with is_valid and issues.
        """
        from mountainash.schema.config import SchemaConfig
        from mountainash.schema.config.schema_config import ValidationResult, ValidationIssue

        config = SchemaConfig(columns=self._spec)
        issues = []

        # Check for missing columns
        if hasattr(df, "columns"):
            df_columns = set(df.columns)
        else:
            df_columns = set()

        for col_name, col_spec in self._spec.items():
            # Check if source column exists (may be renamed)
            source_name = col_spec.get("rename", col_name)
            if source_name not in df_columns:
                issues.append(ValidationIssue(
                    type="missing_columns",
                    severity="error",
                    message=f"Column '{source_name}' not found in DataFrame",
                    columns=[source_name],
                ))

        is_valid = len(issues) == 0
        return ValidationResult(valid=is_valid, issues=issues)

    def __repr__(self) -> str:
        return f"SchemaBuilder(columns={self.columns})"
```

- [ ] **Step 4: Wire `ma.schema` entry point**

Modify `src/mountainash/__init__.py`. Add the import:

```python
from mountainash.schema.schema_builder import SchemaBuilder as schema  # noqa: F401
```

**Important:** This makes `ma.schema({...})` call `SchemaBuilder({...})` since `SchemaBuilder.__init__` takes a spec dict. And `ma.schema.extract(df)` calls the classmethod `SchemaBuilder.extract(df)`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `hatch run test:test-target-quick tests/alignment/test_schema_builder.py -v`
Expected: All PASSED

- [ ] **Step 6: Run full test suite to check for regressions**

Run: `hatch run test:test-target-quick tests/ -v --tb=short -x`
Expected: No new failures.

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/schema/schema_builder.py src/mountainash/__init__.py tests/alignment/test_schema_builder.py
git commit -m "feat(schema): add SchemaBuilder deferred API with ma.schema() entry point"
```

---

### Task 6: Schema extraction and validation tests

**Files:**
- Test: `tests/alignment/test_schema_builder.py`

- [ ] **Step 1: Write extraction and validation tests**

Append to `tests/alignment/test_schema_builder.py`:

```python
from dataclasses import dataclass as dc


@dc
class Employee:
    name: str
    age: int
    salary: float


class TestSchemaExtract:
    """ma.schema.extract() extracts schema from various sources."""

    def test_extract_from_polars_dataframe(self):
        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        s = ma.schema.extract(df)
        assert "a" in s.columns
        assert "b" in s.columns

    def test_extract_from_dataclass(self):
        s = ma.schema.extract(Employee)
        assert "name" in s.columns
        assert "age" in s.columns
        assert "salary" in s.columns

    def test_extract_returns_schema_builder(self):
        df = pl.DataFrame({"x": [1]})
        s = ma.schema.extract(df)
        assert hasattr(s, "apply")
        assert hasattr(s, "validate")

    def test_extract_from_pydantic(self):
        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        class Item(BaseModel):
            name: str
            price: float

        s = ma.schema.extract(Item)
        assert "name" in s.columns
        assert "price" in s.columns


class TestSchemaValidate:
    """ma.schema(spec).validate(df) checks conformance."""

    def test_validate_conforming(self):
        df = pl.DataFrame({"age": [30], "name": ["Alice"]})
        s = ma.schema({"age": {"cast": "integer"}, "name": {"cast": "string"}})
        report = s.validate(df)
        assert report.valid is True
        assert report.issues == []

    def test_validate_missing_column(self):
        df = pl.DataFrame({"age": [30]})
        s = ma.schema({"age": {"cast": "integer"}, "missing_col": {"cast": "string"}})
        report = s.validate(df)
        assert report.valid is False
        assert len(report.issues) >= 1
        assert report.issues[0].type == "missing_columns"

    def test_validate_renamed_column_checks_source(self):
        df = pl.DataFrame({"full_name": ["Alice"]})
        s = ma.schema({"name": {"rename": "full_name"}})
        report = s.validate(df)
        # Should pass — "full_name" exists as the source column
        assert report.valid is True
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/alignment/test_schema_builder.py -v`
Expected: All PASSED

If any `extract` tests fail due to missing extractors, check the exact function names in `mountainash.schema.config.extractors` and update the `SchemaBuilder.extract()` method accordingly.

- [ ] **Step 3: Commit**

```bash
git add tests/alignment/test_schema_builder.py
git commit -m "test(schema): add extraction and validation tests for SchemaBuilder"
```

---

### Task 7: Round-trip integration tests

**Files:**
- Test: `tests/alignment/test_roundtrip.py`

- [ ] **Step 1: Write round-trip tests**

Create `tests/alignment/test_roundtrip.py`:

```python
"""Round-trip integration tests: Python → relation transforms → Python."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

import mountainash as ma


@dataclass
class Product:
    name: str
    price: float


class TestRoundTripDicts:
    """Python dicts → relation → Python dicts."""

    def test_dicts_filter_to_dicts(self):
        data = [
            {"name": "Widget", "price": 9.99},
            {"name": "Gadget", "price": 24.99},
            {"name": "Doohickey", "price": 4.99},
        ]
        result = ma.relation(data).filter(
            ma.col("price").gt(5.0)
        ).sort("price").to_dicts()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Widget"
        assert result[1]["name"] == "Gadget"

    def test_dicts_select_to_dicts(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        result = ma.relation(data).select("a", "c").to_dicts()
        assert result == [{"a": 1, "c": 3}]


class TestRoundTripDataclasses:
    """Python dicts → relation → dataclass instances."""

    def test_dicts_to_dataclasses(self):
        data = [
            {"name": "Widget", "price": 9.99},
            {"name": "Gadget", "price": 24.99},
        ]
        result = ma.relation(data).sort("name").to_dataclasses(Product)

        assert len(result) == 2
        assert isinstance(result[0], Product)
        assert result[0].name == "Gadget"
        assert result[1].name == "Widget"

    def test_filter_to_dataclasses(self):
        data = [
            {"name": "Cheap", "price": 1.0},
            {"name": "Expensive", "price": 100.0},
        ]
        result = ma.relation(data).filter(
            ma.col("price").gt(50.0)
        ).to_dataclasses(Product)

        assert len(result) == 1
        assert result[0].name == "Expensive"
        assert result[0].price == 100.0


class TestRoundTripPydantic:
    """Python dicts → relation → Pydantic model instances."""

    def test_dicts_to_pydantic(self):
        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        class Item(BaseModel):
            name: str
            price: float

        data = [{"name": "Thing", "price": 5.0}]
        result = ma.relation(data).to_pydantic(Item)

        assert len(result) == 1
        assert isinstance(result[0], Item)
        assert result[0].name == "Thing"


class TestRoundTripWithSchema:
    """Python data → schema transform → relation → Python data."""

    def test_schema_apply_then_relation(self):
        import polars as pl

        # Raw data with string ages
        df = pl.DataFrame({"age": ["30", "25"], "name": ["Alice", "Bob"]})

        # Apply schema to cast types
        s = ma.schema({"age": {"cast": "integer"}})
        transformed = s.apply(df)

        # Then use relation for further transforms
        result = ma.relation(transformed).filter(
            ma.col("age").gt(28)
        ).to_dicts()

        assert len(result) == 1
        assert result[0]["name"] == "Alice"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/alignment/test_roundtrip.py -v`
Expected: All PASSED

- [ ] **Step 3: Run full test suite**

Run: `hatch run test:test-target-quick tests/ --tb=short`
Expected: No new failures beyond pre-existing ones.

- [ ] **Step 4: Commit**

```bash
git add tests/alignment/test_roundtrip.py
git commit -m "test(alignment): add round-trip integration tests — Python → relation → Python"
```

---

## Summary

| Task | What | New Tests |
|------|------|-----------|
| 1 | SourceRelNode (node class) | 3 |
| 2 | Visitor + relation() factory extension | 2 |
| 3 | Source transform + introspection tests | 7 |
| 4 | Sink terminals (to_tuples, to_dataclasses, to_pydantic) | 7 |
| 5 | SchemaBuilder (definition + apply) + ma.schema() | 8 |
| 6 | Schema extraction + validation tests | 7 |
| 7 | Round-trip integration tests | 6 |
| **Total** | | **~40 tests** |
