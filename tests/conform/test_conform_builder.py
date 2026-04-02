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
