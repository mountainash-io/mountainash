"""classify(): typed AST analysis routing Rule declarations to RowRule/ScalarRule."""
from dataclasses import dataclass, field
from typing import Any

import pytest

import mountainash as ma
from mountainash.validation.checks import RowRule, ScalarRule, classify
from mountainash.validation.errors import CheckDeclarationError


@dataclass(frozen=True)
class _Rule:  # minimal stand-in matching the datacontracts Rule attribute shape
    id: str
    expr: Any
    mostly: float | None = None
    booleanizer: str | None = None
    error_message: str | None = None
    fields: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def test_row_field_comparison_is_row():
    check = classify(_Rule("r", ma.col("age").ge(0)))
    assert isinstance(check, RowRule)


def test_plain_aggregate_is_scalar():
    check = classify(_Rule("s", ma.col("age").mean().gt(0)))
    assert isinstance(check, ScalarRule)


def test_zero_field_aggregate_root_is_scalar():
    check = classify(_Rule("n", ma.len().gt(0)))
    assert isinstance(check, ScalarRule)


def test_windowed_aggregate_is_row():
    check = classify(_Rule("w", ma.col("x").mean().over("group").gt(0)))
    assert isinstance(check, RowRule)


def test_mixed_broadcast_is_row():
    check = classify(_Rule("m", ma.col("x").gt(ma.col("x").mean())))
    assert isinstance(check, RowRule)


def test_ternary_rule_is_row():
    check = classify(_Rule("t", ma.col("flag").t_eq(1)))
    assert isinstance(check, RowRule)


def test_literal_only_raises():
    with pytest.raises(CheckDeclarationError):
        classify(_Rule("lit", ma.lit(True)))


def test_mostly_on_scalar_raises():
    with pytest.raises(CheckDeclarationError):
        classify(_Rule("s", ma.col("age").mean().gt(0), mostly=0.9))


def test_booleanizer_on_scalar_raises():
    """spec §6.1: silently dropping a declared booleanizer would be a lie."""
    with pytest.raises(CheckDeclarationError):
        classify(_Rule("s", ma.col("age").mean().gt(0), booleanizer="t_maybe_true"))


def test_fields_on_scalar_raises():
    """spec §6.1: scalar rules emit no failure rows; declared fields are inert."""
    with pytest.raises(CheckDeclarationError):
        classify(_Rule("s", ma.col("age").mean().gt(0), fields=["age"]))


def test_row_attributes_carry_through():
    check = classify(
        _Rule(
            "r",
            ma.col("age").ge(0),
            mostly=0.95,
            booleanizer="t_maybe_true",
            error_message="age {age} negative",
            fields=["age"],
            metadata={"severity": "high"},
        )
    )
    assert check == RowRule(
        id="r",
        expr=check.expr,
        mostly=0.95,
        booleanizer="t_maybe_true",
        error_message="age {age} negative",
        fields=["age"],
        metadata={"severity": "high"},
    )
