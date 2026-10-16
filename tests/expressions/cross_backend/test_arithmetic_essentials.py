"""Cross-backend tests for arithmetic essentials: abs, sqrt, sign, exp."""

import math
import pytest
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAbs:
    def test_abs_positive(self, backend_name, backend_factory, collect_expr):
        """abs() on positive values returns same values."""
        data = {"val": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = collect_expr(df, expr)
        assert actual == [1, 2, 3], f"[{backend_name}] got {actual}"

    def test_abs_negative(self, backend_name, backend_factory, collect_expr):
        """abs() on negative values returns positive values."""
        data = {"val": [-10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = collect_expr(df, expr)
        assert actual == [10, 5, 0, 3], f"[{backend_name}] got {actual}"

    def test_abs_floats(self, backend_name, backend_factory, collect_expr):
        """abs() on floats."""
        data = {"val": [-1.5, 2.5, -3.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = collect_expr(df, expr)
        for a, e in zip(actual, [1.5, 2.5, 3.0]):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSqrt:
    def test_sqrt(self, backend_name, backend_factory, collect_expr):
        """sqrt() on positive values."""
        data = {"val": [1.0, 4.0, 9.0, 16.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sqrt()
        actual = collect_expr(df, expr)
        for a, e in zip(actual, [1.0, 2.0, 3.0, 4.0]):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSign:
    def test_sign(self, backend_name, backend_factory, collect_expr):
        """sign() returns -1, 0, or 1."""
        data = {"val": [-10, 0, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sign()
        actual = collect_expr(df, expr)
        assert actual == [-1, 0, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExp:
    def test_exp(self, backend_name, backend_factory, collect_expr):
        """exp() computes e^x."""
        data = {"val": [0.0, 1.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").exp()
        actual = collect_expr(df, expr)
        for a, e in zip(actual, [1.0, math.e, math.e**2]):
            assert math.isclose(a, e, abs_tol=1e-6), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "operation,expected",
    [
        ("negate", ["2.345", "0", "-1.235", None]),
        ("abs", ["2.345", "0", "1.235", None]),
        ("sign", ["-1", "0", "1", None]),
        ("ceil", ["-2", "0", "2", None]),
        ("floor", ["-3", "0", "1", None]),
        ("round", ["-2.34", "0", "1.24", None]),
    ],
)
def test_declared_decimal_unary(
    backend_name, declared_decimal_frame, backend_factory, operation, expected
):
    """Each native operation reaches its own boundary, including signed rounding ties."""
    from decimal import Decimal as D
    import mountainash as ma
    import polars as pl
    from pyarrow import ArrowInvalid
    from fixtures.call_expectations import expect_call_failure
    from mountainash.core.types import BackendCapabilityError

    if backend_name == "ibis-sqlite":
        frame = backend_factory.create({"a": [1]}, backend_name)
        with pytest.raises(BackendCapabilityError, match="fixed-precision decimal"):
            ma.relation(frame).select(
                ma.col("a").cast(ma.DecimalDtype(12, 3), rounding="half_to_even")
            ).to_polars()
        return
    frame = declared_decimal_frame(
        {"a": [D("-2.345"), D("0.000"), D("1.235"), None]}, {"a": (12, 3)}
    )
    expression = ma.col("a").round(2) if operation == "round" else getattr(ma.col("a"), operation)()
    query = ma.relation(frame).select(expression.alias("r"))
    with expect_call_failure(
        when=backend_name == "ibis-polars" and operation in {"ceil", "floor"},
        reason="309: native Ibis-Polars Decimal ceil/floor Arrow precision conversion",
        errors=(ArrowInvalid,),
    ):
        out = query.to_polars()
    dtype = out.schema["r"]
    if backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"} and operation == "sign":
        assert dtype == pl.Int64
    else:
        assert dtype.is_decimal()
        assert dtype.scale == (2 if backend_name.startswith("ibis") and operation == "round" else 3)
        assert dtype.precision is None or dtype.precision >= dtype.scale + 1
    assert query.schema["r"] in (SchemaTypeStatus.UNKNOWN, ma.relation(out).schema["r"])
    with expect_call_failure(
        when=backend_name == "ibis-duckdb" and operation == "round",
        reason="244: DuckDB native round uses half-away-from-zero rather than half-even",
        errors=(AssertionError,),
    ):
        assert out["r"].to_list() == [D(x) if x is not None else None for x in expected]
 

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_decimal_rounding_integer_capacity_boundary(backend_name, declared_decimal_frame, backend_factory):
    """Native rounding retains the signed carry or reports fixed-width overflow."""
    from decimal import Decimal as D
    import mountainash as ma
    from mountainash.core.types import BackendCapabilityError
    from pyarrow import ArrowInvalid
    from mountainash.relations.schema_inference import SchemaTypeStatus

    if backend_name == "ibis-sqlite":
        frame = backend_factory.create({"a": [1]}, backend_name)
        with pytest.raises(BackendCapabilityError, match="fixed-precision decimal"):
            ma.relation(frame).select(
                ma.col("a").cast(ma.DecimalDtype(4, 3), rounding="half_to_even")
            ).to_polars()
        return

    frame = declared_decimal_frame(
        {"a": [D("9.995"), D("-9.995")]}, {"a": (4, 3)}
    )
    query = ma.relation(frame).select(ma.col("a").round(2).alias("r"))
    if backend_name in {"pandas", "narwhals-pandas"}:
        # Arrow preserves the input Decimal(4, 3), so the carry cannot fit.
        with pytest.raises(ArrowInvalid):
            query.to_polars()
        return
    out = query.to_polars()

    dtype = out.schema["r"]
    assert dtype.is_decimal()
    assert dtype.scale == (2 if backend_name.startswith("ibis") else 3)
    assert dtype.precision is None or dtype.precision >= dtype.scale + 2
    assert query.schema["r"] in (SchemaTypeStatus.UNKNOWN, ma.relation(out).schema["r"])
    assert out["r"].to_list() == [D("10.000"), D("-10.000")]
