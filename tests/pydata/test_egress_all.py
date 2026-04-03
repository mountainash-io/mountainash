"""Tests for all egress methods from EgressFromPolars."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

import polars as pl
import pytest

from mountainash.pydata.egress.egress_pydata_from_polars import EgressFromPolars

# ---------------------------------------------------------------------------
# Optional dependency guard
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Inline type definitions
# ---------------------------------------------------------------------------


@dataclass
class SamplePerson:
    name: str
    age: int
    score: Optional[float]


try:
    from pydantic import BaseModel

    class SamplePersonModel(BaseModel):
        name: str
        age: int
        score: Optional[float]

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    SamplePersonModel = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_df():
    return pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "score": [1.5, None, 3.0],
    })


@pytest.fixture
def test_df_with_date():
    return pl.DataFrame({
        "name": ["Alice", "Bob"],
        "age": [30, 25],
        "birth_date": [datetime.date(1994, 1, 1), datetime.date(1999, 5, 15)],
    })


# ---------------------------------------------------------------------------
# TestEgressDataFrame
# ---------------------------------------------------------------------------


class TestEgressDataFrame:
    def test_to_pandas(self, test_df):
        import pandas as pd
        result = EgressFromPolars._to_pandas(test_df)
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "age", "score"]
        assert len(result) == 3

    def test_to_polars_eager(self, test_df):
        result = EgressFromPolars._to_polars(test_df)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 3)

    def test_to_polars_as_lazy(self, test_df):
        result = EgressFromPolars._to_polars(test_df, as_lazy=True)
        assert isinstance(result, pl.LazyFrame)

    def test_to_polars_not_lazy(self, test_df):
        result = EgressFromPolars._to_polars(test_df, as_lazy=False)
        assert isinstance(result, pl.DataFrame)

    def test_to_narwhals(self, test_df):
        import narwhals as nw
        result = EgressFromPolars._to_narwhals(test_df)
        assert isinstance(result, nw.DataFrame)

    def test_to_narwhals_as_lazy(self, test_df):
        import narwhals as nw
        result = EgressFromPolars._to_narwhals(test_df, as_lazy=True)
        assert isinstance(result, nw.LazyFrame)

    def test_to_pyarrow(self, test_df):
        import pyarrow as pa
        result = EgressFromPolars._to_pyarrow(test_df)
        assert isinstance(result, pa.Table)
        assert result.num_rows == 3
        assert result.num_columns == 3


# ---------------------------------------------------------------------------
# TestEgressPythonData
# ---------------------------------------------------------------------------


class TestEgressPythonData:
    def test_to_dictionary_of_lists(self, test_df):
        result = EgressFromPolars._to_dictionary_of_lists(test_df)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"name", "age", "score"}
        assert result["name"] == ["Alice", "Bob", "Charlie"]
        assert result["age"] == [30, 25, 35]

    def test_to_list_of_dictionaries(self, test_df):
        result = EgressFromPolars._to_list_of_dictionaries(test_df)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == {"name": "Alice", "age": 30, "score": 1.5}
        assert isinstance(result[0], dict)

    def test_to_list_of_tuples(self, test_df):
        result = EgressFromPolars._to_list_of_tuples(test_df)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], tuple)
        assert result[0][0] == "Alice"
        assert result[0][1] == 30


# ---------------------------------------------------------------------------
# TestEgressSeries
# ---------------------------------------------------------------------------


class TestEgressSeries:
    def test_to_dictionary_of_series_polars(self, test_df):
        result = EgressFromPolars._to_dictionary_of_series_polars(test_df)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"name", "age", "score"}
        assert isinstance(result["name"], pl.Series)
        assert list(result["name"]) == ["Alice", "Bob", "Charlie"]

    def test_to_dictionary_of_series_pandas(self, test_df):
        import pandas as pd
        result = EgressFromPolars._to_dictionary_of_series_pandas(test_df)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"name", "age", "score"}
        assert isinstance(result["name"], pd.Series)


# ---------------------------------------------------------------------------
# TestEgressNamedTuples
# ---------------------------------------------------------------------------


class TestEgressNamedTuples:
    def test_to_list_of_named_tuples(self, test_df):
        result = EgressFromPolars._to_list_of_named_tuples(test_df)
        assert isinstance(result, list)
        assert len(result) == 3
        row = result[0]
        assert hasattr(row, "name")
        assert hasattr(row, "age")
        assert hasattr(row, "score")
        assert row.name == "Alice"
        assert row.age == 30

    def test_to_list_of_typed_named_tuples_default(self, test_df):
        result = EgressFromPolars._to_list_of_typed_named_tuples(test_df)
        assert isinstance(result, list)
        assert len(result) == 3
        row = result[0]
        assert hasattr(row, "name")
        assert row.name == "Alice"

    def test_to_list_of_typed_named_tuples_with_date_preserve_false(self, test_df_with_date):
        result = EgressFromPolars._to_list_of_typed_named_tuples(
            test_df_with_date, preserve_dates=False
        )
        assert len(result) == 2
        row = result[0]
        assert hasattr(row, "birth_date")

    def test_to_list_of_typed_named_tuples_with_date_preserve_true(self, test_df_with_date):
        result = EgressFromPolars._to_list_of_typed_named_tuples(
            test_df_with_date, preserve_dates=True
        )
        assert len(result) == 2
        row = result[0]
        assert hasattr(row, "birth_date")
        # preserve_dates=True maps date column annotation to datetime.date
        # The actual row values are native Python dates from df.rows()
        assert isinstance(row.birth_date, datetime.date)

    def test_typed_named_tuples_annotations_set(self, test_df):
        result = EgressFromPolars._to_list_of_typed_named_tuples(test_df)
        assert len(result) > 0
        row_class = type(result[0])
        assert hasattr(row_class, "__annotations__")
        assert "name" in row_class.__annotations__
        assert "age" in row_class.__annotations__


# ---------------------------------------------------------------------------
# TestEgressIndexed
# ---------------------------------------------------------------------------


class TestEgressIndexed:
    def test_to_index_of_dictionaries_single_key(self, test_df):
        result = EgressFromPolars._to_index_of_dictionaries(test_df, index_fields="name")
        assert isinstance(result, dict)
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result
        # Each value is a list of rows
        assert isinstance(result["Alice"], list)

    def test_to_index_of_tuples(self, test_df):
        result = EgressFromPolars._to_index_of_tuples(test_df, index_fields="name")
        assert isinstance(result, dict)
        assert "Alice" in result
        rows = result["Alice"]
        assert isinstance(rows, list)
        assert isinstance(rows[0], tuple)

    def test_to_index_of_named_tuples(self, test_df):
        result = EgressFromPolars._to_index_of_named_tuples(test_df, index_fields="name")
        assert isinstance(result, dict)
        assert "Alice" in result
        rows = result["Alice"]
        assert isinstance(rows, list)
        row = rows[0]
        assert hasattr(row, "name")
        assert row.name == "Alice"

    def test_to_index_of_typed_named_tuples(self, test_df):
        result = EgressFromPolars._to_index_of_typed_named_tuples(
            test_df, index_fields="name"
        )
        assert isinstance(result, dict)
        assert "Alice" in result
        rows = result["Alice"]
        assert isinstance(rows, list)
        row = rows[0]
        assert hasattr(row, "name")

    def test_to_index_of_dictionaries_composite_key(self):
        df = pl.DataFrame({
            "name": ["Alice", "Alice", "Bob"],
            "age": [30, 30, 25],
            "score": [1.5, 2.0, 3.0],
        })
        result = EgressFromPolars._to_index_of_dictionaries(df, index_fields=["name", "age"])
        assert isinstance(result, dict)
        # Composite key → tuple keys
        assert ("Alice", 30) in result
        assert ("Bob", 25) in result

    def test_to_index_of_tuples_composite_key(self):
        df = pl.DataFrame({
            "dept": ["eng", "eng", "mkt"],
            "role": ["senior", "junior", "senior"],
            "name": ["Alice", "Bob", "Charlie"],
        })
        result = EgressFromPolars._to_index_of_tuples(df, index_fields=["dept", "role"])
        assert isinstance(result, dict)
        assert ("eng", "senior") in result


# ---------------------------------------------------------------------------
# TestEgressTypedOutput
# ---------------------------------------------------------------------------


class TestEgressTypedOutput:
    def test_to_list_of_dataclasses(self, test_df):
        df = pl.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [30, 25],
            "score": [1.5, 2.0],
        })
        result = EgressFromPolars._to_list_of_dataclasses(df, SamplePerson)
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], SamplePerson)
        assert result[0].name == "Alice"
        assert result[0].age == 30

    @pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic not installed")
    def test_to_list_of_pydantic(self, test_df):
        df = pl.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [30, 25],
            "score": [1.5, 2.0],
        })
        result = EgressFromPolars._to_list_of_pydantic(df, SamplePersonModel)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "Alice"
        assert result[0].age == 30
