"""Tests for contract_from_typespec — TypeSpec to native BaseDataContract."""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.datacontracts.compiler import contract_from_typespec
from mountainash.datacontracts.contract import BaseDataContract


def _make_spec(*fields: FieldSpec) -> TypeSpec:
    return TypeSpec(fields=list(fields))


def _failing_check_ids(result) -> list[str]:
    return result.check_summaries.filter(
        result.check_summaries["status"] != "passed"
    )["check_id"].to_list()


class TestCompileDatacontract:

    def test_basic_string_field(self):
        spec = _make_spec(FieldSpec(name="name", type=UniversalType.STRING))
        Contract = contract_from_typespec(spec)
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"name": ["alice", "bob"]})
        result = Contract.validate_datacontract(df)
        assert result.passes is True

    def test_integer_field(self):
        spec = _make_spec(FieldSpec(name="age", type=UniversalType.INTEGER))
        Contract = contract_from_typespec(spec)
        df = pl.DataFrame({"age": [25, 30]})
        result = Contract.validate_datacontract(df)
        assert result.passes is True

    def test_custom_name(self):
        spec = _make_spec(FieldSpec(name="x", type=UniversalType.STRING))
        Contract = contract_from_typespec(spec, name="MyContract")
        assert Contract.__name__ == "MyContract"

    def test_default_name_from_spec_title(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.STRING)],
            title="AccountSchema",
        )
        Contract = contract_from_typespec(spec)
        assert Contract.__name__ == "AccountSchema"

    def test_nullable_from_required_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="email",
                type=UniversalType.STRING,
                constraints=FieldConstraints(required=True),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_with_null = pl.DataFrame({"email": [None, "a@b.com"]})
        result = Contract.validate_datacontract(df_with_null)
        assert result.passes is False
        assert "email__not_null" in _failing_check_ids(result)

    def test_ge_from_minimum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="age",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(minimum=0),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_bad = pl.DataFrame({"age": [-1, 5]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "age__ge" in _failing_check_ids(result)

    def test_le_from_maximum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="score",
                type=UniversalType.NUMBER,
                constraints=FieldConstraints(maximum=100.0),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_bad = pl.DataFrame({"score": [50.0, 150.0]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "score__le" in _failing_check_ids(result)

    def test_isin_from_enum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="status",
                type=UniversalType.STRING,
                constraints=FieldConstraints(enum=["active", "inactive"]),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_bad = pl.DataFrame({"status": ["active", "deleted"]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "status__isin" in _failing_check_ids(result)

    def test_pattern_from_pattern_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="code",
                type=UniversalType.STRING,
                constraints=FieldConstraints(pattern=r"^[A-Z]{3}$"),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_good = pl.DataFrame({"code": ["ABC", "XYZ"]})
        result = Contract.validate_datacontract(df_good)
        assert result.passes is True
        df_bad = pl.DataFrame({"code": ["abc", "XY"]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "code__pattern" in _failing_check_ids(result)

    def test_unique_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="id",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(unique=True),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_bad = pl.DataFrame({"id": [1, 1, 2]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "id__unique" in _failing_check_ids(result)

    def test_multiple_fields(self):
        spec = _make_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER, constraints=FieldConstraints(required=True, minimum=1)),
            FieldSpec(name="name", type=UniversalType.STRING),
            FieldSpec(name="score", type=UniversalType.NUMBER),
        )
        Contract = contract_from_typespec(spec)
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        result = Contract.validate_datacontract(df)
        assert result.passes is True

    def test_isin_from_categories_plain_values(self):
        spec = _make_spec(
            FieldSpec(
                name="status",
                type=UniversalType.STRING,
                categories=["active", "cancelled", "pending"],
            ),
        )
        Contract = contract_from_typespec(spec)
        df_good = pl.DataFrame({"status": ["active", "pending"]})
        result = Contract.validate_datacontract(df_good)
        assert result.passes is True
        df_bad = pl.DataFrame({"status": ["active", "unknown"]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "status__isin" in _failing_check_ids(result)

    def test_isin_from_categories_value_label_dicts(self):
        spec = _make_spec(
            FieldSpec(
                name="code",
                type=UniversalType.STRING,
                categories=[
                    {"value": "a", "label": "Active"},
                    {"value": "c", "label": "Cancelled"},
                ],
            ),
        )
        Contract = contract_from_typespec(spec)
        df_good = pl.DataFrame({"code": ["a", "c"]})
        result = Contract.validate_datacontract(df_good)
        assert result.passes is True
        df_bad = pl.DataFrame({"code": ["a", "z"]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "code__isin" in _failing_check_ids(result)

    def test_enum_constraint_takes_precedence_over_categories(self):
        spec = _make_spec(
            FieldSpec(
                name="tier",
                type=UniversalType.STRING,
                categories=["a", "b", "c"],
                constraints=FieldConstraints(enum=["x", "y"]),
            ),
        )
        Contract = contract_from_typespec(spec)
        df_good = pl.DataFrame({"tier": ["x", "y"]})
        result = Contract.validate_datacontract(df_good)
        assert result.passes is True
        df_bad = pl.DataFrame({"tier": ["a", "x"]})
        result = Contract.validate_datacontract(df_bad)
        assert result.passes is False
        assert "tier__isin" in _failing_check_ids(result)

    def test_no_constraints_produces_nullable_field(self):
        spec = _make_spec(FieldSpec(name="val", type=UniversalType.STRING))
        Contract = contract_from_typespec(spec)
        df = pl.DataFrame({"val": [None, "x"]})
        result = Contract.validate_datacontract(df)
        assert result.passes is True

class TestPatternCheckCrossBackend:
    """Pattern checks must fail on non-matching values on every backend."""

    def _spec(self):
        return _make_spec(
            FieldSpec(
                name="code",
                type=UniversalType.STRING,
                constraints=FieldConstraints(pattern=r"^[a-z]{3}-[0-9]{2}$"),
            )
        )

    def _data(self, backend, values):
        df = pl.DataFrame({"code": values})
        if backend == "narwhals-pandas":
            import narwhals as nw

            return nw.from_native(df.to_pandas())
        if backend == "ibis-duckdb":
            ibis = pytest.importorskip("ibis")

            return ibis.duckdb.connect().create_table("t", df.to_arrow())
        return df

    @pytest.mark.parametrize("backend", ["polars", "narwhals-pandas", "ibis-duckdb"])
    def test_non_matching_value_fails(self, backend):
        result = self._spec().to_contract(name="pattern_xb").validate_datacontract(
            self._data(backend, ["abc-12", "###"])
        )
        assert not result.passes
        assert "code__pattern" in _failing_check_ids(result)

    @pytest.mark.parametrize("backend", ["polars", "narwhals-pandas", "ibis-duckdb"])
    def test_matching_values_pass(self, backend):
        result = self._spec().to_contract(name="pattern_xb").validate_datacontract(
            self._data(backend, ["abc-12", "xyz-99"])
        )
        assert result.passes
