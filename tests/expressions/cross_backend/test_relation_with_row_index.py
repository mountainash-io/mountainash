"""Cross-backend regression pin for `Relation.with_row_index`.

Tracks mountainash#78 and the upstream gap
https://github.com/ibis-project/ibis/issues/10513 — the Ibis Polars
backend has no translator for `WindowFunction`, so `ibis.row_number()`
(which our `with_row_index` lowers to) cannot compile on `ibis-polars`.

ibis-polars is gated through the capability spine (RKEY_MOUNTAINASH_REL.
WITH_ROW_INDEX, BUILD boundary) — asserted via ``assert_capability_gated``.
narwhals-lazy diverges (with_row_index requires an explicit ``order_by=``);
that is declared as ``NW-REL-01`` and driven by ``xfail_divergence``.

See principle `d.cross-backend/known-divergences.md` §8.
"""
from __future__ import annotations

import pytest

from mountainash.relations import relation
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import (
    assert_capability_gated,
    gate_dialect,
    gate_family,
    xfail_divergence,
)

_WRI = [
    pytest.param(b, marks=xfail_divergence("NW-REL-01", backend=b)) for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _WRI)
class TestWithRowIndex:

    def test_with_row_index_adds_zero_based_sequence(self, backend_name, backend_factory):
        """`with_row_index` adds a 0..N-1 column on every backend (ibis-polars gated)."""
        data = {"name": ["a", "b", "c", "d"]}
        df = backend_factory.create(data, backend_name)

        result = assert_capability_gated(
            RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX,
            gate_family(backend_name),
            dialect=gate_dialect(backend_name),
            build=lambda: relation(df).with_row_index(name="idx").collect(),
        )
        if backend_name == "ibis-polars":
            return  # gate asserted the BUILD-time BackendCapabilityError

        # Result type varies by backend; extract the idx column to a plain list.
        if hasattr(result, "execute"):
            idx_values = result.execute()["idx"].tolist()
        else:
            idx_values = list(result["idx"])

        assert idx_values == [0, 1, 2, 3], (
            f"[{backend_name}] Expected [0, 1, 2, 3], got {idx_values}"
        )
