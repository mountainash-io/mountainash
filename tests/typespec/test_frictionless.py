"""
Tests for mountainash.typespec.frictionless — Frictionless Table Schema import/export.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)
from mountainash.typespec.spec import FieldConstraints, FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


# ============================================================================
# TestToFrictionless
# ============================================================================

class TestToFrictionless:
    def test_minimal_spec(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        result = typespec_to_frictionless(spec)
        assert "fields" in result
        assert len(result["fields"]) == 2
        assert result["fields"][0]["name"] == "id"
        assert result["fields"][0]["type"] == "integer"
        assert result["fields"][1]["name"] == "name"
        assert result["fields"][1]["type"] == "string"

    def test_spec_with_title_description(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="col", type=UniversalType.STRING)],
            title="My Schema",
            description="A test schema",
        )
        result = typespec_to_frictionless(spec)
        assert result["title"] == "My Schema"
        assert result["description"] == "A test schema"

    def test_primary_key_exported(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            primary_key="id",
        )
        result = typespec_to_frictionless(spec)
        assert result["primaryKey"] == "id"

    def test_constraints_exported(self):
        constraints = FieldConstraints(required=True, minimum=0, maximum=100)
        spec = TypeSpec(
            fields=[FieldSpec(name="score", type=UniversalType.INTEGER, constraints=constraints)],
        )
        result = typespec_to_frictionless(spec)
        field_result = result["fields"][0]
        assert "constraints" in field_result
        assert field_result["constraints"]["required"] is True
        assert field_result["constraints"]["minimum"] == 0
        assert field_result["constraints"]["maximum"] == 100

    def test_rename_from_in_x_mountainash(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="age", type=UniversalType.INTEGER, rename_from="AGE_COLUMN")],
        )
        result = typespec_to_frictionless(spec)
        field_result = result["fields"][0]
        assert "x-mountainash" in field_result
        assert field_result["x-mountainash"]["rename_from"] == "AGE_COLUMN"

    def test_null_fill_in_x_mountainash(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="score", type=UniversalType.NUMBER, null_fill=0.0)],
        )
        result = typespec_to_frictionless(spec)
        field_result = result["fields"][0]
        assert "x-mountainash" in field_result
        assert field_result["x-mountainash"]["null_fill"] == 0.0

    def test_keep_only_mapped_in_x_mountainash(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="col", type=UniversalType.STRING)],
            keep_only_mapped=True,
        )
        result = typespec_to_frictionless(spec)
        assert "x-mountainash" in result
        assert result["x-mountainash"]["keep_only_mapped"] is True

    def test_no_x_mountainash_when_no_extensions(self):
        spec = TypeSpec.from_simple_dict({"id": "integer"})
        result = typespec_to_frictionless(spec)
        # No spec-level x-mountainash
        assert "x-mountainash" not in result
        # No field-level x-mountainash
        for field in result["fields"]:
            assert "x-mountainash" not in field


# ============================================================================
# TestFromFrictionless
# ============================================================================

class TestFromFrictionless:
    def test_minimal_import(self):
        descriptor = {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "label", "type": "string"},
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        assert len(spec.fields) == 2
        assert spec.fields[0].name == "id"
        assert spec.fields[0].type == UniversalType.INTEGER
        assert spec.fields[1].name == "label"
        assert spec.fields[1].type == UniversalType.STRING

    def test_title_description_imported(self):
        descriptor = {
            "title": "My Schema",
            "description": "A test schema",
            "fields": [{"name": "col", "type": "string"}],
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.title == "My Schema"
        assert spec.description == "A test schema"

    def test_primary_key_imported(self):
        descriptor = {
            "primaryKey": "id",
            "fields": [{"name": "id", "type": "integer"}],
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.primary_key == "id"

    def test_constraints_imported(self):
        descriptor = {
            "fields": [
                {
                    "name": "score",
                    "type": "integer",
                    "constraints": {
                        "required": True,
                        "minimum": 0,
                        "maximum": 100,
                    },
                }
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        field = spec.fields[0]
        assert field.constraints is not None
        assert field.constraints.required is True
        assert field.constraints.minimum == 0
        assert field.constraints.maximum == 100

    def test_x_mountainash_rename_from_imported(self):
        descriptor = {
            "fields": [
                {
                    "name": "age",
                    "type": "integer",
                    "x-mountainash": {"rename_from": "AGE_COLUMN"},
                }
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.fields[0].rename_from == "AGE_COLUMN"

    def test_x_mountainash_null_fill_imported(self):
        descriptor = {
            "fields": [
                {
                    "name": "score",
                    "type": "number",
                    "x-mountainash": {"null_fill": 0.0},
                }
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.fields[0].null_fill == 0.0

    def test_x_mountainash_keep_only_mapped_imported(self):
        descriptor = {
            "x-mountainash": {"keep_only_mapped": True},
            "fields": [{"name": "col", "type": "string"}],
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.keep_only_mapped is True

    def test_missing_type_defaults_to_string(self):
        descriptor = {
            "fields": [{"name": "mystery_col"}]
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.fields[0].type == UniversalType.STRING

    def test_unknown_extensions_ignored(self):
        descriptor = {
            "x-other-tool": {"some_key": "some_value"},
            "fields": [
                {
                    "name": "col",
                    "type": "string",
                    "x-other-tool": {"another_key": 42},
                }
            ],
        }
        # Should not raise; unknown x- keys are silently ignored
        spec = typespec_from_frictionless(descriptor)
        assert len(spec.fields) == 1
        assert spec.fields[0].name == "col"


# ============================================================================
# TestRoundTrip
# ============================================================================

class TestRoundTrip:
    def test_full_round_trip(self):
        original = TypeSpec(
            fields=[
                FieldSpec(
                    name="id",
                    type=UniversalType.INTEGER,
                    title="Identifier",
                    description="Primary key field",
                    constraints=FieldConstraints(required=True, minimum=1),
                    rename_from="ID_COL",
                    null_fill=0,
                ),
                FieldSpec(
                    name="score",
                    type=UniversalType.NUMBER,
                    null_fill=0.0,
                ),
                FieldSpec(
                    name="label",
                    type=UniversalType.STRING,
                ),
            ],
            title="Test Schema",
            description="Round-trip test",
            primary_key="id",
            keep_only_mapped=True,
        )

        exported = typespec_to_frictionless(original)
        reimported = typespec_from_frictionless(exported)

        assert reimported.title == original.title
        assert reimported.description == original.description
        assert reimported.primary_key == original.primary_key
        assert reimported.keep_only_mapped == original.keep_only_mapped
        assert len(reimported.fields) == len(original.fields)

        id_field = reimported.get_field("id")
        assert id_field is not None
        assert id_field.type == UniversalType.INTEGER
        assert id_field.title == "Identifier"
        assert id_field.description == "Primary key field"
        assert id_field.rename_from == "ID_COL"
        assert id_field.null_fill == 0
        assert id_field.constraints is not None
        assert id_field.constraints.required is True
        assert id_field.constraints.minimum == 1

        score_field = reimported.get_field("score")
        assert score_field is not None
        assert score_field.null_fill == 0.0

    def test_json_serializable(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="id",
                    type=UniversalType.INTEGER,
                    constraints=FieldConstraints(required=True),
                    rename_from="ID",
                    null_fill=0,
                ),
                FieldSpec(name="name", type=UniversalType.STRING),
            ],
            title="JSON Test",
            primary_key="id",
            keep_only_mapped=True,
        )

        exported = typespec_to_frictionless(spec)
        # Must be JSON-serializable
        json_str = json.dumps(exported)
        loaded = json.loads(json_str)
        reimported = typespec_from_frictionless(loaded)

        assert reimported.title == spec.title
        assert reimported.primary_key == spec.primary_key
        assert reimported.keep_only_mapped is True
        id_field = reimported.get_field("id")
        assert id_field is not None
        assert id_field.rename_from == "ID"
        assert id_field.null_fill == 0
