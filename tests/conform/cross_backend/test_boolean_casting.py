"""Tests for trueValues/falseValues boolean casting in conform pipeline."""
from __future__ import annotations

import pytest
import polars as pl

import mountainash as ma
from mountainash.conform.errors import ConformTransformError
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS



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
        """A Boolean source column retains its Boolean values."""
        df = pl.DataFrame({"flag": [True, False, True]})
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="flag", type=UniversalType.BOOLEAN)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flag"].to_list() == [True, False, True]



@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_boolean_throw_preserves_null_and_rejects_invalid_tokens(
    backend_name, backend_factory
):
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
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as raised:
            ma.relation(df).conform(spec).to_polars()
        assert raised.value.function_key is FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS
        assert raised.value.backend == "ibis"
        assert raised.value.limitation is None
        return
    with pytest.raises(ConformTransformError):
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


def test_ibis_sqlite_throw_mode_refuses_parse_tokens(backend_factory):
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
    with pytest.raises(BackendCapabilityError) as raised:
        ma.relation(df).conform(spec).to_polars()
    assert raised.value.function_key is FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS
    assert raised.value.backend == "ibis"
    assert raised.value.limitation is None
