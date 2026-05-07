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
