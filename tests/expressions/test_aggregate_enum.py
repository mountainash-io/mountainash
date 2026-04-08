"""Tests for Substrait scalar aggregate enum + protocol + mapping wiring."""
from __future__ import annotations

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)


def test_count_enum_exists():
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT is not None


def test_count_records_enum_exists():
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS is not None


def test_count_and_count_records_are_distinct():
    assert (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT
        != FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS
    )


def test_count_records_has_function_mapping():
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    # Ensure registry is initialised
    ExpressionFunctionRegistry._init_registry()
    keys = list(ExpressionFunctionRegistry._functions.keys())
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS in keys
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT in keys
