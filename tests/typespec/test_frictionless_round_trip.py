"""
Parametrized round-trip tests for the 6 High/Medium gaps in the
TypeSpec ↔ Frictionless Table Schema conversion.

Each pytest.param exercises one gap from the audit in
notes/typespec-frictionless-gaps.md (gaps 1, 3, 4, 7, 9, 10).
"""
from __future__ import annotations

import pytest

from mountainash.typespec.frictionless import (
    _field_to_frictionless_dict,
    table_schema_from_frictionless,
    table_schema_to_frictionless,
)
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType

# ---------------------------------------------------------------------------
# Gap fixtures
# ---------------------------------------------------------------------------

GAP_FIXTURES = [
    # Gap 1: missingValues (schema-level) not emitted by table_schema_to_frictionless
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
    spec = table_schema_from_frictionless(descriptor)
    result = table_schema_to_frictionless(spec)
    assert result == descriptor




class TestFieldDictSerialization:
    """Serializer coverage rewritten from the deleted to_dict() methods
    (Section 8.11) — exercises the real _field_to_frictionless_dict /
    table_schema_to_frictionless serializer."""

    def test_field_dict_emits_all_new_fields(self):
        # list-only properties (itemType/delimiter) require a list-like type.
        fs = FieldDefinition(type=UniversalType.LIST,
            example=[1, 2],
            rdf_type="http://schema.org/price",
            categories_ordered=True,
            decimal_char=",",
            group_char=".",
            bare_number=False,
            item_type="string",
            delimiter=";",
        )
        d = _field_to_frictionless_dict(fs, "tags")
        assert d["example"] == [1, 2]
        assert d["rdfType"] == "http://schema.org/price"
        assert d["categoriesOrdered"] is True
        assert d["decimalChar"] == ","
        assert d["groupChar"] == "."
        assert d["bareNumber"] is False
        assert d["itemType"] == "string"
        assert d["delimiter"] == ";"

    def test_field_dict_omits_none_fields(self):
        fs = FieldDefinition(type=UniversalType.STRING)
        d = _field_to_frictionless_dict(fs, "x")
        for key in ("example", "rdfType", "categoriesOrdered",
                     "decimalChar", "groupChar", "bareNumber",
                     "itemType", "delimiter"):
            assert key not in d

    def test_schema_dict_emits_schema_url(self):
        ts = TableSchema(
            fields={"x": FieldDefinition(type=UniversalType.STRING)},
            schema_url="https://datapackage.org/profiles/2.0/tableschema.json",
        )
        d = table_schema_to_frictionless(ts)
        assert d["$schema"] == "https://datapackage.org/profiles/2.0/tableschema.json"

    def test_schema_dict_omits_none_schema_url(self):
        ts = TableSchema(fields={"x": FieldDefinition(type=UniversalType.STRING)})
        d = table_schema_to_frictionless(ts)
        assert "$schema" not in d


def test_missing_fields_match_defaults_to_exact():
    """Frictionless descriptors without fieldsMatch get exact per spec."""
    from mountainash.typespec.frictionless import table_schema_from_frictionless

    descriptor = {"fields": [{"name": "a", "type": "string"}]}
    spec = table_schema_from_frictionless(descriptor)
    assert spec.fields_match == "exact"


def test_explicit_fields_match_preserved():
    """Explicit fieldsMatch in descriptor is preserved."""
    from mountainash.typespec.frictionless import table_schema_from_frictionless

    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "fieldsMatch": "subset",
    }
    spec = table_schema_from_frictionless(descriptor)
    assert spec.fields_match == "subset"


# ---------------------------------------------------------------------------
# Actual JSON text: typed values keep their logical meaning
# ---------------------------------------------------------------------------


def _json_text_round_trip(schema):
    import json

    text = json.dumps(table_schema_to_frictionless(schema))
    return text, table_schema_from_frictionless(json.loads(text))


