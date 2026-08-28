"""DivergenceFact data integrity."""

import pytest

from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES, divergence_by_id
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)




def test_ids_unique():
    ids = [d.id for d in KNOWN_DIVERGENCES]
    assert len(ids) == len(set(ids))


def test_lookup_and_unknown_id():
    some = KNOWN_DIVERGENCES[0]
    assert divergence_by_id(some.id) is some
    with pytest.raises(KeyError, match="unknown divergence id"):
        divergence_by_id("XX-NOPE-99")
def test_ma_conf_04_registered_for_native_ibis_sqlite_struct_construction():
    fact = divergence_by_id("MA-CONF-04")
    assert fact is not None
    assert fact.backends == ("ibis-sqlite",)


def test_ma_conf_05_registered_for_temporary_portable_transport_gaps():
    fact = divergence_by_id("MA-CONF-05")
    assert fact is not None
    assert fact.backends == ("pandas", "narwhals-pandas")


def test_narwhals_pandas_titlecase_divergence_registered():
    d = divergence_by_id("NW-STR-14")
    assert d.backends == ("narwhals-pandas",)
    assert d.operation_keys == (FK_STR.TITLE, FK_STR.INITCAP)


def test_narwhals_pandas_null_input_row_divergence_registered():
    d = divergence_by_id("NW-STR-19")
    assert d.backends == ("pandas", "narwhals-pandas")
    assert d.operation_keys == (FK_STR.CONTAINS, FK_STR.STARTS_WITH, FK_STR.ENDS_WITH)


def test_upstream_ref_is_self_ref_or_absent():
    # A divergence's ``upstream_ref`` is either its own id (a registry-cataloged
    # gap — joined to registry/upstream-issues.yaml by test_upstream_registry_join)
    # or ``None`` (an inherent backend divergence with no upstream bug to file,
    # e.g. engine-leniency / semantics differences). The real error this guards
    # against is a MISMATCHED ref — one pointing at some other entry's id, which
    # would silently mis-join in the registry catalog. We do NOT pin the exact
    # set of no-ref facts: an inherent divergence needing no upstream filing is a
    # normal, expected state, not a reviewable exception.
    mismatched = {
        d.id: d.upstream_ref
        for d in KNOWN_DIVERGENCES
        if d.upstream_ref is not None and d.upstream_ref != d.id
    }
    assert not mismatched, (
        f"divergence upstream_ref must self-ref to its own id or be None; "
        f"mismatched refs: {mismatched}"
    )

