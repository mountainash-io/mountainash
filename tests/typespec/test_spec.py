"""
Tests for mountainash.typespec.spec — TypeSpec, FieldSpec, FieldConstraints, SpecDiff.
"""
from __future__ import annotations

import pytest

from mountainash.typespec.spec import (
    FieldConstraints,
    ForeignKeyReference,
    ForeignKey,
    FieldSpec,
    TypeSpec,
    SpecDiff,
    compare_specs,
)
from mountainash.typespec.universal_types import UniversalType


# ============================================================================
# TestFieldConstraints
# ============================================================================

class TestFieldConstraints:
    def test_enum_weights_default_is_none(self):
        c = FieldConstraints()
        assert c.enum_weights is None

    def test_enum_weights_with_values(self):
        c = FieldConstraints(
            enum=["A", "B", "C"],
            enum_weights={"A": 0.5, "B": 0.3, "C": 0.2},
        )
        assert c.enum_weights == {"A": 0.5, "B": 0.3, "C": 0.2}


# ============================================================================
# TestFieldSpec
# ============================================================================

class TestFieldSpec:
    def test_source_name_defaults_to_name(self):
        f = FieldSpec(name="age")
        assert f.source_name == "age"

    def test_source_name_uses_rename_from(self):
        f = FieldSpec(name="age", rename_from="AGE")
        assert f.source_name == "AGE"

    def test_default_type_is_string(self):
        f = FieldSpec(name="col")
        assert f.type == UniversalType.STRING

    def test_null_fill_default_is_none(self):
        f = FieldSpec(name="col")
        assert f.null_fill is None

    def test_to_dict_minimal(self):
        f = FieldSpec(name="id", type=UniversalType.INTEGER)
        d = f.to_dict()
        assert d["name"] == "id"
        assert d["type"] == "integer"
        # Minimal dict should not contain optional keys that are unset
        assert "rename_from" not in d
        assert "null_fill" not in d
        assert "constraints" not in d

    def test_to_dict_with_constraints(self):
        constraints = FieldConstraints(required=True, min_length=2)
        f = FieldSpec(name="username", type=UniversalType.STRING, constraints=constraints)
        d = f.to_dict()
        assert d["name"] == "username"
        assert "constraints" in d
        assert d["constraints"]["required"] is True
        assert d["constraints"]["min_length"] == 2


# ============================================================================
# TestTypeSpec
# ============================================================================

class TestTypeSpec:
    def test_from_simple_dict(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        assert len(spec.fields) == 2
        assert spec.fields[0].name == "id"
        assert spec.fields[0].type == UniversalType.INTEGER
        assert spec.fields[1].name == "name"
        assert spec.fields[1].type == UniversalType.STRING

    def test_field_names_property(self):
        spec = TypeSpec.from_simple_dict({"a": "string", "b": "integer", "c": "number"})
        assert spec.field_names == ["a", "b", "c"]

    def test_get_field_by_name(self):
        spec = TypeSpec.from_simple_dict({"score": "number"})
        f = spec.get_field("score")
        assert f is not None
        assert f.name == "score"
        assert f.type == UniversalType.NUMBER

    def test_get_field_missing_returns_none(self):
        spec = TypeSpec.from_simple_dict({"score": "number"})
        assert spec.get_field("nonexistent") is None

    def test_keep_only_mapped_default_false(self):
        spec = TypeSpec(fields=[])
        assert spec.keep_only_mapped is False

    def test_to_dict(self):
        spec = TypeSpec.from_simple_dict({"id": "integer"}, title="My Spec")
        d = spec.to_dict()
        assert "fields" in d
        assert len(d["fields"]) == 1
        assert d["fields"][0]["name"] == "id"
        assert d["title"] == "My Spec"


# ============================================================================
# TestSpecDiff
# ============================================================================

class TestSpecDiff:
    def _make_spec(self, columns: dict) -> TypeSpec:
        return TypeSpec.from_simple_dict(columns)

    def test_identical_specs_no_diff(self):
        source = self._make_spec({"id": "integer", "name": "string"})
        target = self._make_spec({"id": "integer", "name": "string"})
        diff = compare_specs(source, target)
        assert not diff.has_changes
        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert diff.type_changes == {}

    def test_added_field_detected(self):
        # "added" means present in target but not source
        source = self._make_spec({"id": "integer"})
        target = self._make_spec({"id": "integer", "name": "string"})
        diff = compare_specs(source, target)
        assert diff.has_changes
        assert "name" in diff.added_fields

    def test_removed_field_detected(self):
        # "removed" means present in source but not target
        source = self._make_spec({"id": "integer", "extra": "string"})
        target = self._make_spec({"id": "integer"})
        diff = compare_specs(source, target)
        assert diff.has_changes
        assert "extra" in diff.removed_fields

    def test_type_change_detected(self):
        source = self._make_spec({"id": "integer"})
        target = self._make_spec({"id": "string"})
        diff = compare_specs(source, target)
        assert diff.has_changes
        assert "id" in diff.type_changes
        old_type, new_type = diff.type_changes["id"]
        assert old_type == UniversalType.INTEGER
        assert new_type == UniversalType.STRING


# ============================================================================
# TestForeignKeyReference
# ============================================================================

class TestForeignKeyReference:
    def test_construction(self):
        ref = ForeignKeyReference(resource="customers", fields=["id"])
        assert ref.resource == "customers"
        assert ref.fields == ["id"]

    def test_self_referencing(self):
        ref = ForeignKeyReference(resource="", fields=["manager_id"])
        assert ref.resource == ""

    def test_composite_key(self):
        ref = ForeignKeyReference(resource="orders", fields=["order_id", "line_id"])
        assert len(ref.fields) == 2


# ============================================================================
# TestForeignKey
# ============================================================================

class TestForeignKey:
    def test_construction(self):
        fk = ForeignKey(
            fields=["customer_id"],
            reference=ForeignKeyReference(resource="customers", fields=["id"]),
        )
        assert fk.fields == ["customer_id"]
        assert fk.reference.resource == "customers"
        assert fk.reference.fields == ["id"]

    def test_composite_foreign_key(self):
        fk = ForeignKey(
            fields=["order_id", "line_id"],
            reference=ForeignKeyReference(resource="order_lines", fields=["order_id", "line_id"]),
        )
        assert len(fk.fields) == 2
        assert len(fk.reference.fields) == 2


# ============================================================================
# TestTypeSpec ForeignKeys
# ============================================================================

class TestTypeSpecForeignKeys:
    def test_foreign_keys_default_is_none(self):
        spec = TypeSpec()
        assert spec.foreign_keys is None

    def test_foreign_keys_with_value(self):
        fk = ForeignKey(
            fields=["customer_id"],
            reference=ForeignKeyReference(resource="customers", fields=["id"]),
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="customer_id", type=UniversalType.INTEGER)],
            foreign_keys=[fk],
        )
        assert len(spec.foreign_keys) == 1
        assert spec.foreign_keys[0].fields == ["customer_id"]
        assert spec.foreign_keys[0].reference.resource == "customers"
