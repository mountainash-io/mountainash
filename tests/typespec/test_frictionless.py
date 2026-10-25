"""
Tests for mountainash.typespec.frictionless — Frictionless Table Schema import/export.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

import polars as pl
import pyarrow as pa

from mountainash.core.dtypes import MountainashDtype, SchemaTypeStatus
from mountainash.typespec.converters import to_arrow_schema
from mountainash.typespec.errors import InvalidDtypeDeclaration, IncompatibleFieldPropertiesError

from mountainash.typespec.errors import (
    InvalidDescriptorStructure,
    InvalidFieldMatchDeclaration,
    InvalidKeyShapeError,
)
from mountainash.typespec.frictionless import (
    FrictionlessSchemaCodec,
    table_schema_from_frictionless,
    table_schema_to_frictionless,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    FieldDefinition,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    TableSchema,
)
from mountainash.typespec.universal_types import UniversalType

if TYPE_CHECKING:
    from pathlib import Path


def _f(name, **kwargs):
    """A (local name, unnamed definition) pair for building schema maps."""
    return name, FieldDefinition(**kwargs)


def _schema(fields=(), **kwargs):
    return TableSchema(fields=dict(fields), **kwargs)


def _nth(fields, index):
    return list(fields.values())[index]



@pytest.mark.parametrize("dtype", list(MountainashDtype))
def test_canonical_descriptor_identity_survives_json(dtype):
    descriptor = {"fields": [{"name": "value", "x-mountainash": {
        "dtype": {"kind": "canonical", "name": dtype.value},
    }}]}
    spec = table_schema_from_frictionless(descriptor)
    restored = table_schema_from_frictionless(json.loads(json.dumps(spec.to_frictionless())))
    assert restored.fields["value"].dtype is dtype
    if dtype in (MountainashDtype.JSON, MountainashDtype.DURATION):
        assert "type" not in spec.to_frictionless()["fields"][0]


@pytest.mark.parametrize("name,broad,native", [
    ("i8", "integer", pa.int8()), ("i16", "integer", pa.int16()),
    ("i32", "integer", pa.int32()), ("i64", "integer", pa.int64()),
    ("u8", "integer", pa.uint8()), ("u16", "integer", pa.uint16()),
    ("u32", "integer", pa.uint32()), ("u64", "integer", pa.uint64()),
    ("fp32", "number", pa.float32()), ("fp64", "number", pa.float64()),
    ("binary", "string", pa.binary()),
])
@pytest.mark.parametrize("explicit", [False, True])
def test_precise_declarations_materialize_authored_width(name, broad, native, explicit):
    kwargs = {"type": UniversalType(broad)} if explicit else {}
    field = _f("value", dtype=MountainashDtype(name), **kwargs)
    descriptor = _schema(fields=[field]).to_frictionless()
    assert descriptor["fields"][0]["type"] == broad
    spec = table_schema_from_frictionless(json.loads(json.dumps(descriptor)))
    assert to_arrow_schema(spec).field("value").type == native


@pytest.mark.parametrize("container", [None, "fields", "element"])
def test_native_objects_cannot_escape_through_nested_descriptors(container):
    child = FieldDefinition(backend_type=pl.Datetime("ns", "UTC"))
    if container == "fields":
        field = _f("outer", type=UniversalType.OBJECT, fields={"at": child})
    elif container == "element":
        field = _f("outer", element=child)
    else:
        field = ("at", child)
    with pytest.raises(InvalidDtypeDeclaration, match="at|element"):
        _schema(fields=[field]).to_frictionless()
    assert child.backend_type.value == pl.Datetime("ns", "UTC")


@pytest.mark.parametrize("dtype,broad", [
    (MountainashDtype.I8, UniversalType.STRING),
    (MountainashDtype.FP32, UniversalType.INTEGER),
    (MountainashDtype.DURATION, UniversalType.DURATION),
    (MountainashDtype.STRING, UniversalType.GEOJSON),
])
def test_contradictory_canonical_descriptor_is_rejected(dtype, broad):
    with pytest.raises(IncompatibleFieldPropertiesError):
        table_schema_from_frictionless({"fields": [{
            "name": "value", "type": broad.value,
            "x-mountainash": {"dtype": {"kind": "canonical", "name": dtype.value}},
        }]})


@pytest.mark.parametrize("raw", [
    {"kind": "canonical", "name": "int8"},
    {"kind": "canonical", "name": "unknown"},
    {"kind": "canonical"}, {"kind": "canonical", "name": []},
])
def test_malformed_canonical_descriptor_is_rejected(raw):
    with pytest.raises(InvalidDtypeDeclaration):
        table_schema_from_frictionless({"fields": [{"name": "value", "x-mountainash": {
            "dtype": raw,
        }}]})

# ============================================================================
# TestToFrictionless
# ============================================================================

class TestToFrictionless:
    def test_minimal_spec(self):
        spec = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        result = table_schema_to_frictionless(spec)
        assert "fields" in result
        assert len(result["fields"]) == 2
        assert result["fields"][0]["name"] == "id"
        assert result["fields"][0]["type"] == "integer"
        assert result["fields"][1]["name"] == "name"
        assert result["fields"][1]["type"] == "string"

    def test_spec_with_title_description(self):
        spec = _schema(
            fields=[_f("col", type=UniversalType.STRING)],
            title="My Schema",
            description="A test schema",
        )
        result = table_schema_to_frictionless(spec)
        assert result["title"] == "My Schema"
        assert result["description"] == "A test schema"

    def test_primary_key_exported(self):
        spec = _schema(
            fields=[_f("id", type=UniversalType.INTEGER)],
            primary_key=["id"],
        )
        result = table_schema_to_frictionless(spec)
        assert result["primaryKey"] == ["id"]

    def test_constraints_exported(self):
        constraints = FieldConstraints(required=True, minimum=0, maximum=100)
        spec = _schema(
            fields=[_f("score", type=UniversalType.INTEGER, constraints=constraints)],
        )
        result = table_schema_to_frictionless(spec)
        field_result = result["fields"][0]
        assert "constraints" in field_result
        assert field_result["constraints"]["required"] is True
        assert field_result["constraints"]["minimum"] == 0
        assert field_result["constraints"]["maximum"] == 100

    def test_rename_from_in_x_mountainash(self):
        spec = _schema(
            fields=[_f("age", type=UniversalType.INTEGER, rename_from="AGE_COLUMN")],
        )
        result = table_schema_to_frictionless(spec)
        field_result = result["fields"][0]
        assert "x-mountainash" in field_result
        assert field_result["x-mountainash"]["rename_from"] == "AGE_COLUMN"

    def test_null_fill_in_x_mountainash(self):
        spec = _schema(
            fields=[_f("score", type=UniversalType.NUMBER, null_fill=0.0)],
        )
        result = table_schema_to_frictionless(spec)
        field_result = result["fields"][0]
        assert "x-mountainash" in field_result
        assert field_result["x-mountainash"]["null_fill"] == 0.0

    def test_no_x_mountainash_when_no_extensions(self):
        spec = TableSchema.from_simple_dict({"id": "integer"})
        result = table_schema_to_frictionless(spec)
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
        spec = _schema(
            fields=[_f("customer_id", type=UniversalType.INTEGER)],
            foreign_keys=[fk],
        )
        result = table_schema_to_frictionless(spec)
        assert "foreignKeys" in result
        assert len(result["foreignKeys"]) == 1
        assert result["foreignKeys"][0]["fields"] == ["customer_id"]
        assert result["foreignKeys"][0]["reference"]["resource"] == "customers"
        assert result["foreignKeys"][0]["reference"]["fields"] == ["id"]

    def test_no_foreign_keys_omitted(self):
        spec = _schema(fields=[_f("id", type=UniversalType.INTEGER)])
        result = table_schema_to_frictionless(spec)
        assert "foreignKeys" not in result

    def test_enum_weights_exported_in_extensions(self):
        spec = _schema(
            fields=[
                _f("status", type=UniversalType.STRING,
                    constraints=FieldConstraints(
                        enum=["A", "B"],
                        enum_weights={"A": 0.7, "B": 0.3},
                    ),
                )
            ]
        )
        result = table_schema_to_frictionless(spec)
        field_dict = result["fields"][0]
        assert field_dict["constraints"]["enum"] == ["A", "B"]
        assert field_dict["x-mountainash"]["enum_weights"] == {"A": 0.7, "B": 0.3}
    def test_nested_fields_exported_as_named_descriptors_under_x_mountainash(self):
        spec = _schema(fields=[
            _f("addr", type=UniversalType.OBJECT, fields={
                "street": FieldDefinition(type=UniversalType.STRING),
                "zip": FieldDefinition(type=UniversalType.STRING),
            }),
        ])
        result = table_schema_to_frictionless(spec)
        field_result = result["fields"][0]
        assert field_result["x-mountainash"]["fields"] == [
            {"name": "street", "type": "string"},
            {"name": "zip", "type": "string"},
        ]
        assert "dtype" not in field_result["x-mountainash"]

    def test_nested_fields_two_levels_deep_exported(self):
        spec = _schema(fields=[
            _f("addr", type=UniversalType.OBJECT, fields={
                "geo": FieldDefinition(type=UniversalType.OBJECT, fields={
                    "lat": FieldDefinition(type=UniversalType.NUMBER),
                    "lon": FieldDefinition(type=UniversalType.NUMBER),
                }),
            }),
        ])
        result = table_schema_to_frictionless(spec)
        geo = result["fields"][0]["x-mountainash"]["fields"][0]
        assert geo["name"] == "geo"
        assert geo["type"] == "object"
        assert geo["x-mountainash"]["fields"] == [
            {"name": "lat", "type": "number"},
            {"name": "lon", "type": "number"},
        ]

    def test_nested_field_carries_its_own_categories(self):
        """Nested field entries are complete field descriptors."""
        spec = _schema(fields=[
            _f("addr", type=UniversalType.OBJECT, fields={
                "kind": FieldDefinition(
                    type=UniversalType.STRING,
                    categories=["home", "work"], categories_ordered=False,
                ),
            }),
        ])
        result = table_schema_to_frictionless(spec)
        inner = result["fields"][0]["x-mountainash"]["fields"][0]
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
        spec = table_schema_from_frictionless(descriptor)
        assert list(spec.fields) == ["id", "label"]
        assert spec.fields["id"].type == UniversalType.INTEGER
        assert spec.fields["label"].type == UniversalType.STRING


    def test_mapping_only_rejects_json_text_and_paths(self, tmp_path: Path):
        descriptor = {"fields": [{"name": "id", "type": "integer"}]}
        path = tmp_path / "schema.json"
        path.write_text(json.dumps(descriptor), encoding="utf-8")

        with pytest.raises(TypeError, match="resolved schema mapping"):
            table_schema_from_frictionless(path)
        with pytest.raises(TypeError, match="resolved schema mapping"):
            table_schema_from_frictionless(path.read_text(encoding="utf-8"))
    def test_title_description_imported(self):
        descriptor = {
            "title": "My Schema",
            "description": "A test schema",
            "fields": [{"name": "col", "type": "string"}],
        }
        spec = table_schema_from_frictionless(descriptor)
        assert spec.title == "My Schema"
        assert spec.description == "A test schema"

    def test_primary_key_imported(self):
        # Bare-string primaryKey is normalized to a one-item list on read.
        descriptor = {
            "primaryKey": "id",
            "fields": [{"name": "id", "type": "integer"}],
        }
        spec = table_schema_from_frictionless(descriptor)
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
        spec = table_schema_from_frictionless(descriptor)
        field = _nth(spec.fields, 0)
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
        spec = table_schema_from_frictionless(descriptor)
        assert _nth(spec.fields, 0).rename_from == "AGE_COLUMN"

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
        spec = table_schema_from_frictionless(descriptor)
        assert _nth(spec.fields, 0).null_fill == 0.0

    def test_missing_type_defaults_to_any(self):
        descriptor = {
            "fields": [{"name": "mystery_col"}]
        }
        spec = table_schema_from_frictionless(descriptor)
        assert _nth(spec.fields, 0).type is UniversalType.ANY

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
        spec = table_schema_from_frictionless(descriptor)
        assert list(spec.fields) == ["col"]

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
        spec = table_schema_from_frictionless(descriptor)
        assert spec.foreign_keys is not None
        assert len(spec.foreign_keys) == 1
        assert spec.foreign_keys[0].fields == ["customer_id"]
        assert spec.foreign_keys[0].reference.resource == "customers"

    def test_no_foreign_keys_results_in_none(self):
        descriptor = {"fields": [{"name": "id", "type": "integer"}]}
        spec = table_schema_from_frictionless(descriptor)
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
        spec = table_schema_from_frictionless(descriptor)
        assert _nth(spec.fields, 0).constraints.enum_weights == {"A": 0.7, "B": 0.3}
    def test_nested_fields_imported_recursively(self):
        descriptor = {
            "fields": [
                {
                    "name": "addr", "type": "object",
                    "x-mountainash": {
                        "fields": [
                            {"name": "street", "type": "string"},
                            {
                                "name": "geo", "type": "object",
                                "x-mountainash": {
                                    "fields": [
                                        {"name": "lat", "type": "number"},
                                    ]
                                },
                            },
                        ]
                    },
                }
            ]
        }
        spec = table_schema_from_frictionless(descriptor)
        addr = spec.get_field("addr")
        assert addr is not None
        assert list(addr.fields) == ["street", "geo"]
        geo = addr.fields["geo"]
        assert geo.fields["lat"].type == UniversalType.NUMBER

    def test_no_nested_key_leaves_shape_undeclared(self):
        descriptor = {"fields": [{"name": "x", "type": "string"}]}
        spec = table_schema_from_frictionless(descriptor)
        assert spec.get_field("x").fields is None

    def test_foreign_keys_round_trip(self):
        fk = ForeignKey(
            fields=["dept_id"],
            reference=ForeignKeyReference(resource="departments", fields=["id"]),
        )
        original = _schema(
            fields=[_f("dept_id", type=UniversalType.INTEGER)],
            primary_key=["dept_id"],
            foreign_keys=[fk],
        )
        descriptor = table_schema_to_frictionless(original)
        restored = table_schema_from_frictionless(descriptor)
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
        original = _schema(
            fields=[
                _f("id", type=UniversalType.INTEGER,
                    title="Identifier",
                    description="Primary key field",
                    constraints=FieldConstraints(required=True, minimum=1),
                    rename_from="ID_COL",
                    null_fill=0,
                ),
                _f("score", type=UniversalType.NUMBER,
                    null_fill=0.0,
                ),
                _f("label", type=UniversalType.STRING,
                ),
            ],
            title="Test Schema",
            description="Round-trip test",
            primary_key=["id"],
        )

        exported = table_schema_to_frictionless(original)
        reimported = table_schema_from_frictionless(exported)

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
    def test_nested_fields_round_trip_two_levels_deep(self):
        original = _schema(fields=[
            _f("addr", type=UniversalType.OBJECT, fields={
                "street": FieldDefinition(type=UniversalType.STRING),
                "geo": FieldDefinition(type=UniversalType.OBJECT, fields={
                    "lat": FieldDefinition(type=UniversalType.NUMBER),
                    "lon": FieldDefinition(type=UniversalType.NUMBER),
                }),
            }),
        ])
        descriptor = table_schema_to_frictionless(original)
        restored = table_schema_from_frictionless(descriptor)
        redescriptor = table_schema_to_frictionless(restored)
        assert redescriptor == descriptor
        geo = restored.fields["addr"].fields["geo"]
        assert list(geo.fields) == ["lat", "lon"]

    def test_json_serializable(self):
        spec = _schema(
            fields=[
                _f("id", type=UniversalType.INTEGER,
                    constraints=FieldConstraints(required=True),
                    rename_from="ID",
                    null_fill=0,
                ),
                _f("name", type=UniversalType.STRING),
            ],
            title="JSON Test",
            primary_key=["id"],
        )

        exported = table_schema_to_frictionless(spec)
        # Must be JSON-serializable
        json_str = json.dumps(exported)
        loaded = json.loads(json_str)
        reimported = table_schema_from_frictionless(loaded)

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
    restored = table_schema_from_frictionless({"fields": [{"name": "value"}]})
    assert _nth(restored.fields, 0).type is UniversalType.ANY
    assert restored.fields_match == "exact"
    assert restored.missing_values == [""]
    assert table_schema_to_frictionless(restored)["fields"] == [{"name": "value"}]


@pytest.mark.parametrize("missing_values", [None, []], ids=["none", "empty"])
def test_explicit_empty_missing_values_disables_default(missing_values) -> None:
    schema = _schema(fields=[_f("value")], missing_values=missing_values)
    descriptor = json.loads(json.dumps(table_schema_to_frictionless(schema)))
    assert descriptor.get("missingValues") == []
    restored = table_schema_from_frictionless(descriptor)
    assert restored.missing_values == []


def test_schema_level_missing_values_round_trip() -> None:
    descriptor = {"fields": [{"name": "x", "type": "string"}], "missingValues": ["", "NA"]}
    restored = table_schema_from_frictionless(descriptor)
    assert restored.missing_values == ["", "NA"]
    assert table_schema_to_frictionless(restored)["missingValues"] == ["", "NA"]


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
    restored = table_schema_from_frictionless(descriptor)
    field = _nth(restored.fields, 0)
    assert list(field.categories) == [LabeledValue("a", "Active"), "raw"]
    assert list(field.missing_values) == [LabeledValue("-", "Dash"), ""]
    assert table_schema_to_frictionless(restored)["fields"][0]["categories"] == [
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
    restored = table_schema_from_frictionless(descriptor)
    c = _nth(restored.fields, 0).constraints
    assert c.exclusive_minimum == 0
    assert c.exclusive_maximum == 10
    assert c.json_schema == {"type": "integer"}
    out = table_schema_to_frictionless(restored)["fields"][0]["constraints"]
    assert out == {"exclusiveMinimum": 0, "exclusiveMaximum": 10, "jsonSchema": {"type": "integer"}}


def test_array_element_round_trips_as_unnamed_definition() -> None:
    original = _schema(fields=[
        _f("rows", element=FieldDefinition(fields={
            "a": FieldDefinition(type=UniversalType.STRING),
            "b": FieldDefinition(type=UniversalType.INTEGER),
        })),
    ])
    descriptor = json.loads(json.dumps(table_schema_to_frictionless(original)))
    element = descriptor["fields"][0]["x-mountainash"]["element"]
    assert "name" not in element
    assert [child["name"] for child in element["x-mountainash"]["fields"]] == ["a", "b"]
    restored = table_schema_from_frictionless(descriptor)
    assert restored.fields["rows"].dtype == original.fields["rows"].dtype
    assert list(restored.fields["rows"].element.fields) == ["a", "b"]
    assert table_schema_to_frictionless(restored) == descriptor


def test_fixed_dimensions_and_unknown_dimensions_stay_distinct_on_the_wire() -> None:
    element = FieldDefinition(type=UniversalType.INTEGER)
    original = _schema(fields=[
        _f("plain", element=element),
        _f("fixed", element=element, dimensions=(2, 3)),
        _f("unknown_dims", element=element, dimensions=SchemaTypeStatus.UNKNOWN),
    ])
    restored = table_schema_from_frictionless(
        json.loads(json.dumps(table_schema_to_frictionless(original)))
    )
    assert restored.fields["plain"].dimensions is None
    assert restored.fields["fixed"].dimensions == (2, 3)
    assert restored.fields["unknown_dims"].dimensions is SchemaTypeStatus.UNKNOWN
    assert len({restored.fields[n].dtype for n in restored.fields}) == 3


def test_unknown_and_empty_struct_shape_stay_distinct_on_the_wire() -> None:
    original = _schema(fields=[
        _f("empty", fields={}),
        _f("unknown", fields=SchemaTypeStatus.UNKNOWN),
    ])
    restored = table_schema_from_frictionless(
        json.loads(json.dumps(table_schema_to_frictionless(original)))
    )
    assert dict(restored.fields["empty"].fields) == {}
    assert restored.fields["unknown"].fields is SchemaTypeStatus.UNKNOWN


@pytest.mark.parametrize("retired", ["object_fields", "item_object_fields"])
def test_retired_nested_keys_are_rejected_with_migration_guidance(retired) -> None:
    descriptor = {"fields": [{
        "name": "rows", "x-mountainash": {retired: [{"name": "a", "type": "string"}]},
    }]}
    with pytest.raises(InvalidDescriptorStructure, match="migrate_nested_field_declarations") as exc:
        table_schema_from_frictionless(descriptor)
    assert exc.value.descriptor_path == f"$.fields[0].x-mountainash.{retired}"


def test_retired_nested_keys_are_rejected_at_any_depth_with_their_path() -> None:
    descriptor = {"fields": [{"name": "rows", "x-mountainash": {"element": {
        "type": "object", "x-mountainash": {"fields": [
            {"name": "ok"},
            {"name": "inner", "x-mountainash": {"object_fields": []}},
        ]},
    }}}]}
    with pytest.raises(InvalidDescriptorStructure, match="migrate_nested_field_declarations") as exc:
        table_schema_from_frictionless(descriptor)
    assert exc.value.descriptor_path == (
        "$.fields[0].x-mountainash.element.x-mountainash.fields[1].x-mountainash.object_fields"
    )


def test_duplicate_sibling_field_names_are_rejected_before_mapping_construction() -> None:
    with pytest.raises(InvalidDescriptorStructure, match="duplicate") as exc:
        table_schema_from_frictionless({"fields": [{"name": "a"}, {"name": "a", "type": "integer"}]})
    assert exc.value.descriptor_path == "$.fields[1].name"
    with pytest.raises(InvalidDescriptorStructure, match="duplicate") as exc:
        table_schema_from_frictionless({"fields": [{"name": "s", "x-mountainash": {
            "fields": [{"name": "a"}, {"name": "a"}],
        }}]})
    assert exc.value.descriptor_path == "$.fields[0].x-mountainash.fields[1].name"


@pytest.mark.parametrize("extension,suffix", [
    pytest.param({"element": 12}, ".element", id="scalar-element"),
    pytest.param({"element": {"name": "invented", "type": "integer"}}, ".element", id="named-element"),
    pytest.param({"fields": {}}, ".fields", id="fields-not-a-list"),
    pytest.param({"fields": [7]}, ".fields[0]", id="member-not-an-object"),
    pytest.param({"fields": [{"type": "integer"}]}, ".fields[0]", id="member-without-name"),
    pytest.param({"fields": [], "element": {}}, "", id="fields-with-element"),
    pytest.param({"fields": [], "dimensions": [2]}, "", id="fields-with-dimensions"),
    pytest.param({"dimensions": [2]}, "", id="dimensions-without-element"),
    pytest.param({"element": {}, "dimensions": [-1]}, ".dimensions", id="negative-dimension"),
    pytest.param({"element": {}, "dimensions": []}, ".dimensions", id="empty-dimensions"),
    pytest.param({"fields": [], "dtype": {"kind": "struct"}}, "", id="fields-with-dtype"),
    pytest.param({"element": {}, "dtype": {"kind": "list"}}, "", id="element-with-dtype"),
])
def test_malformed_container_declarations_report_typed_property_paths(extension, suffix) -> None:
    with pytest.raises(InvalidDescriptorStructure) as exc:
        table_schema_from_frictionless({"fields": [{"name": "xs", "x-mountainash": extension}]})
    assert exc.value.descriptor_path == "$.fields[0].x-mountainash" + suffix


@pytest.mark.parametrize("descriptor,path", [
    pytest.param({}, "$", id="root-requires-fields"),
    pytest.param({"fields": {}}, "$.fields", id="fields-not-a-list"),
    pytest.param({"fields": [7]}, "$.fields[0]", id="field-not-an-object"),
    pytest.param({"fields": [{"type": "string"}]}, "$.fields[0]", id="field-without-name"),
    pytest.param({"fields": [{"name": 3}]}, "$.fields[0].name", id="non-string-name"),
    pytest.param({"fields": [{"name": "a", "type": 5}]}, "$.fields[0].type", id="non-string-type"),
    pytest.param({"fields": [{"name": "a", "constraints": {"minLength": -1}}]},
                 "$.fields[0].constraints.minLength", id="negative-length"),
    pytest.param({"fields": [{"name": "a", "constraints": {"minimum": [1]}}]},
                 "$.fields[0].constraints.minimum", id="structured-bound"),
    pytest.param({"fields": [{"name": "a", "x-mountainash": []}]},
                 "$.fields[0].x-mountainash", id="extension-not-an-object"),
    pytest.param({"fields": [{"name": "a", "x-mountainash": {"constraints": {"notin": 3}}}]},
                 "$.fields[0].x-mountainash.constraints.notin", id="extended-notin-not-a-list"),
    pytest.param({"fields": [{"name": "o", "x-mountainash": {"fields": [
        {"name": "n", "constraints": {"maxLength": "x"}}]}}]},
                 "$.fields[0].x-mountainash.fields[0].constraints.maxLength", id="nested-member-constraint"),
])
def test_local_grammar_rejects_malformed_declarations_with_property_paths(descriptor, path) -> None:
    with pytest.raises(InvalidDescriptorStructure) as exc:
        table_schema_from_frictionless(descriptor)
    assert exc.value.descriptor_path == path


def test_unrelated_custom_properties_keep_their_existing_treatment() -> None:
    restored = table_schema_from_frictionless({
        "custom": {"anything": [1, {"k": None}]},
        "fields": [{"name": "a", "type": "string", "x-vendor": {"k": 1}, "constraints": {"x-limit": 3}}],
    })
    assert restored.fields["a"] == FieldDefinition(type=UniversalType.STRING)

def test_schema_codec_delegates_to_the_shared_functions() -> None:
    codec = FrictionlessSchemaCodec()
    schema = _schema(fields=[_f("id", type=UniversalType.INTEGER)], primary_key=["id"])
    descriptor = codec.encode(schema)
    assert descriptor == table_schema_to_frictionless(schema)
    assert codec.decode(descriptor).primary_key == ["id"]


def test_fmt_prefix_normalized_off_on_read_and_write() -> None:
    descriptor = {"fields": [{"name": "d", "type": "date", "format": "fmt:%Y-%m-%d"}]}
    restored = table_schema_from_frictionless(descriptor)
    assert _nth(restored.fields, 0).format == "%Y-%m-%d"
    assert table_schema_to_frictionless(restored)["fields"][0]["format"] == "%Y-%m-%d"


def test_any_type_omitted_on_write_and_read() -> None:
    spec = _schema(fields=[_f("x", type=UniversalType.ANY)])
    descriptor = table_schema_to_frictionless(spec)
    assert descriptor["fields"] == [{"name": "x"}]
    assert table_schema_from_frictionless(descriptor).fields["x"].type is UniversalType.ANY


def test_canonical_self_reference_round_trip() -> None:
    # A None reference resource (self-reference) is omitted on write and an
    # absent-or-empty resource is read back as None.
    fk = ForeignKey(
        fields=["parent_id"],
        reference=ForeignKeyReference(resource=None, fields=["id"]),
    )
    spec = _schema(
        fields=[_f("parent_id", type=UniversalType.INTEGER)],
        foreign_keys=[fk],
    )
    descriptor = table_schema_to_frictionless(spec)
    assert "resource" not in descriptor["foreignKeys"][0]["reference"]
    restored = table_schema_from_frictionless(descriptor)
    assert restored.foreign_keys[0].reference.resource is None


def test_empty_string_resource_normalizes_to_none_on_read() -> None:
    descriptor = {
        "fields": [{"name": "parent_id", "type": "integer"}],
        "foreignKeys": [
            {"fields": ["parent_id"], "reference": {"resource": "", "fields": ["id"]}}
        ],
    }
    restored = table_schema_from_frictionless(descriptor)
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
    restored = table_schema_from_frictionless(descriptor)
    fk = restored.foreign_keys[0]
    assert fk.fields == ["customer_id"]
    assert fk.reference.fields == ["id"]


# --- fields_match six-value vocabulary and invalid/dual forms ---------------

@pytest.mark.parametrize("mode", ["equal", "subset", "superset", "partial"])
def test_standard_fields_match_round_trip(mode) -> None:
    spec = _schema(fields=[_f("a", type=UniversalType.STRING)], fields_match=mode)
    descriptor = table_schema_to_frictionless(spec)
    assert descriptor["fieldsMatch"] == mode
    assert "x-mountainash" not in descriptor
    assert table_schema_from_frictionless(descriptor).fields_match == mode


def test_exact_fields_match_omitted_on_write() -> None:
    spec = _schema(fields=[_f("a", type=UniversalType.STRING)], fields_match="exact")
    assert "fieldsMatch" not in table_schema_to_frictionless(spec)


def test_open_fields_match_only_at_extension() -> None:
    spec = _schema(fields=[_f("a", type=UniversalType.STRING)], fields_match="open")
    descriptor = table_schema_to_frictionless(spec)
    assert "fieldsMatch" not in descriptor
    assert descriptor["x-mountainash"] == {"fields_match": "open"}
    assert table_schema_from_frictionless(descriptor).fields_match == "open"


def test_invalid_standard_fields_match_raises() -> None:
    with pytest.raises(InvalidFieldMatchDeclaration):
        table_schema_from_frictionless({"fields": [], "fieldsMatch": "bogus"})


def test_legacy_standard_open_now_raises() -> None:
    # The legacy standard-location "open" fallback is not retained.
    with pytest.raises(InvalidFieldMatchDeclaration):
        table_schema_from_frictionless({"fields": [], "fieldsMatch": "open"})


def test_invalid_extension_fields_match_raises() -> None:
    with pytest.raises(InvalidFieldMatchDeclaration):
        table_schema_from_frictionless(
            {"fields": [], "x-mountainash": {"fields_match": "subset"}}
        )


def test_dual_location_fields_match_raises() -> None:
    with pytest.raises(InvalidFieldMatchDeclaration):
        table_schema_from_frictionless(
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
        table_schema_from_frictionless({"fields": [], "primaryKey": raw})


def test_primary_key_bare_string_normalized() -> None:
    spec = table_schema_from_frictionless({"fields": [], "primaryKey": "id"})
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
        table_schema_from_frictionless({"fields": [], "uniqueKeys": [raw]})


def test_unique_keys_lists_accepted() -> None:
    spec = table_schema_from_frictionless({"fields": [], "uniqueKeys": [["a"], ["a", "b"]]})
    assert spec.unique_keys == [["a"], ["a", "b"]]


@pytest.mark.parametrize("raw", [("id",), {"id"}, {"field": "id"}, 7, ["id", 7]])
def test_fk_local_fields_reject_noncanonical_iterables(raw) -> None:
    with pytest.raises(InvalidKeyShapeError):
        table_schema_from_frictionless(
            {
                "fields": [],
                "foreignKeys": [{"fields": raw, "reference": {"resource": "r", "fields": ["id"]}}],
            }
        )


@pytest.mark.parametrize("raw", [("id",), {"id"}, {"field": "id"}, 7, ["id", 7]])
def test_fk_reference_fields_reject_noncanonical_iterables(raw) -> None:
    with pytest.raises(InvalidKeyShapeError):
        table_schema_from_frictionless(
            {
                "fields": [],
                "foreignKeys": [{"fields": ["cid"], "reference": {"resource": "r", "fields": raw}}],
            }
        )
@pytest.mark.parametrize("raw", [(["id"],), {"id": ["x"]}, {"id"}, "id", 7])
def test_unique_keys_requires_list_container(raw) -> None:
    with pytest.raises(InvalidKeyShapeError) as exc_info:
        table_schema_from_frictionless({"fields": [], "uniqueKeys": raw})
    assert exc_info.value.field_name == "unique_keys"
    assert exc_info.value.rejected_value is raw


@pytest.mark.parametrize("raw", [["exact"], {"mode": "exact"}, 7])
def test_fields_match_rejects_non_string_values(raw) -> None:
    with pytest.raises(InvalidFieldMatchDeclaration) as exc_info:
        table_schema_from_frictionless({"fields": [], "fieldsMatch": raw})
    assert exc_info.value.standard_value is raw


def test_handwritten_parameterized_dtype_preserves_unknown_and_explicit_none():
    from mountainash.core.dtypes import SchemaTypeStatus, TimestampDtype

    raw = {"fields": [{"name": "at", "type": "datetime", "x-mountainash": {
        "dtype": {"kind": "timestamp", "timezone_aware": True, "timezone": None}
    }}]}
    spec = table_schema_from_frictionless(raw)
    assert _nth(spec.fields, 0).dtype == TimestampDtype(SchemaTypeStatus.UNKNOWN, True, None)
    encoded = table_schema_to_frictionless(spec)["fields"][0]["x-mountainash"]["dtype"]
    assert encoded == {"kind": "timestamp", "timezone_aware": True, "timezone": None}


def test_recursive_parameterized_dtype_round_trip_preserves_child_order():
    from mountainash.core.dtypes import ListDtype, SchemaTypeStatus, StructDtype, TimestampDtype

    dtype = ListDtype(StructDtype((
        ("later", TimestampDtype(SchemaTypeStatus.UNKNOWN, True, None)),
        ("first", MountainashDtype.I64),
    )))
    spec = _schema(fields=[_f("items", dtype=dtype)])
    raw = table_schema_to_frictionless(spec)
    restored = table_schema_from_frictionless(raw)
    assert _nth(restored.fields, 0).dtype == dtype
    element = raw["fields"][0]["x-mountainash"]["element"]
    assert "dtype" not in raw["fields"][0]["x-mountainash"]
    assert [child["name"] for child in element["x-mountainash"]["fields"]] == ["later", "first"]


@pytest.mark.parametrize("nested", [
    {"kind": "list", "element": {"kind": "timestamp", "precision": 6, "native": "bad"}},
    {"kind": "struct", "fields": [{"name": "x", "dtype": {"kind": "time", "native": "bad"}}]},
])
def test_handwritten_nested_native_refinement_is_rejected(nested):
    with pytest.raises(InvalidDtypeDeclaration, match="native"):
        table_schema_from_frictionless({"fields": [{"name": "x", "x-mountainash": {"dtype": nested}}]})


def test_recursive_native_refinement_cannot_be_serialized():
    from mountainash.core.dtypes import ListDtype, NativeDtype, TimestampDtype, TypeTarget

    dtype = ListDtype(TimestampDtype(native=NativeDtype(value=pl.Datetime("ns", "UTC"), target=TypeTarget.POLARS)))
    with pytest.raises(InvalidDtypeDeclaration, match="native"):
        table_schema_to_frictionless(_schema(fields=[_f("values", dtype=dtype)]))


@pytest.mark.parametrize("dtype", [
    {"kind": "timestamp", "precision": True},
    {"kind": "time", "precision": 2.5},
    {"kind": "array", "dimensions": [2, True]},
    {"kind": "struct", "fields": [
        {"name": "x", "dtype": {"kind": "unknown"}},
        {"name": "x", "dtype": {"kind": "unknown"}},
    ]},
])
def test_malformed_parameterized_dtype_uses_field_context(dtype):
    with pytest.raises(InvalidDtypeDeclaration) as exc:
        table_schema_from_frictionless({"fields": [
            {"name": "broken", "x-mountainash": {"dtype": dtype}},
        ]})
    assert exc.value.field_name == "broken"


def _via_json_text(schema):
    return table_schema_from_frictionless(json.loads(json.dumps(table_schema_to_frictionless(schema))))


def _assert_plain_json(value, path="$"):
    """Writer output is plain JSON containers, not owned/frozen declaration types."""
    if isinstance(value, dict):
        assert type(value) is dict, path
        for key, item in value.items():
            assert type(key) is str, path
            _assert_plain_json(item, f"{path}.{key}")
    elif isinstance(value, list):
        assert type(value) is list, path
        for index, item in enumerate(value):
            _assert_plain_json(item, f"{path}[{index}]")
    else:
        assert value is None or type(value) in (str, int, float, bool), (path, type(value))


def test_writer_emits_plain_json_data_that_does_not_alias_the_definition() -> None:
    definition = FieldDefinition(
        type=UniversalType.OBJECT,
        enum=[{"a": [1, 2]}], notin=[{"a": [3]}], eq={"a": [1, 2]},
        categories=["x", LabeledValue("y", "Why")], missing_values=["", LabeledValue("-", "Dash")],
        true_values=["yes"], example={"k": [1]}, null_fill={"k": [0]},
        fields={"member": FieldDefinition(type=UniversalType.INTEGER, enum=[1, 2])},
    )
    encoded = table_schema_to_frictionless(_schema(fields=[("rec", definition)]))
    _assert_plain_json(encoded)
    assert encoded == json.loads(json.dumps(encoded))

    field = encoded["fields"][0]
    field["constraints"]["enum"][0]["a"].append(99)
    field["x-mountainash"]["constraints"]["notin"][0]["a"].append(99)
    field["x-mountainash"]["fields"][0]["constraints"]["enum"].append(99)
    again = table_schema_to_frictionless(_schema(fields=[("rec", definition)]))
    assert again["fields"][0]["constraints"]["enum"] == [{"a": [1, 2]}]
    assert again["fields"][0]["x-mountainash"]["constraints"]["notin"] == [{"a": [3]}]
    assert again["fields"][0]["x-mountainash"]["fields"][0]["constraints"]["enum"] == [1, 2]


def test_standard_constraints_stay_standard_and_extended_requirements_use_the_extension() -> None:
    definition = FieldDefinition(
        type=UniversalType.STRING, required=True, unique=True, min_length=2, max_length=9, pattern="^a",
        enum=["a1", "a2"], eq="a1", ne="a2", notin=["zz", "yy"],
        str_contains="a", str_startswith="a", str_endswith="1", severity="warning",
        enum_weights={"a1": 0.5},
    )
    encoded = table_schema_to_frictionless(_schema(fields=[("code", definition)]))["fields"][0]
    assert encoded["constraints"] == {
        "required": True, "unique": True, "minLength": 2, "maxLength": 9,
        "pattern": "^a", "enum": ["a1", "a2"],
    }
    assert encoded["x-mountainash"] == {
        "constraints": {
            "eq": "a1", "ne": "a2", "notin": ["zz", "yy"],
            "str_contains": "a", "str_startswith": "a", "str_endswith": "1",
        },
        "enum_weights": {"a1": 0.5},
        "severity": "warning",
    }
    restored = _via_json_text(_schema(fields=[("code", definition)]))
    assert restored.fields["code"] == definition


def test_numeric_bounds_and_json_schema_requirement_round_trip_without_extension() -> None:
    definition = FieldDefinition(
        type=UniversalType.INTEGER, minimum=0, maximum=9, exclusive_minimum=-1, exclusive_maximum=10,
        json_schema={"type": "integer"},
    )
    encoded = table_schema_to_frictionless(_schema(fields=[("n", definition)]))["fields"][0]
    assert "x-mountainash" not in encoded
    assert encoded["constraints"] == {
        "minimum": 0, "maximum": 9, "exclusiveMinimum": -1, "exclusiveMaximum": 10,
        "jsonSchema": {"type": "integer"},
    }
    assert _via_json_text(_schema(fields=[("n", definition)])).fields["n"] == definition


def test_requirements_and_severity_are_local_to_each_nested_declaration() -> None:
    inner = FieldDefinition(type=UniversalType.INTEGER, minimum=0, ne=7, severity="blocking")
    outer = FieldDefinition(
        element=FieldDefinition(fields={"qty": inner}, severity="blocking"), min_length=1, severity="warning",
    )
    restored = _via_json_text(_schema(fields=[("batches", outer)]))
    batches = restored.fields["batches"]
    assert (batches.severity, batches.constraints.min_length) == ("warning", 1)
    assert batches.element.severity == "blocking"
    assert batches.element.constraints.min_length is None
    qty = batches.element.fields["qty"]
    assert (qty.severity, qty.constraints.minimum, qty.constraints.ne) == ("blocking", 0, 7)


def test_field_missing_values_inherit_disable_and_replace_stay_distinct() -> None:
    schema = _schema(fields=[
        _f("inherit"),
        _f("disable", missing_values=[]),
        _f("replace", missing_values=["NA", LabeledValue("-", "Dash")]),
        _f("blank", missing_values=[""]),
    ], missing_values=["", "N/A"])
    encoded = table_schema_to_frictionless(schema)["fields"]
    assert "missingValues" not in encoded[0]
    assert encoded[1]["missingValues"] == []
    assert encoded[2]["missingValues"] == ["NA", {"value": "-", "label": "Dash"}]
    assert encoded[3]["missingValues"] == [""]
    restored = _via_json_text(schema)
    assert restored.missing_values == ["", "N/A"]
    assert restored.fields["inherit"].missing_values is None
    assert list(restored.fields["disable"].missing_values) == []
    assert list(restored.fields["replace"].missing_values) == ["NA", LabeledValue("-", "Dash")]
    assert list(restored.fields["blank"].missing_values) == [""]


def test_false_zero_and_empty_declarations_survive_json_text() -> None:
    definition = FieldDefinition(
        type=UniversalType.INTEGER, title="", description="", example=0, categories_ordered=False,
        bare_number=False, true_values=[], false_values=[], min_length=0, minimum=0, null_fill=0,
        categories=[], format="default",
    )
    encoded = table_schema_to_frictionless(_schema(fields=[("n", definition)]))["fields"][0]
    assert (encoded["title"], encoded["description"], encoded["example"]) == ("", "", 0)
    assert (encoded["categoriesOrdered"], encoded["bareNumber"]) == (False, False)
    assert (encoded["trueValues"], encoded["falseValues"], encoded["categories"]) == ([], [], [])
    assert encoded["constraints"] == {"minLength": 0, "minimum": 0}
    assert encoded["x-mountainash"] == {"null_fill": 0}
    assert _via_json_text(_schema(fields=[("n", definition)])).fields["n"] == definition


def test_metadata_without_a_declared_value_type_obeys_the_json_domain() -> None:
    from decimal import Decimal

    with pytest.raises(InvalidDescriptorStructure) as exc:
        table_schema_to_frictionless(_schema(fields=[_f("n", example=Decimal("1.5"))]))
    assert exc.value.descriptor_path == "$.fields[0].example"
    assert _via_json_text(_schema(fields=[_f("n", example={"k": [1, None, "x", 1.5, True]})])).fields[
        "n"
    ].example == {"k": (1, None, "x", 1.5, True)}


def test_unrepresentable_python_values_are_rejected_not_stringified() -> None:
    with pytest.raises(InvalidDescriptorStructure) as exc:
        table_schema_to_frictionless(_schema(fields=[_f("n", enum=[{1, 2}])]))
    assert exc.value.descriptor_path == "$.fields[0].constraints.enum"


def test_known_bare_dtypes_and_composition_have_one_wire_shape() -> None:
    from mountainash.core.dtypes import ArrayDtype, ListDtype, StructDtype

    dtype = ArrayDtype(StructDtype((("quantity", MountainashDtype.I32),)), (2,))
    bare = _schema(fields=[_f("items", dtype=dtype)])
    composed = _schema(fields=[_f(
        "items",
        element=FieldDefinition(fields={"quantity": FieldDefinition(dtype=MountainashDtype.I32)}),
        dimensions=(2,),
    )])
    encoded = table_schema_to_frictionless(bare)
    assert encoded == table_schema_to_frictionless(composed)
    extension = encoded["fields"][0]["x-mountainash"]
    assert "dtype" not in extension
    assert extension["dimensions"] == [2]
    assert "name" not in extension["element"]
    assert extension["element"]["x-mountainash"]["fields"][0]["name"] == "quantity"
    assert "dtype" not in extension["element"]["x-mountainash"]
    for source in (bare, composed):
        restored = _via_json_text(source)
        assert restored.fields["items"].dtype == dtype
        assert table_schema_to_frictionless(restored) == encoded

    plain = table_schema_to_frictionless(_schema(fields=[_f("xs", dtype=ListDtype(MountainashDtype.I64))]))
    assert "dtype" not in plain["fields"][0]["x-mountainash"]
    assert "element" in plain["fields"][0]["x-mountainash"]


@pytest.mark.parametrize("dtype,extension", [
    pytest.param("struct-unknown", {"dtype": {"kind": "struct"}}, id="struct-unknown"),
    pytest.param("struct-empty", {"fields": []}, id="struct-empty"),
    pytest.param("list-unknown", {"element": {"x-mountainash": {"dtype": {"kind": "unknown"}}}}, id="list-unknown"),
    pytest.param("array-unknown", {
        "element": {"x-mountainash": {"dtype": {"kind": "unknown"}}}, "dimensions": {"kind": "unknown"},
    }, id="array-unknown-dimensions"),
    pytest.param("array-fixed", {
        "element": {"type": "integer", "x-mountainash": {"dtype": {"kind": "canonical", "name": "i32"}}},
        "dimensions": [0, 2],
    }, id="array-fixed"),
    pytest.param("canonical-struct", {"dtype": {"kind": "canonical", "name": "struct"}}, id="canonical-struct"),
])
def test_unknown_empty_and_fixed_shapes_survive_json_without_invented_defaults(dtype, extension) -> None:
    from mountainash.core.dtypes import ArrayDtype, ListDtype, StructDtype

    unknown = SchemaTypeStatus.UNKNOWN
    dtype = {
        "struct-unknown": StructDtype(unknown), "struct-empty": StructDtype(()),
        "list-unknown": ListDtype(unknown), "array-unknown": ArrayDtype(unknown, unknown),
        "array-fixed": ArrayDtype(MountainashDtype.I32, (0, 2)), "canonical-struct": MountainashDtype.STRUCT,
    }[dtype]
    encoded = table_schema_to_frictionless(_schema(fields=[_f("value", dtype=dtype)]))
    assert encoded["fields"][0]["x-mountainash"] == extension
    decoded = table_schema_from_frictionless(json.loads(json.dumps(encoded)))
    assert decoded.fields["value"].dtype == dtype
    assert table_schema_to_frictionless(decoded) == encoded


def test_unknown_container_declarations_equal_their_bare_dtype_wire_shape() -> None:
    unknown = SchemaTypeStatus.UNKNOWN
    for definition in (
        FieldDefinition(element=unknown),
        FieldDefinition(element=unknown, dimensions=unknown),
        FieldDefinition(fields=unknown),
        FieldDefinition(fields={}),
    ):
        encoded = table_schema_to_frictionless(_schema(fields=[("v", definition)]))
        restored = table_schema_from_frictionless(json.loads(json.dumps(encoded)))
        assert restored.fields["v"].dtype == definition.dtype
        assert table_schema_to_frictionless(restored) == encoded


def test_lexical_list_keeps_its_parsing_declaration_not_a_json_array_shape() -> None:
    definition = FieldDefinition(type=UniversalType.LIST, item_type="integer", delimiter=";")
    encoded = table_schema_to_frictionless(_schema(fields=[("tags", definition)]))["fields"][0]
    assert encoded == {"name": "tags", "type": "list", "itemType": "integer", "delimiter": ";"}
    restored = _via_json_text(_schema(fields=[("tags", definition)])).fields["tags"]
    assert (restored.type, restored.item_type, restored.delimiter) == (UniversalType.LIST, "integer", ";")
    assert restored.element is None and restored.dtype is None


def test_native_strings_serialize_but_native_objects_fail_at_every_depth() -> None:
    native_text = FieldDefinition(backend_type="String")
    restored = _via_json_text(_schema(fields=[_f(
        "outer", element=FieldDefinition(fields={"leaf": native_text}),
    )]))
    assert restored.fields["outer"].element.fields["leaf"].backend_type == "String"

    leaf = FieldDefinition(backend_type=pl.Datetime("ns", "UTC"))
    deep = FieldDefinition(element=FieldDefinition(fields={"mid": FieldDefinition(element=leaf)}))
    with pytest.raises(InvalidDtypeDeclaration, match="native"):
        table_schema_to_frictionless(_schema(fields=[("deep", deep)]))
    assert leaf.backend_type.value == pl.Datetime("ns", "UTC")
