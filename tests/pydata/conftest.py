"""Shared fixtures for pydata tests."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

import polars as pl
import pytest
from pydantic import BaseModel


@dataclass
class SamplePerson:
    name: str
    age: int
    score: float


@dataclass
class SampleWithDefaults:
    name: str
    age: int = 0
    email: Optional[str] = None


class SamplePersonModel(BaseModel):
    name: str
    age: int
    score: float


SampleRow = namedtuple("SampleRow", ["name", "age", "score"])


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


@pytest.fixture
def sample_persons():
    return [SamplePerson("Alice", 30, 1.5), SamplePerson("Bob", 25, 2.0)]


@pytest.fixture
def sample_pydantic_persons():
    return [SamplePersonModel(name="Alice", age=30, score=1.5), SamplePersonModel(name="Bob", age=25, score=2.0)]


@pytest.fixture
def sample_named_tuples():
    return [SampleRow("Alice", 30, 1.5), SampleRow("Bob", 25, 2.0)]


@pytest.fixture
def sample_polars_df():
    return pl.DataFrame(SAMPLE_DICT_OF_LISTS)
