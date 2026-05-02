"""
Parametrized round-trip tests for the 6 High/Medium gaps in the
TypeSpec ↔ Frictionless Table Schema conversion.

Each pytest.param exercises one gap from the audit in
notes/typespec-frictionless-gaps.md (gaps 1, 3, 4, 7, 9, 10).
"""
from __future__ import annotations

import pytest

from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)

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
            "$schema": "https://datapackage.org/profiles/1.0/tableschema.json",
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
    # Gap 11: list parsing properties
    pytest.param(
        {
            "fields": [{
                "name": "tags",
                "type": "string",
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
    spec = typespec_from_frictionless(descriptor)
    result = typespec_to_frictionless(spec)
    assert result == descriptor


from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestToDict:
    """Direct to_dict tests — independent of frictionless round-trip."""

    def test_fieldspec_to_dict_emits_all_new_fields(self):
        fs = FieldSpec(
            name="price",
            type=UniversalType.NUMBER,
            example=42.5,
            rdf_type="http://schema.org/price",
            categories_ordered=True,
            decimal_char=",",
            group_char=".",
            bare_number=False,
            item_type="string",
            delimiter=";",
        )
        d = fs.to_dict()
        assert d["example"] == 42.5
        assert d["rdfType"] == "http://schema.org/price"
        assert d["categoriesOrdered"] is True
        assert d["decimalChar"] == ","
        assert d["groupChar"] == "."
        assert d["bareNumber"] is False
        assert d["itemType"] == "string"
        assert d["delimiter"] == ";"

    def test_fieldspec_to_dict_omits_none_fields(self):
        fs = FieldSpec(name="x", type=UniversalType.STRING)
        d = fs.to_dict()
        for key in ("example", "rdfType", "categoriesOrdered",
                     "decimalChar", "groupChar", "bareNumber",
                     "itemType", "delimiter"):
            assert key not in d

    def test_typespec_to_dict_emits_schema_url(self):
        ts = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.STRING)],
            schema_url="https://datapackage.org/profiles/1.0/tableschema.json",
        )
        d = ts.to_dict()
        assert d["$schema"] == "https://datapackage.org/profiles/1.0/tableschema.json"

    def test_typespec_to_dict_omits_none_schema_url(self):
        ts = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.STRING)])
        d = ts.to_dict()
        assert "$schema" not in d
