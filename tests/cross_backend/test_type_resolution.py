"""Cross-backend tests for type resolution.

Validates that the dtype system correctly resolves different type specifiers
(canonical strings, aliases, native types, Python types, enum members)
across all backends.
"""

import pytest
import mountainash.expressions as ma
from mountainash.core.dtypes import MountainashDtype


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

INT_CASTABLE_TYPES = [
    ("i8", [1, 2, 3]),
    ("i16", [1, 2, 3]),
    ("i32", [1, 2, 3]),
    ("i64", [1, 2, 3]),
    ("u8", [1, 2, 3]),
    ("u16", [1, 2, 3]),
    ("u32", [1, 2, 3]),
    ("u64", [1, 2, 3]),
    ("fp32", [1, 2, 3]),
    ("fp64", [1, 2, 3]),
    ("bool", [0, 1, 0]),
    ("string", [1, 2, 3]),
]


@pytest.mark.cross_backend
class TestCanonicalTypeStrings:
    """Every tier-1 canonical string works on every backend."""

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize("dtype,input_data", INT_CASTABLE_TYPES,
                             ids=[t[0] for t in INT_CASTABLE_TYPES])
    def test_canonical_type_accepted(self, backend_name, backend_factory, collect_expr, dtype, input_data):
        data = {"value": input_data}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(dtype)
        values = collect_expr(df, expr)
        assert len(values) == len(input_data), (
            f"[{backend_name}] cast to {dtype!r}: expected {len(input_data)} values, got {len(values)}"
        )


@pytest.mark.cross_backend
class TestTypeAliases:
    """Common aliases resolve to the same result as their canonical form."""

    ALIAS_PAIRS = [
        ("boolean", "bool"),
        ("int64", "i64"),
        ("int32", "i32"),
        ("float64", "fp64"),
        ("float32", "fp32"),
        ("Int64", "i64"),
        ("Float64", "fp64"),
        ("Utf8", "string"),
        ("String", "string"),
        ("Boolean", "bool"),
        ("Datetime", "timestamp"),
        ("f64", "fp64"),
        ("f32", "fp32"),
        ("UInt32", "u32"),
        ("uint16", "u16"),
    ]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize("alias,canonical", ALIAS_PAIRS,
                             ids=[f"{a}->{c}" for a, c in ALIAS_PAIRS])
    def test_alias_produces_same_result_as_canonical(
        self, backend_name, backend_factory, collect_expr, alias, canonical
    ):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr_alias = ma.col("value").cast(alias)
        expr_canonical = ma.col("value").cast(canonical)
        values_alias = collect_expr(df, expr_alias)
        values_canonical = collect_expr(df, expr_canonical)
        assert values_alias == values_canonical, (
            f"[{backend_name}] alias {alias!r} produced {values_alias}, "
            f"canonical {canonical!r} produced {values_canonical}"
        )


@pytest.mark.cross_backend
class TestNativeTypesOwnBackend:
    """Native backend types work when passed to their own backend."""

    def test_polars_native_on_polars(self, backend_factory, collect_expr):
        import polars as pl
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "polars")
        expr = ma.col("value").cast(pl.Int64)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]

    def test_polars_utf8_on_polars(self, backend_factory, collect_expr):
        import polars as pl
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "polars")
        expr = ma.col("value").cast(pl.Utf8)
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3"]

    def test_narwhals_native_on_narwhals(self, backend_factory, collect_expr):
        import narwhals as nw
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "narwhals")
        expr = ma.col("value").cast(nw.Int64)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]

    def test_narwhals_string_on_narwhals(self, backend_factory, collect_expr):
        import narwhals as nw
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "narwhals")
        expr = ma.col("value").cast(nw.String)
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3"]

    def test_ibis_native_on_ibis_duckdb(self, backend_factory, collect_expr):
        import ibis.expr.datatypes as dt
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "ibis-duckdb")
        expr = ma.col("value").cast(dt.int64)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]


@pytest.mark.cross_backend
class TestNativeTypesCrossBackend:
    """Native types from one backend resolve via str() on another backend."""

    def test_polars_int64_on_ibis(self, backend_factory, collect_expr):
        import polars as pl
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "ibis-duckdb")
        expr = ma.col("value").cast(pl.Int64)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]

    def test_polars_utf8_on_narwhals(self, backend_factory, collect_expr):
        import polars as pl
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "narwhals")
        expr = ma.col("value").cast(pl.Utf8)
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3"]

    def test_narwhals_string_on_polars(self, backend_factory, collect_expr):
        import narwhals as nw
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "polars")
        expr = ma.col("value").cast(nw.String)
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3"]

    def test_narwhals_int64_on_ibis(self, backend_factory, collect_expr):
        import narwhals as nw
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "ibis-duckdb")
        expr = ma.col("value").cast(nw.Int64)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]

    def test_polars_uint16_on_ibis(self, backend_factory, collect_expr):
        import polars as pl
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "ibis-polars")
        expr = ma.col("value").cast(pl.UInt16)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]


@pytest.mark.cross_backend
class TestInvalidTypeStrings:
    """Invalid type strings raise ValueError at build time."""

    @pytest.mark.parametrize("bad_dtype", [
        "foobar",
        "",
        "int999",
        "FLOAT",
        "INTEGER",
    ])
    def test_invalid_string_raises(self, bad_dtype):
        with pytest.raises(ValueError, match="Unknown dtype"):
            ma.col("value").cast(bad_dtype)

    def test_none_raises(self):
        with pytest.raises(ValueError, match="Unknown dtype"):
            ma.col("value").cast(None)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestPythonBuiltinTypes:
    """Python built-in types (int, float, str, bool) work in cast()."""

    def test_cast_with_python_int(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB uses banker's rounding for float-to-int cast.")
        data = {"value": [1.5, 2.5, 3.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(int)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]

    def test_cast_with_python_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(float)
        values = collect_expr(df, expr)
        assert values == [1.0, 2.0, 3.0]

    def test_cast_with_python_str(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(str)
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3"]

    def test_cast_with_python_bool(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0, 1, 0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(bool)
        values = collect_expr(df, expr)
        assert values == [False, True, False]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMountainashDtypeEnum:
    """MountainashDtype enum members work directly in cast()."""

    def test_cast_with_enum_i64(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB uses banker's rounding for float-to-int cast.")
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(MountainashDtype.I64)
        values = collect_expr(df, expr)
        assert values == [1, 2, 3]

    def test_cast_with_enum_string(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(MountainashDtype.STRING)
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3"]

    def test_cast_with_enum_fp64(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(MountainashDtype.FP64)
        values = collect_expr(df, expr)
        assert values == [1.0, 2.0, 3.0]

    def test_cast_with_enum_bool(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0, 1, 0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast(MountainashDtype.BOOL)
        values = collect_expr(df, expr)
        assert values == [False, True, False]
