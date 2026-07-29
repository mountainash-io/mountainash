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


def test_narwhals_pandas_titlecase_divergence_registered():
    d = divergence_by_id("NW-STR-14")
    assert d.backends == ("narwhals-pandas",)
    assert d.operation_keys == (FK_STR.TITLE, FK_STR.INITCAP)


def test_every_divergence_has_upstream_ref_joined():
    # Every divergence self-refs to its own id EXCEPT NW-STR-14, an inherent
    # Unicode-standard titlecase difference (pandas str.title vs polars to_titlecase)
    # with no upstream bug to file. Closed-by-default: the no-ref set is pinned.
    no_ref = {d.id for d in KNOWN_DIVERGENCES if not d.upstream_ref}
    assert no_ref == {"NW-STR-14"}, no_ref

