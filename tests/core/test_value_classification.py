"""Observable scalar-domain boundaries for eager value classification."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from mountainash.core.value_classification import ValueKind, boolean_value, text_value, value_kind


class _HostileObject:
    def __bool__(self) -> bool:
        raise AssertionError("truthiness must not be inspected")

    def __eq__(self, other: object) -> bool:
        raise AssertionError("comparison must not be inspected")

    def __str__(self) -> str:
        raise AssertionError("string conversion must not be inspected")

    def __int__(self) -> int:
        raise AssertionError("integer conversion must not be inspected")

    def __float__(self) -> float:
        raise AssertionError("float conversion must not be inspected")


class _HostileInt(int):
    def __bool__(self) -> bool:
        raise AssertionError("truthiness must not be inspected")

    def __eq__(self, other: object) -> bool:
        raise AssertionError("comparison must not be inspected")

    def __str__(self) -> str:
        raise AssertionError("string conversion must not be inspected")

    def __int__(self) -> int:
        raise AssertionError("integer conversion must not be inspected")

    def __float__(self) -> float:
        raise AssertionError("float conversion must not be inspected")


class _HostileFloat(float):
    def __bool__(self) -> bool:
        raise AssertionError("truthiness must not be inspected")

    def __eq__(self, other: object) -> bool:
        raise AssertionError("comparison must not be inspected")

    def __str__(self) -> str:
        raise AssertionError("string conversion must not be inspected")

    def __int__(self) -> int:
        raise AssertionError("integer conversion must not be inspected")

    def __float__(self) -> float:
        raise AssertionError("float conversion must not be inspected")


class _HostileText(str):
    def __bool__(self) -> bool:
        raise AssertionError("truthiness must not be inspected")

    def __eq__(self, other: object) -> bool:
        raise AssertionError("comparison must not be inspected")

    def __str__(self) -> str:
        raise AssertionError("string conversion must not be inspected")

    def __int__(self) -> int:
        raise AssertionError("integer conversion must not be inspected")

    def __float__(self) -> float:
        raise AssertionError("float conversion must not be inspected")


def test_builtin_values_do_not_import_optional_backends() -> None:
    """The eager core path remains usable before any dataframe backend is loaded."""
    script = """
import builtins

blocked = {\"numpy\", \"pandas\", \"polars\", \"narwhals\", \"ibis\", \"pyarrow\"}
original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name.split(".", 1)[0] in blocked:
        raise AssertionError(f"unexpected optional import: {name}")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
from mountainash import boolean_value, text_value, value_kind
assert value_kind(True).value == \"boolean\"
assert boolean_value(1, source=\"binary_number\") is True
assert text_value(\"text\") == \"text\"
for module_name in ("numpy", "pandas.fake", None):
    fake_type = type("Fake", (), {"__module__": module_name})
    value = fake_type()
    assert value_kind(value).value == "unsupported"
    assert boolean_value(value) is None
    assert text_value(value) is None
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_public_export_discovery_includes_eager_and_lazy_symbols() -> None:
    import mountainash as ma

    assert set(ma.__all__) <= set(dir(ma))


@pytest.mark.parametrize(
    ("value", "expected_kind"),
    [
        (None, ValueKind.ABSENT),
        (True, ValueKind.BOOLEAN),
        (False, ValueKind.BOOLEAN),
        (0, ValueKind.INTEGER),
        (1, ValueKind.INTEGER),
        (1 << 200, ValueKind.INTEGER),
        (0.0, ValueKind.FLOAT),
        (-0.0, ValueKind.FLOAT),
        ("true", ValueKind.TEXT),
        ("false", ValueKind.TEXT),
        ("not-a-token", ValueKind.TEXT),
    ],
)
def test_builtin_scalar_classification(value: object, expected_kind: ValueKind) -> None:
    assert value_kind(value) is expected_kind


@pytest.mark.parametrize(
    ("value", "source", "expected"),
    [
        (True, "boolean", True),
        (False, "boolean", False),
        (True, "binary_number", None),
        (False, "finite_number", None),
        (0, "binary_number", False),
        (1, "binary_number", True),
        (1 << 200, "finite_number", True),
        (2, "binary_number", None),
        (2, "finite_number", True),
        (0.0, "binary_number", False),
        (-0.0, "finite_number", False),
        (1.0, "binary_number", True),
        (2.0, "binary_number", None),
        (2.0, "finite_number", True),
        (float("nan"), "finite_number", None),
        (float("inf"), "finite_number", None),
        (float("-inf"), "binary_number", None),
    ],
)
def test_boolean_candidate_domains_are_disjoint(value: object, source: str, expected: bool | None) -> None:
    assert boolean_value(value, source=source) is expected


def test_boolean_value_rejects_unknown_source_string() -> None:
    with pytest.raises(ValueError):
        boolean_value(1, source="number")


def test_boolean_value_rejects_non_exact_string_without_interaction() -> None:
    with pytest.raises(TypeError):
        boolean_value(1, source=_HostileText("boolean"))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        np.int8(-1),
        np.int16(-2),
        np.int32(-3),
        np.int64(-4),
        np.uint8(1),
        np.uint16(2),
        np.uint32(3),
        np.uint64((1 << 63) + 1),
    ],
)
def test_numpy_integer_scalars_preserve_integer_domain(value: object) -> None:
    assert value_kind(value) is ValueKind.INTEGER
    assert boolean_value(value, source="finite_number") is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (np.int64(0), False),
        (np.int64(1), True),
        (np.uint64(0), False),
        (np.uint64(1), True),
        (np.uint64((1 << 63) + 1), None),
    ],
)
def test_numpy_integer_binary_candidates_are_exact(value: object, expected: bool | None) -> None:
    assert boolean_value(value, source="binary_number") is expected


