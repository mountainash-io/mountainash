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


def convert_numeric(
    value: object,
    dtype: CanonicalDtype,
    rounding: str = "TIE_TO_EVEN",
    failure_behavior: str = "throw",
    *,
    preserve: bool = False,
) -> Decimal | str | None:
    """Convert an original value without an intermediate binary floating carrier.

    Preserving construction rejects value changes; explicit casts round once.
    Configuration errors are never row-null failures. Backend capability checks
    belong outside this codec and must run even for empty/all-null inputs.
    """
    if rounding not in _ROUNDING:
        raise ValueError("Unknown numeric rounding policy")
    if failure_behavior not in ("throw", "null"):
        raise ValueError("Unknown numeric failure policy")
    if not isinstance(dtype, DecimalDtype) and dtype not in _LEXICAL:
        raise ValueError("An exact decimal descriptor or lexical numeric target is required")
    if value is None:
        return None
    try:
        number = _decimal_value(value)
        if isinstance(dtype, DecimalDtype):
            return _fixed_decimal(number, dtype, _ROUNDING[rounding], preserve)
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
