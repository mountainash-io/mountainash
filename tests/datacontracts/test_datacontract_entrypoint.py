"""Tests for ma.datacontract() input type detection."""
from __future__ import annotations

import json

import pytest
import polars as pl

import mountainash as ma
from mountainash.typespec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.datacontracts.contract import BaseDataContract


class TestDatacontractFromTableSchema:
    def test_table_schema_compiles(self):
        spec = TableSchema(fields={"x": FieldDefinition(type=UniversalType.STRING)})
        Contract = ma.datacontract(spec)
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"x": ["a"]})
        Contract.validate_datacontract(df)


class TestDatacontractFromSimpleDict:
    def test_simple_dict_compiles(self):
        Contract = ma.datacontract({"name": "string", "age": "integer"})
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"name": ["a"], "age": [1]})
        Contract.validate_datacontract(df)


class TestDatacontractFromFrictionlessDict:
    def test_frictionless_dict_with_fields_key(self):
        descriptor = {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
            ]
        }
        Contract = ma.datacontract(descriptor)
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"id": [1], "name": ["a"]})
        Contract.validate_datacontract(df)


class TestDatacontractFromFrictionlessPath:
    def test_json_path_compiles(self, tmp_path):
        descriptor = {"fields": [{"name": "x", "type": "string"}]}
        path = tmp_path / "schema.json"
        path.write_text(json.dumps(descriptor))
        Contract = ma.datacontract(str(path))
        assert issubclass(Contract, BaseDataContract)

    def test_pathlib_path_compiles(self, tmp_path):
        descriptor = {"fields": [{"name": "x", "type": "string"}]}
        path = tmp_path / "schema.json"
        path.write_text(json.dumps(descriptor))
        Contract = ma.datacontract(path)
        assert issubclass(Contract, BaseDataContract)


class TestDatacontractFromPydantic:
    def test_pydantic_model_compiles(self):
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int

        Contract = ma.datacontract(User)
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"name": ["alice"], "age": [30]})
        Contract.validate_datacontract(df)


class TestDatacontractFromDataFrameModel:
    def test_existing_base_data_contract_returned_as_is(self):
        class MyContract(BaseDataContract):
            name: str = FieldDefinition(type=UniversalType.STRING)

        result = ma.datacontract(MyContract)
        assert result is MyContract

    def test_table_schema_source_round_trips_through_compiled_contract(self):
        # Replaces the removed Pandera-DataFrameModel-wrapping test: the
        # native entrypoint no longer accepts an arbitrary pa.DataFrameModel
        # source (no honest analogue — compile_datacontract/contract_from_table_schema
        # only understand TableSchema-shaped sources). The equivalent native
        # guarantee is that a TableSchema source compiles to a working contract
        # whose declared field survives the TableSchema round-trip.
        spec = TableSchema(fields={"name": FieldDefinition(type=UniversalType.STRING)})
        Contract = ma.datacontract(spec)
        assert issubclass(Contract, BaseDataContract)
        assert hasattr(Contract, "validate_datacontract")
        round_tripped = Contract.to_table_schema()
        assert list(round_tripped.fields) == ["name"]
        df = pl.DataFrame({"name": ["a"]})
        result = Contract.validate_datacontract(df)
        assert result.passes is True
