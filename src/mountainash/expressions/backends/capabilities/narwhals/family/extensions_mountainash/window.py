"""Narwhals window-order refusals shared by every Narwhals dialect."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.predicates import WINDOW_ROOT
from mountainash.core.capabilities.schema import (
    CapabilityLevel,
    Clause,
    ClauseOp,
    InformationLayer,
    Predicate,
)
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW

_MESSAGE = "Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported."
_KEYS = tuple(
    CapabilityKey(
        operation=operation,
        subject=WINDOW_ROOT,
        selector=Selector(kind="predicate", value=Predicate(clauses=(
            Clause(path=f"{WINDOW_ROOT}.any_descending", op=ClauseOp.EQ, operand=True),
        ))),
    )
    for operation in (
        FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
        FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
        FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
        FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
        FKEY_MOUNTAINASH_WINDOW.CUM_PROD,
        FKEY_MOUNTAINASH_WINDOW.DIFF,
        FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL,
        FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL,
    )
)

SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    changes=(),
    information=tuple(
        CapabilityInformation(
            key=key,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            applicability=unbounded,
        )
        for key in _KEYS
    ),
)
