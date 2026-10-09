"""Exact literal preparation shared by numeric cast dispatch and type resolution."""
from __future__ import annotations

from decimal import Decimal
import math
from typing import Any


def prepare_numeric_cast_literal(value: Any) -> Any:
    """Prepare exact Python numerics as text before backend literal construction."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return format(Decimal(value), "f")
    if isinstance(value, Decimal):
        # Retain exponent notation until the bounded target has checked magnitude.
        return str(value)
    if isinstance(value, float) and math.isfinite(value):
        return format(Decimal.from_float(value), "f")
    return value
