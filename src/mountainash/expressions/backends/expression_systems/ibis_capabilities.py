"""Import-safe Ibis capability declarations.

This module contains the dependency-free Ibis capability data so the
capability-spine bootstrap can load all 19 Ibis facts even when the optional
Ibis package is not installed.  The native Ibis implementation remains in
``ibis.base``; this is Finding A's import-safe declaration boundary.
"""

from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel, CapabilityRegistry
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


_IB_DT_MSG = "Ibis datetime offset operations require literal integer values"
_IB_STR_MSG = (
    "Ibis has no native equivalent; mountainash composes this operation "
    "from literal parameters — dynamic column parameters are unsupported"
)


IBIS_EXPR_CAPABILITIES: tuple[CapabilityFact, ...] = tuple(
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
) + tuple(
    CapabilityFact(
        operation_key=op, param=param, level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS, message=_IB_STR_MSG,
        workaround="Use a literal value, or the polars backend",
        since="2026-07-05",
    )
    for op, param in [
        (FK_STR.CENTER, "length"), (FK_STR.CENTER, "character"),
        (FK_STR.REPLACE_SLICE, "start"), (FK_STR.REPLACE_SLICE, "length"),
        (FK_STR.REPLACE_SLICE, "replacement"),
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


CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, IBIS_EXPR_CAPABILITIES)
