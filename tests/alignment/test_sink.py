"""Tests for sink terminal methods on Relation."""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl
import pytest

import mountainash as ma


@dataclass
class Person:
    name: str
    age: int


@pytest.fixture
def people_df():
    return pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
    })


class TestSinkToTuples:
    """Relation.to_tuples() returns list of tuples."""

    def test_to_tuples(self, people_df):
        result = ma.relation(people_df).to_tuples()
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == ("Alice", 30)
        assert result[1] == ("Bob", 25)

    def test_to_tuples_after_filter(self, people_df):
        result = ma.relation(people_df).filter(ma.col("age").gt(28)).to_tuples()
        assert len(result) == 2


class TestSinkToDataclasses:
    """Relation.to_dataclasses() returns list of dataclass instances."""

    def test_to_dataclasses(self, people_df):
        result = ma.relation(people_df).to_dataclasses(Person)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], Person)
        assert result[0].name == "Alice"
        assert result[0].age == 30

    def test_to_dataclasses_after_sort(self, people_df):
        result = ma.relation(people_df).sort("age").to_dataclasses(Person)
        assert result[0].name == "Bob"
        assert result[2].name == "Charlie"


class TestSinkToPydantic:
    """Relation.to_pydantic() returns list of Pydantic model instances."""

    def test_to_pydantic(self, people_df):
        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        class PersonModel(BaseModel):
            name: str
            age: int

        result = ma.relation(people_df).to_pydantic(PersonModel)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], PersonModel)
        assert result[0].name == "Alice"
        assert result[0].age == 30