def _temporal_decimal_schema():
    from datetime import date, datetime, time
    from decimal import Decimal

    from mountainash.core.dtypes import DecimalDtype

    stamp = datetime(2024, 1, 2, 3, 4, 5, 123456)
    return TableSchema(fields={
        "day": FieldDefinition(
            type=UniversalType.DATE, minimum=date(2024, 1, 1), maximum=date(2024, 12, 31),
            exclusive_minimum=date(2023, 12, 31), exclusive_maximum=date(2025, 1, 1),
            eq=date(2024, 6, 1), ne=date(2024, 6, 2),
            enum=[date(2024, 6, 1), date(2024, 6, 3)], notin=[date(2024, 7, 4)],
            null_fill=date(2024, 1, 1),
        ),
        "stamp": FieldDefinition(
            type=UniversalType.DATETIME, minimum=stamp, enum=[stamp], null_fill=stamp,
        ),
        "clock": FieldDefinition(
            type=UniversalType.TIME, maximum=time(23, 59, 59, 999999), ne=time(0, 0), null_fill=time(1, 2, 3),
        ),
        "price": FieldDefinition(
            type=UniversalType.NUMBER, dtype=DecimalDtype(30, 9),
            minimum=Decimal("0.10"), maximum=Decimal("12345678901234567890.123456789"),
            eq=Decimal("1.50"), ne=Decimal("2.50"),
            enum=[Decimal("1.10"), Decimal("2.20")], notin=[Decimal("0.00")], null_fill=Decimal("0.10"),
        ),
    })


def test_temporal_and_decimal_requirement_values_survive_actual_json_text():
    from datetime import date
    from decimal import Decimal

    schema = _temporal_decimal_schema()
    text, restored = _json_text_round_trip(schema)

    assert '"0.10"' in text and '"12345678901234567890.123456789"' in text
    assert '"2024-01-02T03:04:05.123456"' in text and '"23:59:59.999999"' in text
    encoded = table_schema_to_frictionless(schema)["fields"]
    assert encoded[0]["constraints"]["minimum"] == "2024-01-01"
    assert encoded[0]["constraints"]["enum"] == ["2024-06-01", "2024-06-03"]
    assert encoded[0]["x-mountainash"]["constraints"] == {
        "eq": "2024-06-01", "ne": "2024-06-02", "notin": ["2024-07-04"],
    }
    assert encoded[0]["x-mountainash"]["null_fill"] == "2024-01-01"
    assert encoded[3]["constraints"]["minimum"] == "0.10"

    wire_fills = {
        "day": "2024-01-01", "stamp": "2024-01-02T03:04:05.123456", "clock": "01:02:03", "price": "0.10",
    }
    for name, original in schema.fields.items():
        # Requirement values are checker inputs and decode to logical values; a fill is
        # conversion input and stays the lossless lexical text the conform path already parses.
        assert restored.fields[name].constraints == original.constraints, name
        assert restored.fields[name].null_fill == wire_fills[name], name
    assert table_schema_to_frictionless(restored) == table_schema_to_frictionless(schema)
    price = restored.fields["price"].constraints
    assert (str(price.minimum), str(price.maximum), str(price.eq)) == (
        "0.10", "12345678901234567890.123456789", "1.50",
    )
    assert [str(item) for item in price.enum] == ["1.10", "2.20"]
    assert restored.fields["price"].constraints.eq == Decimal("1.50")
    assert restored.fields["day"].constraints.minimum == date(2024, 1, 1)
    assert type(restored.fields["day"].constraints.minimum) is date


def test_native_and_lexical_requirement_values_share_meaning_after_json_text():
    from datetime import date
    from decimal import Decimal

    native = TableSchema(fields={
        "day": FieldDefinition(type=UniversalType.DATE, minimum=date(2024, 1, 1)),
        "price": FieldDefinition(type=UniversalType.NUMBER, minimum=Decimal("0.10")),
    })
    lexical = TableSchema(fields={
        "day": FieldDefinition(type=UniversalType.DATE, minimum="2024-01-01"),
        "price": FieldDefinition(type=UniversalType.NUMBER, minimum="0.10"),
    })
    native_wire = table_schema_to_frictionless(native)
    assert table_schema_to_frictionless(lexical) == native_wire
    _, from_native = _json_text_round_trip(native)
    _, from_lexical = _json_text_round_trip(lexical)
    assert from_native.fields == from_lexical.fields
    assert from_lexical.fields["day"].constraints.minimum == date(2024, 1, 1)
    assert str(from_lexical.fields["price"].constraints.minimum) == "0.10"


def test_declared_format_governs_the_lexical_value_and_lossy_formats_are_rejected():
    from datetime import date

    from mountainash.typespec.errors import InvalidDescriptorStructure

    exact = TableSchema(fields={"day": FieldDefinition(
        type=UniversalType.DATE, format="%Y%m%d", minimum=date(2024, 5, 2), null_fill=date(2024, 5, 3),
    )})
    text, restored = _json_text_round_trip(exact)
    assert '"20240502"' in text and '"20240503"' in text
    assert restored.fields["day"].constraints.minimum == date(2024, 5, 2)
    assert restored.fields["day"].null_fill == "20240503"

    lossy = TableSchema(fields={"day": FieldDefinition(
        type=UniversalType.DATE, format="%Y", minimum=date(2024, 5, 2),
    )})
    assert lossy.fields["day"].constraints.minimum == date(2024, 5, 2)
    with pytest.raises(InvalidDescriptorStructure, match="losslessly") as exc:
        table_schema_to_frictionless(lossy)
    assert exc.value.descriptor_path == "$.fields[0].constraints.minimum"


