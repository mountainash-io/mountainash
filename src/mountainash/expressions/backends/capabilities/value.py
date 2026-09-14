"""Implemented-API evidence for original-domain value operations."""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)
from mountainash.core.constants import CONST_BACKEND

_EVIDENCE = ProbeEvidence(
    probe_date="2026-09-14",
    library_versions=(
        ("narwhals", "2.26.0"),
        ("polars", "1.44.2"),
        ("pandas", "3.0.5"),
        ("numpy", "2.5.3"),
        ("ibis-framework", "12.0.0"),
        ("pyarrow", "25.0.1"),
    ),
    fixtures=(
        "normal-mountainash-item228-consumer-smoke",
        "normal-mountainash-item228-lazy-object-smoke",
    ),
)

# The original public Narwhals map_batches probe rejected lazy Object storage.
# The native elementwise adapter now executes it, including composed aggregation.
# Do not retain an unsupported fact for a superseded lowering mechanism.
DECLARATIONS = tuple(
    CapabilityDeclaration(
        backend=backend,
        domain=Domain.VALUE,
        source=FactSource.MOUNTAINASH,
        facts=(),
        evidence=_EVIDENCE,
    )
    for backend in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS)
)
