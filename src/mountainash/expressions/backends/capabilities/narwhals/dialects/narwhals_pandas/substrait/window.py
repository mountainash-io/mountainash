"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW

_FLOAT_RANK_MESSAGE = (
    "Backlog 367: pandas `rank` returns float64, so row_number/rank/dense_rank "
    "values are floats (1.0, 2.0, ...) on NumPy-backed pandas; the values match "
    "other backends. No integer cast is applied: null sort keys rank as NaN, "
    "which NumPy integers cannot hold (see 252)."
)

_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier="==2.27.1"),
    CoordinateConstraint("package", "pandas", specifier="==3.0.6"),
)),))


SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    changes=(),
    information=tuple(
        CapabilityInformation(
            key=CapabilityKey(function_key, "*"),
            layer=InformationLayer.NATIVE,
            # Ranking works; only the result dtype differs. Not a refusal or policy.
            level=CapabilityLevel.EXPR_CAPABLE,
            message=_FLOAT_RANK_MESSAGE,
            applicability=_APPLICABILITY,
        )
        for function_key in (
            SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
            SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
            SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
        )
    ),
)