def test_values_without_a_declaring_type_are_never_stringified_or_floated():
    from decimal import Decimal

    from mountainash.typespec.errors import InvalidDescriptorStructure

    for kwargs in ({"minimum": Decimal("1.5")}, {"enum": [Decimal("1.5")]}, {"null_fill": Decimal("1.5")}):
        schema = TableSchema(fields={"v": FieldDefinition(type=UniversalType.STRING, **kwargs)})
        with pytest.raises(InvalidDescriptorStructure, match="losslessly"):
            table_schema_to_frictionless(schema)


def test_nested_typed_values_use_their_own_declaration_through_json_text():
    from datetime import date
    from decimal import Decimal

    schema = TableSchema(fields={"batches": FieldDefinition(
        element=FieldDefinition(fields={
            "due": FieldDefinition(type=UniversalType.DATE, format="%d/%m/%Y", minimum=date(2024, 3, 9)),
            "cost": FieldDefinition(type=UniversalType.NUMBER, ne=Decimal("0.30")),
        }),
    )})
    wire = table_schema_to_frictionless(schema)["fields"][0]["x-mountainash"]["element"]
    members = wire["x-mountainash"]["fields"]
    assert members[0]["constraints"]["minimum"] == "09/03/2024"
    assert members[1]["x-mountainash"]["constraints"]["ne"] == "0.30"
    _, restored = _json_text_round_trip(schema)
    assert restored.fields["batches"] == schema.fields["batches"]


def test_decoded_requirement_values_drive_the_existing_value_checks():
    from datetime import date
    from decimal import Decimal

    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.validation import ValidationRunner

    schema = TableSchema(fields={
        "day": FieldDefinition(
            type=UniversalType.DATE, minimum=date(2024, 1, 1), maximum=date(2024, 12, 31),
        ),
        "price": FieldDefinition(
            type=UniversalType.NUMBER, minimum=Decimal("0.10"), maximum=Decimal("12.50"),
        ),
        "tier": FieldDefinition(type=UniversalType.NUMBER, enum=[Decimal("1.10"), Decimal("2.20")]),
    })
    _, restored = _json_text_round_trip(schema)
    frame = pl.DataFrame({
        "day": [date(2024, 1, 1), date(2024, 12, 31), date(2023, 12, 31)],
        "price": pl.Series([Decimal("0.10"), Decimal("12.50"), Decimal("0.09")], dtype=pl.Decimal(10, 2)),
        "tier": pl.Series([Decimal("1.10"), Decimal("2.20"), Decimal("3.30")], dtype=pl.Decimal(10, 2)),
    })
    result = ValidationRunner().validate_relation(frame, plan=compile_datacontract(restored))
    summaries = {
        row["check_id"]: row for row in result.check_summaries.to_dicts()
    }
    for check_id in ("day_range", "price_range", "tier_enum_membership"):
        assert (summaries[check_id]["pass_count"], summaries[check_id]["fail_count"]) == (2, 1), check_id


# ---------------------------------------------------------------------------
# Explicit pure legacy migration (migrate_nested_field_declarations)
# ---------------------------------------------------------------------------


def test_legacy_migration_retains_parent_type_and_matching_child_metadata():
    from copy import deepcopy

    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.frictionless import migrate_nested_field_declarations

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
    child = table_schema_from_frictionless(migrated).fields["record"].fields["quantity"]
    assert child.dtype is MountainashDtype.I32
    assert child.constraints.minimum == 0
    assert child.description == "Quantity"
    assert "object_fields" not in migrated["fields"][0]["x-mountainash"]
    assert "dtype" not in migrated["fields"][0]["x-mountainash"]
    migrated["custom"]["retain"].append(2)
    migrated["fields"][0]["x-mountainash"]["fields"][0]["constraints"]["minimum"] = 99
    assert descriptor == original


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
    restored = table_schema_from_frictionless(json.loads(json.dumps(migrated)))
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


