"""Tests for unified backend constants in mountainash.core.constants."""

from enum import StrEnum, Enum

import pytest

from mountainash.core.constants import (
    CONST_BACKEND,
    CONST_BACKEND_SYSTEM,
    CONST_DATAFRAME_TYPE,
    CONST_IBIS_INMEMORY_BACKEND,
    CONST_VISITOR_BACKENDS,
    backend_to_system,
)


class TestConstBackend:
    """Tests for CONST_BACKEND unified detection enum."""

    def test_is_strenum(self):
        assert issubclass(CONST_BACKEND, StrEnum)

    def test_has_five_members(self):
        assert len(CONST_BACKEND) == 5

    def test_string_equality(self):
        """StrEnum values must equal their string for registry lookups."""
        assert CONST_BACKEND.POLARS == "polars"
        assert CONST_BACKEND.PANDAS == "pandas"
        assert CONST_BACKEND.PYARROW == "pyarrow"
        assert CONST_BACKEND.IBIS == "ibis"
        assert CONST_BACKEND.NARWHALS == "narwhals"

    def test_visitor_backends_alias(self):
        """CONST_VISITOR_BACKENDS is an alias for CONST_BACKEND."""
        assert CONST_VISITOR_BACKENDS is CONST_BACKEND


class TestConstBackendSystem:
    """Tests for CONST_BACKEND_SYSTEM unified routing enum."""

    def test_is_strenum(self):
        assert issubclass(CONST_BACKEND_SYSTEM, StrEnum)

    def test_has_three_members(self):
        assert len(CONST_BACKEND_SYSTEM) == 3

    def test_members(self):
        assert CONST_BACKEND_SYSTEM.POLARS == "polars"
        assert CONST_BACKEND_SYSTEM.NARWHALS == "narwhals"
        assert CONST_BACKEND_SYSTEM.IBIS == "ibis"


class TestBackendToSystem:
    """Tests for backend_to_system() mapping."""

    @pytest.mark.parametrize(
        "backend, expected_system",
        [
            (CONST_BACKEND.POLARS, CONST_BACKEND_SYSTEM.POLARS),
            (CONST_BACKEND.PANDAS, CONST_BACKEND_SYSTEM.NARWHALS),
            (CONST_BACKEND.PYARROW, CONST_BACKEND_SYSTEM.NARWHALS),
            (CONST_BACKEND.IBIS, CONST_BACKEND_SYSTEM.IBIS),
            (CONST_BACKEND.NARWHALS, CONST_BACKEND_SYSTEM.NARWHALS),
        ],
    )
    def test_mapping(self, backend, expected_system):
        assert backend_to_system(backend) == expected_system


class TestConstDataframeType:
    """Tests for CONST_DATAFRAME_TYPE."""

    def test_is_enum(self):
        assert issubclass(CONST_DATAFRAME_TYPE, Enum)

    def test_has_seven_members(self):
        assert len(CONST_DATAFRAME_TYPE) == 7

    def test_all_members_exist(self):
        expected = {
            "IBIS_TABLE", "PANDAS_DATAFRAME", "POLARS_DATAFRAME",
            "POLARS_LAZYFRAME", "PYARROW_TABLE",
            "NARWHALS_DATAFRAME", "NARWHALS_LAZYFRAME",
        }
        actual = {m.name for m in CONST_DATAFRAME_TYPE}
        assert actual == expected


class TestConstIbisInmemoryBackend:
    """Tests for CONST_IBIS_INMEMORY_BACKEND."""

    def test_is_strenum(self):
        assert issubclass(CONST_IBIS_INMEMORY_BACKEND, StrEnum)

    def test_has_three_members(self):
        assert len(CONST_IBIS_INMEMORY_BACKEND) == 3

    def test_string_values(self):
        assert CONST_IBIS_INMEMORY_BACKEND.POLARS == "polars"
        assert CONST_IBIS_INMEMORY_BACKEND.DUCKDB == "duckdb"
        assert CONST_IBIS_INMEMORY_BACKEND.SQLITE == "sqlite"


class TestShimImports:
    """Tests that old import paths resolve to the unified enums."""

    def test_dataframes_constants_dataframe_type(self):
        from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE as df_type
        from mountainash.core.constants import CONST_DATAFRAME_TYPE as core_type
        assert df_type is core_type

    def test_dataframes_constants_framework_is_backend(self):
        from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK
        assert CONST_DATAFRAME_FRAMEWORK is CONST_BACKEND

    def test_dataframes_core_backend_is_const_backend(self):
        from mountainash.dataframes.core.constants import Backend
        assert Backend is CONST_BACKEND

    def test_dataframes_core_system_is_const_backend_system(self):
        from mountainash.dataframes.core.constants import DataFrameSystemBackend
        assert DataFrameSystemBackend is CONST_BACKEND_SYSTEM

    def test_dataframe_system_backend_is_const_backend_system(self):
        from mountainash.dataframes.core.dataframe_system.constants import CONST_DATAFRAME_BACKEND
        assert CONST_DATAFRAME_BACKEND is CONST_BACKEND_SYSTEM

    def test_expressions_visitor_backends(self):
        from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
        assert CONST_VISITOR_BACKENDS is CONST_BACKEND
