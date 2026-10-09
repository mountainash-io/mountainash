"""Whole-domain guarantees, with independently specified classifications."""
import pytest

from mountainash.core.dtypes import DecimalDtype, MountainashDtype as D, classify_cast, is_safe_cast


def decimal(p, s):
    return DecimalDtype(precision=p, scale=s)


@pytest.mark.parametrize("source,target,expected", [
    (D.I64, D.I64, "safe"),
    (D.I32, D.I64, "safe"),
    (D.I64, D.I32, "narrowing"),
    (D.U8, D.I16, "safe"),
    (D.U8, D.I8, "narrowing"),
    (D.I8, D.U64, "narrowing"),
    (D.I16, D.FP32, "safe"),
    (D.I32, D.FP32, "lossy"),
    (D.U32, D.FP64, "safe"),
    (D.I64, D.FP64, "lossy"),
    (D.U64, D.FP64, "lossy"),
    (D.FP32, D.FP64, "safe"),
    (D.FP64, D.FP32, "lossy"),
    (D.FP64, D.I64, "lossy"),
    (D.TIMESTAMP, D.DATE, "lossy"),
    (D.DATE, D.TIMESTAMP, "unsafe"),
    (D.TIMESTAMP, D.STRING, "unsafe"),
    (D.FP64, D.STRING, "unsafe"),
    (D.STRING, D.I64, "unsafe"),
    (D.STRING, D.LEXICAL_INTEGER, "unsafe"),
    (D.LEXICAL_INTEGER, D.I64, "narrowing"),
    (D.LEXICAL_DECIMAL, D.I64, "narrowing"),
    (D.LEXICAL_INTEGER, D.LEXICAL_DECIMAL, "safe"),
    (D.LEXICAL_DECIMAL, D.LEXICAL_INTEGER, "narrowing"),
    (D.I64, D.LEXICAL_INTEGER, "safe"),
    (D.I64, D.LEXICAL_DECIMAL, "safe"),
    (decimal(5, 2), decimal(7, 3), "safe"),
    (decimal(5, 2), decimal(4, 2), "narrowing"),
    (decimal(5, 3), decimal(3, 2), "lossy"),
    (decimal(5, 2), decimal(5, 2), "safe"),
    (D.I8, decimal(3, 0), "safe"),
    (D.U8, decimal(2, 0), "narrowing"),
    (decimal(2, 0), D.I8, "safe"),
    (decimal(3, 0), D.I8, "narrowing"),
    (decimal(2, 1), D.I64, "lossy"),
    (decimal(20, 0), D.FP64, "lossy"),
    (decimal(5, 2), D.FP64, "lossy"),
    (D.FP64, decimal(38, 10), "lossy"),
    (decimal(5, 2), D.LEXICAL_DECIMAL, "safe"),
    (decimal(5, 0), D.LEXICAL_INTEGER, "safe"),
    (decimal(5, 2), D.LEXICAL_INTEGER, "narrowing"),
    (D.LEXICAL_INTEGER, decimal(38, 0), "narrowing"),
    (D.LEXICAL_DECIMAL, decimal(38, 10), "lossy"),
])
def test_whole_domain_classification(source, target, expected):
    assert classify_cast(source, target).value == expected
    assert is_safe_cast(source, target) is (expected == "safe")


@pytest.mark.parametrize("source,target", [(D.DECIMAL, D.DECIMAL), (D.DECIMAL, D.STRING), (D.I64, D.DECIMAL)])
def test_bare_decimal_cannot_claim_a_cast_guarantee(source, target):
    with pytest.raises(ValueError):
        classify_cast(source, target)
