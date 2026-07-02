"""Unit tests for data_type dimension drift detection + policy (item 48 Task 6).

Canonical-space evaluator tests: build a TypeSpec + actual_dtypes evidence
(a plain ``{column_name: MountainashDtype}`` mapping) and assert against
``resolve_conform_output``'s returned ``ConformOutputContract`` — no frames,
no backend compilation. See conform/expressions.py's ``resolve_conform_output``
Task 6 block and ``_build_field_expr`` stage 5d for the implementation.
"""
from __future__ import annotations

import dataclasses

import pytest

from mountainash.conform.contract import resolve_contract
from mountainash.conform.drift import TypeDrift
from mountainash.conform.errors import SchemaDriftError
from mountainash.conform.expressions import resolve_conform_output
from mountainash.core.dtypes import CastSafety, MountainashDtype
from mountainash.relations.schema_inference import SchemaTypeStatus
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _spec(*fields, fields_match="open"):
    return TypeSpec(fields=list(fields), fields_match=fields_match)


def _resolve(spec, cols, dtypes, contract):
    return resolve_conform_output(
        spec, available_columns=cols, actual_dtypes=dtypes, contract=contract
    )


def _contract(data_type):
    """A non-preset "open" contract with only data_type overridden."""
    return dataclasses.replace(
        resolve_contract("open"), from_preset=False, data_type=data_type,
    )


def test_safe_cast_is_not_drift():
    """actual I32 -> declared I64 is a safe widening cast: never drift."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    out = _resolve(spec, ["v"], {"v": MountainashDtype.I32}, _contract("coerce"))

    assert out.drift.type_mismatches == []
    em = out.emitted[0]
    assert em.type_action == "coerce"
    assert em.effective_type is None


def test_unsafe_cast_coerce_reports_and_casts():
    """actual STRING -> declared I64 is unsafe; data_type="coerce" reports
    it but keeps casting as today (type_action stays "coerce")."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    out = _resolve(spec, ["v"], {"v": MountainashDtype.STRING}, _contract("coerce"))

    assert out.drift.type_mismatches == [
        TypeDrift(
            name="v", declared=MountainashDtype.I64, actual=MountainashDtype.STRING,
            safety=CastSafety.UNSAFE.value, action="coerce",
        )
    ]
    em = out.emitted[0]
    assert em.type_action == "coerce"
    assert em.effective_type is None


def test_unsafe_cast_evolve_keeps_source_type():
    """data_type="evolve": type_action == "evolve", effective_type == actual."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    out = _resolve(spec, ["v"], {"v": MountainashDtype.STRING}, _contract("evolve"))

    em = out.emitted[0]
    assert em.type_action == "evolve"
    assert em.effective_type == MountainashDtype.STRING
    assert out.drift.type_mismatches[0].action == "evolve"


def test_unsafe_cast_freeze_raises_schema_drift_error():
    """data_type="freeze": raises SchemaDriftError with the TypeDrift attached."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    with pytest.raises(SchemaDriftError) as exc_info:
        _resolve(spec, ["v"], {"v": MountainashDtype.STRING}, _contract("freeze"))

    assert exc_info.value.drift.type_mismatches == [
        TypeDrift(
            name="v", declared=MountainashDtype.I64, actual=MountainashDtype.STRING,
            safety=CastSafety.UNSAFE.value, action="freeze",
        )
    ]


def test_discard_value_marks_null_cast():
    """data_type="discard_value": type_action == "discard_value"."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    out = _resolve(
        spec, ["v"], {"v": MountainashDtype.STRING}, _contract("discard_value"),
    )

    em = out.emitted[0]
    assert em.type_action == "discard_value"
    assert out.row_filter_sources == []


def test_discard_row_registers_row_filter():
    """data_type="discard_row": value nulled (same as discard_value) AND the
    source registers in row_filter_sources for a downstream row-drop filter."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    out = _resolve(
        spec, ["v"], {"v": MountainashDtype.STRING}, _contract("discard_row"),
    )

    em = out.emitted[0]
    assert em.type_action == "discard_value"
    assert out.row_filter_sources == [("v", MountainashDtype.I64)]


def test_dotted_source_excluded_from_type_detection():
    """finding 10: the struct ROOT's actual dtype is never compared to the
    nested field's declared type — no TypeDrift for dotted sources, even
    when the root's actual dtype would otherwise be an unsafe mismatch."""
    spec = _spec(
        FieldSpec(name="city", type=UniversalType.STRING, rename_from="address.city"),
    )
    out = _resolve(
        spec, ["address"], {"address": MountainashDtype.I64}, _contract("freeze"),
    )

    assert out.drift.type_mismatches == []
    em = out.emitted[0]
    assert em.source_name == "address.city"
    assert em.type_action == "coerce"


def test_missing_dtype_evidence_no_false_drift():
    """No actual_dtypes entry, or a SchemaTypeStatus.UNKNOWN entry -> no
    assessment possible, no TypeDrift; coerce proceeds exactly as today."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))

    out_missing = _resolve(spec, ["v"], {}, _contract("freeze"))
    out_unknown = _resolve(
        spec, ["v"], {"v": SchemaTypeStatus.UNKNOWN}, _contract("freeze"),
    )

    for out in (out_missing, out_unknown):
        assert out.drift.type_mismatches == []
        assert out.emitted[0].type_action == "coerce"


# --- Parity: no actual_dtypes evidence at all -> no assessment, drift stays None ---


def test_no_actual_dtypes_and_no_columns_drift_stays_none():
    """With no contract configured and no actual_dtypes evidence, behaviour
    reduces exactly to today's: no drift assessment at all (drift is None,
    not an empty ConformDrift), coerce as always."""
    spec = _spec(FieldSpec(name="v", type=UniversalType.INTEGER))
    out = resolve_conform_output(spec)

    assert out.drift is None
    assert out.row_filter_sources == []
    assert out.emitted[0].type_action == "coerce"
