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
]


@pytest.mark.parametrize("descriptor", GAP_FIXTURES)
def test_field_round_trip(descriptor):
    """Import a descriptor, re-export it, and check the output equals the input."""
    spec = typespec_from_frictionless(descriptor)
    result = typespec_to_frictionless(spec)
    assert result == descriptor
