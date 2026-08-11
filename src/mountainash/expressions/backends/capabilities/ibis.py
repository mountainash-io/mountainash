"""Import-safe Ibis expression-backend capability declarations (LITERAL_ONLY).

Migrated from ``mountainash.expressions.backends.expression_systems.ibis_capabilities``
(2026-08 capability-architecture PR). Extracted; the source file still
self-registers until Task 11 rewires the class bodies.
"""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


_IB_DT_MSG = "Ibis datetime offset operations require literal integer values"
_IB_STR_MSG = (
    "Ibis has no native equivalent; mountainash composes this operation "
    "from literal parameters — dynamic column parameters are unsupported"
)


_IBIS_DT_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=op, param=param, level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS, message=_IB_DT_MSG,
        workaround="Use a literal integer for the offset amount",
        since="2026-07-05",
        upstream_ref="IB-DT-01",
    )
    for op, param in [
        (FK_DT.ADD_YEARS, "years"), (FK_DT.ADD_MONTHS, "months"),
        (FK_DT.ADD_DAYS, "days"), (FK_DT.ADD_HOURS, "hours"),
        (FK_DT.ADD_MINUTES, "minutes"), (FK_DT.ADD_SECONDS, "seconds"),
        (FK_DT.ADD_MILLISECONDS, "milliseconds"),
        (FK_DT.ADD_MICROSECONDS, "microseconds"),
    ]
)


_IBIS_STR_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=op, param=param, level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS, message=_IB_STR_MSG,
        workaround="Use a literal value, or the polars backend",
        since="2026-07-05",
    )
    for op, param in [
        (FK_STR.CENTER, "length"),
        (FK_STR.REPLACE_SLICE, "start"), (FK_STR.REPLACE_SLICE, "length"),
    ]
) + tuple(
    # CENTER.character / REPLACE_SLICE.replacement are string-typed LITERAL_ONLY
    # params, probe-exempt for the same reason as trim/ltrim/rtrim below: with a
    # dynamic arg the native path does NOT raise — str(Expr) bakes the Python
    # repr of the unresolved backend expression into the output as a literal
    # (verified: 'a'.center(...) with a dynamic fill produced
    # "_['fill']_['fill']_['fill']_['fill']a" rather than raising). An
    # exception-based probe cannot detect this.
    CapabilityFact(
        operation_key=op, param=param, level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS, message=_IB_STR_MSG,
        workaround="Use a literal value, or the polars backend",
        since="2026-07-05",
        probe_exempt=(
            "dynamic arg silently miscompiles: str(Expr) bakes the unresolved "
            "expression's Python repr into the output as a literal string "
            "rather than raising — cannot be confirmed by an exception-based probe"
        ),
    )
    for op, param in [
        (FK_STR.CENTER, "character"), (FK_STR.REPLACE_SLICE, "replacement"),
    ]
) + tuple(
    # trim/ltrim/rtrim are probe-exempt: with a dynamic `characters` arg the
    # native path does NOT raise — the composition strips a char-class built
    # from str(Expr), a silent no-op that returns the input unchanged
    # (verified: ['xxhelloxx','yyworldyy'] in and out). An exception-based
    # probe cannot detect this.
    CapabilityFact(
        operation_key=op, param=param, level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS, message=_IB_STR_MSG,
        workaround="Use a literal value, or the polars backend",
        since="2026-07-05",
        probe_exempt=(
            "dynamic arg silently miscompiles via str(Expr) into a no-op "
            "char-class, returning the input unchanged rather than raising — "
            "cannot be confirmed by an exception-based probe"
        ),
    )
    for op, param in [
        (FK_STR.TRIM, "characters"), (FK_STR.LTRIM, "characters"),
        (FK_STR.RTRIM, "characters"),
    ]
)


IBIS_EXPR_CAPABILITIES: tuple[CapabilityFact, ...] = _IBIS_DT_FACTS + _IBIS_STR_FACTS


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)


_EVIDENCE = ProbeEvidence(
    probe_date="2026-07-05",
    library_versions=(),
    fixtures=(),
)


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH, facts=_IBIS_DT_FACTS,
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=_IBIS_STR_FACTS,
        evidence=_EVIDENCE,
    ),
)
