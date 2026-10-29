"""Tests for Rule dataclass and combinators."""
from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma
from mountainash.datacontracts.rule import Rule, guarded


class TestRule:
    """Rule is a frozen dataclass holding an id and an expression."""

    def test_create_simple_rule(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        assert rule.id == "VR01"
        assert rule.expr is not None

    def test_rule_is_frozen(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        with pytest.raises(AttributeError):
            rule.id = "VR02"

    def test_rule_with_metadata(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0), metadata={"severity": "error"})
        assert rule.metadata["severity"] == "error"

    def test_rule_metadata_defaults_empty(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        assert rule.metadata == {}

    def test_rule_expr_compiles_to_polars(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        df = pl.DataFrame({"age": [10, -1, 5]})
        result = df.select(rule.expr.compile(df))
        assert result.to_series().to_list() == [True, False, True]


class TestGuarded:
    """guarded(precondition, test) returns (~precondition) | test."""

    def test_guarded_passes_when_precondition_false(self):
        expr = guarded(
            precondition=ma.col("val").is_not_null(),
            test=ma.col("val").gt(0),
        )
        df = pl.DataFrame({"val": [None, 5, -1]})
        result = df.select(expr.compile(df))
        # row 0: precondition=False → True (skip test)
        # row 1: precondition=True, test=True → True
        # row 2: precondition=True, test=False → False
        assert result.to_series().to_list() == [True, True, False]

    def test_guarded_returns_expression_api(self):
        expr = guarded(
            precondition=ma.col("x").is_not_null(),
            test=ma.col("x").gt(0),
        )
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_guarded_composes_with_other_expressions(self):
        expr = guarded(
            precondition=ma.col("x").is_not_null(),
            test=ma.col("x").gt(0),
        ) & ma.col("y").eq(1)
        df = pl.DataFrame({"x": [5, -1], "y": [1, 1]})
        result = df.select(expr.compile(df))
        assert result.to_series().to_list() == [True, False]


def test_rule_extended_kwargs_default_none():
    import mountainash as ma
    from mountainash.datacontracts.rule import Rule

    rule = Rule("r", expr=ma.col("a").ge(0))
    assert rule.mostly is None
    assert rule.booleanizer is None
    assert rule.error_message is None
    assert rule.fields is None


def test_rule_extended_kwargs_carry():
    import mountainash as ma
    from mountainash.datacontracts.rule import Rule

    rule = Rule(
        "r", expr=ma.col("a").ge(0), mostly=0.9, booleanizer="t_maybe_true",
        severity="warning", error_message="a {a} bad", fields=["a"],
    )
    assert (rule.mostly, rule.booleanizer) == (0.9, "t_maybe_true")
    assert rule.severity == "warning"
    assert rule.fields == ["a"]


def test_rule_severity_closed_vocabulary():
    import pytest

    import mountainash as ma
    from mountainash.datacontracts.rule import ContextualRule, Rule
    from mountainash.validation.errors import CheckDeclarationError

    assert Rule("r", expr=ma.col("a").ge(0)).severity == "blocking"
    with pytest.raises(CheckDeclarationError):
        Rule("r", expr=ma.col("a").ge(0), severity="warn")
    with pytest.raises(CheckDeclarationError):
        ContextualRule("c", build=lambda ctx: ma.col("a").ge(0), severity="advisory")


def test_contextual_rule_carries_build_and_kwargs():
    import mountainash as ma
    from mountainash.datacontracts.rule import ContextualRule

    rule = ContextualRule(
        "vr02_not_future",
        build=lambda ctx: ma.col("extract_date").str.to_datetime("%Y-%m-%dT%H:%M:%S")
                            .le(ma.lit(ctx["as_of"])),
        fields=["extract_date"],
    )
    assert rule.id == "vr02_not_future"
    assert callable(rule.build)
    assert rule.mostly is None
