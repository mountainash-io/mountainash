"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ROUNDING

SEGMENT = CapabilitySegment(
    domain=Domain.ROUNDING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND, "*"),
            layer=InformationLayer.NATIVE,
            # Narwhals Expr.round has no rounding mode; no predicate can see
            # the operand dtype or values, so there is no gate.
            level=CapabilityLevel.EXPR_CAPABLE,
            message=(
                "Narwhals PyArrow rounds Decimal ties half away from zero "
                "(e.g. -2.345 -> -2.35), where Polars and pandas round half to "
                "even; Narwhals Expr.round has no rounding mode. No runtime "
                "refusal is applied."
            ),
            issue="NW-MATH-11",
            applicability=Applicability((Region((
                CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
                CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
            )),)),
        ),
    ),
)
