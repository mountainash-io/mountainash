import pytest
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_datetime import (
    MountainAshNarwhalsScalarDatetimeExpressionSystem,
)


def test_narwhals_iso_week_raises_capability_error_not_attribute_error():
    """The ISO_WEEK branch must raise BackendCapabilityError, not AttributeError."""
    import narwhals as nw

    system = MountainAshNarwhalsScalarDatetimeExpressionSystem()
    # component is POSITIONAL_ONLY -- passing it as a keyword raises TypeError
    # before the ISO_WEEK branch is reached.
    with pytest.raises(BackendCapabilityError):
        system.extract(nw.col("x"), "ISO_WEEK")