@pytest.mark.parametrize("value", [np.bool_(True), np.bool_(False)])
def test_numpy_booleans_are_not_numeric_candidates(value: object) -> None:
    assert value_kind(value) is ValueKind.BOOLEAN
    assert boolean_value(value, source="boolean") is bool(value)
    assert boolean_value(value, source="binary_number") is None
    assert boolean_value(value, source="finite_number") is None


@pytest.mark.parametrize("scalar_type", [np.float16, np.float32, np.float64, np.longdouble])
def test_numpy_float_binary_candidate_uses_its_own_precision(scalar_type: type[np.generic]) -> None:
    one = scalar_type(1)
    above_one = np.nextafter(one, scalar_type(2))

    assert value_kind(above_one) is ValueKind.FLOAT
    assert boolean_value(above_one, source="binary_number") is None
    assert boolean_value(above_one, source="finite_number") is True


@pytest.mark.parametrize("scalar_type", [np.float16, np.float32, np.float64, np.longdouble])
def test_numpy_nonfinite_floats_are_concrete_and_not_candidates(scalar_type: type[np.generic]) -> None:
    for value in (scalar_type(np.nan), scalar_type(np.inf), scalar_type(-np.inf)):
        assert value_kind(value) is ValueKind.FLOAT
        assert boolean_value(value, source="binary_number") is None
        assert boolean_value(value, source="finite_number") is None


def test_extended_precision_longdouble_never_narrows_before_admission() -> None:
    longdouble_info = np.finfo(np.longdouble)
    float64_info = np.finfo(np.float64)

    if longdouble_info.max > float64_info.max:
        finite_only_as_longdouble = np.longdouble(float64_info.max) * np.longdouble(2)
        assert np.isfinite(finite_only_as_longdouble)
        assert boolean_value(finite_only_as_longdouble, source="finite_number") is True
        assert boolean_value(finite_only_as_longdouble, source="binary_number") is None

    if longdouble_info.smallest_subnormal < float64_info.smallest_subnormal:
        finite_only_as_longdouble = np.nextafter(np.longdouble(0), np.longdouble(1))
        assert finite_only_as_longdouble != 0
        assert boolean_value(finite_only_as_longdouble, source="finite_number") is True
        assert boolean_value(finite_only_as_longdouble, source="binary_number") is None


@pytest.mark.parametrize(
    "value",
    [
        None,
        pd.NA,
        pd.NaT,
        np.datetime64("NaT", "ns"),
        np.timedelta64("NaT", "ns"),
    ],
)
def test_recognized_missing_scalars_are_absent(value: object) -> None:
    assert value_kind(value) is ValueKind.ABSENT
    assert boolean_value(value, source="boolean") is None
    assert text_value(value) is None


@pytest.mark.parametrize("value", [float("nan"), np.float64(np.nan)])
def test_direct_floating_nan_is_concrete_float_not_absence(value: object) -> None:
    assert value_kind(value) is ValueKind.FLOAT
    assert boolean_value(value, source="finite_number") is None
    assert text_value(value) is None


@pytest.mark.parametrize(
    "value",
    [
        date(2026, 9, 14),
        datetime(2026, 9, 14, 12, 0),
        np.datetime64("2026-09-14"),
        np.timedelta64(1, "D"),
    ],
)
def test_valid_temporal_scalars_are_unsupported_not_absent(value: object) -> None:
    assert value_kind(value) is ValueKind.UNSUPPORTED
    assert boolean_value(value, source="finite_number") is None
    assert text_value(value) is None


@pytest.mark.parametrize("value", [np.str_("true"), np.str_("false"), np.str_("not-a-token")])
def test_numpy_text_scalars_preserve_text_without_parsing(value: np.str_) -> None:
    assert value_kind(value) is ValueKind.TEXT
    assert text_value(value) == str(value)
    assert type(text_value(value)) is str
    assert boolean_value(value, source="boolean") is None


@pytest.mark.parametrize("value", [Decimal("1.5"), 1 + 2j, b"true", [True], {"true"}, object()])
def test_non_admitted_concrete_values_are_unsupported(value: object) -> None:
    assert value_kind(value) is ValueKind.UNSUPPORTED
    assert boolean_value(value, source="finite_number") is None
    assert text_value(value) is None


@pytest.mark.parametrize(
    "value",
    [_HostileObject(), _HostileInt(1), _HostileFloat(1.0), _HostileText("true")],
    ids=["hostile-object", "hostile-int", "hostile-float", "hostile-text"],
)
def test_hostile_objects_and_scalar_subclasses_are_rejected_without_interaction(value: object) -> None:
    assert value_kind(value) is ValueKind.UNSUPPORTED
    assert boolean_value(value, source="boolean") is None
    assert boolean_value(value, source="binary_number") is None
    assert boolean_value(value, source="finite_number") is None
    assert text_value(value) is None
