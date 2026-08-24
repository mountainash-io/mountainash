"""Capability declarations for recursive struct casts."""
from __future__ import annotations

from dataclasses import replace
from mountainash.core.capabilities import CapabilityDeclaration, FactSource, Domain, ProbeEvidence
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT
from ._structural_common import unsupported, SINCE

_MSG = "This backend cannot execute STRUCT.CAST for the requested failure behavior"

_FACTS = (
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.NARWHALS, "narwhals-pandas", message=_MSG, option="failure_behavior", failure_behavior="throw"),
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.IBIS, "ibis-sqlite", message=_MSG, option="failure_behavior", failure_behavior="throw"),
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.NARWHALS, "narwhals-polars", message=_MSG, option="failure_behavior", failure_behavior="null"),
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.NARWHALS, "narwhals-pandas", message=_MSG, option="failure_behavior", failure_behavior="null"),
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.IBIS, "ibis-duckdb", message=_MSG, option="failure_behavior", failure_behavior="null"),
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.IBIS, "ibis-polars", message=_MSG, option="failure_behavior", failure_behavior="null"),
    unsupported(FK_STRUCT.CAST, CONST_BACKEND.IBIS, "ibis-sqlite", message=_MSG, option="failure_behavior", failure_behavior="null"),
)

_FACTS = _FACTS + tuple(
    replace(f, dialect="narwhals-lazy")
    for f in _FACTS
    if f.backend is CONST_BACKEND.NARWHALS
)

_EVIDENCE = ProbeEvidence(probe_date=SINCE, library_versions=(), fixtures=("plain-struct", "recursive-struct"))
DECLARATIONS = tuple(
    CapabilityDeclaration(backend=backend, domain=Domain.STRUCT, source=FactSource.MOUNTAINASH, facts=tuple(f for f in _FACTS if f.backend is backend), evidence=_EVIDENCE)
    for backend in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS)
)
