"""DivergenceFact data integrity."""

import pytest

from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES, divergence_by_id


def test_ids_unique():
    ids = [d.id for d in KNOWN_DIVERGENCES]
    assert len(ids) == len(set(ids))


def test_lookup_and_unknown_id():
    some = KNOWN_DIVERGENCES[0]
    assert divergence_by_id(some.id) is some
    with pytest.raises(KeyError, match="unknown divergence id"):
        divergence_by_id("XX-NOPE-99")


def test_every_divergence_has_upstream_ref_joined():
    # The Phase 2 join test picks these up via _code_refs(); this asserts
    # the local invariant: every divergence carries a ref (its own id).
    for divergence in KNOWN_DIVERGENCES:
        assert divergence.upstream_ref, divergence.id
