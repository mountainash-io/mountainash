"""Tests for Relation terminal methods delegating to the egress module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import polars as pl
import pytest

import mountainash as ma


@dataclass
class PersonDC:
    name: str
    age: int
    score: Optional[float] = None


try:
    from pydantic import BaseModel

    class PersonPydantic(BaseModel):
        name: str
        age: int
        score: Optional[float] = None

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    PersonPydantic = None  # type: ignore


@pytest.fixture
def sample_rel():
    df = pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "score": [1.5, None, 3.0],
    })
    return ma.relation(df)


class TestToDictDelegation:
    def test_returns_dict_of_lists(self, sample_rel):
        result = sample_rel.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == ["Alice", "Bob", "Charlie"]
        assert result["age"] == [30, 25, 35]

    def test_values_not_series(self, sample_rel):
        result = sample_rel.to_dict()
        assert isinstance(result["name"], list)


class TestToDictsDelegation:
    def test_returns_list_of_dicts(self, sample_rel):
        result = sample_rel.to_dicts()
        assert isinstance(result, list)
        assert result[0] == {"name": "Alice", "age": 30, "score": 1.5}

    def test_null_preserved(self, sample_rel):
        result = sample_rel.to_dicts()
        assert result[1]["score"] is None


class TestToTuplesDelegation:
    def test_returns_list_of_tuples(self, sample_rel):
        result = sample_rel.to_tuples()
        assert isinstance(result, list)
        assert result[0] == ("Alice", 30, 1.5)


class TestToPandasDelegation:
    def test_returns_pandas_dataframe(self, sample_rel):
        pytest.importorskip("pandas")
        import pandas as pd
        result = sample_rel.to_pandas()
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "age", "score"]


class TestToDataclassesDelegation:
    def test_returns_dataclass_instances(self, sample_rel):
        result = sample_rel.to_dataclasses(PersonDC)
        assert len(result) == 3
        assert isinstance(result[0], PersonDC)
        assert result[0].name == "Alice"
        assert result[0].age == 30

    def test_auto_derive_schema_false_skips_hybrid(self, sample_rel):
        result = sample_rel.to_dataclasses(PersonDC, auto_derive_schema=False)
        assert len(result) == 3
        assert isinstance(result[0], PersonDC)


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic not installed")
class TestToPydanticDelegation:
    def test_returns_pydantic_instances(self, sample_rel):
        result = sample_rel.to_pydantic(PersonPydantic)
        assert len(result) == 3
        assert result[0].name == "Alice"

    def test_non_pydantic_class_raises(self, sample_rel):
        """Non-Pydantic fallback is removed -- must raise, not silently work."""
        with pytest.raises((ValueError, TypeError, ImportError, AttributeError)):
            sample_rel.to_pydantic(PersonDC)
