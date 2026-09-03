"""The CSV dialect routing tables and the declared facts stay in sync."""

from mountainash.core.capabilities import (
    CapabilityRegistry,
    Enforcement,
    load_all_capability_declarations,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.resource_files import (
    IBIS_NON_DEFAULT_DIALECT_CONDITION,
    NATIVE_UNSAFE_DIALECT_CONDITION,
    _MAPPABLE_DIALECT_FIELDS,
    _NATIVE_SAFE_DIALECT_FIELDS,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)
from mountainash.typespec.datapackage import TableDialect


NON_DEFAULT_DIALECT_VALUES = {
    "delimiter": ";",
    "line_terminator": "\r\n",
    "quote_char": "'",
    "double_quote": False,
    "escape_char": "\\",
    "null_sequence": "NULL",
    "skip_initial_space": True,
    "header": False,
    "header_rows": [2],
    "header_join": " / ",
    "comment_char": "#",
    "comment_rows": [2],
}


def _dialects_with_one_non_default_field() -> dict[str, TableDialect]:
    return {
        field: TableDialect(**{field: NON_DEFAULT_DIALECT_VALUES[field]})
        for field in _MAPPABLE_DIALECT_FIELDS
    }


def _routing_fact(backend):
    return next(
        fact
        for fact in CapabilityRegistry.facts(enforcement=Enforcement.ROUTER_METADATA)
        if fact.operation_key is RKEY_MOUNTAINASH_REL.READ_RESOURCE
        and fact.param == "resource"
        and fact.backend is backend
    )


def _condition_fields(condition: str) -> tuple[str, ...]:
    return tuple(clause.removeprefix("resource.dialect.").split(" ", 1)[0]
                 for clause in condition.split(" or "))


def test_exact_polars_and_narwhals_fallback_condition_coverage():
    load_all_capability_declarations()
    dialects = _dialects_with_one_non_default_field()
    expected_fields = tuple(sorted(
        _MAPPABLE_DIALECT_FIELDS - _NATIVE_SAFE_DIALECT_FIELDS
    ))
    expected_condition = " or ".join(
        f"resource.dialect.{field} is set" for field in expected_fields
    )

    assert set(dialects) == _MAPPABLE_DIALECT_FIELDS
    assert _condition_fields(NATIVE_UNSAFE_DIALECT_CONDITION) == expected_fields
    assert NATIVE_UNSAFE_DIALECT_CONDITION == expected_condition
    for backend in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS):
        assert _routing_fact(backend).condition == NATIVE_UNSAFE_DIALECT_CONDITION


def test_exact_ibis_fallback_condition_coverage():
    load_all_capability_declarations()
    dialects = _dialects_with_one_non_default_field()
    expected_fields = tuple(sorted(_MAPPABLE_DIALECT_FIELDS))
    expected_condition = " or ".join(
        (
            "resource.dialect.delimiter is non-default"
            if field == "delimiter"
            else "resource.dialect.header is false"
            if field == "header"
            else f"resource.dialect.{field} is set"
        )
        for field in expected_fields
    )

    assert set(dialects) == _MAPPABLE_DIALECT_FIELDS
    assert _condition_fields(IBIS_NON_DEFAULT_DIALECT_CONDITION) == expected_fields
    assert IBIS_NON_DEFAULT_DIALECT_CONDITION == expected_condition
    assert "resource.dialect.delimiter is non-default" in (
        IBIS_NON_DEFAULT_DIALECT_CONDITION
    )
    assert "resource.dialect.header is false" in IBIS_NON_DEFAULT_DIALECT_CONDITION
    assert _routing_fact(CONST_BACKEND.IBIS).condition == (
        IBIS_NON_DEFAULT_DIALECT_CONDITION
    )


def test_every_non_default_dialect_value_is_represented_by_a_condition_clause():
    for field, dialect in _dialects_with_one_non_default_field().items():
        assert f"resource.dialect.{field}" in NATIVE_UNSAFE_DIALECT_CONDITION or (
            field in _NATIVE_SAFE_DIALECT_FIELDS
        )
        assert f"resource.dialect.{field}" in IBIS_NON_DEFAULT_DIALECT_CONDITION


def test_every_fallback_routed_field_is_declared():
    load_all_capability_declarations()

    fallback_fields = _MAPPABLE_DIALECT_FIELDS - _NATIVE_SAFE_DIALECT_FIELDS
    declared_conditions = {
        fact.condition
        for fact in CapabilityRegistry.facts(enforcement=Enforcement.ROUTER_METADATA)
        if "dialect." in (fact.condition or "")
    }
    undeclared = {
        field
        for field in fallback_fields
        if not any(field in condition for condition in declared_conditions)
    }

    assert not undeclared, (
        f"CSV dialect fields routed to fallback but not declared as facts: {undeclared}"
    )


def test_escape_char_fact_declared_on_every_backend():
    """Every backend declares the escape-char routing limitation explicitly."""
    load_all_capability_declarations()

    for family in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS):
        assert any(
            fact.operation_key is RKEY_MOUNTAINASH_REL.READ_RESOURCE
            and fact.param == "resource"
            and fact.backend is family
            and "escape_char" in (fact.condition or "")
            for fact in CapabilityRegistry.facts()
        ), f"Missing escape_char CapabilityFact for backend {family.value}"
