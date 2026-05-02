"""Tests for compile_datacontract — TypeSpec to pandera DataFrameModel."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa

from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.datacontracts.contract import BaseDataContract


def _make_spec(*fields: FieldSpec) -> TypeSpec:
    return TypeSpec(fields=list(fields))


class TestCompileDatacontract:

    def test_basic_string_field(self):
        spec = _make_spec(FieldSpec(name="name", type=UniversalType.STRING))
        Contract = compile_datacontract(spec)
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"name": ["alice", "bob"]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2

    def test_integer_field(self):
        spec = _make_spec(FieldSpec(name="age", type=UniversalType.INTEGER))
        Contract = compile_datacontract(spec)
        df = pl.DataFrame({"age": [25, 30]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2

    def test_custom_name(self):
        spec = _make_spec(FieldSpec(name="x", type=UniversalType.STRING))
        Contract = compile_datacontract(spec, name="MyContract")
        assert Contract.__name__ == "MyContract"

    def test_default_name_from_spec_title(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.STRING)],
            title="AccountSchema",
        )
        Contract = compile_datacontract(spec)
        assert Contract.__name__ == "AccountSchema"

    def test_nullable_from_required_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="email",
                type=UniversalType.STRING,
                constraints=FieldConstraints(required=True),
            ),
        )
        Contract = compile_datacontract(spec)
        df_with_null = pl.DataFrame({"email": [None, "a@b.com"]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_with_null)

    def test_ge_from_minimum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="age",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(minimum=0),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"age": [-1, 5]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_le_from_maximum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="score",
                type=UniversalType.NUMBER,
                constraints=FieldConstraints(maximum=100.0),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"score": [50.0, 150.0]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_isin_from_enum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="status",
                type=UniversalType.STRING,
                constraints=FieldConstraints(enum=["active", "inactive"]),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"status": ["active", "deleted"]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_pattern_from_pattern_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="code",
                type=UniversalType.STRING,
                constraints=FieldConstraints(pattern=r"^[A-Z]{3}$"),
            ),
        )
        Contract = compile_datacontract(spec)
        df_good = pl.DataFrame({"code": ["ABC", "XYZ"]})
        result = Contract.validate_datacontract(df_good)
        assert len(result) == 2
        df_bad = pl.DataFrame({"code": ["abc", "XY"]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_unique_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="id",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(unique=True),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"id": [1, 1, 2]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_multiple_fields(self):
        spec = _make_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER, constraints=FieldConstraints(required=True, minimum=1)),
            FieldSpec(name="name", type=UniversalType.STRING),
            FieldSpec(name="score", type=UniversalType.NUMBER),
        )
        Contract = compile_datacontract(spec)
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2

    def test_no_constraints_produces_nullable_field(self):
        spec = _make_spec(FieldSpec(name="val", type=UniversalType.STRING))
        Contract = compile_datacontract(spec)
        df = pl.DataFrame({"val": [None, "x"]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2
