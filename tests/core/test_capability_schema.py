"""Durable schema values used by information, policy, and gap records."""
from __future__ import annotations

from datetime import date
from enum import Enum

import pytest

from mountainash.core.capabilities.schema import CaptureValue, GapKind, KnownGap
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR


def test_known_gap_requires_valid_date_and_reports_staleness():
    with pytest.raises(ValueError, match="since"):
        KnownGap(GapKind.ASPIRATIONAL, "not wired", "not-a-date")
    old = KnownGap(GapKind.ASPIRATIONAL, "not wired", "2025-01-01")
    current = KnownGap(GapKind.ASPIRATIONAL, "not wired", date.today().isoformat())
    assert old.is_stale(today=date.today())
    assert not current.is_stale(today=date.today())


def test_capture_values_keep_type_distinctions_and_canonical_mapping_order():
    assert CaptureValue.of(True) != CaptureValue.of(1)
    assert CaptureValue.of(-0.0) != CaptureValue.of(0.0)
    assert CaptureValue.of(float("nan")) == CaptureValue.of(float("nan"))
    assert CaptureValue.of({"b": 2, "a": 1}) == CaptureValue.of({"a": 1, "b": 2})
    assert CaptureValue.of((1, 2)) != CaptureValue.of((2, 1))


def test_capture_values_detach_mutable_inputs_and_reject_unknown_values():
    original = {"values": [1, 2]}
    captured = CaptureValue.of(original)
    original["values"].append(3)
    assert captured == CaptureValue.of({"values": [1, 2]})
    with pytest.raises(TypeError):
        CaptureValue.of(object())


def test_capture_values_preserve_known_enum_identity():
    captured = CaptureValue.of(FK_STR.LPAD)
    assert captured == CaptureValue(
        "enum", (type(FK_STR.LPAD).__module__, type(FK_STR.LPAD).__qualname__, "LPAD")
    )

    class UnknownEnum(Enum):
        VALUE = "value"

    with pytest.raises(ValueError, match="unknown enum"):
        CaptureValue.of(UnknownEnum.VALUE)


def test_capture_values_round_trip_clause_operator_authority():
    from mountainash.core.capabilities.schema import ClauseOp

    captured = CaptureValue.of(ClauseOp.EQ)
    assert captured == CaptureValue(
        "enum",
        (type(ClauseOp.EQ).__module__, type(ClauseOp.EQ).__qualname__, "EQ"),
    )
    assert CaptureValue("enum", captured.value) == captured
