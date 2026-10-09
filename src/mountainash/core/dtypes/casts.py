"""Whole-domain cast guarantees; row-level success does not imply preservation."""
from __future__ import annotations

from enum import Enum

from .canonical import CanonicalDtype, DecimalDtype, MountainashDtype as D
from .numeric import _INTEGER_RANGES

_FLOAT_MANTISSAS = {D.FP32: 24, D.FP64: 53}
_LEXICAL = frozenset({D.LEXICAL_INTEGER, D.LEXICAL_DECIMAL})


class CastSafety(Enum):
    """Full-domain preservation, checked domain restriction, value loss, or no guarantee."""

    SAFE = "safe"
    NARROWING = "narrowing"
    LOSSY = "lossy"
    UNSAFE = "unsafe"


def _range_safety(source: tuple[int, int], target: tuple[int, int]) -> CastSafety:
    return (CastSafety.SAFE if target[0] <= source[0] and source[1] <= target[1]
            else CastSafety.NARROWING)


def classify_cast(from_type: CanonicalDtype, to_type: CanonicalDtype) -> CastSafety:
    """Classify actual → declared, with scale/value loss preceding range restriction.

    Lexical integer conversions are checked: fractional or out-of-range values
    fail rather than round. Arbitrary strings carry no numeric-domain evidence.
    Temporal parameters absent from the canonical vocabulary cannot prove safety.
    """
    if from_type is D.DECIMAL or to_type is D.DECIMAL:
        raise ValueError("Decimal cast safety requires precision and scale")
    if from_type == to_type:
        return CastSafety.SAFE

    source_range = _INTEGER_RANGES.get(from_type)
    target_range = _INTEGER_RANGES.get(to_type)
    source_decimal = isinstance(from_type, DecimalDtype)
    target_decimal = isinstance(to_type, DecimalDtype)

    if to_type in _LEXICAL:
        if source_range is not None:
            return CastSafety.SAFE
        if from_type in _LEXICAL:
            return CastSafety.SAFE if to_type is D.LEXICAL_DECIMAL else CastSafety.NARROWING
        if source_decimal:
            return (CastSafety.SAFE if to_type is D.LEXICAL_DECIMAL or from_type.scale == 0
                    else CastSafety.NARROWING)
        if from_type in _FLOAT_MANTISSAS:
            # Finite values have an exact lexical decimal representation;
            # nonfinite values (and fractional lexical integers) are rejected.
            return CastSafety.NARROWING
        return CastSafety.UNSAFE

    if from_type in _LEXICAL:
        if to_type is D.STRING:
            return CastSafety.SAFE
        if target_range is not None:
            return CastSafety.NARROWING
        if target_decimal:
            return (CastSafety.NARROWING if from_type is D.LEXICAL_INTEGER
                    else CastSafety.LOSSY)
        if to_type in _FLOAT_MANTISSAS:
            return CastSafety.LOSSY
        return CastSafety.UNSAFE

    if target_decimal:
        if source_decimal:
            if from_type.scale > to_type.scale:
                return CastSafety.LOSSY
            return (CastSafety.SAFE
                    if from_type.precision - from_type.scale <= to_type.precision - to_type.scale
                    else CastSafety.NARROWING)
        if source_range is not None:
            maximum = 10 ** (to_type.precision - to_type.scale) - 1
            return _range_safety(source_range, (-maximum, maximum))
        if from_type in _FLOAT_MANTISSAS:
            return CastSafety.LOSSY
        return CastSafety.UNSAFE

    if source_decimal:
        if to_type is D.STRING:
            return CastSafety.SAFE
        if target_range is not None:
            if from_type.scale:
                return CastSafety.LOSSY
            maximum = 10 ** from_type.precision - 1
            return _range_safety((-maximum, maximum), target_range)
        if to_type in _FLOAT_MANTISSAS:
            if from_type.scale or 10 ** from_type.precision - 1 > 2 ** _FLOAT_MANTISSAS[to_type]:
                return CastSafety.LOSSY
            return CastSafety.SAFE
        return CastSafety.UNSAFE

    if source_range is not None:
        if target_range is not None:
            return _range_safety(source_range, target_range)
        if to_type in _FLOAT_MANTISSAS:
            exact_limit = 2 ** _FLOAT_MANTISSAS[to_type]
            return (CastSafety.SAFE if -exact_limit <= source_range[0] and source_range[1] <= exact_limit
                    else CastSafety.LOSSY)
        if to_type is D.STRING:
            return CastSafety.SAFE

    if from_type in _FLOAT_MANTISSAS:
        if to_type in _FLOAT_MANTISSAS:
            return CastSafety.SAFE if from_type is D.FP32 else CastSafety.LOSSY
        if target_range is not None:
            return CastSafety.LOSSY
    if from_type is D.BOOL and target_range is not None:
        return CastSafety.SAFE
    if to_type is D.STRING and from_type in {D.BOOL, D.DATE}:
        return CastSafety.SAFE
    if from_type is D.TIMESTAMP and to_type is D.DATE:
        return CastSafety.LOSSY
    return CastSafety.UNSAFE


def is_safe_cast(from_type: CanonicalDtype, to_type: CanonicalDtype) -> bool:
    """Whether every source value survives the conversion exactly."""
    return classify_cast(from_type, to_type) is CastSafety.SAFE
