"""Tests for all 10 pydata ingress handlers via PydataIngress.convert()."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import polars as pl
import pytest
from pydantic import BaseModel

from mountainash.pydata.ingress.pydata_ingress import PydataIngress
from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory

# ---------------------------------------------------------------------------
# Inline test types (conftest types available as fixtures but not importable)
# ---------------------------------------------------------------------------


@dataclass
class Person:
    name: str
    age: int
    score: float


class PersonModel(BaseModel):
    name: str
    age: int
    score: float


Row = namedtuple("Row", ["name", "age", "score"])

SAMPLE_DICTS = [
    {"name": "Alice", "age": 30, "score": 1.5},
    {"name": "Bob", "age": 25, "score": 2.0},
    {"name": "Charlie", "age": 35, "score": 3.0},
]

SAMPLE_DICT_OF_LISTS = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [30, 25, 35],
    "score": [1.5, 2.0, 3.0],
}


# ---------------------------------------------------------------------------
# TestIngressFromPylist
# ---------------------------------------------------------------------------


class TestIngressFromPylist:
    def test_basic_list_of_dicts(self):
        df = PydataIngress.convert(SAMPLE_DICTS)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 3)
        assert set(df.columns) == {"name", "age", "score"}

    def test_correct_values(self):
        df = PydataIngress.convert(SAMPLE_DICTS)
        assert df["name"].to_list() == ["Alice", "Bob", "Charlie"]
        assert df["age"].to_list() == [30, 25, 35]

    def test_none_values_become_null(self):
        data = [{"a": 1, "b": None}, {"a": 2, "b": "x"}]
        df = PydataIngress.convert(data)
        assert df.shape == (2, 2)
        assert df["b"][0] is None

    def test_single_dict_in_list(self):
        df = PydataIngress.convert([{"x": 42}])
        assert df.shape == (1, 1)
        assert df["x"][0] == 42


# ---------------------------------------------------------------------------
# TestIngressFromPydict
# ---------------------------------------------------------------------------


class TestIngressFromPydict:
    def test_basic_dict_of_lists(self):
        df = PydataIngress.convert(SAMPLE_DICT_OF_LISTS)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 3)

    def test_column_order_preserved(self):
        data = {"c": [1, 2], "a": [3, 4], "b": [5, 6]}
        df = PydataIngress.convert(data)
        assert df.columns == ["c", "a", "b"]


# ---------------------------------------------------------------------------
# TestIngressFromDataclass
# ---------------------------------------------------------------------------


class TestIngressFromDataclass:
    def test_single_instance(self):
        df = PydataIngress.convert(Person("Alice", 30, 1.5))
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] >= 1
        assert "name" in df.columns

    def test_list_of_instances(self):
        persons = [Person("Alice", 30, 1.5), Person("Bob", 25, 2.0)]
        df = PydataIngress.convert(persons)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 3)
        assert df["name"].to_list() == ["Alice", "Bob"]
        assert df["age"].to_list() == [30, 25]


# ---------------------------------------------------------------------------
# TestIngressFromPydantic
# ---------------------------------------------------------------------------


class TestIngressFromPydantic:
    def test_single_instance(self):
        df = PydataIngress.convert(PersonModel(name="Alice", age=30, score=1.5))
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] >= 1

    def test_list_of_instances(self):
        persons = [
            PersonModel(name="Alice", age=30, score=1.5),
            PersonModel(name="Bob", age=25, score=2.0),
        ]
        df = PydataIngress.convert(persons)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 3)
        assert df["name"].to_list() == ["Alice", "Bob"]


# ---------------------------------------------------------------------------
# TestIngressFromNamedTuple
# ---------------------------------------------------------------------------


class TestIngressFromNamedTuple:
    def test_single_instance(self):
        df = PydataIngress.convert(Row("Alice", 30, 1.5))
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] >= 1

    def test_list_of_instances(self):
        rows = [Row("Alice", 30, 1.5), Row("Bob", 25, 2.0)]
        df = PydataIngress.convert(rows)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 3)

    def test_field_names_become_columns(self):
        rows = [Row("Alice", 30, 1.5), Row("Bob", 25, 2.0)]
        df = PydataIngress.convert(rows)
        assert set(df.columns) == {"name", "age", "score"}


# ---------------------------------------------------------------------------
# TestIngressFromTuple
# ---------------------------------------------------------------------------


class TestIngressFromTuple:
    def test_list_of_plain_tuples(self):
        data = [(1, "a"), (2, "b"), (3, "c")]
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)


# ---------------------------------------------------------------------------
# TestIngressFromSeriesDict
# ---------------------------------------------------------------------------


class TestIngressFromSeriesDict:
    def test_polars_series_dict(self):
        data = {
            "a": pl.Series([1, 2, 3]),
            "b": pl.Series(["x", "y", "z"]),
        }
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)
        assert set(df.columns) == {"a", "b"}

    def test_pandas_series_dict(self):
        data = {
            "a": pd.Series([1, 2, 3]),
            "b": pd.Series(["x", "y", "z"]),
        }
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)
        assert set(df.columns) == {"a", "b"}


# ---------------------------------------------------------------------------
# TestIngressFromIndexedData
# ---------------------------------------------------------------------------


class TestIngressFromIndexedData:
    def test_basic_indexed_data(self):
        data = {
            "group_a": [{"x": 1}, {"x": 2}],
            "group_b": [{"x": 3}],
        }
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 3


# ---------------------------------------------------------------------------
# TestIngressFromCollection
# ---------------------------------------------------------------------------


class TestIngressFromCollection:
    def test_list_of_scalars(self):
        data = [1, 2, 3]
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 3

    def test_set_of_strings(self):
        data = {"a", "b", "c"}
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 3


# ---------------------------------------------------------------------------
# TestIngressFromDefault
# ---------------------------------------------------------------------------


class TestIngressFromDefault:
    def test_polars_dataframe_falls_back_to_default(self):
        # A pl.DataFrame is not explicitly handled by any specific ingress type,
        # so it routes to the UNKNOWN/default strategy
        df_input = pl.DataFrame(SAMPLE_DICT_OF_LISTS)
        strategy = PydataIngressFactory.get_strategy(df_input)
        assert strategy is not None
