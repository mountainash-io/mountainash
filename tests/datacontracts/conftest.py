"""Shared fixtures for datacontracts tests."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa
import mountainash as ma

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.rule import Rule, guarded
from mountainash.datacontracts.registry import RuleRegistry


class PersonContract(BaseDataContract):
    """Hand-built contract for testing."""

    name: str
    age: int = pa.Field(ge=0)
    email: str = pa.Field(nullable=True)


@pytest.fixture
def person_contract():
    return PersonContract


@pytest.fixture
def person_rules() -> RuleRegistry:
    return RuleRegistry([
        Rule("age_under_150", expr=ma.col("age").lt(150)),
        Rule("name_not_empty", expr=guarded(
            precondition=ma.col("name").is_not_null(),
            test=ma.col("name").str.len_chars().gt(0),
        )),
    ])


@pytest.fixture
def valid_person_df() -> pl.DataFrame:
    return pl.DataFrame({
        "name": ["alice", "bob", "charlie"],
        "age": [30, 25, 40],
        "email": ["a@b.com", None, "c@d.com"],
    })


