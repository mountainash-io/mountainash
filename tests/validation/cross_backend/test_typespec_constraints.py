"""Compiled Frictionless constraints execute against logical values on every backend."""

import pytest

import mountainash as ma
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.typespec import FieldConstraints, FieldSpec, TypeSpec, UniversalType
from mountainash.validation import ValidationRunner

from fixtures.backend_registry import ALL_BACKENDS


def _status(result, check_id: str) -> str:
    summary = result.check_summaries.filter(result.check_summaries["check_id"] == check_id)
    assert summary.height == 1, f"missing check {check_id!r}: {result.check_summaries.to_dicts()}"
    return summary.row(0, named=True)["status"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_compiled_scalar_constraints_use_logical_values(backend_name, backend_factory):
    """Range, XML Schema pattern, enum, and categories agree cross-backend."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="amount",
                    type=UniversalType.INTEGER,
                    constraints=FieldConstraints(minimum=1, exclusive_maximum=3),
                ),
                FieldSpec(
                    name="code",
                    type=UniversalType.STRING,
                    categories=["AB12"],
                    constraints=FieldConstraints(
                        pattern="[A-Z]{2}[0-9]{2}", enum=["AB12"]
                    ),
                ),
            ]
        )
    )

    result = ValidationRunner().validate_relation(
        ma.relation(
            backend_factory.create(
                {"amount": [1, 3], "code": ["AB12", "bad"]}, backend_name
            )
        ),
        plan=plan,
    )

    assert _status(result, "amount_range") == "failed", backend_name
    assert _status(result, "code_pattern") == "failed", backend_name
    assert _status(result, "code_enum_membership") == "failed", backend_name
    assert _status(result, "code_category_membership") == "failed", backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_compiled_required_and_unique_constraints_share_null_semantics(
    backend_name, backend_factory
):
    """Null fails required but does not enter a field-uniqueness comparison."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="id",
                    type=UniversalType.STRING,
                    constraints=FieldConstraints(required=True, unique=True),
                )
            ]
        )
    )

    result = ValidationRunner().validate_relation(
        ma.relation(backend_factory.create({"id": ["1", "1", None]}, backend_name)),
        plan=plan,
    )

    assert _status(result, "id__not_null") == "failed", backend_name
    assert _status(result, "id_unique") == "failed", backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_compiled_date_ranges_compare_conformed_logical_values(
    backend_name, backend_factory
):
    """ISO date text becomes logical dates before the range validator runs."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="day",
                    type=UniversalType.DATE,
                    constraints=FieldConstraints(minimum="2024-01-01"),
                )
            ]
        )
    )

    result = ValidationRunner().validate_relation(
        ma.relation(
            backend_factory.create(
                {"day": ["2024-01-01", "2023-12-31"]}, backend_name
            )
        ),
        plan=plan,
    )

    assert _status(result, "day_range") == "failed", backend_name
