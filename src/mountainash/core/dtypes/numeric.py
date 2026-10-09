"""Internal, backend-independent exact numeric representation and cast semantics."""
from __future__ import annotations

import re
from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    ROUND_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    Context,
    Decimal,
    DecimalException,
    InvalidOperation,
    Overflow,
    localcontext,
)
from typing import TYPE_CHECKING

from .canonical import DecimalDtype, MountainashDtype
from .errors import NumericConversionError

if TYPE_CHECKING:
    from .canonical import CanonicalDtype

_ROUNDING = {"TIE_TO_EVEN": ROUND_HALF_EVEN, "TIE_AWAY_FROM_ZERO": ROUND_HALF_UP}
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
_LEXICAL = frozenset({MountainashDtype.LEXICAL_INTEGER, MountainashDtype.LEXICAL_DECIMAL})
_INTEGER_RANGES = {
    MountainashDtype.I8: (-(2**7), 2**7 - 1),
    MountainashDtype.I16: (-(2**15), 2**15 - 1),
    MountainashDtype.I32: (-(2**31), 2**31 - 1),
    MountainashDtype.I64: (-(2**63), 2**63 - 1),
    MountainashDtype.U8: (0, 2**8 - 1),
    MountainashDtype.U16: (0, 2**16 - 1),
    MountainashDtype.U32: (0, 2**32 - 1),
    MountainashDtype.U64: (0, 2**64 - 1),
}
_FLOAT_MAX = {
    MountainashDtype.FP32: Decimal("3.4028234663852886e38"),
    MountainashDtype.FP64: Decimal("1.7976931348623157e308"),
}