def test_legacy_migration_recurses_and_keeps_container_and_element_scope():
    import json
    from copy import deepcopy

    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.frictionless import migrate_nested_field_declarations

    descriptor = {"fields": [{"name": "rows", "type": "array", "constraints": {"minLength": 1}, "x-mountainash": {
        "dtype": {"kind": "list", "element": {"kind": "struct", "fields": [
            {"name": "inner", "dtype": {"kind": "struct", "fields": [{"name": "v", "dtype": {"kind": "unknown"}}]}},
        ]}},
        "item_object_fields": [{"name": "inner", "type": "object", "description": "In", "x-mountainash": {
            "object_fields": [{"name": "v", "type": "integer", "constraints": {"maximum": 5}}],
        }}],
    }}]}
    original = deepcopy(descriptor)
    migrated = migrate_nested_field_declarations(descriptor)
    assert descriptor == original
    assert migrate_nested_field_declarations(migrated) == migrated
    rows = table_schema_from_frictionless(json.loads(json.dumps(migrated))).fields["rows"]
    assert rows.constraints.min_length == 1
    assert rows.element.constraints.min_length is None and rows.element.constraints.maximum is None
    inner = rows.element.fields["inner"]
    assert inner.description == "In"
    assert inner.fields["v"].dtype is MountainashDtype.I64
    assert inner.fields["v"].constraints.maximum == 5


@pytest.mark.parametrize("descriptor", [
    pytest.param({"fields": [{"name": "r", "type": "object", "x-mountainash": {
        "fields": [{"name": "q", "type": "integer"}]}}]}, id="already-new"),
    pytest.param({"custom": 1, "fields": [{"name": "a", "type": "string", "x-vendor": {"k": 1}}]}, id="nonlegacy"),
    pytest.param({"fields": [{"name": "d", "x-mountainash": {
        "dtype": {"kind": "list", "element": {"kind": "canonical", "name": "i32"}}}}]}, id="supported-dtype-only"),
])
def test_legacy_migration_leaves_current_descriptors_unchanged_and_owned(descriptor):
    from copy import deepcopy

    from mountainash.typespec.frictionless import migrate_nested_field_declarations

    original = deepcopy(descriptor)
    migrated = migrate_nested_field_declarations(descriptor)
    assert migrated == descriptor
    assert migrated is not descriptor and migrated["fields"] is not descriptor["fields"]
    migrated["fields"][0]["name"] = "changed"
    assert descriptor == original


def test_legacy_migration_lets_known_canonical_child_type_win_without_rejection():
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.frictionless import migrate_nested_field_declarations

    migrated = migrate_nested_field_declarations({"fields": [{"name": "r", "type": "object", "x-mountainash": {
        "dtype": {"kind": "struct", "fields": [{"name": "q", "dtype": {"kind": "canonical", "name": "i32"}}]},
        "object_fields": [{"name": "q", "type": "date", "description": "Quantity"}],
    }}]})
    child = table_schema_from_frictionless(migrated).fields["r"].fields["q"]
    assert child.dtype is MountainashDtype.I32
    assert child.description == "Quantity"


def test_legacy_migration_fills_unknown_parent_members_from_compatible_legacy_declarations():
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.frictionless import migrate_nested_field_declarations

    migrated = migrate_nested_field_declarations({"fields": [{"name": "r", "type": "object", "x-mountainash": {
        "object_fields": [
            {"name": "a", "type": "integer", "constraints": {"minimum": 1}},
            {"name": "b", "type": "string", "title": "B"},
        ],
    }}]})
    record = table_schema_from_frictionless(migrated).fields["r"]
    assert list(record.fields) == ["a", "b"]
    assert record.fields["a"].dtype is MountainashDtype.I64 and record.fields["a"].constraints.minimum == 1
    assert record.fields["b"].dtype is MountainashDtype.STRING and record.fields["b"].title == "B"


def test_legacy_migration_rejects_malformed_legacy_members_with_property_paths():
    from mountainash.typespec.errors import InvalidDescriptorStructure
    from mountainash.typespec.frictionless import migrate_nested_field_declarations

    with pytest.raises(InvalidDescriptorStructure) as exc:
        migrate_nested_field_declarations({"fields": [{"name": "r", "x-mountainash": {
            "object_fields": [{"name": "a"}, {"name": "a"}],
        }}]})
    assert exc.value.descriptor_path == "$.fields[0].x-mountainash.object_fields[1].name"
    with pytest.raises(TypeError):
        migrate_nested_field_declarations([])


def test_ordinary_typed_reads_never_migrate_but_name_the_explicit_route():
    from mountainash.typespec.errors import InvalidDescriptorStructure

    legacy = {"fields": [{"name": "r", "type": "object", "x-mountainash": {
        "object_fields": [{"name": "q", "type": "integer"}],
    }}]}
    with pytest.raises(InvalidDescriptorStructure, match="migrate_nested_field_declarations") as exc:
        table_schema_from_frictionless(legacy)
    assert exc.value.descriptor_path == "$.fields[0].x-mountainash.object_fields"
