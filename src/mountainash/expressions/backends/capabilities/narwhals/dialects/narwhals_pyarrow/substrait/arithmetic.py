"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilitySegment, Domain, Selector,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                "overflow",
                Selector(kind="exact", value="SILENT"),
            ),
            layer=InformationLayer.NATIVE,
            # Only the signed-minimum % -1 operand pair diverges; no predicate
            # can see operand values, so there is no gate (backlog 428).
            level=CapabilityLevel.EXPR_CAPABLE,
            message=(
                "Narwhals PyArrow integer modulus raises ArrowInvalid for the signed "
                "minimum % -1 (e.g. int8 -128 % -1) where Polars and pandas wrap; "
                "all other operands behave as native wrapping. No runtime refusal is applied."
            ),
            issue="NW-MATH-12",
            applicability=Applicability((Region((
                CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
                CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
            )),)),
        ),
    ),
)