def convert_numeric(
    value: object,
    dtype: CanonicalDtype,
    rounding: str = "TIE_TO_EVEN",
    failure_behavior: str = "throw",
    *,
    preserve: bool = False,
) -> Decimal | int | float | str | None:
    """Convert an original value exactly before bounded/native numeric lowering.

    Preserving construction rejects value changes; explicit casts round once.
    Configuration errors are never row-null failures. Backend capability checks
    belong outside this codec and must run even for empty/all-null inputs.
    """
    if rounding not in _ROUNDING:
        raise ValueError("Unknown numeric rounding policy")
    if failure_behavior not in ("throw", "null"):
        raise ValueError("Unknown numeric failure policy")
    if not isinstance(dtype, DecimalDtype) and dtype not in (
        _LEXICAL | frozenset(_INTEGER_RANGES) | frozenset(_FLOAT_MAX)
    ):
        raise ValueError("A numeric dtype or exact decimal descriptor is required")
    if value is None:
        return None
    try:
        number = _decimal_value(value)
        if isinstance(dtype, DecimalDtype):
            return _fixed_decimal(number, dtype, _ROUNDING[rounding], preserve)
        if dtype in _INTEGER_RANGES:
            lower, upper = _INTEGER_RANGES[dtype]
            if number != number.to_integral_value(rounding=ROUND_DOWN):
                raise NumericConversionError("A fractional value is not an integer")
            if number < lower or number > upper:
                raise NumericConversionError("Numeric value exceeds the bounded integer range")
            return int(number)
        if dtype in _FLOAT_MAX:
            if number.copy_abs() > _FLOAT_MAX[dtype]:
                raise NumericConversionError("Numeric value exceeds the bounded float range")
            converted = float(number)
            if not converted == converted or converted in (float("inf"), float("-inf")):
                raise NumericConversionError("Numeric value exceeds the bounded float range")
            return converted
        if dtype == MountainashDtype.LEXICAL_INTEGER:
            if number != number.to_integral_value(rounding=ROUND_DOWN):
                raise NumericConversionError("A fractional value is not an integer")
        if number.is_zero():
            return "0"
        text = format(number, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    except (NumericConversionError, DecimalException, OverflowError) as error:
        if failure_behavior == "null":
            return None
        if isinstance(error, NumericConversionError):
            raise
        raise NumericConversionError("Numeric value cannot be represented") from error


def convert_nested_numeric(value: object, fields: tuple[object, ...]) -> object:
    """Apply declared exact codecs to numeric leaves of a structured value."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise NumericConversionError("Structured numeric conversion requires a mapping")
    converted: dict[str, object] = {}
    for field in fields:
        name = field.name
        child = value.get(name)
        dtype = field.dtype
        if isinstance(dtype, DecimalDtype) or dtype in _LEXICAL:
            child = convert_numeric(child, dtype)
        object_fields = tuple(field.object_fields or ())
        if object_fields:
            child = convert_nested_numeric(child, object_fields)
        item_fields = tuple(field.item_object_fields or ())
        if item_fields and child is not None:
            if not isinstance(child, (list, tuple)):
                raise NumericConversionError("Structured numeric array conversion requires a sequence")
            child = [
                convert_nested_numeric(item, item_fields) if item is not None else None
                for item in child
            ]
        converted[name] = child
    return converted



def has_nested_numeric_fields(fields: tuple[object, ...]) -> bool:
    """Whether declared children require the exact numeric codec."""
    for field in fields:
        dtype = field.dtype
        if isinstance(dtype, DecimalDtype) or dtype in _LEXICAL:
            return True
        if has_nested_numeric_fields(tuple(field.object_fields or ())):
            return True
        if has_nested_numeric_fields(tuple(field.item_object_fields or ())):
            return True
    return False


def convert_nested_numeric_shape(value: object, shape: object) -> object:
    """Normalize declared numeric leaves using immutable recursive SourceShape evidence."""
    if value is None:
        return None
    dtype = shape.canonical_type
    if isinstance(dtype, DecimalDtype) or dtype in _LEXICAL:
        return convert_numeric(value, dtype)
    if dtype == MountainashDtype.STRUCT and shape.struct_fields:
        if not isinstance(value, dict):
            raise NumericConversionError("Structured numeric conversion requires a mapping")
        converted = dict(value)
        for name, child_shape in shape.struct_fields:
            if name in converted:
                converted[name] = convert_nested_numeric_shape(converted[name], child_shape)
        return converted
    if dtype == MountainashDtype.LIST and shape.item_shape is not None:
        if not isinstance(value, (list, tuple)):
            raise NumericConversionError("Structured numeric array conversion requires a sequence")
        return [
            convert_nested_numeric_shape(item, shape.item_shape) if item is not None else None
            for item in value
        ]
    return value

def _decimal_value(value: object) -> Decimal:
    if isinstance(value, bool):
        raise NumericConversionError("Boolean values are not numeric values")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        # Explicit float conversion means the stored binary value, not its repr.
        number = Decimal.from_float(value)
    elif isinstance(value, str):
        text = value.strip()
        if _NUMBER.fullmatch(text) is None:
            raise NumericConversionError("Invalid numeric text")
        number = Decimal(text)
    else:
        raise NumericConversionError("Unsupported numeric source value")
    if not number.is_finite():
        raise NumericConversionError("Nonfinite values are not exact numeric values")
    return number


def _fixed_decimal(number: Decimal, dtype: DecimalDtype, rounding: str, preserve: bool) -> Decimal:
    integer_digits = dtype.precision - dtype.scale
    # Reject enormous positive exponents without expanding them to text/digits.
    if not number.is_zero() and number.adjusted() >= integer_digits:
        raise NumericConversionError("Numeric value exceeds decimal precision")
    quantum = Decimal((0, (1,), -dtype.scale))
    with localcontext(Context(
        prec=dtype.precision + 1,
        rounding=rounding,
        Emin=MIN_EMIN,
        Emax=MAX_EMAX,
        traps=[InvalidOperation, Overflow],
    )):
        rounded = number.quantize(quantum)
    if not rounded.is_zero() and rounded.adjusted() >= integer_digits:
        raise NumericConversionError("Rounded value exceeds decimal precision")
    if preserve and rounded != number:
        raise NumericConversionError("Decimal representation would change the numeric value")
    return rounded
