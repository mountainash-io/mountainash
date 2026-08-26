"""Immutable TypeSpec-to-validation-plan compilation."""

import pytest

from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.exceptions import InvalidTypeSpecSemantics
from mountainash.typespec import (
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    TypeSpec,
    UniversalType,
)
from mountainash.validation import CompiledValidationPlan


def test_compiled_plan_isolated_from_nested_mutation() -> None:
    """Mutating a declaration after compilation must not alter executable checks."""
    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="payload",
                type=UniversalType.OBJECT,
                object_fields=[FieldSpec(name="child", type=UniversalType.STRING)],
            )
        ],
        foreign_keys=[
            ForeignKey(
                fields=["payload"],
                reference=ForeignKeyReference(resource=None, fields=["payload"]),
            )
        ],
    )

    plan = compile_datacontract(spec)
    fingerprint = plan.declaration_fingerprint
    check_ids = tuple(check.id for check in plan.checks)

    spec.fields[0].object_fields[0].name = "renamed"
    spec.foreign_keys[0].reference.fields.append("other")

    assert isinstance(plan, CompiledValidationPlan)
    assert plan.declaration_fingerprint == fingerprint
    assert tuple(check.id for check in plan.checks) == check_ids
    assert plan.field_plan.by_name["payload"].name == "payload"


def test_compile_datacontract_rejects_semantics_before_compilation() -> None:
    """An executable plan cannot be built from a semantically invalid declaration."""
    spec = TypeSpec(fields=[FieldSpec(name="", type=UniversalType.STRING)])

    with pytest.raises(InvalidTypeSpecSemantics):
        compile_datacontract(spec)


def test_compilation_preserves_native_field_extensions_and_severity() -> None:
    """Dropping native rules during plan compilation would weaken a contract."""
    from mountainash.datacontracts import BaseDataContract, Field

    class NativeContract(BaseDataContract):
        value: int = Field(
            eq=1,
            ne=2,
            gt=0,
            lt=3,
            notin=[-1],
            str_contains="1",
            str_startswith="1",
            str_endswith="1",
            severity="warning",
        )

    plan = compile_datacontract(
        NativeContract.to_typespec(),
        extensions=NativeContract._contract_fields,
    )

    checks = {check.id: check for check in plan.checks}
    expected = {
        "value__eq",
        "value__ne",
        "value__gt",
        "value__lt",
        "value__notin",
        "value__str_contains",
        "value__str_startswith",
        "value__str_endswith",
    }
    assert expected <= set(checks)
    assert {checks[check_id].severity for check_id in expected} == {"warning"}
