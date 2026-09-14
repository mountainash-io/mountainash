"""Original-domain projections across exact native representations."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from sqlite3 import ProgrammingError

import ibis
import narwhals as nw
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.expressions.core.expression_api import BooleanExpressionAPI
from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode
from tests.fixtures.backend_registry import ALL_BACKENDS, create_ibis_sqlite_table

_ARROW_TYPES = {
    "boolean": pa.bool_(), "integer": pa.int64(), "float": pa.float64(),
    "text": pa.string(), "date": pa.date32(), "binary": pa.binary(),
    "decimal": pa.decimal128(20, 2),
}
_POLARS_TYPES = {
    "boolean": pl.Boolean, "integer": pl.Int64, "float": pl.Float64,
    "text": pl.String, "date": pl.Date, "binary": pl.Binary,
    "decimal": pl.Decimal(20, 2), "object": pl.Object,
}
_PANDAS_TYPES = {
    "boolean": "boolean", "integer": "Int64", "float": "Float64",
    "text": "string", "object": object,
}


def _frame(backend, kind, values, *, index=None):
    if backend in ("pandas", "narwhals-pandas"):
        dtype = _PANDAS_TYPES.get(kind)
        if dtype is None:
            dtype = pd.ArrowDtype(_ARROW_TYPES[kind])
        frame = pd.DataFrame({"x": pd.Series(values, dtype=dtype, index=index)})
        return frame if backend == "pandas" else nw.from_native(frame)
    frame = pl.DataFrame({"x": pl.Series("x", values, dtype=_POLARS_TYPES[kind])})
    if backend == "polars":
        return frame
    if backend == "polars-lazy":
        return frame.lazy()
    if backend == "narwhals-polars":
        return nw.from_native(frame)
    if backend == "narwhals-lazy":
        return nw.from_native(frame.lazy())
    table = pa.table({"x": pa.array(values, type=_ARROW_TYPES[kind])})
    if backend == "ibis-polars":
        return ibis.polars.connect().create_table("value_input", frame, overwrite=True)
    if backend == "ibis-duckdb":
        return ibis.duckdb.connect().create_table("value_input", table, overwrite=True)
    if backend == "ibis-sqlite":
        return create_ibis_sqlite_table(ibis.sqlite.connect(":memory:"), "value_input", table)
    raise AssertionError(f"unhandled backend {backend}")


def _project(frame, expression):
    compiled = expression.compile(frame)
    if isinstance(frame, ibis.expr.types.Table):
        output = frame.select(compiled.name("result")).to_pyarrow()["result"]
        return output.to_pylist(), str(output.type)
    selected = nw.from_native(frame) if isinstance(frame, pd.DataFrame) else frame
    output = selected.select(compiled.alias("result"))
    if isinstance(output, (pl.LazyFrame, nw.LazyFrame)):
        output = output.collect()
    series = output["result"]
    values = series.to_list()
    return [None if value is pd.NA else value for value in values], str(series.dtype)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "kind,values,boolean,binary,finite,text",
    [
        ("boolean", [True, False, None], [True, False, None],
         [None]*3, [None]*3, [None]*3),
        ("integer", [0, 1, -(2**62), None], [None]*4,
         [False, True, None, None], [False, True, True, None], [None]*4),
        ("float", [-0.0, 1.0, 2.5, float("inf"), float("-inf"), None],
         [None]*6, [False, True, None, None, None, None],
         [False, True, True, None, None, None], [None]*6),
        ("text", ["true", "0", "2", None], [None]*4, [None]*4,
         [None]*4, ["true", "0", "2", None]),
    ],
)
def test_typed_original_domains(backend_name, kind, values, boolean, binary, finite, text):
    frame = _frame(backend_name, kind, values)
    operand = ma.col("x")
    assert _project(frame, operand.value_kind())[0] == [
        "absent" if value is None else kind for value in values
    ]
    for source, expected in (
        ("boolean", boolean), ("binary_number", binary), ("finite_number", finite),
    ):
        actual, dtype = _project(frame, operand.boolean_value(source=source))
        assert actual == expected
        assert "bool" in dtype.lower()
    actual, dtype = _project(frame, operand.text_value())
    assert actual == text
    assert "str" in dtype.lower()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_declared_literal_dtype_controls_native_value_kind(backend_name):
    frame = _frame(backend_name, "boolean", [True])
    floating = BooleanExpressionAPI(LiteralNode(value=1, dtype=D.FP64))
    absent = BooleanExpressionAPI(LiteralNode(value=None, dtype=D.BOOL))

    assert _project(frame, floating.value_kind())[0] == ["float"]
    assert _project(frame, absent.value_kind())[0] == ["absent"]
    values, dtype = _project(frame, absent.boolean_value())
    assert values == [None]
    assert "bool" in dtype.lower()


@pytest.mark.parametrize(
    "backend_name,kind,value",
    [
        pytest.param(
            backend, kind, value,
            marks=(
                pytest.mark.xfail(
                    strict=True, raises=ProgrammingError,
                    reason="SQLite cannot bind Decimal to decimal128(20,2) during input construction",
                )
                if backend == "ibis-sqlite" and kind == "decimal" else ()
            ),
        )
        for backend in ALL_BACKENDS
        for kind, value in (
            ("date", date(2024, 1, 2)), ("binary", b"x"), ("decimal", Decimal("1.00")),
        )
    ],
)
def test_unsupported_typed_values_preserve_native_absence(backend_name, kind, value):
    # Decimal is deliberately not included in the admitted numeric domain.
    frame = _frame(backend_name, kind, [value, None])
    assert _project(frame, ma.col("x").value_kind())[0] == ["unsupported", "absent"]
    for source in ("boolean", "binary_number", "finite_number"):
        values, dtype = _project(frame, ma.col("x").boolean_value(source=source))
        assert values == [None, None]
        assert "bool" in dtype.lower()
    values, dtype = _project(frame, ma.col("x").text_value())
    assert values == [None, None]
    assert "str" in dtype.lower()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("values", [[], [None, None]], ids=["empty", "all-null"])
def test_empty_and_all_null_projections_preserve_column_shape(backend_name, values):
    frame = _frame(backend_name, "boolean", values)
    assert _project(frame, ma.col("x").value_kind())[0] == ["absent"] * len(values)
    for expression in (ma.col("x").text_value(), ma.col("x").boolean_value(source="finite_number")):
        assert _project(frame, expression)[0] == values


class _Hostile:
    def _fail(self, *args, **kwargs):
        raise AssertionError("arbitrary object hooks must not run")

    __bool__ = __eq__ = __ne__ = __str__ = __float__ = __int__ = __iter__ = _fail


# SQL cannot represent arbitrary Python objects. All eager/lazy Polars routes and
# native Pandas with its explicit wrapper preserve the original scalar domains.
@pytest.mark.parametrize("backend_name", [
    "polars", "polars-lazy", "pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy",
])
def test_mixed_object_projection_preserves_identity_and_hostile_objects(backend_name):
    values = [True, np.bool_(False), 1, 2**100, "true", None, float("nan"), _Hostile()]
    pandas_storage = backend_name in ("pandas", "narwhals-pandas")
    frame = _frame(backend_name, "object", values, index=[9, 2, 9, -1, 4, 4, 8, 8])
    assert _project(frame, ma.col("x").value_kind())[0] == [
        "boolean", "boolean", "integer", "integer", "text", "absent",
        "absent" if pandas_storage else "float", "unsupported",
    ]
    for source, expected in [
        ("boolean", [True, False, None, None, None, None, None, None]),
        ("binary_number", [None, None, True, None, None, None, None, None]),
        ("finite_number", [None, None, True, True, None, None, None, None]),
    ]:
        assert _project(frame, ma.col("x").boolean_value(source=source))[0] == expected
    assert _project(frame, ma.col("x").text_value())[0] == [
        None, None, None, None, "true", None, None, None,
    ]
    if pandas_storage:
        native = frame if isinstance(frame, pd.DataFrame) else frame.to_native()
        wrapped = nw.from_native(native)
        result = wrapped.select(ma.col("x").boolean_value().compile(native).alias("result"))
        assert result.to_native().index.equals(native.index)


# These representations belong specifically to Pandas, exercised both directly
# and through Narwhals; SQL/Polars have different native validity contracts.
@pytest.mark.parametrize("wrapped", [False, True], ids=["pandas", "narwhals-pandas"])
@pytest.mark.parametrize("storage", ["numpy", "nullable", "arrow"])
def test_pandas_float_validity_distinguishes_concrete_nan(wrapped, storage):
    if storage == "numpy":
        array = np.array([float("nan"), 0.0, 1.0, float("nan")])
        expected_kinds = ["absent", "float", "float", "absent"]
    elif storage == "nullable":
        array = pd.arrays.FloatingArray(
            np.array([float("nan"), 0.0, 1.0, float("nan")]),
            np.array([False, False, False, True]),
        )
        expected_kinds = ["float", "float", "float", "absent"]
    else:
        array = pd.array(
            pa.array([float("nan"), 0.0, 1.0, None], type=pa.float64()),
            dtype=pd.ArrowDtype(pa.float64()),
        )
        expected_kinds = ["float", "float", "float", "absent"]
    native = pd.DataFrame({"x": pd.Series(array, index=[4, 4, -1, 4])})
    frame = nw.from_native(native) if wrapped else native
    assert _project(frame, ma.col("x").value_kind())[0] == expected_kinds
    for source in ("binary_number", "finite_number"):
        values, dtype = _project(frame, ma.col("x").boolean_value(source=source))
        assert values == [None, False, True, None]
        assert "bool" in dtype.lower()
    assert _project(frame, ma.col("x").text_value())[0] == [None] * 4


# SQLite alone permits these heterogeneous storage classes in one SQL column.
@pytest.mark.parametrize("first", [b"binary", None], ids=["blob-first", "null-first"])
def test_sqlite_dynamic_storage_does_not_trust_first_row_schema(first):
    connection = ibis.sqlite.connect(":memory:")
    connection.con.execute("CREATE TABLE mixed_value (x)")
    connection.con.executemany(
        "INSERT INTO mixed_value VALUES (?)",
        [(value,) for value in [first, 0, 1, 2.5, "text", None]],
    )
    frame = connection.table("mixed_value")
    expected_first = "absent" if first is None else "unsupported"
    assert _project(frame, ma.col("x").value_kind())[0] == [
        expected_first, "integer", "integer", "float", "text", "absent",
    ]
    assert _project(frame, ma.col("x").boolean_value(source="binary_number"))[0] == [
        None, False, True, None, None, None,
    ]
    assert _project(frame, ma.col("x").boolean_value(source="finite_number"))[0] == [
        None, False, True, True, None, None,
    ]
    assert _project(frame, ma.col("x").text_value())[0] == [
        None, None, None, None, "text", None,
    ]
