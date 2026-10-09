"""Disposable item-241 shape probe; not production implementation."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, model_validator

from .targets import TypeTarget
from .errors import DtypeMappingError


class NumericDtype(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    kind: Literal["decimal", "lexical_integer", "lexical_decimal"]
    precision: int | None = None
    scale: int | None = None

    @model_validator(mode="after")
    def parameters(self):
        if self.kind == "decimal":
            if self.precision is None or self.scale is None or not (1 <= self.precision <= 38 and 0 <= self.scale <= self.precision):
                raise ValueError("spike standard decimal requires 1 <= precision <= 38 and 0 <= scale <= precision; use lexical storage otherwise")
        elif self.precision is not None or self.scale is not None:
            raise ValueError("lexical numeric types have no precision or scale bound")
        return self

    @property
    def name(self):
        return self.kind.upper()

    @property
    def value(self):
        return self.kind


def DecimalDtype(precision: int, scale: int) -> NumericDtype:
    return NumericDtype(kind="decimal", precision=precision, scale=scale)


LEXICAL_INTEGER = NumericDtype(kind="lexical_integer")
LEXICAL_DECIMAL = NumericDtype(kind="lexical_decimal")
_NUMERIC = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def numeric_text(value, dtype: NumericDtype, rounding="TIE_TO_EVEN", failure_behavior="throw", preserve=False):
    """Exact shared codec; no binary float or context-limited normalization."""
    if value is None:
        return None
    try:
        text = str(value)
        if not _NUMERIC.fullmatch(text):
            raise ValueError(f"invalid numeric text: {text!r}")
        number = Decimal(text)
        if dtype.kind == "decimal":
            if number and number.adjusted() >= dtype.precision - dtype.scale:
                raise ValueError("decimal overflow")
            quantum = Decimal((0, (1,), -dtype.scale))
            if number and number.adjusted() < -dtype.scale - 1:
                rounded = Decimal((0, (0,), -dtype.scale))
            else:
                with localcontext() as ctx:
                    ctx.prec = max(len(number.as_tuple().digits), dtype.precision) + dtype.scale + 2
                    rounded = number.quantize(quantum, rounding=ROUND_HALF_EVEN if rounding == "TIE_TO_EVEN" else ROUND_HALF_UP)
            if preserve and rounded != number:
                raise ValueError("exact physicalisation would lose precision; declare a cast or use lexical storage")
            if rounded and rounded.adjusted() >= dtype.precision - dtype.scale:
                raise ValueError("decimal overflow after rounding")
            return format(rounded, "f")
        if dtype.kind == "lexical_integer":
            if number != number.to_integral_value():
                raise ValueError("non-integral value for lexical integer")
            result = format(number, "f").split(".", 1)[0]
        else:
            result = format(number, "f")
            if "." in result:
                result = result.rstrip("0").rstrip(".")
        return "0" if not number else result
    except (InvalidOperation, ValueError) as error:
        if failure_behavior == "null":
            return None
        raise ValueError(f"{dtype.kind} conversion failed for {value!r}: {error}") from error


def numeric_native(dtype: NumericDtype, target: TypeTarget):
    if target is TypeTarget.POLARS:
        import polars as pl
        return pl.Decimal(dtype.precision, dtype.scale) if dtype.kind == "decimal" else pl.String
    if target is TypeTarget.PYARROW:
        import pyarrow as pa
        return pa.decimal128(dtype.precision, dtype.scale) if dtype.kind == "decimal" else pa.string()
    if target is TypeTarget.IBIS:
        import ibis.expr.datatypes as dt
        return dt.Decimal(dtype.precision, dtype.scale) if dtype.kind == "decimal" else dt.string
    raise DtypeMappingError(f"disposable numeric spike does not implement target {target.value}")


def native_decimal(native, target):
    if target is TypeTarget.PYARROW:
        import pyarrow as pa
        if pa.types.is_decimal(native):
            return DecimalDtype(native.precision, native.scale)
    elif target is TypeTarget.POLARS:
        import polars as pl
        if isinstance(native, pl.Decimal) and native.precision is not None:
            return DecimalDtype(native.precision, native.scale)
    elif target is TypeTarget.IBIS:
        if getattr(native, "is_decimal", lambda: False)():
            return DecimalDtype(native.precision, native.scale)
    return None
