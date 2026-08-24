"""
Tests for mountainash.typespec.frictionless — Frictionless Table Schema import/export.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from mountainash.typespec.errors import (
    InvalidFieldMatchDeclaration,
    InvalidKeyShapeError,
)
from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    TypeSpec,
)
from mountainash.typespec.universal_types import UniversalType

if TYPE_CHECKING:
    from pathlib import Path


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
            primary_key=["id"],
        )
        result = typespec_to_frictionless(spec)
        assert result["primaryKey"] == ["id"]

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

    def test_no_x_mountainash_when_no_extensions(self):
        spec = TypeSpec.from_simple_dict({"id": "integer"})
        result = typespec_to_frictionless(spec)
        # No spec-level x-mountainash
        assert "x-mountainash" not in result
        # No field-level x-mountainash
        for field in result["fields"]:
            assert "x-mountainash" not in field

    def test_foreign_keys_exported(self):
        fk = ForeignKey(
            fields=["customer_id"],
            reference=ForeignKeyReference(resource="customers", fields=["id"]),
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="customer_id", type=UniversalType.INTEGER)],
            foreign_keys=[fk],
        )
        result = typespec_to_frictionless(spec)
        assert "foreignKeys" in result
        assert len(result["foreignKeys"]) == 1
        assert result["foreignKeys"][0]["fields"] == ["customer_id"]
        assert result["foreignKeys"][0]["reference"]["resource"] == "customers"
        assert result["foreignKeys"][0]["reference"]["fields"] == ["id"]

    def test_no_foreign_keys_omitted(self):
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
        result = typespec_to_frictionless(spec)
        assert "foreignKeys" not in result

    def test_enum_weights_exported_in_extensions(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="status",
                    type=UniversalType.STRING,
                    constraints=FieldConstraints(
                        enum=["A", "B"],
                        enum_weights={"A": 0.7, "B": 0.3},
                    ),
                )
            ]
        )
        result = typespec_to_frictionless(spec)
        field_dict = result["fields"][0]
        assert field_dict["constraints"]["enum"] == ["A", "B"]
        assert field_dict["x-mountainash"]["enum_weights"] == {"A": 0.7, "B": 0.3}
    def test_object_fields_exported_under_x_mountainash(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="street", type=UniversalType.STRING),
                FieldSpec(name="zip", type=UniversalType.STRING),
            ]),
        ])
        result = typespec_to_frictionless(spec)
        field_result = result["fields"][0]
        assert field_result["x-mountainash"]["object_fields"] == [
            {"name": "street", "type": "string"},
            {"name": "zip", "type": "string"},
        ]

    def test_object_fields_two_levels_deep_exported(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="geo", type=UniversalType.OBJECT, object_fields=[
                    FieldSpec(name="lat", type=UniversalType.NUMBER),
                    FieldSpec(name="lon", type=UniversalType.NUMBER),
                ]),
            ]),
        ])
        result = typespec_to_frictionless(spec)
        geo = result["fields"][0]["x-mountainash"]["object_fields"][0]
        assert geo["name"] == "geo"
        assert geo["type"] == "object"
        assert geo["x-mountainash"]["object_fields"] == [
            {"name": "lat", "type": "number"},
            {"name": "lon", "type": "number"},
        ]

    def test_nested_field_carries_its_own_categories(self):
        """Nested object_fields entries are complete field descriptors."""
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="kind", type=UniversalType.STRING,
                          categories=["home", "work"], categories_ordered=False),
            ]),
        ])
        result = typespec_to_frictionless(spec)
        inner = result["fields"][0]["x-mountainash"]["object_fields"][0]
        assert inner["categories"] == ["home", "work"]


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


    def test_mapping_only_rejects_json_text_and_paths(self, tmp_path: Path):
        descriptor = {"fields": [{"name": "id", "type": "integer"}]}
        path = tmp_path / "schema.json"
        path.write_text(json.dumps(descriptor), encoding="utf-8")

        with pytest.raises(TypeError, match="resolved schema mapping"):
            typespec_from_frictionless(path)
        with pytest.raises(TypeError, match="resolved schema mapping"):
            typespec_from_frictionless(path.read_text(encoding="utf-8"))
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
        # Bare-string primaryKey is normalized to a one-item list on read.
        descriptor = {
            "primaryKey": "id",
            "fields": [{"name": "id", "type": "integer"}],
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.primary_key == ["id"]

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

    def test_missing_type_defaults_to_any(self):
        descriptor = {
            "fields": [{"name": "mystery_col"}]
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.fields[0].type is UniversalType.ANY

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

    def test_foreign_keys_imported(self):
        descriptor = {
            "fields": [{"name": "customer_id", "type": "integer"}],
            "foreignKeys": [
                {
                    "fields": ["customer_id"],
                    "reference": {"resource": "customers", "fields": ["id"]},
                }
            ],
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.foreign_keys is not None
        assert len(spec.foreign_keys) == 1
        assert spec.foreign_keys[0].fields == ["customer_id"]
        assert spec.foreign_keys[0].reference.resource == "customers"

    def test_no_foreign_keys_results_in_none(self):
        descriptor = {"fields": [{"name": "id", "type": "integer"}]}
        spec = typespec_from_frictionless(descriptor)
        assert spec.foreign_keys is None

    def test_enum_weights_imported_from_extensions(self):
        descriptor = {
            "fields": [
                {
                    "name": "status",
                    "type": "string",
                    "constraints": {"enum": ["A", "B"]},
                    "x-mountainash": {"enum_weights": {"A": 0.7, "B": 0.3}},
                }
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.fields[0].constraints.enum_weights == {"A": 0.7, "B": 0.3}
    def test_object_fields_imported_recursively(self):
        descriptor = {
            "fields": [
                {
                    "name": "addr", "type": "object",
                    "x-mountainash": {
                        "object_fields": [
                            {"name": "street", "type": "string"},
                            {
                                "name": "geo", "type": "object",
                                "x-mountainash": {
                                    "object_fields": [
                                        {"name": "lat", "type": "number"},
                                    ]
                                },
                            },
                        ]
                    },
                }
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        addr = spec.get_field("addr")
        assert addr is not None
        assert [f.name for f in addr.object_fields] == ["street", "geo"]
        geo = addr.object_fields[1]
        assert geo.object_fields[0].name == "lat"
        assert geo.object_fields[0].type == UniversalType.NUMBER

    def test_no_object_fields_key_leaves_none(self):
        descriptor = {"fields": [{"name": "x", "type": "string"}]}
        spec = typespec_from_frictionless(descriptor)
        assert spec.get_field("x").object_fields is None

    def test_foreign_keys_round_trip(self):
        fk = ForeignKey(
            fields=["dept_id"],
            reference=ForeignKeyReference(resource="departments", fields=["id"]),
        )
        original = TypeSpec(
            fields=[FieldSpec(name="dept_id", type=UniversalType.INTEGER)],
            primary_key=["dept_id"],
            foreign_keys=[fk],
        )
        descriptor = typespec_to_frictionless(original)
        restored = typespec_from_frictionless(descriptor)
        assert restored.foreign_keys is not None
        assert len(restored.foreign_keys) == 1
        assert restored.foreign_keys[0].fields == ["dept_id"]
        assert restored.foreign_keys[0].reference.resource == "departments"
        assert restored.foreign_keys[0].reference.fields == ["id"]


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
            primary_key=["id"],
        )

        exported = typespec_to_frictionless(original)
        reimported = typespec_from_frictionless(exported)

        assert reimported.title == original.title
        assert reimported.description == original.description
        assert reimported.primary_key == original.primary_key
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
    def test_object_fields_round_trip_two_levels_deep(self):
        original = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="street", type=UniversalType.STRING),
                FieldSpec(name="geo", type=UniversalType.OBJECT, object_fields=[
                    FieldSpec(name="lat", type=UniversalType.NUMBER),
                    FieldSpec(name="lon", type=UniversalType.NUMBER),
                ]),
            ]),
        ])
        descriptor = typespec_to_frictionless(original)
        restored = typespec_from_frictionless(descriptor)
        redescriptor = typespec_to_frictionless(restored)
        assert redescriptor == descriptor
        assert restored.get_field("addr").object_fields[1].object_fields[0].name == "lat"

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
            primary_key=["id"],
        )

        exported = typespec_to_frictionless(spec)
        # Must be JSON-serializable
        json_str = json.dumps(exported)
        loaded = json.loads(json_str)
        reimported = typespec_from_frictionless(loaded)

        assert reimported.title == spec.title
        assert reimported.primary_key == spec.primary_key
        id_field = reimported.get_field("id")
        assert id_field is not None
        assert id_field.rename_from == "ID"
        assert id_field.null_fill == 0


# ============================================================================
# TestUnitBAdapter — v2 operational defaults, labeled values, constraints,
# nested item fields, fmt: normalization, ANY omission, self-reference, and
# the strict key-shape / fields_match matrices (Step 2).
# ============================================================================

def test_omitted_defaults_are_operational_defaults() -> None:
    restored = typespec_from_frictionless({"fields": [{"name": "value"}]})
    assert restored.fields[0].type is UniversalType.ANY
    assert restored.fields_match == "exact"
    assert restored.missing_values == [""]
    assert typespec_to_frictionless(restored)["fields"] == [{"name": "value"}]


def test_explicit_empty_missing_values_disables_default() -> None:
    restored = typespec_from_frictionless(
        {"fields": [{"name": "value"}], "missingValues": []}
    )
    assert restored.missing_values == []
    assert typespec_to_frictionless(restored)["missingValues"] == []


def test_schema_level_missing_values_round_trip() -> None:
    descriptor = {"fields": [{"name": "x", "type": "string"}], "missingValues": ["", "NA"]}
    restored = typespec_from_frictionless(descriptor)
    assert restored.missing_values == ["", "NA"]
    assert typespec_to_frictionless(restored)["missingValues"] == ["", "NA"]


def test_labeled_categories_and_missing_values_round_trip() -> None:
    descriptor = {
        "fields": [
            {
                "name": "status",
                "type": "string",
                "categories": [{"value": "a", "label": "Active"}, "raw"],
                "missingValues": [{"value": "-", "label": "Dash"}, ""],
            }
        ]
    }
    restored = typespec_from_frictionless(descriptor)
    field = restored.fields[0]
    assert field.categories == [LabeledValue("a", "Active"), "raw"]
    assert field.missing_values == [LabeledValue("-", "Dash"), ""]
    assert typespec_to_frictionless(restored)["fields"][0]["categories"] == [
        {"value": "a", "label": "Active"},
        "raw",
    ]


def test_v2_constraints_round_trip() -> None:
    descriptor = {
        "fields": [
            {
                "name": "n",
                "type": "integer",
                "constraints": {
                    "exclusiveMinimum": 0,
                    "exclusiveMaximum": 10,
                    "jsonSchema": {"type": "integer"},
                },
            }
        ]
    }
    restored = typespec_from_frictionless(descriptor)
    c = restored.fields[0].constraints
    assert c.exclusive_minimum == 0
    assert c.exclusive_maximum == 10
    assert c.json_schema == {"type": "integer"}
    out = typespec_to_frictionless(restored)["fields"][0]["constraints"]
    assert out == {"exclusiveMinimum": 0, "exclusiveMaximum": 10, "jsonSchema": {"type": "integer"}}


def test_item_object_fields_round_trip_under_x_mountainash() -> None:
    descriptor = {
        "fields": [
            {
                "name": "rows",
                "type": "array",
                "x-mountainash": {
                    "item_object_fields": [
                        {"name": "a", "type": "string"},
                        {"name": "b", "type": "integer"},
                    ]
                },
            }
        ]
    }
    restored = typespec_from_frictionless(descriptor)
    iof = restored.fields[0].item_object_fields
    assert [f.name for f in iof] == ["a", "b"]
    assert typespec_to_frictionless(restored) == descriptor


def test_fmt_prefix_normalized_off_on_read_and_write() -> None:
    descriptor = {"fields": [{"name": "d", "type": "date", "format": "fmt:%Y-%m-%d"}]}
    restored = typespec_from_frictionless(descriptor)
    assert restored.fields[0].format == "%Y-%m-%d"
    assert typespec_to_frictionless(restored)["fields"][0]["format"] == "%Y-%m-%d"


def test_any_type_omitted_on_write_and_read() -> None:
    spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.ANY)])
    descriptor = typespec_to_frictionless(spec)
    assert descriptor["fields"] == [{"name": "x"}]
    assert typespec_from_frictionless(descriptor).fields[0].type is UniversalType.ANY


def test_canonical_self_reference_round_trip() -> None:
    # A None reference resource (self-reference) is omitted on write and an
    # absent-or-empty resource is read back as None.
    fk = ForeignKey(
        fields=["parent_id"],
        reference=ForeignKeyReference(resource=None, fields=["id"]),
    )
    spec = TypeSpec(
        fields=[FieldSpec(name="parent_id", type=UniversalType.INTEGER)],
        foreign_keys=[fk],
    )
    descriptor = typespec_to_frictionless(spec)
    assert "resource" not in descriptor["foreignKeys"][0]["reference"]
    restored = typespec_from_frictionless(descriptor)
    assert restored.foreign_keys[0].reference.resource is None


def test_empty_string_resource_normalizes_to_none_on_read() -> None:
    descriptor = {
        "fields": [{"name": "parent_id", "type": "integer"}],
        "foreignKeys": [
            {"fields": ["parent_id"], "reference": {"resource": "", "fields": ["id"]}}
        ],
    }
    restored = typespec_from_frictionless(descriptor)
    assert restored.foreign_keys[0].reference.resource is None


def test_foreign_key_fields_bare_string_normalized() -> None:
    # Regression for the character-explosion bug (Section 8.9): a bare-string
    # FK field must become a one-item list, not a list of characters.
    descriptor = {
        "fields": [{"name": "customer_id", "type": "integer"}],
        "foreignKeys": [
            {"fields": "customer_id", "reference": {"resource": "customers", "fields": "id"}}
        ],
    }
    restored = typespec_from_frictionless(descriptor)
    fk = restored.foreign_keys[0]
    assert fk.fields == ["customer_id"]
    assert fk.reference.fields == ["id"]


# --- fields_match six-value vocabulary and invalid/dual forms ---------------

@pytest.mark.parametrize("mode", ["equal", "subset", "superset", "partial"])
def test_standard_fields_match_round_trip(mode) -> None:
    spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.STRING)], fields_match=mode)
    descriptor = typespec_to_frictionless(spec)
    assert descriptor["fieldsMatch"] == mode
    assert "x-mountainash" not in descriptor
    assert typespec_from_frictionless(descriptor).fields_match == mode


def test_exact_fields_match_omitted_on_write() -> None:
    spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.STRING)], fields_match="exact")
    assert "fieldsMatch" not in typespec_to_frictionless(spec)


def test_open_fields_match_only_at_extension() -> None:
    spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.STRING)], fields_match="open")
    descriptor = typespec_to_frictionless(spec)
    assert "fieldsMatch" not in descriptor
    assert descriptor["x-mountainash"] == {"fields_match": "open"}
    assert typespec_from_frictionless(descriptor).fields_match == "open"


def test_invalid_standard_fields_match_raises() -> None:
    with pytest.raises(InvalidFieldMatchDeclaration):
        typespec_from_frictionless({"fields": [], "fieldsMatch": "bogus"})


def test_legacy_standard_open_now_raises() -> None:
    # The legacy standard-location "open" fallback is not retained.
    with pytest.raises(InvalidFieldMatchDeclaration):
        typespec_from_frictionless({"fields": [], "fieldsMatch": "open"})


def test_invalid_extension_fields_match_raises() -> None:
    with pytest.raises(InvalidFieldMatchDeclaration):
        typespec_from_frictionless(
            {"fields": [], "x-mountainash": {"fields_match": "subset"}}
        )


def test_dual_location_fields_match_raises() -> None:
    with pytest.raises(InvalidFieldMatchDeclaration):
        typespec_from_frictionless(
            {
                "fields": [],
                "fieldsMatch": "subset",
                "x-mountainash": {"fields_match": "open"},
            }
        )


# --- strict key-shape matrix ------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    [
        ("id",),
        {"id"},
        {"field": "id"},
        7,
        ["id", 7],
    ],
)
def test_primary_key_rejects_noncanonical_iterables(raw) -> None:
    with pytest.raises(InvalidKeyShapeError):
        typespec_from_frictionless({"fields": [], "primaryKey": raw})


def test_primary_key_bare_string_normalized() -> None:
    spec = typespec_from_frictionless({"fields": [], "primaryKey": "id"})
    assert spec.primary_key == ["id"]


@pytest.mark.parametrize(
    "raw",
    [
        ("id",),
        {"id"},
        {"field": "id"},
        7,
        ["id", 7],
        "id",  # bare strings are NOT allowed for uniqueKeys entries
    ],
)
def test_unique_keys_reject_noncanonical_and_bare_string(raw) -> None:
    with pytest.raises(InvalidKeyShapeError):
        typespec_from_frictionless({"fields": [], "uniqueKeys": [raw]})


def test_unique_keys_lists_accepted() -> None:
    spec = typespec_from_frictionless({"fields": [], "uniqueKeys": [["a"], ["a", "b"]]})
    assert spec.unique_keys == [["a"], ["a", "b"]]


@pytest.mark.parametrize("raw", [("id",), {"id"}, {"field": "id"}, 7, ["id", 7]])
def test_fk_local_fields_reject_noncanonical_iterables(raw) -> None:
    with pytest.raises(InvalidKeyShapeError):
        typespec_from_frictionless(
            {
                "fields": [],
                "foreignKeys": [{"fields": raw, "reference": {"resource": "r", "fields": ["id"]}}],
            }
        )


@pytest.mark.parametrize("raw", [("id",), {"id"}, {"field": "id"}, 7, ["id", 7]])
def test_fk_reference_fields_reject_noncanonical_iterables(raw) -> None:
    with pytest.raises(InvalidKeyShapeError):
        typespec_from_frictionless(
            {
                "fields": [],
                "foreignKeys": [{"fields": ["cid"], "reference": {"resource": "r", "fields": raw}}],
            }
        )
