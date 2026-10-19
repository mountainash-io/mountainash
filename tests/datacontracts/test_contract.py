"""Tests for BaseDataContract FieldSpec declaration and validation."""
from __future__ import annotations

import polars as pl

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.typespec import FieldSpec, UniversalType
from mountainash.validation.result import ValidationResult


class SampleContract(BaseDataContract):
    """Test contract: id (int, >=1), name (str), score (float, nullable)."""

    id = FieldSpec(type=UniversalType.INTEGER, minimum=1, required=True)
    name = FieldSpec(type=UniversalType.STRING)
    score = FieldSpec(type=UniversalType.NUMBER, required=False)


class TestBaseDataContract:
    def test_validate_valid_data(self):
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, None]})
        result = SampleContract.validate_datacontract(df)
        assert isinstance(result, ValidationResult)
        assert result.passes is True

    def test_validate_invalid_data_fails(self):
        df = pl.DataFrame({"id": [0, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        result = SampleContract.validate_datacontract(df)
        assert result.passes is False
        failing = result.check_summaries.filter(
            result.check_summaries["status"] != "passed"
        )["check_id"].to_list()
        assert "id_range" in failing
        assert isinstance(result.failure_cases, pl.DataFrame)

    def test_validate_quick_fails_on_first(self):
        df = pl.DataFrame({"id": [0, -1], "name": ["a", "b"], "score": [1.0, 2.0]})
        assert SampleContract.validate_datacontract_quick(df).passes is False

    def test_validate_accepts_pandas_input(self):
        import pandas as pd
        result = SampleContract.validate_datacontract(pd.DataFrame({"id": [1], "name": ["a"], "score": [1.0]}))
        assert isinstance(result, ValidationResult)
        assert result.passes is True

    def test_validate_returns_polars_structures_regardless_of_input(self):
        import pandas as pd
        result = SampleContract.validate_datacontract(pd.DataFrame({"id": [1], "name": ["a"], "score": [1.0]}))
        assert isinstance(result.check_summaries, pl.DataFrame)
        assert isinstance(result.failure_cases, pl.DataFrame)

    def test_contract_members_preserve_order_and_shared_definition(self):
        shared_definition = FieldSpec(type=UniversalType.STRING, description="shared")
        class Parent(BaseDataContract):
            first = shared_definition
            second = FieldSpec(type=UniversalType.INTEGER)
        class Child(Parent):
            first = FieldSpec(type=UniversalType.STRING, description="replacement")
            third = FieldSpec(type=UniversalType.BOOLEAN)
        assert list(Child.to_typespec().fields) == ["first", "second", "third"]
        assert Child.to_typespec().get_field("first") is Child.first
        assert Child.to_typespec().get_field("first").description == "replacement"
