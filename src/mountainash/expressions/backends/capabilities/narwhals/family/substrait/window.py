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
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW

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
        SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
        SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,
        SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE,
        SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE,
        SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE,
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
