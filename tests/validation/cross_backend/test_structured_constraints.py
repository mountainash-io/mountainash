"""Structured Frictionless constraints execute against logical containers cross-backend."""

import pytest

import mountainash as ma
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.typespec import FieldConstraints, FieldSpec, TypeSpec, UniversalType
from mountainash.validation import ValidationRunner

from fixtures.backend_registry import ALL_BACKENDS

from fixtures.capability_gating import xfail_divergence

_STRUCTURED_BACKENDS = [
    pytest.param(
        backend,
        marks=xfail_divergence("MA-CONF-04", backend=backend),
    )
    for backend in ALL_BACKENDS
]


@pytest.mark.parametrize("backend_name", _STRUCTURED_BACKENDS)
def test_compiled_json_schema_reports_logical_object_failure(backend_name, backend_factory):
    """JSON Schema receives a logical object rather than backend-native state."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="payload",
                    type=UniversalType.OBJECT,
                    constraints=FieldConstraints(
                        json_schema={
                            "type": "object",
                            "required": ["id"],
                            "properties": {"id": {"type": "integer", "minimum": 1}},
                        }
                    ),
                )
            ]
        )
    )

    result = ValidationRunner().validate_relation(
        ma.relation(backend_factory.create({"payload": [{"id": 0}]}, backend_name)),
        plan=plan,
    )

    summary = result.check_summaries.filter(
        result.check_summaries["check_id"] == "payload_json_schema"
    ).row(0, named=True)
    assert summary["status"] == "failed", backend_name
    failure = result.failure_cases.row(0, named=True)
    assert failure["instance_path"] == "/id", backend_name
    assert failure["validator"] == "minimum", backend_name
