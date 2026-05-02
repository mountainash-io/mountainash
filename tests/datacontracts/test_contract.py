"""Tests for BaseDataContract — pandera DataFrameModel wrapper."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa

from mountainash.datacontracts.contract import BaseDataContract


class SampleContract(BaseDataContract):
    """Test contract: id (int, >=1), name (str), score (float, nullable)."""

    id: int = pa.Field(ge=1)
    name: str
    score: float = pa.Field(nullable=True)


class TestBaseDataContract:

    def test_validate_valid_data(self):
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, None]})
        result = SampleContract.validate_datacontract(df)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2

    def test_validate_invalid_data_raises(self):
        df = pl.DataFrame({"id": [0, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        with pytest.raises(pa.errors.SchemaErrors) as exc_info:
            SampleContract.validate_datacontract(df)
        fc = exc_info.value.failure_cases
        assert isinstance(fc, pl.DataFrame)
        assert "schema_context" in fc.columns

    def test_validate_quick_fails_on_first(self):
        df = pl.DataFrame({"id": [0, -1], "name": ["a", "b"], "score": [1.0, 2.0]})
        with pytest.raises(pa.errors.SchemaError):
            SampleContract.validate_datacontract_quick(df)

    def test_validate_accepts_pandas_input(self):
        import pandas as pd
        pdf = pd.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        result = SampleContract.validate_datacontract(pdf)
        assert isinstance(result, pl.DataFrame)

    def test_validate_returns_polars_regardless_of_input(self):
        import pandas as pd
        pdf = pd.DataFrame({"id": [1], "name": ["a"], "score": [1.0]})
        result = SampleContract.validate_datacontract(pdf)
        assert isinstance(result, pl.DataFrame)
