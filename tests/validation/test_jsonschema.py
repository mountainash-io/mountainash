"""Closed, deterministic JSON Schema declaration and instance validation."""

import pytest

from mountainash.typespec.errors import JSONSchemaReferenceDenied
from mountainash.validation.jsonschema import compile_json_schema


def test_json_schema_collects_all_sorted_instance_errors() -> None:
    """One logical value can produce every stable JSON Schema diagnostic."""
    compiled = compile_json_schema(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
            "additionalProperties": False,
        }
    )

    diagnostics = compiled.validate({"id": "bad", "extra": 1})

    assert [(item.instance_path, item.validator) for item in diagnostics] == [
        ("", "additionalProperties"),
        ("/id", "type"),
    ]


def test_json_schema_supports_local_definitions() -> None:
    """Fragment-only references remain available without a network resolver."""
    compiled = compile_json_schema(
        {
            "$defs": {"identifier": {"type": "integer"}},
            "properties": {"id": {"$ref": "#/$defs/identifier"}},
        }
    )

    diagnostics = compiled.validate({"id": "bad"})

    assert [(item.instance_path, item.schema_path, item.validator) for item in diagnostics] == [
        ("/id", "/properties/id/type", "type")
    ]



def test_json_schema_value_rule_reports_instance_failure() -> None:
    """Schema instance violations are data failures, never runner errors."""
    import polars as pl

    from mountainash.validation import ValidationRunner, ValueRule, ValueValidatorKey

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"id": "bad"}]}),
        [
            ValueRule(
                id="payload_schema",
                fields=["payload"],
                validator=ValueValidatorKey.JSON_SCHEMA,
                options={"schema": {"type": "object", "properties": {"id": {"type": "integer"}}}},
            )
        ],
    )

    summary = result.check_summaries.row(0, named=True)
    assert summary["status"] == "failed"
    assert summary["fail_count"] == 1


def test_json_schema_value_rule_preserves_all_structured_diagnostics() -> None:
    """Two nested failures remain two deterministic failure-case records."""
    import polars as pl

    from mountainash.validation import ValidationRunner, ValueRule, ValueValidatorKey

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"id": "bad", "extra": 1}]}),
        [
            ValueRule(
                id="payload_schema",
                fields=["payload"],
                validator=ValueValidatorKey.JSON_SCHEMA,
                options={
                    "schema": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                        "additionalProperties": False,
                    }
                },
            )
        ],
    )

    assert result.check_summaries.row(0, named=True)["fail_count"] == 1
    assert result.failure_cases.select(
        "instance_path", "schema_path", "validator"
    ).to_dicts() == [
        {
            "instance_path": "",
            "schema_path": "/additionalProperties",
            "validator": "additionalProperties",
        },
        {
            "instance_path": "/id",
            "schema_path": "/properties/id/type",
            "validator": "type",
        },
    ]

@pytest.mark.parametrize("keyword", ["$ref", "$dynamicRef", "$recursiveRef"])
def test_remote_references_are_denied_at_compile_time(keyword: str) -> None:
    """Validation cannot fetch a declaration-controlled remote document."""
    with pytest.raises(JSONSchemaReferenceDenied):
        compile_json_schema({keyword: "https://example.com/schema.json"})


def test_remote_reference_inside_frozen_sequence_is_denied() -> None:
    """Rule-option freezing must not bypass the local-reference policy."""
    with pytest.raises(JSONSchemaReferenceDenied):
        compile_json_schema(
            {"allOf": ({"$ref": "https://example.com/schema.json"},)}
        )
