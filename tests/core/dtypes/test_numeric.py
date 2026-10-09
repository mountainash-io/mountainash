"""Exact scalar boundary cases not reachable after native inference has lost digits."""
from decimal import Decimal, localcontext

import pytest


def test_preserving_decimal_rejects_loss_but_allows_equivalent_scale():
    from mountainash.core.dtypes import DecimalDtype
    from mountainash.core.dtypes.numeric import convert_numeric
    from mountainash.core.dtypes.errors import NumericConversionError

    target = DecimalDtype(precision=5, scale=2)
    assert convert_numeric(Decimal("12.340"), target, preserve=True) == Decimal("12.34")
    with pytest.raises(NumericConversionError):
        convert_numeric(Decimal("12.345"), target, preserve=True)
    with pytest.raises(NumericConversionError):
        convert_numeric(True, target, preserve=True)


def test_lexical_codec_is_independent_of_decimal_context_and_integer_string_limit():
    from mountainash.core.dtypes import MountainashDtype as D
    from mountainash.core.dtypes.numeric import convert_numeric

    digits = "9" * 5000
    with localcontext() as context:
        context.prec = 6
        assert convert_numeric(Decimal(digits), D.LEXICAL_INTEGER) == digits
        assert convert_numeric(10**4999 + 1, D.LEXICAL_INTEGER) == "1" + "0" * 4998 + "1"
        assert convert_numeric(Decimal("12345678901234567890.0012300"), D.LEXICAL_DECIMAL) == "12345678901234567890.00123"
        assert context.prec == 6


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "1.5", "12x"])
def test_invalid_integral_domain_is_a_row_error(value):
    from mountainash.core.dtypes import MountainashDtype as D
    from mountainash.core.dtypes.numeric import convert_numeric
    from mountainash.core.dtypes.errors import NumericConversionError

    with pytest.raises(NumericConversionError):
        convert_numeric(value, D.LEXICAL_INTEGER)
    assert convert_numeric(value, D.LEXICAL_INTEGER, failure_behavior="null") is None


def test_extreme_exponents_do_not_expand_before_bounded_conversion():
    from mountainash.core.dtypes import DecimalDtype
    from mountainash.core.dtypes.numeric import convert_numeric
    from mountainash.core.dtypes.errors import NumericConversionError

    target = DecimalDtype(precision=5, scale=2)
    with pytest.raises(NumericConversionError):
        convert_numeric("1e100000000", target)
    assert convert_numeric("1e-100000000", target) == Decimal("0.00")
    with pytest.raises(NumericConversionError):
        convert_numeric("1e-100000000", target, preserve=True)


def test_explicit_rounding_does_not_inherit_callers_decimal_traps():
    from decimal import Inexact
    from mountainash.core.dtypes import DecimalDtype
    from mountainash.core.dtypes.numeric import convert_numeric

    target = DecimalDtype(precision=5, scale=2)
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        assert convert_numeric("12.345", target) == Decimal("12.34")
        assert context.prec == 2
        assert context.traps[Inexact]
@pytest.mark.parametrize(
    "kind,value,expected",
    [
        ("I8", "127", 127),
        ("I8", "-128", -128),
        ("U8", "255", 255),
        ("U8", "+00020", 20),
        ("I64", "9223372036854775807", 9223372036854775807),
        ("U64", "18446744073709551615", 18446744073709551615),
        ("FP32", "1.25", 1.25),
        ("FP64", "-1.25", -1.25),
    ],
)
def test_bounded_numeric_conversion_accepts_exact_in_domain_values(kind, value, expected):
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.core.dtypes.numeric import convert_numeric

    assert convert_numeric(value, getattr(MountainashDtype, kind)) == expected


@pytest.mark.parametrize(
    "kind,value",
    [
        ("I8", "128"),
        ("I8", "-129"),
        ("U8", "-1"),
        ("U8", "256"),
        ("I64", "9223372036854775808"),
        ("U64", "18446744073709551616"),
        ("I16", "1.5"),
        ("I32", "12x"),
        ("FP32", "3.5e38"),
        ("FP64", "Infinity"),
    ],
)
def test_bounded_numeric_conversion_rejects_fraction_junk_and_out_of_range(kind, value):
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.core.dtypes.errors import NumericConversionError
    from mountainash.core.dtypes.numeric import convert_numeric

    target = getattr(MountainashDtype, kind)
    with pytest.raises(NumericConversionError):
        convert_numeric(value, target)
    assert convert_numeric(value, target, failure_behavior="null") is None


def test_bounded_numeric_conversion_preserves_null_and_never_accepts_prefixes():
    from mountainash.core.dtypes import MountainashDtype as D
    from mountainash.core.dtypes.errors import NumericConversionError
    from mountainash.core.dtypes.numeric import convert_numeric

    assert convert_numeric(None, D.I32) is None
    with pytest.raises(NumericConversionError):
        convert_numeric("20junk", D.I32)
