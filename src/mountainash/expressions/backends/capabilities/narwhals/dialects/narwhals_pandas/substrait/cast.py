"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST


SEGMENT = CapabilitySegment(
    domain=Domain.CAST,
    changes=(),
    information=(
        CapabilityInformation(
            key=CapabilityKey(FKEY_SUBSTRAIT_CAST.CAST, "*"),
            layer=InformationLayer.NATIVE,
            # Casting works generally; the value-dependent exception below is
            # not an operation-wide refusal or an executable policy.
            level=CapabilityLevel.EXPR_CAPABLE,
            message=(
                "Backlog 252: integer casts (i8/i16/i32/i64/u8/u16/u32/u64) "
                "cannot preserve NaN-backed missing values in NumPy float64 pandas "
                "columns: native Narwhals selects non-nullable NumPy integers and "
                "raises IntCastingNaNError. Nullable Float64 and Arrow-backed float64 "
                "columns preserve ordinary nulls; finite integral and empty NumPy "
                "float64 inputs also work. Fractional, infinite and out-of-range "
                "values have separate native casting semantics. No automatic source "
                "normalization or runtime refusal is applied."
            ),
            applicability=Applicability((Region((
                CoordinateConstraint("package", "narwhals", specifier="==2.27.1"),
                CoordinateConstraint("package", "pandas", specifier="==3.0.6"),
            )),)),
        ),
    ),
)
