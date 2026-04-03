# TypeSpec & Conform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the monolithic `schema/` module with two focused modules — `typespec` (metadata) and `conform` (transforms) — eliminating ~2,800 lines of broken backend infrastructure by compiling transforms to the existing relations/expressions layer.

**Architecture:** `typespec/` holds the serializable type specification (Frictionless Table Schema-aligned). `conform/` compiles a TypeSpec into mountainash relation/expression operations. The entire `schema/` directory is deleted with no backward compatibility shim.

**Tech Stack:** Python dataclasses, mountainash expressions (col, lit, coalesce, cast), mountainash relations (relation, select, to_polars), Frictionless Table Schema JSON format.

---

## File Structure

**New files to create:**

| File | Responsibility |
|------|---------------|
| `src/mountainash/typespec/__init__.py` | Public API re-exports for typespec module |
| `src/mountainash/typespec/universal_types.py` | UniversalType enum, normalize_type(), backend type mappings |
| `src/mountainash/typespec/type_bridge.py` | UniversalType ↔ MountainashDtype interim mapping |
| `src/mountainash/typespec/spec.py` | TypeSpec, FieldSpec, FieldConstraints, SpecDiff, compare_specs() |
| `src/mountainash/typespec/extraction.py` | Extract TypeSpec from DataFrames, dataclasses, Pydantic models |
| `src/mountainash/typespec/validation.py` | Validate DataFrames against a TypeSpec |
| `src/mountainash/typespec/converters.py` | UniversalType → backend-specific type objects |
| `src/mountainash/typespec/custom_types.py` | CustomTypeRegistry, semantic converters |
| `src/mountainash/typespec/frictionless.py` | Frictionless Table Schema import/export |
| `src/mountainash/conform/__init__.py` | Public API re-exports for conform module |
| `src/mountainash/conform/builder.py` | ConformBuilder — user-facing DSL |
| `src/mountainash/conform/compiler.py` | Compiles TypeSpec → relation/expression plan |
| `tests/typespec/__init__.py` | Test package |
| `tests/typespec/conftest.py` | Shared fixtures for typespec tests |
| `tests/typespec/test_universal_types.py` | Type normalization & mapping tests |
| `tests/typespec/test_spec.py` | TypeSpec/FieldSpec data class tests |
| `tests/typespec/test_type_bridge.py` | Type bridge mapping tests |
| `tests/typespec/test_frictionless.py` | Frictionless import/export round-trip tests |
| `tests/typespec/test_extraction.py` | Extractor function tests |
| `tests/typespec/test_validation.py` | Validation function tests |
| `tests/typespec/test_converters.py` | Converter function tests |
| `tests/typespec/test_custom_types.py` | Custom type registry tests |
| `tests/conform/__init__.py` | Test package |
| `tests/conform/test_conform_builder.py` | ConformBuilder dict parsing, API surface |
| `tests/conform/test_conform_transforms.py` | Cross-backend parametrized conform tests |

**Files to modify:**

| File | Change |
|------|--------|
| `src/mountainash/__init__.py` | Replace `schema` import with `typespec`/`conform` entry points |

**Files to delete (entire `schema/` module):**

```
src/mountainash/schema/__init__.py
src/mountainash/schema/schema_builder.py
src/mountainash/schema/config/__init__.py
src/mountainash/schema/config/schema_config.py
src/mountainash/schema/config/types.py
src/mountainash/schema/config/universal_schema.py
src/mountainash/schema/config/extractors.py
src/mountainash/schema/config/validators.py
src/mountainash/schema/config/converters.py
src/mountainash/schema/config/custom_types.py
src/mountainash/schema/transform/__init__.py
src/mountainash/schema/transform/cast_schema_factory.py
src/mountainash/schema/transform/base_schema_transform_strategy.py
src/mountainash/schema/transform/cast_schema_polars.py
src/mountainash/schema/transform/cast_schema_pandas.py
src/mountainash/schema/transform/cast_schema_narwhals.py
src/mountainash/schema/transform/cast_schema_ibis.py
src/mountainash/schema/transform/cast_schema_pyarrow.py
src/mountainash/schema/column_mapper/__init__.py
tests/schema/ (entire directory)
```

---

### Task 1: Create `typespec/universal_types.py` and `typespec/type_bridge.py`

The foundation — the type system that everything else depends on.

**Files:**
- Create: `src/mountainash/typespec/__init__.py`
- Create: `src/mountainash/typespec/universal_types.py`
- Create: `src/mountainash/typespec/type_bridge.py`
- Create: `tests/typespec/__init__.py`
- Create: `tests/typespec/test_universal_types.py`
- Create: `tests/typespec/test_type_bridge.py`
- Read: `src/mountainash/schema/config/types.py` (source for move)
- Read: `src/mountainash/core/dtypes.py` (MountainashDtype for bridge)

- [ ] **Step 1: Write failing tests for type bridge**

Create `tests/typespec/__init__.py` (empty file) and `tests/typespec/test_type_bridge.py`:

```python
"""Tests for UniversalType ↔ MountainashDtype bridge mapping."""
from __future__ import annotations

import pytest

from mountainash.typespec.type_bridge import bridge_type, UNIVERSAL_TO_MOUNTAINASH
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import MountainashDtype


class TestBridgeType:
    """bridge_type() converts UniversalType to MountainashDtype."""

    def test_string(self):
        assert bridge_type(UniversalType.STRING) == MountainashDtype.STRING

    def test_integer(self):
        assert bridge_type(UniversalType.INTEGER) == MountainashDtype.I64

    def test_number(self):
        assert bridge_type(UniversalType.NUMBER) == MountainashDtype.FP64

    def test_boolean(self):
        assert bridge_type(UniversalType.BOOLEAN) == MountainashDtype.BOOL

    def test_date(self):
        assert bridge_type(UniversalType.DATE) == MountainashDtype.DATE

    def test_time(self):
        assert bridge_type(UniversalType.TIME) == MountainashDtype.TIME

    def test_datetime(self):
        assert bridge_type(UniversalType.DATETIME) == MountainashDtype.TIMESTAMP

    def test_unsupported_raises(self):
        with pytest.raises(ValueError, match="No MountainashDtype mapping"):
            bridge_type(UniversalType.DURATION)

    def test_any_raises(self):
        with pytest.raises(ValueError, match="No MountainashDtype mapping"):
            bridge_type(UniversalType.ANY)


class TestMappingCompleteness:
    """UNIVERSAL_TO_MOUNTAINASH covers all bridgeable types."""

    def test_seven_types_mapped(self):
        assert len(UNIVERSAL_TO_MOUNTAINASH) == 7

    def test_all_mapped_types_are_valid(self):
        for ut, md in UNIVERSAL_TO_MOUNTAINASH.items():
            assert isinstance(ut, UniversalType)
            assert isinstance(md, MountainashDtype)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/typespec/test_type_bridge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mountainash.typespec'`

- [ ] **Step 3: Create typespec package and move universal_types.py**

Create `src/mountainash/typespec/__init__.py`:

