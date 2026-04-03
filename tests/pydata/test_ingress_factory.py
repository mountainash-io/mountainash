"""Tests for PydataIngressFactory format detection and strategy retrieval."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import polars as pl
import pytest
from pydantic import BaseModel

from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory


# ---------------------------------------------------------------------------
# Inline type definitions (mirrors conftest but available without import)
# ---------------------------------------------------------------------------

@dataclass
class _Person:
    name: str
    age: int
    score: float


class _PersonModel(BaseModel):
    name: str
    age: int
    score: float


_Row = namedtuple("_Row", ["name", "age", "score"])

_SAMPLE_DICTS = [
    {"name": "Alice", "age": 30, "score": 1.5},
    {"name": "Bob", "age": 25, "score": 2.0},
]

_SAMPLE_DICT_OF_LISTS = {
    "name": ["Alice", "Bob"],
    "age": [30, 25],
    "score": [1.5, 2.0],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _key(data):
    return PydataIngressFactory._get_strategy_key(data)


# ---------------------------------------------------------------------------
# TestFormatDetection
# ---------------------------------------------------------------------------

class TestFormatDetection:
    def test_single_dataclass(self):
        assert _key(_Person("Alice", 30, 1.5)) == CONST_PYTHON_DATAFORMAT.DATACLASS

    def test_list_of_dataclasses(self):
        assert _key([_Person("Alice", 30, 1.5), _Person("Bob", 25, 2.0)]) == CONST_PYTHON_DATAFORMAT.DATACLASS

    def test_single_pydantic_model(self):
        assert _key(_PersonModel(name="Alice", age=30, score=1.5)) == CONST_PYTHON_DATAFORMAT.PYDANTIC

    def test_list_of_pydantic_models(self):
        models = [_PersonModel(name="Alice", age=30, score=1.5), _PersonModel(name="Bob", age=25, score=2.0)]
        assert _key(models) == CONST_PYTHON_DATAFORMAT.PYDANTIC

    def test_dict_of_lists(self):
        assert _key(_SAMPLE_DICT_OF_LISTS) == CONST_PYTHON_DATAFORMAT.PYDICT

    def test_list_of_dicts(self):
        assert _key(_SAMPLE_DICTS) == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_single_named_tuple(self):
        assert _key(_Row("Alice", 30, 1.5)) == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_list_of_named_tuples(self):
        assert _key([_Row("Alice", 30, 1.5), _Row("Bob", 25, 2.0)]) == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_single_plain_tuple(self):
        assert _key(("Alice", 30, 1.5)) == CONST_PYTHON_DATAFORMAT.TUPLE

    def test_list_of_plain_tuples(self):
        assert _key([("Alice", 30, 1.5), ("Bob", 25, 2.0)]) == CONST_PYTHON_DATAFORMAT.TUPLE

    def test_dict_of_polars_series(self):
        data = {
            "name": pl.Series("name", ["Alice", "Bob"]),
            "age": pl.Series("age", [30, 25]),
        }
        assert _key(data) == CONST_PYTHON_DATAFORMAT.SERIES_DICT

    def test_dict_of_pandas_series(self):
        data = {
            "name": pd.Series(["Alice", "Bob"]),
            "age": pd.Series([30, 25]),
        }
        assert _key(data) == CONST_PYTHON_DATAFORMAT.SERIES_DICT

    def test_indexed_data(self):
        data = {
            "alice": [{"field": "value1"}, {"field": "value2"}],
            "bob": [{"field": "value3"}],
        }
        assert _key(data) == CONST_PYTHON_DATAFORMAT.INDEXED_DATA

    def test_list_of_scalars(self):
        assert _key([1, 2, 3]) == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_set_of_scalars(self):
        assert _key({1, 2, 3}) == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_frozenset_of_scalars(self):
        assert _key(frozenset({1, 2, 3})) == CONST_PYTHON_DATAFORMAT.COLLECTION


# ---------------------------------------------------------------------------
# TestFormatDetectionEdgeCases
# ---------------------------------------------------------------------------

class TestFormatDetectionEdgeCases:
    def test_empty_list(self):
        assert _key([]) == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_empty_dict_does_not_crash(self):
        # Empty dict should return some result without raising
        result = _key({})
        assert result is not None

    def test_single_item_list_of_dicts(self):
        assert _key([{"name": "Alice"}]) == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_unknown_type(self):
        assert _key(object()) == CONST_PYTHON_DATAFORMAT.UNKNOWN


# ---------------------------------------------------------------------------
# TestGetStrategy
# ---------------------------------------------------------------------------

class TestGetStrategy:
    def test_get_strategy_for_list_of_dicts(self):
        strategy = PydataIngressFactory.get_strategy(_SAMPLE_DICTS)
        assert hasattr(strategy, "convert")

    def test_get_strategy_for_dict_of_lists(self):
        strategy = PydataIngressFactory.get_strategy(_SAMPLE_DICT_OF_LISTS)
        assert hasattr(strategy, "convert")
