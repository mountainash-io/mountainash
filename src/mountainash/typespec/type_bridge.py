"""
Type bridge: Universal Type → MountainashDtype

Maps the 7 core UniversalType values to their canonical MountainashDtype
equivalents. Only the 7 types with a clear, unambiguous mapping are included.
Types like DURATION, YEAR, YEARMONTH, ARRAY, OBJECT, and ANY are not bridged
because they either have no direct MountainashDtype equivalent or require
additional context.
"""
from __future__ import annotations

from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.universal_types import UniversalType


UNIVERSAL_TO_MOUNTAINASH: dict[UniversalType, MountainashDtype] = {
    UniversalType.STRING: MountainashDtype.STRING,
    UniversalType.INTEGER: MountainashDtype.I64,
    UniversalType.NUMBER: MountainashDtype.FP64,
    UniversalType.BOOLEAN: MountainashDtype.BOOL,
    UniversalType.DATE: MountainashDtype.DATE,
    UniversalType.TIME: MountainashDtype.TIME,
    UniversalType.DATETIME: MountainashDtype.TIMESTAMP,
}


def bridge_type(universal_type: UniversalType) -> MountainashDtype:
    """
    Map a UniversalType to the corresponding MountainashDtype.

    Only the 7 core types are supported. Any type not in the mapping raises
    ValueError to make gaps explicit rather than silently producing wrong types.

    Args:
        universal_type: A UniversalType enum member to bridge.

    Returns:
        The corresponding MountainashDtype.

    Raises:
        ValueError: If universal_type has no mapping in UNIVERSAL_TO_MOUNTAINASH.

    Examples:
        >>> bridge_type(UniversalType.STRING)
        <MountainashDtype.STRING: 'string'>
        >>> bridge_type(UniversalType.INTEGER)
        <MountainashDtype.I64: 'i64'>
    """
    result = UNIVERSAL_TO_MOUNTAINASH.get(universal_type)
    if result is None:
        raise ValueError(
            f"No MountainashDtype mapping for UniversalType '{universal_type}'. "
            f"Supported types: {list(UNIVERSAL_TO_MOUNTAINASH)}"
        )
    return result


__all__ = [
    "UNIVERSAL_TO_MOUNTAINASH",
    "bridge_type",
]