```python
"""TypeSpec — backend-agnostic data type specification and metadata.

Provides:
- UniversalType: Frictionless Table Schema-aligned type enum
- TypeSpec/FieldSpec: Serializable type specifications
- Extraction: Infer TypeSpec from DataFrames, dataclasses, Pydantic models
- Validation: Check DataFrames against a TypeSpec
- Converters: UniversalType → backend-specific types
- Frictionless: Import/export Frictionless Table Schema JSON
"""
from mountainash.typespec.universal_types import (
    UniversalType,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    get_arrow_type,
    get_universal_to_backend_mapping,
    get_backend_to_universal_mapping,
    UNIVERSAL_TO_PANDAS,
    SAFE_CASTS,
    UNSAFE_CASTS,
)
from mountainash.typespec.type_bridge import bridge_type, UNIVERSAL_TO_MOUNTAINASH
from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints, SpecDiff, compare_specs

__all__ = [
    # Types
    "UniversalType",
    "normalize_type",
    "is_safe_cast",
    "get_polars_type",
    "get_arrow_type",
    "get_universal_to_backend_mapping",
    "get_backend_to_universal_mapping",
    "UNIVERSAL_TO_PANDAS",
    "SAFE_CASTS",
    "UNSAFE_CASTS",
    # Bridge
    "bridge_type",
    "UNIVERSAL_TO_MOUNTAINASH",
    # Spec
    "TypeSpec",
    "FieldSpec",
    "FieldConstraints",
    "SpecDiff",
    "compare_specs",
]
```

Create `src/mountainash/typespec/universal_types.py` — copy the entire contents of `src/mountainash/schema/config/types.py` verbatim. This is a move, not a rewrite. The only change is the module path.

Create `src/mountainash/typespec/type_bridge.py`:

```python
"""Interim bridge between UniversalType and MountainashDtype.

Maps the Frictionless-aligned UniversalType enum to the Substrait-aligned
MountainashDtype enum so that the conform compiler can generate .cast()
expressions.

This bridge will be removed when the two type systems are unified.
"""
from __future__ import annotations

from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import MountainashDtype


UNIVERSAL_TO_MOUNTAINASH: dict[UniversalType, MountainashDtype] = {
    UniversalType.STRING:   MountainashDtype.STRING,
    UniversalType.INTEGER:  MountainashDtype.I64,
    UniversalType.NUMBER:   MountainashDtype.FP64,
    UniversalType.BOOLEAN:  MountainashDtype.BOOL,
    UniversalType.DATE:     MountainashDtype.DATE,
    UniversalType.TIME:     MountainashDtype.TIME,
    UniversalType.DATETIME: MountainashDtype.TIMESTAMP,
}


def bridge_type(universal: UniversalType) -> MountainashDtype:
    """Convert UniversalType to MountainashDtype for expression compilation.

    Args:
        universal: A UniversalType enum member.

    Returns:
        The corresponding MountainashDtype.

    Raises:
        ValueError: If the UniversalType has no MountainashDtype equivalent.
            Currently unsupported: DURATION, YEAR, YEARMONTH, ARRAY, OBJECT, ANY.
    """
    if universal not in UNIVERSAL_TO_MOUNTAINASH:
        raise ValueError(
            f"No MountainashDtype mapping for {universal}. "
            f"Supported: {list(UNIVERSAL_TO_MOUNTAINASH.keys())}"
        )
    return UNIVERSAL_TO_MOUNTAINASH[universal]
```

- [ ] **Step 4: Run type bridge tests to verify they pass**

Run: `hatch run test:test-target tests/typespec/test_type_bridge.py -v`
Expected: PASS (all 10 tests)

- [ ] **Step 5: Write and run universal types tests**

Create `tests/typespec/test_universal_types.py` — copy `tests/schema/test_universal_types.py` verbatim, then update all imports from `mountainash.schema.config.types` to `mountainash.typespec.universal_types`:

Replace:
```python
from mountainash.schema.config.types import UniversalType, normalize_type, is_safe_cast, ...
```
With:
```python
from mountainash.typespec.universal_types import UniversalType, normalize_type, is_safe_cast, ...
```

Run: `hatch run test:test-target tests/typespec/test_universal_types.py -v`
Expected: PASS (all existing type tests pass against the moved module)

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/typespec/ tests/typespec/
git commit -m "feat: create typespec module with universal types and type bridge"
```

---

### Task 2: Create `typespec/spec.py` — TypeSpec, FieldSpec, FieldConstraints

The core data classes that replace `TableSchema`, `SchemaField`, and `SchemaDiff`.

**Files:**
- Create: `src/mountainash/typespec/spec.py`
- Create: `tests/typespec/test_spec.py`
- Read: `src/mountainash/schema/config/universal_schema.py` (source)

- [ ] **Step 1: Write failing tests for TypeSpec/FieldSpec**

Create `tests/typespec/test_spec.py`:

```python
"""Tests for TypeSpec, FieldSpec, FieldConstraints data classes."""
from __future__ import annotations

import pytest

from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints, SpecDiff, compare_specs
from mountainash.typespec.universal_types import UniversalType


class TestFieldSpec:
    """FieldSpec data class behavior."""

    def test_source_name_defaults_to_name(self):
        field = FieldSpec(name="user_id", type=UniversalType.INTEGER)
        assert field.source_name == "user_id"

    def test_source_name_uses_rename_from(self):
        field = FieldSpec(name="user_id", type=UniversalType.INTEGER, rename_from="raw_id")
        assert field.source_name == "raw_id"

    def test_default_type_is_string(self):
        field = FieldSpec(name="col")
        assert field.type == UniversalType.STRING

    def test_null_fill_default_is_none(self):
        field = FieldSpec(name="col")
        assert field.null_fill is None

    def test_to_dict_minimal(self):
        field = FieldSpec(name="id", type=UniversalType.INTEGER)
        d = field.to_dict()
        assert d == {"name": "id", "type": "integer"}

    def test_to_dict_with_constraints(self):
        field = FieldSpec(
            name="age",
            type=UniversalType.INTEGER,
            constraints=FieldConstraints(required=True, minimum=0),
        )
        d = field.to_dict()
        assert d["constraints"]["required"] is True
        assert d["constraints"]["minimum"] == 0


