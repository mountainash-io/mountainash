"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_AGGREGATE

SEGMENT = CapabilitySegment(
    domain=Domain.AGGREGATE,
    information=(
        CapabilityInformation(
            key=CapabilityKey(FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE, "*"),
            layer=InformationLayer.NATIVE,
            # Global aggregation works; only grouped execution of a
            # non-elementary measure is refused, and no predicate can see
            # grouped-ness or measure shape, so there is no gate.
            level=CapabilityLevel.EXPR_CAPABLE,
            message=(
                "Narwhals PyArrow group_by().agg() raises ValueError ('Non-trivial "
                "complex aggregation found') for complex aggregations such as "
                "mode() and aggregates over a composed expression like "
                "(lit + x).sum(); the same expressions compute in a global select. "
                "No runtime refusal is applied."
            ),
            issue="NW-AGG-04",
            applicability=Applicability((Region((
                CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
                CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
            )),)),
        ),
    ),
)
