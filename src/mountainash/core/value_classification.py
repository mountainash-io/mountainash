"""Eager, domain-safe scalar classification and projections."""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
import math
import sys
from typing import Any, cast

from mountainash.core.lazy_imports import import_numpy


class ValueKind(str, Enum):
    """The admitted scalar representation of an eager input value."""

    ABSENT = "absent"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    TEXT = "text"
    UNSUPPORTED = "unsupported"


_BOOLEAN_SOURCES = frozenset({"boolean", "binary_number", "finite_number"})


def value_kind(value: object) -> ValueKind:
    """Classify a scalar without coercing or inspecting arbitrary objects."""
    value_type = type(value)

    if value is None:
        return ValueKind.ABSENT
    if value_type is bool:
        return ValueKind.BOOLEAN
    if value_type is int:
        return ValueKind.INTEGER
    if value_type is float:
        return ValueKind.FLOAT
    if value_type is str:
        return ValueKind.TEXT

    if type(value_type) is not type:
        return ValueKind.UNSUPPORTED
    numpy = sys.modules.get("numpy")
    if numpy is not None:
        kind = _numpy_value_kind(value, value_type, numpy)
        if kind is not ValueKind.UNSUPPORTED:
            return kind
    pandas = sys.modules.get("pandas")
    if pandas is not None and (value is pandas.NA or value is pandas.NaT):
        return ValueKind.ABSENT
    return ValueKind.UNSUPPORTED


def boolean_value(
    value: object,
    *,
    source: str = "boolean",
) -> bool | None:
    """Project one explicitly selected Boolean-producing scalar domain."""
    _validate_boolean_source(source)
    kind = value_kind(value)

    if source == "boolean":
        if kind is ValueKind.BOOLEAN:
            return bool(value)
        return None

    if kind is ValueKind.INTEGER:
        if source == "binary_number":
            if value == 0:
                return False
            if value == 1:
                return True
            return None
        return bool(value != 0)

    if kind is not ValueKind.FLOAT or not _is_finite_float(value):
        return None

    if source == "binary_number":
        if value == 0:
            return False
        if value == 1:
            return True
        return None
    return bool(value != 0)


def text_value(value: object) -> str | None:
    """Return actual text without stringifying a different scalar domain."""
    if value_kind(value) is not ValueKind.TEXT:
        return None
    value_type = type(value)
    if value_type is str:
        return cast(str, value)
    return str(value)


def _validate_boolean_source(source: str) -> None:
    source_type = type(source)
    if source_type is not str:
        raise TypeError("source must be one of 'boolean', 'binary_number', or 'finite_number'")
    if source not in _BOOLEAN_SOURCES:
        raise ValueError(f"Unknown Boolean value source: {source!r}")


def _numpy_value_kind(value: object, value_type: type[object], np: Any) -> ValueKind:
    if value_type in _numpy_temporal_types(np):
        if np.isnat(value):
            return ValueKind.ABSENT
        return ValueKind.UNSUPPORTED
    if value_type is np.bool_:
        return ValueKind.BOOLEAN
    if value_type in _numpy_integer_types(np):
        return ValueKind.INTEGER
    if value_type in _numpy_float_types(np):
        return ValueKind.FLOAT
    if value_type is np.str_:
        return ValueKind.TEXT
    return ValueKind.UNSUPPORTED


def _is_finite_float(value: object) -> bool:
    value_type = type(value)
    if value_type is float:
        return math.isfinite(cast(float, value))
    return bool(import_numpy().isfinite(value))


@lru_cache(maxsize=1)
def _numpy_temporal_types(np: Any) -> frozenset[type[object]]:
    return frozenset({np.datetime64, np.timedelta64})


@lru_cache(maxsize=1)
def _numpy_integer_types(np: Any) -> frozenset[type[object]]:
    return frozenset(
        {
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.longlong,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
            np.ulonglong,
            np.intp,
            np.uintp,
        }
    )


@lru_cache(maxsize=1)
def _numpy_float_types(np: Any) -> frozenset[type[object]]:
    return frozenset({np.float16, np.float32, np.float64, np.longdouble})
