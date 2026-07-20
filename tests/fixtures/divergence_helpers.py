"""Declaration-driven divergence xfails (spec Section 4).

Usage:
    @xfail_divergence("IB-CAST-01", backend=backend)   # inside a parametrized test
or as a param mark:
    pytest.param("ibis-duckdb", marks=xfail_divergence("IB-CAST-01", backend="ibis-duckdb"))

Reason, backend scope, and the upstream ref all come from the fact — the
reconciliation audit joins on the ID, not path heuristics.
"""
from __future__ import annotations

import pytest

from mountainash.core.capabilities.divergences import divergence_by_id


def xfail_divergence(divergence_id: str, *, backend: str, strict: bool = True):
    d = divergence_by_id(divergence_id)
    if backend not in d.backends and not any(
        backend.startswith(b) or b.startswith(backend) for b in d.backends
    ):
        # The divergence does not apply to this backend — no mark.
        return pytest.mark.usefixtures()  # no-op mark
    return pytest.mark.xfail(
        strict=strict,
        reason=f"[{divergence_id}] {d.summary} — workaround: {d.workaround}",
    )
