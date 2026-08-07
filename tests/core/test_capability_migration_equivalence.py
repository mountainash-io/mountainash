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