class TestTypeSpec:
    """TypeSpec data class behavior."""

    def test_from_simple_dict(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        assert len(spec.fields) == 2
        assert spec.fields[0].name == "id"
        assert spec.fields[0].type == UniversalType.INTEGER
        assert spec.fields[1].name == "name"
        assert spec.fields[1].type == UniversalType.STRING

    def test_field_names_property(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        assert spec.field_names == ["id", "name"]

    def test_get_field_by_name(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        field = spec.get_field("name")
        assert field is not None
        assert field.type == UniversalType.STRING

    def test_get_field_missing_returns_none(self):
        spec = TypeSpec.from_simple_dict({"id": "integer"})
        assert spec.get_field("nonexistent") is None

    def test_keep_only_mapped_default_false(self):
        spec = TypeSpec(fields=[])
        assert spec.keep_only_mapped is False

    def test_to_dict(self):
        spec = TypeSpec.from_simple_dict(
            {"id": "integer"},
            title="Test",
            description="A test spec",
        )
        d = spec.to_dict()
        assert d["title"] == "Test"
        assert d["description"] == "A test spec"
        assert len(d["fields"]) == 1


class TestSpecDiff:
    """SpecDiff and compare_specs behavior."""

    def test_identical_specs_no_diff(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        diff = compare_specs(spec, spec)
        assert not diff.has_changes
        assert diff.is_compatible

    def test_added_field_detected(self):
        source = TypeSpec.from_simple_dict({"id": "integer"})
        target = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        diff = compare_specs(source, target)
        assert "name" in diff.added_fields

    def test_removed_field_detected(self):
        source = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        target = TypeSpec.from_simple_dict({"id": "integer"})
        diff = compare_specs(source, target)
        assert "name" in diff.removed_fields

    def test_type_change_detected(self):
        source = TypeSpec.from_simple_dict({"id": "integer"})
        target = TypeSpec.from_simple_dict({"id": "string"})
        diff = compare_specs(source, target)
        assert "id" in diff.type_changes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/typespec/test_spec.py -v`
Expected: FAIL — `ImportError: cannot import name 'TypeSpec' from 'mountainash.typespec.spec'`

- [ ] **Step 3: Create spec.py**

Create `src/mountainash/typespec/spec.py`. This is based on `src/mountainash/schema/config/universal_schema.py` with these changes:
- `TableSchema` → `TypeSpec`
- `SchemaField` → `FieldSpec`
- `SchemaDiff` → `SpecDiff`
- `compare_schemas()` → `compare_specs()`
- Add `null_fill`, `rename_from`, `source_name`, `keep_only_mapped` fields per spec
- Import from `mountainash.typespec.universal_types` instead of `.types`

```python
"""TypeSpec — backend-agnostic data type specification.

Based on the Frictionless Table Schema specification with mountainash extensions
for conformance operations (rename, null_fill, keep_only_mapped).

This module is backend-agnostic and has ZERO imports of DataFrame libraries.

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .universal_types import UniversalType, normalize_type


@dataclass
class FieldConstraints:
    """Constraints for a field (Frictionless Table Schema compliant)."""

    required: bool = False
    unique: bool = False
    minimum: Optional[Any] = None
    maximum: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None


@dataclass
class FieldSpec:
    """A single field in a TypeSpec.

    Combines Frictionless Table Schema field definition with mountainash
    conformance extensions (rename_from, null_fill).
    """

    name: str
    type: UniversalType = UniversalType.STRING
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[List[str]] = None
    true_values: Optional[List[str]] = None
    false_values: Optional[List[str]] = None
    backend_type: Optional[str] = None
    # Mountainash conformance extensions
    null_fill: Any = None
    rename_from: Optional[str] = None

    @property
    def source_name(self) -> str:
        """The column name to read from the source DataFrame."""
        return self.rename_from or self.name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Frictionless-compatible dict."""
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.type.value if isinstance(self.type, UniversalType) else str(self.type),
        }
        if self.format != "default":
            result["format"] = self.format
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.constraints:
            result["constraints"] = {
                k: v for k, v in self.constraints.__dict__.items() if v is not None and v is not False
            }
        if self.missing_values:
            result["missingValues"] = self.missing_values
        if self.backend_type:
            result["backend_type"] = self.backend_type
        return result


@dataclass
class TypeSpec:
    """A serializable specification of data types and conformance rules.

    Based on Frictionless Table Schema with mountainash extensions.
    """

    fields: List[FieldSpec] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    primary_key: Optional[Union[str, List[str]]] = None
    missing_values: Optional[List[str]] = field(default_factory=lambda: [""])
    keep_only_mapped: bool = False

    @classmethod
    def from_simple_dict(cls, columns: Dict[str, str], **metadata) -> TypeSpec:
        """Create TypeSpec from a simple {name: type_string} dict.

        Args:
            columns: Dict mapping column names to type strings (e.g. "integer", "string")
            **metadata: Additional metadata (title, description, primary_key)

        Returns:
            TypeSpec with fields derived from the dict

        Example:
            >>> spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        """
        fields = []
        for col_name, type_str in columns.items():
            universal_type = normalize_type(type_str)
            fields.append(FieldSpec(name=col_name, type=universal_type))
        return cls(
            fields=fields,
            title=metadata.get("title"),
            description=metadata.get("description"),
            primary_key=metadata.get("primary_key"),
        )

    @classmethod
    def from_frictionless(cls, data: 'dict | str') -> TypeSpec:
        """Import from Frictionless Table Schema."""
        from .frictionless import from_frictionless
        return from_frictionless(data)

    def to_frictionless(self) -> dict:
        """Export as Frictionless Table Schema dict."""
        from .frictionless import to_frictionless
        return to_frictionless(self)

    def get_field(self, name: str) -> Optional[FieldSpec]:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @property
    def field_names(self) -> List[str]:
        """Get list of field names."""
        return [f.name for f in self.fields]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Frictionless-compatible dict."""
        result: Dict[str, Any] = {
            "fields": [f.to_dict() for f in self.fields],
        }
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.primary_key:
            result["primaryKey"] = self.primary_key
        if self.missing_values:
            result["missingValues"] = self.missing_values
        return result


@dataclass
class SpecDiff:
    """Result of comparing two TypeSpecs."""

    added_fields: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    type_changes: Dict[str, tuple] = field(default_factory=dict)
    is_compatible: bool = True

    @property
    def has_changes(self) -> bool:
        return bool(self.added_fields or self.removed_fields or self.type_changes)

    @property
    def missing_columns(self) -> List[str]:
        """Columns present in expected (target) but absent in actual (source)."""
        return self.added_fields

    @property
    def extra_columns(self) -> List[str]:
        """Columns present in actual (source) but absent in expected (target)."""
        return self.removed_fields

    @property
    def type_mismatches(self) -> List[tuple]:
        """List of (column, actual_type, expected_type) tuples."""
        return [(col, actual, expected) for col, (actual, expected) in self.type_changes.items()]


def compare_specs(
    source: TypeSpec,
    target: TypeSpec,
    check_constraints: bool = True,
) -> SpecDiff:
    """Compare two TypeSpecs and return a SpecDiff.

    Args:
        source: The actual / output spec
        target: The expected spec to compare against
        check_constraints: Reserved for future constraint comparison

    Returns:
        SpecDiff describing the differences
    """
    source_names = set(source.field_names)
    target_names = set(target.field_names)

    diff = SpecDiff(
        added_fields=sorted(target_names - source_names),
        removed_fields=sorted(source_names - target_names),
    )

    for name in source_names & target_names:
        source_field = source.get_field(name)
        target_field = target.get_field(name)
        if source_field and target_field and source_field.type != target_field.type:
            diff.type_changes[name] = (source_field.type, target_field.type)

    diff.is_compatible = not diff.added_fields and not diff.type_changes
    return diff
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `hatch run test:test-target tests/typespec/test_spec.py -v`
Expected: PASS (all 14 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/typespec/spec.py tests/typespec/test_spec.py
git commit -m "feat: add TypeSpec, FieldSpec, FieldConstraints data classes"
```

---

### Task 3: Create `typespec/frictionless.py` — Frictionless Table Schema import/export

**Files:**
- Create: `src/mountainash/typespec/frictionless.py`
- Create: `tests/typespec/test_frictionless.py`

- [ ] **Step 1: Write failing tests for Frictionless round-trip**

Create `tests/typespec/test_frictionless.py`:

```python
"""Tests for Frictionless Table Schema import/export."""
from __future__ import annotations

import json
import pytest

from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.frictionless import to_frictionless, from_frictionless


class TestToFrictionless:
    """Export TypeSpec → Frictionless dict."""

    def test_minimal_spec(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        result = to_frictionless(spec)
        assert len(result["fields"]) == 2
        assert result["fields"][0] == {"name": "id", "type": "integer"}
        assert result["fields"][1] == {"name": "name", "type": "string"}

    def test_spec_with_title_description(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            title="Employees",
            description="Employee records",
        )
        result = to_frictionless(spec)
        assert result["title"] == "Employees"
        assert result["description"] == "Employee records"

    def test_primary_key_exported(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            primary_key="id",
        )
        result = to_frictionless(spec)
        assert result["primaryKey"] == "id"

    def test_constraints_exported(self):
        spec = TypeSpec(fields=[
            FieldSpec(
                name="age",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(required=True, minimum=0, maximum=150),
            ),
        ])
        result = to_frictionless(spec)
        constraints = result["fields"][0]["constraints"]
        assert constraints["required"] is True
        assert constraints["minimum"] == 0
        assert constraints["maximum"] == 150

    def test_rename_from_in_x_mountainash(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="user_id", type=UniversalType.INTEGER, rename_from="raw_id"),
        ])
        result = to_frictionless(spec)
        assert result["fields"][0]["x-mountainash"]["rename_from"] == "raw_id"

    def test_null_fill_in_x_mountainash(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="email", type=UniversalType.STRING, null_fill="unknown"),
        ])
        result = to_frictionless(spec)
        assert result["fields"][0]["x-mountainash"]["null_fill"] == "unknown"

    def test_keep_only_mapped_in_x_mountainash(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            keep_only_mapped=True,
        )
        result = to_frictionless(spec)
        assert result["x-mountainash"]["keep_only_mapped"] is True

    def test_no_x_mountainash_when_no_extensions(self):
        spec = TypeSpec.from_simple_dict({"id": "integer"})
        result = to_frictionless(spec)
        assert "x-mountainash" not in result
        assert "x-mountainash" not in result["fields"][0]


class TestFromFrictionless:
    """Import Frictionless dict → TypeSpec."""

    def test_minimal_import(self):
        data = {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
            ]
        }
        spec = from_frictionless(data)
        assert len(spec.fields) == 2
        assert spec.fields[0].name == "id"
        assert spec.fields[0].type == UniversalType.INTEGER

    def test_title_description_imported(self):
        data = {
            "fields": [{"name": "id", "type": "integer"}],
            "title": "Test",
            "description": "A test",
        }
        spec = from_frictionless(data)
        assert spec.title == "Test"
        assert spec.description == "A test"

    def test_primary_key_imported(self):
        data = {
            "fields": [{"name": "id", "type": "integer"}],
            "primaryKey": "id",
        }
        spec = from_frictionless(data)
        assert spec.primary_key == "id"

    def test_constraints_imported(self):
        data = {
            "fields": [{
                "name": "age",
                "type": "integer",
                "constraints": {"required": True, "minimum": 0},
            }],
        }
        spec = from_frictionless(data)
        assert spec.fields[0].constraints is not None
        assert spec.fields[0].constraints.required is True
        assert spec.fields[0].constraints.minimum == 0

    def test_x_mountainash_rename_from_imported(self):
        data = {
            "fields": [{
                "name": "user_id",
                "type": "integer",
                "x-mountainash": {"rename_from": "raw_id"},
            }],
        }
        spec = from_frictionless(data)
        assert spec.fields[0].rename_from == "raw_id"

    def test_x_mountainash_null_fill_imported(self):
        data = {
            "fields": [{
                "name": "email",
                "type": "string",
                "x-mountainash": {"null_fill": "unknown"},
            }],
        }
        spec = from_frictionless(data)
        assert spec.fields[0].null_fill == "unknown"

    def test_x_mountainash_keep_only_mapped_imported(self):
        data = {
            "fields": [{"name": "id", "type": "integer"}],
            "x-mountainash": {"keep_only_mapped": True},
        }
        spec = from_frictionless(data)
        assert spec.keep_only_mapped is True

    def test_missing_type_defaults_to_string(self):
        data = {"fields": [{"name": "col"}]}
        spec = from_frictionless(data)
        assert spec.fields[0].type == UniversalType.STRING

    def test_unknown_extensions_ignored(self):
        data = {
            "fields": [{"name": "id", "type": "integer", "x-other-tool": {"foo": "bar"}}],
        }
        spec = from_frictionless(data)
        assert spec.fields[0].name == "id"


class TestRoundTrip:
    """Export then import should preserve all data."""

    def test_full_round_trip(self):
        original = TypeSpec(
            fields=[
                FieldSpec(
                    name="user_id",
                    type=UniversalType.INTEGER,
                    rename_from="raw_id",
                    title="User ID",
                    description="Primary key",
                    constraints=FieldConstraints(required=True, unique=True),
                ),
                FieldSpec(
                    name="email",
                    type=UniversalType.STRING,
                    null_fill="unknown",
                ),
                FieldSpec(
                    name="score",
                    type=UniversalType.NUMBER,
                ),
            ],
            title="Users",
            description="User records",
            primary_key="user_id",
            keep_only_mapped=True,
        )
        exported = to_frictionless(original)
        reimported = from_frictionless(exported)

        assert reimported.title == "Users"
        assert reimported.description == "User records"
        assert reimported.primary_key == "user_id"
        assert reimported.keep_only_mapped is True
        assert len(reimported.fields) == 3
        assert reimported.fields[0].rename_from == "raw_id"
        assert reimported.fields[0].constraints.required is True
        assert reimported.fields[1].null_fill == "unknown"
        assert reimported.fields[2].type == UniversalType.NUMBER

    def test_json_serializable(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw"),
        ], keep_only_mapped=True)
        exported = to_frictionless(spec)
        json_str = json.dumps(exported)
        reimported = from_frictionless(json.loads(json_str))
        assert reimported.fields[0].rename_from == "raw"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/typespec/test_frictionless.py -v`
Expected: FAIL — `ImportError: cannot import name 'to_frictionless' from 'mountainash.typespec.frictionless'`

- [ ] **Step 3: Implement frictionless.py**

Create `src/mountainash/typespec/frictionless.py`:

```python
"""Frictionless Table Schema import/export for TypeSpec.

Converts between TypeSpec and the Frictionless Table Schema JSON format.
Mountainash-specific extensions (rename_from, null_fill, keep_only_mapped)
are stored in 'x-mountainash' namespaced keys per Frictionless convention.

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .spec import TypeSpec, FieldSpec, FieldConstraints
from .universal_types import UniversalType, normalize_type


def to_frictionless(spec: TypeSpec) -> dict:
    """Convert TypeSpec to Frictionless Table Schema dict.

    Standard Frictionless fields go in their standard locations.
    Mountainash-specific extensions (rename_from, null_fill, keep_only_mapped)
    go in 'x-mountainash' namespaced keys per Frictionless convention.
    """
    result: dict = {"fields": []}

    for field in spec.fields:
        fd: dict = {
            "name": field.name,
            "type": field.type.value if isinstance(field.type, UniversalType) else str(field.type),
        }
        if field.format != "default":
            fd["format"] = field.format
        if field.title:
            fd["title"] = field.title
        if field.description:
            fd["description"] = field.description
        if field.constraints:
            fd["constraints"] = _constraints_to_dict(field.constraints)
        if field.missing_values:
            fd["missingValues"] = field.missing_values

        # Mountainash extensions
        ma_ext: dict = {}
        if field.rename_from:
            ma_ext["rename_from"] = field.rename_from
        if field.null_fill is not None:
            ma_ext["null_fill"] = field.null_fill
        if ma_ext:
            fd["x-mountainash"] = ma_ext

        result["fields"].append(fd)

    # Spec-level standard fields
    if spec.title:
        result["title"] = spec.title
    if spec.description:
        result["description"] = spec.description
    if spec.primary_key:
        result["primaryKey"] = spec.primary_key
    if spec.missing_values:
        result["missingValues"] = spec.missing_values

    # Spec-level mountainash extensions
    if spec.keep_only_mapped:
        result.setdefault("x-mountainash", {})["keep_only_mapped"] = True

    return result


def from_frictionless(data: Union[dict, str, Path]) -> TypeSpec:
    """Create TypeSpec from Frictionless Table Schema.

    Args:
        data: Dict, JSON string, or path to .json file.

    Recognizes standard Frictionless fields and x-mountainash extensions.
    Unknown extensions are silently ignored.
    """
    if isinstance(data, Path):
        data = json.loads(data.read_text())
    elif isinstance(data, str):
        # Could be JSON string or file path
        path = Path(data)
        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = json.loads(data)

    fields = []
    for fd in data.get("fields", []):
        ma_ext = fd.get("x-mountainash", {})
        fields.append(FieldSpec(
            name=fd["name"],
            type=normalize_type(fd.get("type", "string")),
            format=fd.get("format", "default"),
            title=fd.get("title"),
            description=fd.get("description"),
            constraints=_parse_constraints(fd.get("constraints")),
            missing_values=fd.get("missingValues"),
            rename_from=ma_ext.get("rename_from"),
            null_fill=ma_ext.get("null_fill"),
        ))

    spec_ext = data.get("x-mountainash", {})
    return TypeSpec(
        fields=fields,
        title=data.get("title"),
        description=data.get("description"),
        primary_key=data.get("primaryKey"),
        missing_values=data.get("missingValues"),
        keep_only_mapped=spec_ext.get("keep_only_mapped", False),
    )


def _constraints_to_dict(constraints: FieldConstraints) -> dict:
    """Convert FieldConstraints to a dict, omitting defaults."""
    result = {}
    if constraints.required:
        result["required"] = True
    if constraints.unique:
        result["unique"] = True
    if constraints.minimum is not None:
        result["minimum"] = constraints.minimum
    if constraints.maximum is not None:
        result["maximum"] = constraints.maximum
    if constraints.min_length is not None:
        result["minLength"] = constraints.min_length
    if constraints.max_length is not None:
        result["maxLength"] = constraints.max_length
    if constraints.pattern is not None:
        result["pattern"] = constraints.pattern
    if constraints.enum is not None:
        result["enum"] = constraints.enum
    return result


def _parse_constraints(data: Optional[dict]) -> Optional[FieldConstraints]:
    """Parse a Frictionless constraints dict into FieldConstraints."""
    if not data:
        return None
    return FieldConstraints(
        required=data.get("required", False),
        unique=data.get("unique", False),
        minimum=data.get("minimum"),
        maximum=data.get("maximum"),
        min_length=data.get("minLength"),
        max_length=data.get("maxLength"),
        pattern=data.get("pattern"),
        enum=data.get("enum"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `hatch run test:test-target tests/typespec/test_frictionless.py -v`
Expected: PASS (all 19 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/typespec/frictionless.py tests/typespec/test_frictionless.py
git commit -m "feat: add Frictionless Table Schema import/export for TypeSpec"
```

---

### Task 4: Move remaining typespec modules (extraction, validation, converters, custom_types)

These are bulk moves with import path updates and class renames.

**Files:**
- Create: `src/mountainash/typespec/extraction.py`
- Create: `src/mountainash/typespec/validation.py`
- Create: `src/mountainash/typespec/converters.py`
- Create: `src/mountainash/typespec/custom_types.py`
- Create: `tests/typespec/conftest.py`
- Create: `tests/typespec/test_extraction.py`
- Create: `tests/typespec/test_validation.py`
- Create: `tests/typespec/test_converters.py`
- Create: `tests/typespec/test_custom_types.py`
- Read: `src/mountainash/schema/config/extractors.py` (source)
- Read: `src/mountainash/schema/config/validators.py` (source)
- Read: `src/mountainash/schema/config/converters.py` (source)
- Read: `src/mountainash/schema/config/custom_types.py` (source)
- Read: `tests/schema/conftest.py` (source for fixtures)

- [ ] **Step 1: Create typespec conftest.py**

Create `tests/typespec/conftest.py` — copy `tests/schema/conftest.py` verbatim, then update all imports:

Replace:
```python
from mountainash.schema.config.types import UniversalType
from mountainash.schema.config.universal_schema import FieldConstraints, SchemaField, TableSchema
from mountainash.schema.config.custom_types import CustomTypeRegistry, _register_standard_converters
```
With:
```python
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.spec import FieldConstraints, FieldSpec, TypeSpec
from mountainash.typespec.custom_types import CustomTypeRegistry, _register_standard_converters
```

Also rename fixture types:
- `simple_table_schema` fixture: change `TableSchema.from_simple_dict` → `TypeSpec.from_simple_dict`
- `full_table_schema` fixture: change `SchemaField(` → `FieldSpec(`, `TableSchema(` → `TypeSpec(`
- `source_schema` fixture: change `TableSchema.from_simple_dict` → `TypeSpec.from_simple_dict`
- `target_schema` fixture: change `TableSchema.from_simple_dict` → `TypeSpec.from_simple_dict`

Keep all fixture names and DataFrame fixtures identical.

- [ ] **Step 2: Move extraction.py**

Create `src/mountainash/typespec/extraction.py` — copy `src/mountainash/schema/config/extractors.py` verbatim, then:

1. Replace all `from mountainash.schema.config.types import` → `from mountainash.typespec.universal_types import`
2. Replace all `from mountainash.schema.config.universal_schema import` → `from mountainash.typespec.spec import`
3. Replace `TableSchema` → `TypeSpec` throughout
4. Replace `SchemaField` → `FieldSpec` throughout
5. Rename public functions:
   - `from_dataframe` → `extract_from_dataframe`
   - `from_dataclass` → `extract_from_dataclass`
   - `from_pydantic` → `extract_from_pydantic`
   - Keep `extract_schema_from_dataframe` as alias for `extract_from_dataframe`

Create `tests/typespec/test_extraction.py` — copy `tests/schema/test_schema_extractors.py` verbatim, then update all imports from `mountainash.schema.config.*` to `mountainash.typespec.*` and rename `TableSchema` → `TypeSpec`, `SchemaField` → `FieldSpec`, function names as above.

Run: `hatch run test:test-target tests/typespec/test_extraction.py -v`
Expected: PASS

- [ ] **Step 3: Move validation.py**

Create `src/mountainash/typespec/validation.py` — copy `src/mountainash/schema/config/validators.py` verbatim, then:

1. Replace all `from mountainash.schema.config.*` → `from mountainash.typespec.*`
2. Replace `TableSchema` → `TypeSpec`, `SchemaField` → `FieldSpec`
3. Rename: `validate_schema_match` → `validate_match`, `assert_schema_match` → `assert_match`
4. Remove `validate_transformation_config` and `assert_transformation_config` (transform config no longer exists)
5. Update `compare_schemas` → `compare_specs` references

Create `tests/typespec/test_validation.py` — copy `tests/schema/test_schema_validators.py` verbatim, then update imports and names. Remove any tests for `validate_transformation_config` / `assert_transformation_config`.

Run: `hatch run test:test-target tests/typespec/test_validation.py -v`
Expected: PASS

- [ ] **Step 4: Move converters.py**

Create `src/mountainash/typespec/converters.py` — copy `src/mountainash/schema/config/converters.py` verbatim, then update imports from `mountainash.schema.config.*` to `mountainash.typespec.*` and `TableSchema` → `TypeSpec`.

Create `tests/typespec/test_converters.py` — copy `tests/schema/test_schema_converters.py` verbatim, then update imports.

Run: `hatch run test:test-target tests/typespec/test_converters.py -v`
Expected: PASS

- [ ] **Step 5: Move custom_types.py**

Create `src/mountainash/typespec/custom_types.py` — copy `src/mountainash/schema/config/custom_types.py` verbatim, then update imports from `mountainash.schema.config.*` to `mountainash.typespec.*`.

Create `tests/typespec/test_custom_types.py` — copy `tests/schema/test_custom_types.py` verbatim, then update imports.

Run: `hatch run test:test-target tests/typespec/test_custom_types.py -v`
Expected: PASS

- [ ] **Step 6: Update typespec/__init__.py with all exports**

Update `src/mountainash/typespec/__init__.py` to add exports for extraction, validation, converters, and custom_types:

```python
"""TypeSpec — backend-agnostic data type specification and metadata.

Provides:
- UniversalType: Frictionless Table Schema-aligned type enum
- TypeSpec/FieldSpec: Serializable type specifications
- Extraction: Infer TypeSpec from DataFrames, dataclasses, Pydantic models
- Validation: Check DataFrames against a TypeSpec
- Converters: UniversalType → backend-specific types
- Custom Types: CustomTypeRegistry for semantic converters
- Frictionless: Import/export Frictionless Table Schema JSON
"""
from mountainash.typespec.universal_types import (
    UniversalType,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    get_arrow_type,
    get_universal_to_backend_mapping,
    get_backend_to_universal_mapping,
    UNIVERSAL_TO_PANDAS,
    SAFE_CASTS,
    UNSAFE_CASTS,
)
from mountainash.typespec.type_bridge import bridge_type, UNIVERSAL_TO_MOUNTAINASH
from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints, SpecDiff, compare_specs
from mountainash.typespec.extraction import (
    extract_from_dataframe,
    extract_from_dataclass,
    extract_from_pydantic,
)
from mountainash.typespec.validation import (
    SchemaValidationError,
    validate_round_trip,
    assert_round_trip,
    validate_match,
    assert_match,
)
from mountainash.typespec.converters import (
    to_polars_schema,
    to_pandas_dtypes,
    to_arrow_schema,
    to_ibis_schema,
    convert_to_backend,
)
from mountainash.typespec.custom_types import (
    CustomTypeRegistry,
    TypeConverter,
    TypeConverterSpec,
)

__all__ = [
    # Types
    "UniversalType",
    "normalize_type",
    "is_safe_cast",
    "get_polars_type",
    "get_arrow_type",
    "get_universal_to_backend_mapping",
    "get_backend_to_universal_mapping",
    "UNIVERSAL_TO_PANDAS",
    "SAFE_CASTS",
    "UNSAFE_CASTS",
    # Bridge
    "bridge_type",
    "UNIVERSAL_TO_MOUNTAINASH",
    # Spec
    "TypeSpec",
    "FieldSpec",
    "FieldConstraints",
    "SpecDiff",
    "compare_specs",
    # Extraction
    "extract_from_dataframe",
    "extract_from_dataclass",
    "extract_from_pydantic",
    # Validation
    "SchemaValidationError",
    "validate_round_trip",
    "assert_round_trip",
    "validate_match",
    "assert_match",
    # Converters
    "to_polars_schema",
    "to_pandas_dtypes",
    "to_arrow_schema",
    "to_ibis_schema",
    "convert_to_backend",
    # Custom Types
    "CustomTypeRegistry",
    "TypeConverter",
    "TypeConverterSpec",
]
```

- [ ] **Step 7: Run all typespec tests together**

Run: `hatch run test:test-target tests/typespec/ -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/typespec/ tests/typespec/
git commit -m "feat: move extraction, validation, converters, custom_types to typespec module"
```

---

### Task 5: Create `conform/builder.py` — ConformBuilder

**Files:**
- Create: `src/mountainash/conform/__init__.py`
- Create: `src/mountainash/conform/builder.py`
- Create: `tests/conform/__init__.py`
- Create: `tests/conform/test_conform_builder.py`

- [ ] **Step 1: Write failing tests for ConformBuilder**

Create `tests/conform/__init__.py` (empty file) and `tests/conform/test_conform_builder.py`:

```python
"""Tests for ConformBuilder — the user-facing DSL."""
from __future__ import annotations

import pytest

from mountainash.conform.builder import ConformBuilder
from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType


class TestConformBuilderFromDict:
    """ConformBuilder constructed from dict."""

    def test_cast_only(self):
        builder = ConformBuilder({"val": {"cast": "integer"}})
        spec = builder.spec
        assert len(spec.fields) == 1
        assert spec.fields[0].name == "val"
        assert spec.fields[0].type == UniversalType.INTEGER

    def test_rename_from(self):
        builder = ConformBuilder({"user_id": {"rename_from": "raw_id", "cast": "integer"}})
        spec = builder.spec
        assert spec.fields[0].rename_from == "raw_id"
        assert spec.fields[0].source_name == "raw_id"

    def test_null_fill(self):
        builder = ConformBuilder({"email": {"cast": "string", "null_fill": "unknown"}})
        spec = builder.spec
        assert spec.fields[0].null_fill == "unknown"

    def test_no_cast_defaults_to_any(self):
        builder = ConformBuilder({"val": {"rename_from": "old_val"}})
        spec = builder.spec
        assert spec.fields[0].type == UniversalType.ANY

    def test_multiple_fields(self):
        builder = ConformBuilder({
            "id": {"cast": "integer", "rename_from": "raw_id"},
            "name": {"cast": "string"},
            "score": {"cast": "number", "null_fill": 0.0},
        })
        spec = builder.spec
        assert len(spec.fields) == 3
        assert spec.fields[0].name == "id"
        assert spec.fields[1].name == "name"
        assert spec.fields[2].null_fill == 0.0


class TestConformBuilderFromTypeSpec:
    """ConformBuilder constructed from TypeSpec."""

    def test_passthrough(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        builder = ConformBuilder(spec)
        assert builder.spec is spec


class TestConformBuilderFromFrictionless:
    """ConformBuilder.from_frictionless()."""

    def test_from_frictionless_dict(self):
        data = {
            "fields": [
                {"name": "id", "type": "integer", "x-mountainash": {"rename_from": "raw_id"}},
                {"name": "email", "type": "string"},
            ],
        }
        builder = ConformBuilder.from_frictionless(data)
        assert builder.spec.fields[0].rename_from == "raw_id"
        assert builder.spec.fields[1].type == UniversalType.STRING


class TestConformBuilderToFrictionless:
    """ConformBuilder.to_frictionless()."""

    def test_round_trip(self):
        builder = ConformBuilder({
            "id": {"cast": "integer", "rename_from": "raw_id"},
            "email": {"cast": "string", "null_fill": "n/a"},
        })
        exported = builder.to_frictionless()
        assert exported["fields"][0]["x-mountainash"]["rename_from"] == "raw_id"
        assert exported["fields"][1]["x-mountainash"]["null_fill"] == "n/a"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/conform/test_conform_builder.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mountainash.conform'`

- [ ] **Step 3: Implement builder.py**

Create `src/mountainash/conform/__init__.py`:

```python
"""Conform — compile type specifications to relation/expression operations.

Provides ConformBuilder, the user-facing DSL for conforming DataFrames
to a TypeSpec via the mountainash relations/expressions layer.
"""
from mountainash.conform.builder import ConformBuilder

__all__ = ["ConformBuilder"]
```

Create `src/mountainash/conform/builder.py`:

```python
"""ConformBuilder — user-facing DSL for data conformance.

Follows the mountainash build-then-X pattern:
- Build phase: construct from dict, TypeSpec, or Frictionless JSON
- Apply phase: .apply(df) compiles to relations and executes
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType, normalize_type


class ConformBuilder:
    """Build-then-apply conformance of DataFrames to a TypeSpec.

    Examples:
        # From dict (target-oriented keys)
        conform = ConformBuilder({
            "user_id": {"rename_from": "raw_id", "cast": "integer"},
            "email":   {"cast": "string", "null_fill": "unknown"},
        })
        result = conform.apply(df)

        # From TypeSpec
        conform = ConformBuilder(spec)
        result = conform.apply(df)

        # From Frictionless JSON file
        conform = ConformBuilder.from_frictionless("schema.json")
        result = conform.apply(df)
    """

    def __init__(self, source: Union[dict, TypeSpec]):
        if isinstance(source, dict):
            self._spec = self._dict_to_spec(source)
        else:
            self._spec = source

    @classmethod
    def from_frictionless(cls, data: Union[dict, str, Path]) -> ConformBuilder:
        """Create ConformBuilder from Frictionless Table Schema."""
        return cls(TypeSpec.from_frictionless(data))

    @property
    def spec(self) -> TypeSpec:
        """Access the underlying TypeSpec."""
        return self._spec

    def to_frictionless(self) -> dict:
        """Export as Frictionless Table Schema dict."""
        return self._spec.to_frictionless()

    def apply(self, df: Any) -> Any:
        """Compile conformance to relations and execute.

        Args:
            df: Source DataFrame (any supported backend).

        Returns:
            Transformed Polars DataFrame.
        """
        from .compiler import compile_conform
        return compile_conform(self._spec, df)

    @staticmethod
    def _dict_to_spec(columns: dict) -> TypeSpec:
        """Convert target-oriented dict to TypeSpec.

        Dict format (target column names as keys):
            {
                "user_id": {"rename_from": "raw_id", "cast": "integer"},
                "email":   {"cast": "string", "null_fill": "unknown"},
            }

        The "cast" key in the dict maps to FieldSpec.type (UniversalType).
        "cast" is used in the dict API because it describes the user's intent
        (cast this column), while .type describes the spec's state (target type).
        """
        fields = []
        for target_name, config in columns.items():
            fields.append(FieldSpec(
                name=target_name,
                type=normalize_type(config["cast"]) if "cast" in config else UniversalType.ANY,
                rename_from=config.get("rename_from"),
                null_fill=config.get("null_fill"),
            ))
        return TypeSpec(fields=fields)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `hatch run test:test-target tests/conform/test_conform_builder.py -v`
Expected: PASS (all 10 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/conform/ tests/conform/
git commit -m "feat: add ConformBuilder — user-facing DSL for data conformance"
```

---

### Task 6: Create `conform/compiler.py` — Compile TypeSpec to relations

**Files:**
- Create: `src/mountainash/conform/compiler.py`
- Create: `tests/conform/test_conform_transforms.py`

- [ ] **Step 1: Write failing cross-backend conform tests**

Create `tests/conform/test_conform_transforms.py`:

```python
"""Cross-backend parametrized tests for conform compilation.

Verifies that ConformBuilder.apply() correctly transforms DataFrames
by compiling to mountainash relation/expression operations.

Uses the standard ALL_BACKENDS parametrization and collect_expr/collect_col
extraction pattern from the testing philosophy.
"""
from __future__ import annotations

import pytest
import mountainash as ma

from mountainash.conform.builder import ConformBuilder
from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformCast:
    """Cast transforms across all backends."""

    def test_cast_string_to_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "2", "3"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "integer"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1, 2, 3]

    def test_cast_string_to_number(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1.5", "2.5", "3.5"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "number"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1.5, 2.5, 3.5]

    def test_cast_string_to_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["hello", "world"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "string"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == ["hello", "world"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformRename:
    """Rename transforms across all backends."""

    def test_rename_column(self, backend_name, backend_factory):
        df = backend_factory.create({"old_name": ["a", "b", "c"]}, backend_name)
        result = ConformBuilder({"new_name": {"rename_from": "old_name", "cast": "string"}}).apply(df)
        actual = ma.relation(result).select("new_name").to_dict()["new_name"]
        assert actual == ["a", "b", "c"]

    def test_rename_preserves_other_columns(self, backend_name, backend_factory):
        df = backend_factory.create({"old": ["a", "b"], "keep": [1, 2]}, backend_name)
        result = ConformBuilder({"new": {"rename_from": "old", "cast": "string"}}).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert "new" in result_dict
        assert "keep" in result_dict
        assert "old" not in result_dict


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformNullFill:
    """Null fill transforms across all backends."""

    def test_null_fill_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": [1, None, 3]}, backend_name)
        result = ConformBuilder({"val": {"cast": "integer", "null_fill": -1}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1, -1, 3]

    def test_null_fill_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["x", None, "z"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "string", "null_fill": "unknown"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == ["x", "unknown", "z"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformKeepOnlyMapped:
    """keep_only_mapped behavior across all backends."""

    def test_keep_only_mapped_drops_extra(self, backend_name, backend_factory):
        df = backend_factory.create({"keep": ["a", "b"], "drop": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
            keep_only_mapped=True,
        )
        result = ConformBuilder(spec).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert "keep" in result_dict
        assert "drop" not in result_dict

    def test_keep_only_mapped_false_preserves_extra(self, backend_name, backend_factory):
        df = backend_factory.create({"mapped": ["a", "b"], "extra": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="mapped", type=UniversalType.STRING)],
            keep_only_mapped=False,
        )
        result = ConformBuilder(spec).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert "mapped" in result_dict
        assert "extra" in result_dict


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformMultiTransform:
    """Combined cast + rename + null_fill across all backends."""

    def test_cast_and_rename(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2", "3"]}, backend_name)
        result = ConformBuilder({
            "user_id": {"rename_from": "raw_id", "cast": "integer"},
        }).apply(df)
        actual = ma.relation(result).select("user_id").to_dict()["user_id"]
        assert actual == [1, 2, 3]

    def test_full_pipeline(self, backend_name, backend_factory):
        df = backend_factory.create({
            "raw_score": ["1.5", None, "3.5"],
            "raw_label": ["foo", "bar", None],
            "extra": [10, 20, 30],
        }, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="score", type=UniversalType.NUMBER, rename_from="raw_score", null_fill=0.0),
                FieldSpec(name="label", type=UniversalType.STRING, rename_from="raw_label", null_fill="n/a"),
            ],
            keep_only_mapped=False,
        )
        result = ConformBuilder(spec).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert result_dict["score"] == [1.5, 0.0, 3.5]
        assert result_dict["label"] == ["foo", "bar", "n/a"]
        assert "extra" in result_dict


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformFromFrictionless:
    """Conform from Frictionless Table Schema dict."""

    def test_from_frictionless_dict(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2"]}, backend_name)
        frictionless_data = {
            "fields": [
                {"name": "user_id", "type": "integer", "x-mountainash": {"rename_from": "raw_id"}},
            ],
            "x-mountainash": {"keep_only_mapped": True},
        }
        result = ConformBuilder.from_frictionless(frictionless_data).apply(df)
        actual = ma.relation(result).select("user_id").to_dict()["user_id"]
        assert actual == [1, 2]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/conform/test_conform_transforms.py -v`
Expected: FAIL — `ImportError: cannot import name 'compile_conform' from 'mountainash.conform.compiler'`

- [ ] **Step 3: Implement compiler.py**

Create `src/mountainash/conform/compiler.py`:

```python
"""Conform compiler — compiles TypeSpec to relation/expression operations.

Replaces the entire schema/transform/ backend strategy system (~1,400 lines)
with ~60 lines that compile to the existing relations/expressions layer.
"""
from __future__ import annotations

from typing import Any

from mountainash.typespec.spec import TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.type_bridge import bridge_type


def _get_source_columns(df: Any) -> list[str]:
    """Get column names from a native DataFrame without executing a relation.

    Handles all supported backend types via duck-typing.
    """
    # Polars, Narwhals, pandas: .columns attribute
    if hasattr(df, 'columns'):
        cols = df.columns
        if isinstance(cols, list):
            return cols
        return list(cols)
    # Ibis: .columns returns list[str]
    if hasattr(df, 'schema'):
        return list(df.schema().keys())
    raise ValueError(f"Cannot get columns from {type(df)}")


def compile_conform(spec: TypeSpec, df: Any) -> Any:
    """Compile a TypeSpec conformance plan to relation operations and execute.

    Builds a relation plan that:
    1. Reads from the source DataFrame
    2. For each field: null_fill (via coalesce), cast, rename (via alias)
    3. Selects mapped columns (+ unmapped if keep_only_mapped is False)
    4. Executes via .to_polars()

    Args:
        spec: The TypeSpec defining target structure.
        df: Source DataFrame (any supported backend).

    Returns:
        Polars DataFrame with conformance applied.
    """
    import mountainash as ma

    r = ma.relation(df)
    source_columns = _get_source_columns(df)

    mapped_exprs = []
    mapped_source_names: set[str] = set()

    for field in spec.fields:
        source_name = field.source_name
        mapped_source_names.add(source_name)

        expr = ma.col(source_name)

        # Null fill (before cast — fill with compatible value first)
        if field.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(field.null_fill))

        # Cast (via type bridge: UniversalType → MountainashDtype)
        if field.type and field.type != UniversalType.ANY:
            dtype = bridge_type(field.type)
            expr = expr.cast(dtype)

        # Rename (alias to target name)
        expr = expr.name.alias(field.name)
        mapped_exprs.append(expr)

    # Handle unmapped columns — pass through as-is
    if not spec.keep_only_mapped:
        for col in source_columns:
            if col not in mapped_source_names:
                mapped_exprs.append(ma.col(col))

    return r.select(*mapped_exprs).to_polars()
```

- [ ] **Step 4: Run cross-backend conform tests**

Run: `hatch run test:test-target tests/conform/test_conform_transforms.py -v`
Expected: PASS (all tests across all 6 backends)

Note: If any string→boolean cast tests exist, those may xfail on Polars/Narwhals. The tests above deliberately avoid boolean casts.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/conform/compiler.py tests/conform/test_conform_transforms.py
git commit -m "feat: add conform compiler — compiles TypeSpec to relation operations"
```

---

### Task 7: Wire up public API entry points in `mountainash.__init__`

**Files:**
- Modify: `src/mountainash/__init__.py`

- [ ] **Step 1: Write a failing test for the public API**

Add to `tests/conform/test_conform_builder.py` at the end of the file:

```python
class TestPublicAPI:
    """ma.conform() and ma.typespec() entry points."""

    def test_ma_conform_from_dict(self):
        import mountainash as ma
        builder = ma.conform({"val": {"cast": "integer"}})
        assert isinstance(builder, ConformBuilder)

    def test_ma_typespec_from_dict(self):
        import mountainash as ma
        spec = ma.typespec({"id": "integer", "name": "string"})
        assert isinstance(spec, TypeSpec)
        assert spec.fields[0].type == UniversalType.INTEGER

    def test_ma_typespec_class_accessible(self):
        import mountainash as ma
        assert hasattr(ma, "TypeSpec")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/conform/test_conform_builder.py::TestPublicAPI -v`
Expected: FAIL — `AttributeError: module 'mountainash' has no attribute 'conform'`

- [ ] **Step 3: Update mountainash/__init__.py**

Replace the contents of `src/mountainash/__init__.py` with:

```python
# Re-export the full expressions public API at the top level
# so that `import mountainash as ma; ma.col("x")` works
from mountainash.expressions import (
    BaseExpressionAPI,
    BooleanExpressionAPI,
    col,
    lit,
    native,
    coalesce,
    greatest,
    least,
    when,
    t_col,
    always_true,
    always_false,
    always_unknown,
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
)  # noqa: F401

from mountainash.__version__ import __version__  # noqa: F401

# Relations - Substrait-aligned relational AST
from mountainash.relations import relation, concat  # noqa: F401

# TypeSpec - backend-agnostic type specification
from mountainash.typespec.spec import TypeSpec  # noqa: F401

# Conform - compile type specifications to relation operations
from mountainash.conform.builder import ConformBuilder  # noqa: F401


def typespec(columns: dict[str, str], **metadata) -> TypeSpec:
    """Create a TypeSpec from a simple {name: type_string} dict."""
    return TypeSpec.from_simple_dict(columns, **metadata)


def conform(source: dict | TypeSpec) -> ConformBuilder:
    """Create a ConformBuilder from a dict or TypeSpec."""
    return ConformBuilder(source)


"""Mountainash - Unified cross-backend DataFrame expression system."""
```

- [ ] **Step 4: Run public API tests**

Run: `hatch run test:test-target tests/conform/test_conform_builder.py -v`
Expected: PASS (all tests including TestPublicAPI)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/__init__.py tests/conform/test_conform_builder.py
git commit -m "feat: wire up ma.conform() and ma.typespec() public API entry points"
```

---

### Task 8: Delete the `schema/` module and its tests

**Files:**
- Delete: `src/mountainash/schema/` (entire directory)
- Delete: `tests/schema/` (entire directory)

- [ ] **Step 1: Verify no remaining imports of mountainash.schema**

Search the codebase for any remaining references to the old schema module:

Run: `grep -r "mountainash.schema" src/ tests/ --include="*.py" | grep -v "typespec" | grep -v "conform" | grep -v "__pycache__"`

Expected: Only `src/mountainash/__init__.py` (which we already updated in Task 7 — confirm the old `schema` import line is gone) and possibly some docs or comments.

If any source files still import from `mountainash.schema`, update them to use `mountainash.typespec` or `mountainash.conform` before proceeding.

- [ ] **Step 2: Delete the schema module**

```bash
rm -rf src/mountainash/schema/
rm -rf tests/schema/
```

- [ ] **Step 3: Run the full test suite**

Run: `hatch run test:test-quick`

Expected: ALL tests pass. The old 27 xfailed schema transform tests are gone. The new conform tests pass across all 6 backends. The typespec tests pass with the moved modules.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: delete schema/ module — replaced by typespec/ and conform/"
```

---

### Task 9: Run full test suite and verify xfail reduction

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite with verbose output**

Run: `hatch run test:test`

Expected: All tests pass. Note the test counts:
- Previous: 27 xfailed schema transform tests
- Now: 0 xfailed conform tests (string→boolean casts are not tested in conform suite)
- All cross-backend conform tests pass across 6 backends

- [ ] **Step 2: Check for any leftover schema references**

Run: `grep -r "schema" src/mountainash/ --include="*.py" -l | grep -v __pycache__`

Verify no files reference the old schema module paths. Some files may legitimately use the word "schema" in docstrings or comments referring to database schemas — that's fine.

- [ ] **Step 3: Run typespec tests specifically**

Run: `hatch run test:test-target tests/typespec/ -v`

Verify all typespec module tests pass.

- [ ] **Step 4: Run conform tests specifically**

Run: `hatch run test:test-target tests/conform/ -v`

Verify all conform tests pass across all 6 backends.

- [ ] **Step 5: Commit (if any fixes were needed)**

Only if fixes were needed in steps 1-4. Otherwise, no commit needed — the suite is clean.
