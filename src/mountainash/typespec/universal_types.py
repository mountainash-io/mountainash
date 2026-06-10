"""
Universal Type System for DataFrame Schema Transformations

Provides a centralized type mapping system based on Frictionless Table Schema
specification, enabling consistent type conversions across all supported
DataFrame backends (Polars, pandas, PyArrow, Ibis, Narwhals).

This module is the single source of truth for ALL type conversions in the
package. No other module should contain hardcoded type mappings.

Architecture:
- Universal types based on Frictionless Data standard
- Bidirectional mappings: Universal ↔ Backend-specific
- Python type mappings for dataclass/Pydantic extraction
- Safe cast detection to prevent data loss
"""
from __future__ import annotations

from enum import StrEnum
from typing import Optional, Tuple

from mountainash.core.dtypes import MountainashDtype
from mountainash.core.dtypes.errors import UnknownDtypeError



# ============================================================================
# Universal Type Enum (Based on Frictionless Table Schema)
# ============================================================================

class UniversalType(StrEnum):
    """
    Universal data types based on Frictionless Table Schema specification.

    These types provide a common vocabulary for describing data across all
    DataFrame backends and Python type systems.

    Reference: https://specs.frictionlessdata.io/table-schema/#types-and-formats
    """
    # Basic types
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"  # Floating point
    BOOLEAN = "boolean"

    # Temporal types
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DURATION = "duration"
    YEAR = "year"
    YEARMONTH = "yearmonth"

    # Complex types
    ARRAY = "array"
    OBJECT = "object"

    # Special
    ANY = "any"


# ============================================================================
# Boundary map: UniversalType (Frictionless) <-> MountainashDtype (canon)
# Complete in both directions by construction (gated by test_boundary_map +
# test_completeness). ANY <-> None means "no constraint".
# ============================================================================

UNIVERSAL_TO_CANONICAL: dict[UniversalType, Optional[MountainashDtype]] = {
    UniversalType.STRING: MountainashDtype.STRING,
    UniversalType.INTEGER: MountainashDtype.I64,
    UniversalType.NUMBER: MountainashDtype.FP64,
    UniversalType.BOOLEAN: MountainashDtype.BOOL,
    UniversalType.DATE: MountainashDtype.DATE,
    UniversalType.TIME: MountainashDtype.TIME,
    UniversalType.DATETIME: MountainashDtype.TIMESTAMP,
    UniversalType.DURATION: MountainashDtype.DURATION,
    UniversalType.YEAR: MountainashDtype.I32,        # semantic refinement of int
    UniversalType.YEARMONTH: MountainashDtype.STRING,  # "2024-01"
    UniversalType.ARRAY: MountainashDtype.LIST,
    UniversalType.OBJECT: MountainashDtype.STRUCT,
    UniversalType.ANY: None,                          # unconstrained
}

CANONICAL_TO_UNIVERSAL: dict[MountainashDtype, Tuple[UniversalType, Optional[str]]] = {
    MountainashDtype.BOOL: (UniversalType.BOOLEAN, None),
    MountainashDtype.I8: (UniversalType.INTEGER, None),
    MountainashDtype.I16: (UniversalType.INTEGER, None),
    MountainashDtype.I32: (UniversalType.INTEGER, None),
    MountainashDtype.I64: (UniversalType.INTEGER, None),
    MountainashDtype.U8: (UniversalType.INTEGER, None),
    MountainashDtype.U16: (UniversalType.INTEGER, None),
    MountainashDtype.U32: (UniversalType.INTEGER, None),
    MountainashDtype.U64: (UniversalType.INTEGER, None),
    MountainashDtype.FP32: (UniversalType.NUMBER, None),
    MountainashDtype.FP64: (UniversalType.NUMBER, None),
    MountainashDtype.STRING: (UniversalType.STRING, None),
    MountainashDtype.BINARY: (UniversalType.STRING, "binary"),  # Frictionless string format
    MountainashDtype.DATE: (UniversalType.DATE, None),
    MountainashDtype.TIME: (UniversalType.TIME, None),
    MountainashDtype.TIMESTAMP: (UniversalType.DATETIME, None),
    MountainashDtype.DURATION: (UniversalType.DURATION, None),
    MountainashDtype.LIST: (UniversalType.ARRAY, None),
    MountainashDtype.STRUCT: (UniversalType.OBJECT, None),
}


def to_canonical(universal: UniversalType) -> Optional[MountainashDtype]:
    """Map a Frictionless type to canon. None = unconstrained (ANY)."""
    return UNIVERSAL_TO_CANONICAL[universal]


def from_canonical(
    dtype: Optional[MountainashDtype],
) -> Tuple[UniversalType, Optional[str]]:
    """Map canon (or None = untyped) back to (UniversalType, format hint)."""
    if dtype is None:
        return (UniversalType.ANY, None)
    return CANONICAL_TO_UNIVERSAL[dtype]


def parse_universal(type_str: str) -> UniversalType:
    """Parse a Frictionless type string strictly. Raises on anything else."""
    try:
        return UniversalType(type_str)
    except ValueError:
        raise UnknownDtypeError(
            f"{type_str!r} is not a frictionless Table Schema type. "
            f"Valid: {sorted(t.value for t in UniversalType)}"
        ) from None


__all__ = [
    "UniversalType",
    "UNIVERSAL_TO_CANONICAL",
    "CANONICAL_TO_UNIVERSAL",
    "to_canonical",
    "from_canonical",
    "parse_universal",
]
