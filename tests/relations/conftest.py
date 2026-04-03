"""Shared fixtures for relation tests."""

import pytest
import polars as pl
import pandas as pd
import pyarrow as pa


@pytest.fixture
def sample_data():
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "score": [85, 92, 78, 95, 88],
        "active": [True, False, True, True, False],
    }


@pytest.fixture
def polars_df(sample_data):
    return pl.DataFrame(sample_data)


@pytest.fixture
def pandas_df(sample_data):
    return pd.DataFrame(sample_data)


@pytest.fixture
def pyarrow_table(sample_data):
    return pa.table(sample_data)


@pytest.fixture
def join_data():
    return {
        "id": [1, 2, 3],
        "label": ["x", "y", "z"],
    }


@pytest.fixture
def polars_join_df(join_data):
    return pl.DataFrame(join_data)
