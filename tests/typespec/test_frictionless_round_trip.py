"""
Parametrized round-trip tests for the 6 High/Medium gaps in the
TypeSpec ↔ Frictionless Table Schema conversion.

Each pytest.param exercises one gap from the audit in
notes/typespec-frictionless-gaps.md (gaps 1, 3, 4, 7, 9, 10).
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import (
    ArrayDtype, ListDtype, MountainashDtype, SchemaTypeStatus, StructDtype,
)

from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

# ---------------------------------------------------------------------------
# Gap fixtures
# ---------------------------------------------------------------------------

GAP_FIXTURES = [
    # Gap 1: missingValues (schema-level) not emitted by typespec_to_frictionless
    pytest.param(
        {
            "fields": [{"name": "x", "type": "string"}],
            "missingValues": ["", "NA", "N/A"],
        },
        id="schema-level-missingValues",
    ),
    # Gap 3: fieldsMatch not modelled in TypeSpec
    pytest.param(
        {
            "fields": [{"name": "x", "type": "string"}],
            "fieldsMatch": "subset",
        },
        id="fieldsMatch",
    ),
    # Gap 4: uniqueKeys not modelled in TypeSpec
    pytest.param(
        {
            "fields": [{"name": "x", "type": "string"}],
            "uniqueKeys": [["x"], ["x", "y"]],
        },
        id="uniqueKeys",
    ),
    # Gap 7: categories (array of values) not modelled in FieldSpec
    pytest.param(
        {
            "fields": [{
                "name": "status",
                "type": "string",
                "categories": ["active", "cancelled", "pending"],
            }],
        },
        id="categories-array",
    ),
    # Gap 7: categories (array of {value, label} objects) not modelled in FieldSpec
    pytest.param(
        {
            "fields": [{
                "name": "status",
                "type": "string",
                "categories": [
                    {"value": "a", "label": "Active"},
                    {"value": "c", "label": "Cancelled"},
                ],
            }],
        },
        id="categories-objects",
    ),
    # Gap 9: trueValues/falseValues modelled on FieldSpec but never serialised
    pytest.param(
        {
            "fields": [{
                "name": "is_active",
                "type": "boolean",
                "trueValues": ["yes", "Y", "1"],
                "falseValues": ["no", "N", "0"],
            }],
        },
        id="trueValues-falseValues",
    ),
    # Gap 10: backend_type emitted as top-level key; should be under x-mountainash
    pytest.param(
        {
            "fields": [{
                "name": "score",
                "type": "number",
                "x-mountainash": {"backend_type": "Float32"},
            }],
        },
        id="backend_type-under-x-mountainash",
    ),
    # Gap 2: $schema not modelled in TypeSpec
    pytest.param(
        {
            "$schema": "https://datapackage.org/profiles/2.0/tableschema.json",
            "fields": [{"name": "x", "type": "string"}],
        },
        id="schema-url",
    ),
    # Gap 5: example not modelled in FieldSpec
    pytest.param(
        {
            "fields": [{"name": "city", "type": "string", "example": "London"}],
        },
        id="example",
    ),
    # Gap 6: rdfType not modelled in FieldSpec
    pytest.param(
        {
            "fields": [{
                "name": "name",
                "type": "string",
                "rdfType": "http://schema.org/name",
            }],
        },
        id="rdfType",
    ),
    # Gap 8: categoriesOrdered not modelled in FieldSpec
    pytest.param(
        {
            "fields": [{
                "name": "rating",
                "type": "string",
                "categories": ["low", "medium", "high"],
                "categoriesOrdered": True,
            }],
        },
        id="categoriesOrdered",
    ),
    # Gap 11: number/integer parsing properties
    pytest.param(
        {
            "fields": [{
                "name": "price",
                "type": "number",
                "decimalChar": ",",
                "groupChar": ".",
                "bareNumber": False,
            }],
        },
        id="number-format-properties",
    ),
    # Gap 11: list parsing properties (itemType/delimiter require a list-like
    # type post-Unit-B — canonical "list", not the pre-cutover "string").
    pytest.param(
        {
            "fields": [{
                "name": "tags",
                "type": "list",
                "itemType": "string",
                "delimiter": ";",
            }],
        },
        id="list-parsing-properties",
    ),
]


@pytest.mark.parametrize("descriptor", GAP_FIXTURES)
def test_field_round_trip(descriptor):
    """Import a descriptor, re-export it, and check the output equals the input."""
    import json
    spec = typespec_from_frictionless(json.loads(json.dumps(descriptor)))
    result = typespec_to_frictionless(spec)
    assert result == descriptor





def test_recursive_declarations_survive_json_text_and_own_both_boundaries():
    import json

    item = FieldSpec(type=UniversalType.INTEGER, minimum=0, ne=7, null_fill=0,
                     severity="warning", description="Reusable quantity")
    schema = TypeSpec(fields={"batches": FieldSpec(element=FieldSpec(fields={"qty": item}))})
    encoded = typespec_to_frictionless(schema)
    restored = typespec_from_frictionless(json.loads(json.dumps(encoded)))
    child = restored.fields["batches"].element.fields["qty"]
    assert (child.constraints.minimum, child.constraints.ne, child.null_fill) == (0, 7, 0)
    assert (child.severity, child.description) == ("warning", "Reusable quantity")
    assert typespec_to_frictionless(restored) == encoded
    encoded["fields"][0]["x-mountainash"]["element"]["x-mountainash"]["fields"][0]["constraints"]["minimum"] = 99
    assert child.constraints.minimum == 0
    assert item.constraints.minimum == 0


def test_native_and_lexical_requirement_values_share_json_meaning():
    import json
    from datetime import date
    from decimal import Decimal

    native = TypeSpec(fields={
        "day": FieldSpec(type=UniversalType.DATE, minimum=date(2024, 1, 1)),
        "price": FieldSpec(type=UniversalType.NUMBER, minimum=Decimal("0.10")),
    })
    lexical = TypeSpec(fields={
        "day": FieldSpec(type=UniversalType.DATE, minimum="2024-01-01"),
        "price": FieldSpec(type=UniversalType.NUMBER, minimum="0.10"),
    })
    encoded = typespec_to_frictionless(native)
    assert encoded["fields"][0]["constraints"]["minimum"] == "2024-01-01"
    assert encoded["fields"][1]["constraints"]["minimum"] == "0.10"
    restored = typespec_from_frictionless(json.loads(json.dumps(encoded)))
    for name, value in (("day", date(2024, 1, 1)), ("price", Decimal("0.10"))):
        assert native.fields[name].constraints.minimum == value
        assert lexical.fields[name].constraints.minimum == value
        assert restored.fields[name].constraints.minimum == value


def test_known_structured_dtype_and_composition_have_one_wire_shape():
    from mountainash.core.dtypes import ArrayDtype, MountainashDtype, StructDtype

    dtype = ArrayDtype(StructDtype((("quantity", MountainashDtype.I32),)), (2,))
    bare = TypeSpec(fields={"items": FieldSpec(dtype=dtype)})
    composed = TypeSpec(fields={"items": FieldSpec(
        element=FieldSpec(fields={"quantity": FieldSpec(dtype=MountainashDtype.I32)}),
        dimensions=(2,),
    )})
    encoded = typespec_to_frictionless(bare)
    assert encoded == typespec_to_frictionless(composed)
    extension = encoded["fields"][0]["x-mountainash"]
    assert "dtype" not in extension
    assert extension["dimensions"] == [2]
    assert "name" not in extension["element"]
    assert extension["element"]["x-mountainash"]["fields"][0]["name"] == "quantity"


def test_legacy_migration_retains_parent_type_and_matching_child_metadata():
    from copy import deepcopy
    from mountainash.typespec.frictionless import migrate_nested_field_declarations
    from mountainash.core.dtypes import MountainashDtype

    descriptor = {"custom": {"retain": [1]}, "fields": [{
        "name": "record", "type": "object", "x-mountainash": {
            "dtype": {"kind": "struct", "fields": [
                {"name": "quantity", "dtype": {"kind": "canonical", "name": "i32"}},
            ]},
            "object_fields": [{
                "name": "quantity", "type": "string", "description": "Quantity",
                "constraints": {"minimum": 0},
            }],
        },
    }]}
    original = deepcopy(descriptor)
    migrated = migrate_nested_field_declarations(descriptor)
    assert descriptor == original
    assert migrated["custom"] == {"retain": [1]}
    child = typespec_from_frictionless(migrated).fields["record"].fields["quantity"]
    assert child.dtype is MountainashDtype.I32
    assert child.constraints.minimum == 0
    assert child.description == "Quantity"
    assert "object_fields" not in migrated["fields"][0]["x-mountainash"]
    migrated["custom"]["retain"].append(2)
    assert descriptor == original


@pytest.mark.parametrize("dtype,extension", [
    (StructDtype(SchemaTypeStatus.UNKNOWN), {"dtype": {"kind": "struct"}}),
    (StructDtype(()), {"fields": []}),
    (ListDtype(SchemaTypeStatus.UNKNOWN), {"element": {"x-mountainash": {"dtype": {"kind": "unknown"}}}}),
    (
        ArrayDtype(SchemaTypeStatus.UNKNOWN, SchemaTypeStatus.UNKNOWN),
        {"element": {"x-mountainash": {"dtype": {"kind": "unknown"}}}, "dimensions": {"kind": "unknown"}},
    ),
    (
        ArrayDtype(MountainashDtype.I32, (0, 2)),
        {"element": {"type": "integer", "x-mountainash": {"dtype": {"kind": "canonical", "name": "i32"}}},
         "dimensions": [0, 2]},
    ),
    (MountainashDtype.STRUCT, {"dtype": {"kind": "canonical", "name": "struct"}}),
])
def test_unknown_empty_and_fixed_shapes_survive_json_without_invented_defaults(dtype, extension):
    import json

    encoded = typespec_to_frictionless(TypeSpec(fields={"value": FieldSpec(dtype=dtype)}))
    assert encoded["fields"][0]["x-mountainash"] == extension
    decoded = typespec_from_frictionless(json.loads(json.dumps(encoded)))
    assert decoded.fields["value"].dtype == dtype
    assert typespec_to_frictionless(decoded) == encoded


@pytest.mark.parametrize("extension,path", [
    ({"element": 12}, ".element"),
    ({"element": {"name": "invented", "type": "integer"}}, ".element"),
    ({"fields": {}}, ".fields"),
    ({"fields": [], "element": {}}, ""),
    ({"dimensions": [2]}, ""),
    ({"element": {}, "dimensions": [-1]}, ".dimensions"),
    ({"fields": [{"name": "a"}, {"name": "a"}]}, ".fields[1].name"),
])
@pytest.mark.parametrize("via_resource", [False, True])
def test_nested_wire_shape_errors_share_resource_boundary(extension, path, via_resource):
    from mountainash.typespec.datapackage import DataResource
    from mountainash.typespec.errors import InvalidDescriptorStructure

    descriptor = {"fields": [{"name": "value", "x-mountainash": extension}]}
    resource = DataResource(name="r", data=[], table_schema=descriptor) if via_resource else None
    with pytest.raises(InvalidDescriptorStructure) as caught:
        resource.to_typespec() if resource is not None else typespec_from_frictionless(descriptor)
    assert caught.value.descriptor_path == "$.fields[0].x-mountainash" + path


def test_duplicate_top_level_names_are_rejected_before_mapping_construction():
    from mountainash.typespec.errors import InvalidDescriptorStructure

    with pytest.raises(InvalidDescriptorStructure) as caught:
        typespec_from_frictionless({"fields": [{"name": "x"}, {"name": "x", "type": "integer"}]})
    assert caught.value.descriptor_path == "$.fields[1].name"


def test_mutable_requirement_values_are_owned_across_json_boundaries():
    import json

    descriptor = {"fields": [{
        "name": "record", "type": "object", "missingValues": [], "categoriesOrdered": False,
        "constraints": {"enum": [{"items": [1, 2]}]},
        "x-mountainash": {"fields": [{
            "name": "items", "type": "array",
            "x-mountainash": {"element": {"type": "integer"}},
        }]},
    }]}
    definition = typespec_from_frictionless(descriptor)
    descriptor["fields"][0]["constraints"]["enum"][0]["items"].append(3)
    encoded = json.loads(json.dumps(typespec_to_frictionless(definition)))
    assert encoded["fields"][0]["constraints"]["enum"] == [{"items": [1, 2]}]
    assert encoded["fields"][0]["missingValues"] == []
    assert encoded["fields"][0]["categoriesOrdered"] is False
    encoded["fields"][0]["constraints"]["enum"][0]["items"].clear()
    assert typespec_to_frictionless(definition)["fields"][0]["constraints"]["enum"] == [{"items": [1, 2]}]


def test_lossy_native_format_is_rejected_only_at_persistence():
    from datetime import date
    from mountainash.typespec.errors import InvalidDescriptorStructure

    field = FieldSpec(type=UniversalType.DATE, format="%Y", minimum=date(2024, 5, 2))
    assert field.constraints.minimum == date(2024, 5, 2)
    with pytest.raises(InvalidDescriptorStructure, match="losslessly"):
        typespec_to_frictionless(TypeSpec(fields={"day": field}))


@pytest.mark.parametrize("key,type_name", [("object_fields", "object"), ("item_object_fields", "array")])
def test_retired_nested_keys_require_explicit_migration(key, type_name):
    from mountainash.typespec.errors import InvalidDescriptorStructure

    descriptor = {"fields": [{"name": "value", "type": type_name, "x-mountainash": {key: []}}]}
    with pytest.raises(InvalidDescriptorStructure, match="migrate_nested_field_declarations") as caught:
        typespec_from_frictionless(descriptor)
    assert caught.value.descriptor_path == f"$.fields[0].x-mountainash.{key}"


def test_multidimensional_typed_fill_retains_leaf_format_through_json():
    import json
    from datetime import date

    field = FieldSpec(
        element=FieldSpec(type=UniversalType.DATE, format="%Y%m%d"),
        dimensions=(2, 2),
        null_fill=[["20240101", "20240102"], ["20240103", "20240104"]],
    )
    expected = ((date(2024, 1, 1), date(2024, 1, 2)),
                (date(2024, 1, 3), date(2024, 1, 4)))
    assert field.null_fill == expected
    encoded = typespec_to_frictionless(TypeSpec(fields={"grid": field}))
    restored = typespec_from_frictionless(json.loads(json.dumps(encoded)))
    assert restored.fields["grid"].null_fill == expected
    assert typespec_to_frictionless(restored) == encoded


@pytest.mark.parametrize("native_override", [None, "String"])
def test_legacy_list_migration_preserves_portable_metadata_with_native_override(native_override):
    import json
    from copy import deepcopy
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.frictionless import migrate_nested_field_declarations

    extension = {
        "dtype": {"kind": "list", "element": {"kind": "struct", "fields": [
            {"name": "id", "dtype": {"kind": "canonical", "name": "i32"}},
            {"name": "day", "dtype": {"kind": "unknown"}},
        ]}},
        "item_object_fields": [
            {"name": "day", "type": "date", "format": "%Y%m%d"},
            {"name": "id", "type": "string", "constraints": {"minimum": 0},
             "x-vendor": {"meaning": "identifier"}},
            {"name": "extra", "type": "string"},
        ],
    }
    if native_override is not None:
        extension["backend_type"] = native_override
    descriptor = {"fields": [{"name": "rows", "type": "array", "x-mountainash": extension}]}
    original = deepcopy(descriptor)
    migrated = migrate_nested_field_declarations(descriptor)
    assert descriptor == original
    restored = typespec_from_frictionless(json.loads(json.dumps(migrated)))
    field = restored.fields["rows"]
    assert field.backend_type == native_override
    assert list(field.element.fields) == ["id", "day"]
    assert field.element.fields["id"].dtype is MountainashDtype.I32
    assert field.element.fields["id"].constraints.minimum == 0
    assert field.element.fields["day"].dtype is MountainashDtype.DATE
    assert field.element.fields["day"].format == "%Y%m%d"
    members = migrated["fields"][0]["x-mountainash"]["element"]["x-mountainash"]["fields"]
    assert members[0]["x-vendor"] == {"meaning": "identifier"}
    assert migrate_nested_field_declarations(migrated) == migrated
