"""Ingress → egress round-trip tests."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

import polars as pl
import pytest

from mountainash.pydata.ingress.pydata_ingress import PydataIngress
from mountainash.pydata.egress.egress_pydata_from_polars import EgressFromPolars

# ---------------------------------------------------------------------------
# Optional dependency guard
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

# ---------------------------------------------------------------------------
# Inline type definitions
# ---------------------------------------------------------------------------


@dataclass
class SamplePerson:
    name: str
    age: int
    score: Optional[float] = None


if HAS_PYDANTIC:
    from pydantic import BaseModel

    class SamplePersonModel(BaseModel):
        name: str
        age: int
        score: Optional[float] = None
else:
    SamplePersonModel = None  # type: ignore[misc,assignment]


SampleNamedTuple = namedtuple("SampleNamedTuple", ["name", "age", "score"])

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DICT_OF_LISTS = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [30, 25, 35],
    "score": [1.5, 2.0, 3.0],
}

SAMPLE_DICTS = [
    {"name": "Alice", "age": 30, "score": 1.5},
    {"name": "Bob", "age": 25, "score": 2.0},
]


# ---------------------------------------------------------------------------
# TestRoundTripDictOfLists
# ---------------------------------------------------------------------------


class TestRoundTripDictOfLists:
    def test_dict_of_lists_roundtrip(self):
        """Dict of lists → DataFrame → dict of lists matches original."""
        df = PydataIngress.convert(SAMPLE_DICT_OF_LISTS)
        result = EgressFromPolars._to_dictionary_of_lists(df)
        assert result["name"] == SAMPLE_DICT_OF_LISTS["name"]
        assert result["age"] == SAMPLE_DICT_OF_LISTS["age"]
        assert result["score"] == SAMPLE_DICT_OF_LISTS["score"]


# ---------------------------------------------------------------------------
# TestRoundTripListOfDicts
# ---------------------------------------------------------------------------


class TestRoundTripListOfDicts:
    def test_list_of_dicts_roundtrip(self):
        """List of dicts → DataFrame → list of dicts, first row name matches."""
        df = PydataIngress.convert(SAMPLE_DICTS)
        result = EgressFromPolars._to_list_of_dictionaries(df)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_list_of_dicts_roundtrip_full(self):
        """All values preserved after round-trip."""
        df = PydataIngress.convert(SAMPLE_DICTS)
        result = EgressFromPolars._to_list_of_dictionaries(df)
        assert result[0] == {"name": "Alice", "age": 30, "score": 1.5}
        assert result[1] == {"name": "Bob", "age": 25, "score": 2.0}


# ---------------------------------------------------------------------------
# TestRoundTripDataclass
# ---------------------------------------------------------------------------


class TestRoundTripDataclass:
    def test_dataclass_roundtrip(self):
        """Dataclass → DataFrame → list of dataclasses, field values match."""
        person1 = SamplePerson(name="Alice", age=30, score=1.5)
        person2 = SamplePerson(name="Bob", age=25, score=2.0)
        df = PydataIngress.convert([person1, person2])
        result = EgressFromPolars._to_list_of_dataclasses(df, SamplePerson)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "Alice"
        assert result[0].age == 30
        assert result[0].score == 1.5


# ---------------------------------------------------------------------------
# TestRoundTripPydantic
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic not available")
class TestRoundTripPydantic:
    def test_pydantic_roundtrip(self):
        """Pydantic model → DataFrame → list of pydantic models, field values match."""
        record1 = SamplePersonModel(name="Alice", age=30, score=1.5)
        record2 = SamplePersonModel(name="Bob", age=25, score=2.0)
        df = PydataIngress.convert([record1, record2])
        result = EgressFromPolars._to_list_of_pydantic(df, SamplePersonModel)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "Alice"
        assert result[0].age == 30


# ---------------------------------------------------------------------------
# TestRoundTripNamedTuples
# ---------------------------------------------------------------------------


class TestRoundTripNamedTuples:
    def test_named_tuples_roundtrip(self):
        """Named tuples → DataFrame → list of named tuples, field values match."""
        nt1 = SampleNamedTuple(name="Alice", age=30, score=1.5)
        nt2 = SampleNamedTuple(name="Bob", age=25, score=2.0)
        df = PydataIngress.convert([nt1, nt2])
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert isinstance(result, list)
        assert len(result) == 2
        row = result[0]
        assert hasattr(row, "name")
        assert hasattr(row, "age")
        assert row.name == "Alice"
        assert row.age == 30


# ---------------------------------------------------------------------------
# TestRoundTripPlainTuples
# ---------------------------------------------------------------------------


class TestRoundTripPlainTuples:
    def test_plain_tuples_roundtrip(self):
        """List of tuples → DataFrame → list of tuples, length matches."""
        data = [(1, "a"), (2, "b")]
        df = PydataIngress.convert(data)
        result = EgressFromPolars._to_list_of_tuples(df)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_plain_tuples_values(self):
        """Plain tuple round-trip preserves values."""
        data = [(1, "a"), (2, "b")]
        df = PydataIngress.convert(data)
        result = EgressFromPolars._to_list_of_tuples(df)
        # Values are accessible by index
        assert result[0][0] == 1
        assert result[0][1] == "a"
        assert result[1][0] == 2


# ---------------------------------------------------------------------------
# TestRoundTripCollection
# ---------------------------------------------------------------------------


class TestRoundTripCollection:
    def test_collection_roundtrip(self):
        """List of scalars → single-column DataFrame → list matches original."""
        data = [10, 20, 30]
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        # First (and only) column
        col_values = df[df.columns[0]].to_list()
        assert col_values == data

    def test_collection_string_values(self):
        """Collection of strings round-trips correctly."""
        data = ["alpha", "beta", "gamma"]
        df = PydataIngress.convert(data)
        col_values = df[df.columns[0]].to_list()
        assert col_values == data
