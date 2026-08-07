"""Each migrated declaration module registers EXACTLY the facts its
predecessor registered (spec: fact identity is the drift detector).

These tests import BOTH old and new modules; they are deleted in Task 11
together with the old files.
"""
from __future__ import annotations


def _multiset_equal(new_facts, old_facts):
    old = list(old_facts)
    assert len(new_facts) == len(old)
    for f in new_facts:
        assert f in old, f"fact not in legacy set: {f}"
        old.remove(f)
    assert old == [], f"legacy facts missing from new module: {old}"


def test_string_module_equivalence():
    from mountainash.expressions.backends.capabilities import string as new
    from mountainash.expressions.backends.expression_systems import (
        string_option_capabilities as old,
    )
    from mountainash.core.constants import CONST_BACKEND

    legacy = (
        list(old._POLARS_FACTS)
        + list(old._IBIS_FAMILY_DEFAULTS) + list(old._IBIS_DUCKDB_FACTS)
        + list(old._op_level_facts(CONST_BACKEND.IBIS))
        + list(old._NARWHALS_FACTS)
        + list(old._op_level_facts(CONST_BACKEND.NARWHALS))
    )
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
    assert new.BROKEN_STRING_OPS_BY_BACKEND == old._BROKEN_STRING_OPS_BY_BACKEND
    assert new.OP_LEVEL_FKEYS == old._OP_LEVEL_FKEYS


def test_arithmetic_module_equivalence():
    from mountainash.expressions.backends.capabilities import arithmetic as new
    from mountainash.expressions.backends.expression_systems import (
        arithmetic_option_capabilities as old,
    )

    legacy = (
        list(old.POLARS_ARITHMETIC_OPTION_CAPABILITIES)
        + list(old._SEMANTIC_FACTS["polars"]) + list(old._ROUNDING_FACTS["polars"])
        + list(old.IBIS_ARITHMETIC_OPTION_CAPABILITIES)
        + list(old.IBIS_DUCKDB_OVERFLOW_REFINEMENTS)
        + list(old._IBIS_SEMANTIC_FAMILY_DEFAULTS) + list(old._IBIS_ROUNDING_FAMILY_DEFAULTS)
        + list(old._SEMANTIC_FACTS["ibis"]) + list(old._ROUNDING_FACTS["ibis"])
        + list(old.NARWHALS_ARITHMETIC_OPTION_CAPABILITIES)
        + list(old._SEMANTIC_FACTS["narwhals-polars"]) + list(old._SEMANTIC_FACTS["narwhals-pandas"])
        + list(old._ROUNDING_FACTS["narwhals-polars"]) + list(old._ROUNDING_FACTS["narwhals-pandas"])
    )
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)


def test_datetime_options_module_equivalence():
    from mountainash.expressions.backends.capabilities.datetime import options as new
    from mountainash.expressions.backends.expression_systems import (
        datetime_option_capabilities as old,
    )

    legacy = (
        list(old._IBIS_FAMILY_DEFAULTS) + list(old._IBIS_DUCKDB_FACTS)
        + list(old._NARWHALS_POLARS_FACTS) + list(old._NARWHALS_PANDAS_FACTS)
    )
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)


def test_datetime_value_classes_ma_module_equivalence():
    from mountainash.expressions.backends.capabilities.datetime import (
        value_classes_ma as new,
    )
    from mountainash.expressions.backends.expression_systems import (
        datetime_value_class_capabilities_ma as old,
    )

    legacy = list(old._IBIS_FACTS) + list(old._NARWHALS_FACTS)
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)


def test_datetime_value_classes_substrait_module_equivalence():
    from mountainash.expressions.backends.capabilities.datetime import (
        value_classes_substrait as new,
    )
    from mountainash.expressions.backends.expression_systems import (
        datetime_value_class_capabilities_substrait as old,
    )

    legacy = list(old._IBIS_FACTS) + list(old._NARWHALS_FACTS)
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)


def test_strptime_module_equivalence():
    from mountainash.expressions.backends.capabilities.datetime import (
        strptime as new,
    )
    from mountainash.expressions.backends.expression_systems import (
        strptime_format_capabilities as old,
    )

    legacy = list(old._IBIS_SQLITE_FACTS) + list(old._NARWHALS_FACTS)
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)


def test_ibis_module_equivalence():
    from mountainash.expressions.backends.capabilities import ibis as new
    from mountainash.expressions.backends.expression_systems import (
        ibis_capabilities as old,
    )

    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, old.IBIS_EXPR_CAPABILITIES)
    assert new.IBIS_EXPR_CAPABILITIES == old.IBIS_EXPR_CAPABILITIES


def test_polars_module_equivalence():
    from mountainash.expressions.backends.capabilities import polars as new
    from mountainash.expressions.backends.expression_systems.polars.base import (
        PolarsBaseExpressionSystem,
    )

    legacy = PolarsBaseExpressionSystem.CAPABILITIES
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
    assert new.POLARS_EXPR_CAPABILITIES == legacy


def test_narwhals_module_equivalence():
    from mountainash.expressions.backends.capabilities import narwhals as new
    from mountainash.expressions.backends.expression_systems.narwhals.base import (
        NarwhalsBaseExpressionSystem,
    )

    legacy = NarwhalsBaseExpressionSystem.CAPABILITIES
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
    assert new.NARWHALS_EXPR_CAPABILITIES == legacy


def test_polymorphic_module_equivalence(monkeypatch):
    from mountainash.expressions.backends.capabilities import polymorphic as new
    from mountainash.core import capabilities as core_facts

    snap = core_facts.CapabilityRegistry.snapshot()
    try:
        core_facts.CapabilityRegistry.reset()
        monkeypatch.setattr(core_facts.core_facts, "_REGISTERED", False)
        core_facts.core_facts.register_core_polymorphic_facts()
        legacy = core_facts.CapabilityRegistry.facts()
        new_facts = [f for d in new.DECLARATIONS for f in d.facts]
        _multiset_equal(new_facts, legacy)
    finally:
        core_facts.CapabilityRegistry.restore(snap)


def test_relations_ibis_module_equivalence():
    from mountainash.relations.backends.capabilities import ibis as new
    from mountainash.relations.backends.relation_systems import (
        ibis_relation_capabilities as old,
    )

    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, old.IBIS_REL_CAPABILITIES)
    assert new.IBIS_REL_CAPABILITIES == old.IBIS_REL_CAPABILITIES


def test_relations_polars_module_equivalence():
    from mountainash.relations.backends.capabilities import polars as new
    from mountainash.relations.backends.relation_systems.polars.base import (
        PolarsBaseRelationSystem,
    )

    legacy = PolarsBaseRelationSystem.CAPABILITIES
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
    assert new.POLARS_REL_CAPABILITIES == legacy


def test_relations_narwhals_module_equivalence():
    from mountainash.relations.backends.capabilities import narwhals as new
    from mountainash.relations.backends.relation_systems.narwhals.base import (
        NarwhalsBaseRelationSystem,
    )

    legacy = NarwhalsBaseRelationSystem.CAPABILITIES
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
    assert new.NARWHALS_REL_CAPABILITIES == legacy
