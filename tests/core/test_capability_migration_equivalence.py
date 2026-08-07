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
