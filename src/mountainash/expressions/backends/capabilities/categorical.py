"""Capability declarations for categorical casts."""
from __future__ import annotations

from dataclasses import replace
from mountainash.core.capabilities import CapabilityDeclaration, FactSource, Domain, ProbeEvidence
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT
from ._structural_common import unsupported, SINCE

_MSG = "This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior"

_FACTS = (
    unsupported(FK_CAT.CAST, CONST_BACKEND.IBIS, "ibis-sqlite", message=_MSG, option="value_type", value_type="integer"),
    unsupported(FK_CAT.CAST, CONST_BACKEND.NARWHALS, "narwhals-polars", message=_MSG, option="value_type", value_type="integer", failure_behavior="null"),
)
_FACTS = _FACTS + tuple(
    replace(f, dialect="narwhals-lazy")
    for f in _FACTS
    if f.backend is CONST_BACKEND.NARWHALS
)

_EVIDENCE = ProbeEvidence(probe_date=SINCE, library_versions=(), fixtures=("categorical-base-scalar",))
DECLARATIONS = tuple(
    CapabilityDeclaration(backend=backend, domain=Domain.CATEGORICAL, source=FactSource.MOUNTAINASH, facts=tuple(f for f in _FACTS if f.backend is backend), evidence=_EVIDENCE)
    for backend in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS)
)
