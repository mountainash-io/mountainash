"""Core polymorphic declarations — LIST-wrapper literal marker semantics
shared by every family (arguments-vs-options.md §Polymorphic Parameters).
Migrated from mountainash.core.capabilities.core_facts (2026-08 capability-architecture PR).
"""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_SET as FK_SET,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_TERN,
)

_MSG = (
    "literal collections unwrap to raw values; "
    "expressions compile through (LIST-wrapper marker)"
)


def _fact(op, param, family):
    return CapabilityFact(
        operation_key=op, param=param,
        level=CapabilityLevel.POLYMORPHIC, backend=family,
        message=_MSG, since="2026-07-05",
        probe_exempt="polymorphic — both paths supported by design",
    )


_FAMILIES = (CONST_BACKEND.POLARS, CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS)

from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
)

DECLARATIONS = tuple(
    CapabilityDeclaration(
        backend=family, domain=Domain.SET, source=FactSource.MOUNTAINASH,
        facts=(
            _fact(FK_SET.IS_IN, "haystack", family),
            _fact(FK_SET.IS_NOT_IN, "haystack", family),
        ),
    )
    for family in _FAMILIES
) + tuple(
    CapabilityDeclaration(
        backend=family, domain=Domain.TERNARY, source=FactSource.MOUNTAINASH,
        facts=(_fact(FK_TERN.COLLECT_VALUES, "*", family),),
    )
    for family in _FAMILIES
)
