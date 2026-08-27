"""Compiled validation-plan snapshot tests."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import RowRule
from mountainash.validation.plan import build_compiled_plan, thaw_value


def test_compiled_plan_copies_mutable_check_declarations():
    fields = ["id"]
    metadata = {"provenance": {"source": "initial"}}
    check = RowRule(
        id="id_present",
        expr=ma.col("id").is_not_null(),
        fields=fields,
        metadata=metadata,
    )

    plan = build_compiled_plan(
        TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)]),
        [check],
    )
    fields.append("later")
    metadata["provenance"]["source"] = "mutated"

    compiled_check = plan.checks[0]
    assert compiled_check is not check
    assert compiled_check.fields == ("id",)
    assert compiled_check.metadata["provenance"]["source"] == "initial"
    with pytest.raises(TypeError):
        compiled_check.metadata["new"] = "value"


def test_thaw_rejects_unregistered_dataclass_identifiers():
    with pytest.raises(ValueError, match="unsupported frozen dataclass"):
        thaw_value(
            {
                "__dataclass__": "pathlib:Path",
                "fields": {},
            }
        )
