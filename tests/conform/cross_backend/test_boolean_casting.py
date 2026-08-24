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
        result = ma.relation(df).conform(
            spec, contract={"data_type": "discard_value"}
        ).to_polars()
        assert result["flag"].to_list() == [True, True, True, True]

    def test_default_false_values(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"flag": ["false", "False", "FALSE", "0"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(
            spec, contract={"data_type": "discard_value"}
        ).to_polars()
        assert result["flag"].to_list() == [False, False, False, False]

    def test_mixed_true_false(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"flag": ["true", "false", "TRUE", "0"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(
            spec, contract={"data_type": "discard_value"}
        ).to_polars()
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
        result = ma.relation(df).conform(
            spec, contract={"data_type": "discard_value"}
        ).to_polars()
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


def test_boolean_cast_uses_parse_tokens_operation():
    from mountainash.conform.expressions import _build_conform_exprs
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
    )

    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
    )
    result = _build_conform_exprs(spec)
    operation = result.exprs[0].node.arguments[0]
    assert operation.function_key is FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS
    assert operation.options["true_values"] == ("true", "True", "TRUE", "1")
    assert operation.options["false_values"] == ("false", "False", "FALSE", "0")
    assert operation.options["failure_behavior"] == "throw"

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_boolean_cast_preserves_null_and_rejects_invalid_tokens(backend_name, backend_factory):
    df = backend_factory.create({"flag": ["yes", "no", None, "maybe"]}, backend_name)
    spec = TypeSpec(
        fields_match="open",
        fields=[
            FieldSpec(
                name="flag",
                type=UniversalType.BOOLEAN,
                true_values=["yes"],
                false_values=["no"],
            ),
        ],
    )
    with pytest.raises(Exception):
        ma.relation(df).conform(spec).to_polars()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_boolean_discard_value_turns_invalid_tokens_into_null(backend_name, backend_factory):
    df = backend_factory.create({"flag": ["yes", "no", None, "maybe"]}, backend_name)
    spec = TypeSpec(
        fields_match="open",
        fields=[
            FieldSpec(
                name="flag",
                type=UniversalType.BOOLEAN,
                true_values=["yes"],
                false_values=["no"],
            ),
        ],
    )
    result = ma.relation(df).conform(
        spec, contract={"data_type": "discard_value"}
    ).to_polars()
    assert result["flag"].to_list() == [True, False, None, None]




@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_boolean_tokens_match_exactly_without_substring_replacement(backend_name, backend_factory):
    df = backend_factory.create({"flag": ["maybe", "y"]}, backend_name)
    spec = TypeSpec(
        fields_match="open",
        fields=[
            FieldSpec(
                name="flag",
                type=UniversalType.BOOLEAN,
                true_values=["y"],
                false_values=["maybe"],
            ),
        ],
    )
    result = ma.relation(df).conform(
        spec, contract={"data_type": "discard_value"}
    ).to_polars()
    assert result["flag"].to_list() == [False, True]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_boolean_throw_rejects_numeric_unconfigured_token(backend_name, backend_factory):
    df = backend_factory.create({"flag": ["yes", "no", "2"]}, backend_name)
    spec = TypeSpec(
        fields_match="open",
        fields=[
            FieldSpec(
                name="flag",
                type=UniversalType.BOOLEAN,
                true_values=["yes"],
                false_values=["no"],
            ),
        ],
    )
    with pytest.raises(Exception):
        ma.relation(df).conform(spec).to_polars()
def test_ibis_sqlite_throw_mode_is_gated(backend_factory):
    from mountainash.core.types import BackendCapabilityError

    df = backend_factory.create({"flag": ["yes"]}, "ibis-sqlite")
    spec = TypeSpec(
        fields_match="open",
        fields=[
            FieldSpec(
                name="flag",
                type=UniversalType.BOOLEAN,
                true_values=["yes"],
                false_values=["no"],
            ),
        ],
    )
    with pytest.raises(BackendCapabilityError, match="ibis-sqlite"):
        ma.relation(df).conform(spec).to_polars()
