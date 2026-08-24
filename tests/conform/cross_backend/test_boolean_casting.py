"""Tests for trueValues/falseValues boolean casting in conform pipeline."""
from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals",
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


# ---------------------------------------------------------------------------
# Unit tests: _build_conform_exprs produces boolean-cast expressions
# ---------------------------------------------------------------------------


class TestBuildConformExprsBooleanCast:
    """Unit tests that the expression builder emits boolean casting logic."""

    def test_emits_expr_for_boolean_field(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_custom_true_false_values(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="flag",
                    type=UniversalType.BOOLEAN,
                    true_values=["yes"],
                    false_values=["no"],
                ),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1


# ---------------------------------------------------------------------------
# Cross-backend: default trueValues/falseValues
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestBooleanCastingDefaults:
    def test_default_true_values(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"flag": ["true", "True", "TRUE", "1"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flag"].to_list() == [True, True, True, True]

    def test_default_false_values(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"flag": ["false", "False", "FALSE", "0"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flag"].to_list() == [False, False, False, False]

    def test_mixed_true_false(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"flag": ["true", "false", "TRUE", "0"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flag"].to_list() == [True, False, True, False]


# ---------------------------------------------------------------------------
# Cross-backend: custom trueValues/falseValues
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestBooleanCastingCustom:
    def test_custom_true_false_values(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"flag": ["yes", "no", "yes"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="flag",
                    type=UniversalType.BOOLEAN,
                    true_values=["yes"],
                    false_values=["no"],
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flag"].to_list() == [True, False, True]


# ---------------------------------------------------------------------------
# Boolean source column (already boolean, not string)
# ---------------------------------------------------------------------------


class TestBooleanCastingAlreadyBoolean:
    def test_preserves_existing_boolean_values(self):
        """Boolean source column: cast(str).is_in() matches, preserves values."""
        df = pl.DataFrame({"flag": [True, False, True]})
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flag"].to_list() == [True, False, True]
