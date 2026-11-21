"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    information=(
        CapabilityInformation(
            key=CapabilityKey(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO, "*"),
            layer=InformationLayer.NATIVE,
            # Only a Decimal divisor with an integer-literal dividend diverges;
            # no predicate can see operand dtype, so there is no gate.
            level=CapabilityLevel.EXPR_CAPABLE,
            message=(
                "Narwhals PyArrow reflected remainder of an integer literal by a "
                "Decimal column (e.g. 2 % decimal_col) raises ArrowInvalid because "
                "the intermediate Decimal precision exceeds Arrow's 38-digit "
                "maximum. No runtime refusal is applied."
            ),
            issue="NW-MATH-13",
            applicability=Applicability((Region((
                CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
                CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
            )),)),
        ),
    ),
)
