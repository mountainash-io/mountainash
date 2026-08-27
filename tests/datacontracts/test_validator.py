"""Tests for Validator — unified validation orchestrator."""
from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma

from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.field import Field
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.result import ValidationResult


class TestValidatorContractOnly:
    """Validator with contract but no rules — column-level validation only."""

    def test_valid_data_passes(self, person_contract, valid_person_df):
        v = Validator(name="person", contract=person_contract)
        result = v.validate(valid_person_df)
        assert isinstance(result, ValidationResult)
        assert result.passes is True

    def test_invalid_data_fails(self, person_contract):
        df = pl.DataFrame({"name": ["a"], "age": [-1], "email": [None]})
        v = Validator(name="person", contract=person_contract)
        result = v.validate(df)
        assert result.passes is False
        assert result.processor is not None
        assert result.processor.failure_count() > 0

    def test_validator_name_in_result(self, person_contract, valid_person_df):
        v = Validator(name="my_validator", contract=person_contract)
        result = v.validate(valid_person_df)
        assert result.validator_name == "my_validator"


def test_coerce_false_still_applies_structural_conform():
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    class Contract(BaseDataContract):
        value: str = Field(str_matches="^.+$")

        class Config(BaseDataContract.Config):
            coerce = False

    Contract.__typespec__ = TypeSpec(
        fields=[
            FieldSpec(
                name="value",
                type=UniversalType.INTEGER,
                rename_from="raw_value",
            )
        ],
        fields_match="open",
    )

    result = Validator(
        name="contract",
        contract=Contract,
    ).validate(pl.DataFrame({"raw_value": ["1"]}))

    assert result.passes is False
    assert result._materialized_source.to_dict(as_series=False) == {"value": ["1"]}
    assert result.check_summaries["check_id"].to_list() == ["value_type_format"]


@pytest.mark.parametrize(
    "fields_match",
    ["open", "exact", "equal", "subset", "superset", "partial"],
)
@pytest.mark.parametrize("coerce", [True, False])
def test_validator_conforms_all_fields_match_modes(fields_match, coerce):
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    class Contract(BaseDataContract):
        value: object = Field()

        class Config(BaseDataContract.Config):
            pass

    Contract.Config.coerce = coerce
    Contract.__typespec__ = TypeSpec(
        fields=[FieldSpec(name="value", type=UniversalType.INTEGER)],
        fields_match=fields_match,
    )
    source = {"value": ["1"]}
    if fields_match in {"open", "subset", "partial"}:
        source["extra"] = [1]

    result = Validator(name="contract", contract=Contract).validate(
        pl.DataFrame(source),
    )

    assert result.passes is coerce
    assert result._materialized_source["value"].to_list() == (
        [1] if coerce else ["1"]
    )




class TestValidatorWithRules:
    """Validator with contract + expression-based rules."""

    def test_rules_applied_and_checked(self, person_contract, person_rules):
        df = pl.DataFrame({"name": ["alice"], "age": [200], "email": [None]})
        v = Validator(name="person", contract=person_contract, rules=person_rules)
        result = v.validate(df)
        assert result.passes is False
        assert result.processor.passed_for_rule("age_under_150") is False

    def test_all_rules_pass(self, person_contract, person_rules, valid_person_df):
        v = Validator(name="person", contract=person_contract, rules=person_rules)
        result = v.validate(valid_person_df)
        assert result.passes is True

    def test_contract_not_mutated_by_rules(self, person_contract, person_rules, valid_person_df):
        v = Validator(name="person", contract=person_contract, rules=person_rules)
        v.validate(valid_person_df)
        # The original contract class should have no _check_ methods
        check_methods = [m for m in dir(person_contract) if m.startswith("_check_")]
        assert len(check_methods) == 0


class TestValidatorContextExclusions:
    """Rules excluded by context are not applied."""

    def test_excluded_rule_not_checked(self, person_contract):
        rules = RuleRegistry([
            Rule("strict_age", expr=ma.col("age").lt(50)),
        ])
        rules.exclude("strict_age", when={"mode": "lenient"})
        v = Validator(name="person", contract=person_contract, rules=rules)
        df = pl.DataFrame({"name": ["a"], "age": [100], "email": [None]})

        # Without exclusion context — rule applies, fails
        result = v.validate(df)
        assert result.passes is False

        # With exclusion context — rule excluded, passes
        result = v.validate(df, context={"mode": "lenient"})
        assert result.passes is True


class TestValidatorPrepare:
    """Validator with prepare callable for multi-source data."""

    def test_prepare_called_with_data(self, person_contract):
        called_with = []

        def my_prepare(data):
            called_with.append(data)
            return data["people"]

        v = Validator(name="person", contract=person_contract, prepare=my_prepare)
        data = {"people": pl.DataFrame({"name": ["a"], "age": [30], "email": [None]})}
        result = v.validate(data)
        assert result.passes is True
        assert len(called_with) == 1

    def test_prepare_not_called_when_none(self, person_contract, valid_person_df):
        v = Validator(name="person", contract=person_contract)
        result = v.validate(valid_person_df)
        assert result.passes is True


class TestValidatorQuick:
    """validate_quick fails on first error."""

    def test_quick_validation_passes(self, person_contract, valid_person_df):
        v = Validator(name="person", contract=person_contract)
        result = v.validate_quick(valid_person_df)
        assert result.passes is True

    def test_quick_validation_fails(self, person_contract):
        df = pl.DataFrame({"name": ["a"], "age": [-1], "email": [None]})
        v = Validator(name="person", contract=person_contract)
        result = v.validate_quick(df)
        assert result.passes is False


class TestValidatorPandasInput:
    """Validator accepts pandas DataFrames."""

    def test_pandas_input(self, person_contract):
        import pandas as pd
        pdf = pd.DataFrame({"name": ["a", "b"], "age": [10, 20], "email": ["x", None]})
        v = Validator(name="person", contract=person_contract)
        result = v.validate(pdf)
        assert result.passes is True


class TestValidatorProcessorWiring:

    def test_processor_receives_validator_name(self):

        class SimpleContract(BaseDataContract):
            age: int = Field(ge=0)

        validator = Validator(name="test_v", contract=SimpleContract)
        df = pl.DataFrame({"age": [-1, 5, 10]})
        result = validator.validate(df)
        assert result.passes is False
        assert result.processor is not None
        assert result.processor._validator_name == "test_v"

    def test_processor_receives_natural_key(self):

        class SimpleContract(BaseDataContract):
            age: int = Field(ge=0)

        validator = Validator(
            name="test_v", contract=SimpleContract, natural_key=["age"],
        )
        df = pl.DataFrame({"age": [-1, 5, 10]})
        result = validator.validate(df)
        assert result.processor is not None
        assert result.processor._natural_key == ["age"]

    def test_processor_receives_source_data(self):

        class SimpleContract(BaseDataContract):
            age: int = Field(ge=0)

        validator = Validator(name="test_v", contract=SimpleContract)
        df = pl.DataFrame({"age": [-1, 5, 10]})
        result = validator.validate(df)
        assert result.processor is not None
        assert result.processor._source_data is not None
        assert len(result.processor._source_data) == 3

    def test_processor_source_data_reflects_head_slice(self):

        class SimpleContract(BaseDataContract):
            age: int = Field(ge=0)

        validator = Validator(name="test_v", contract=SimpleContract)
        df = pl.DataFrame({"age": [-1, -2, -3, -4, -5]})
        result = validator.validate(df, head=2)
        assert result.processor is not None
        assert len(result.processor._source_data) == 2

class TestSeededSlice:
    """Seeded validation slices stay on backend and avoid vacuous passes."""

    def _contract(self):
        from mountainash.typespec.spec import FieldConstraints, FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import parse_universal

        spec = TypeSpec(fields=[
            FieldSpec(
                name="a",
                type=parse_universal("integer"),
                constraints=FieldConstraints(minimum=0),
            ),
        ])
        return spec.to_contract(name="seeded_slice")

    def test_empty_sample_slice_falls_back_and_records_diagnostics(self, monkeypatch):
        from mountainash.relations import Relation

        def empty_sample(self, *, n=None, fraction=None, seed=None):
            return self.head(0)

        monkeypatch.setattr(Relation, "sample", empty_sample)
        df = pl.DataFrame({"a": list(range(20))})
        result = self._contract().validate_datacontract(df, sample=5, random_seed=1)
        assert "sample_fallback" in result.diagnostics
        assert result.diagnostics["sample_fallback"]["requested_sample"] == 5
        totals = [
            summary["total_rows"]
            for summary in result.check_summaries.to_dicts()
            if summary["total_rows"] is not None
        ]
        assert totals and all(total == 5 for total in totals)

    def test_implicit_fallback_records_effective_seed(self, monkeypatch):
        from mountainash.datacontracts import validator as validator_module
        from mountainash.relations import Relation

        monkeypatch.setattr(validator_module.random, "randrange", lambda _: 12345)
        monkeypatch.setattr(Relation, "sample", lambda self, **_: self.head(0))
        result = self._contract().validate_datacontract(
            pl.DataFrame({"a": list(range(20))}), sample=5
        )
        assert result.diagnostics["sample_fallback"]["random_seed"] == 12345

    @pytest.mark.parametrize("backend", ["polars", "pandas", "ibis-duckdb"])
    def test_seeded_validate_is_deterministic(self, backend):
        df = pl.DataFrame({"a": [i - 10 for i in range(100)]})
        if backend == "pandas":
            data = df.to_pandas()
        elif backend == "ibis-duckdb":
            ibis = pytest.importorskip("ibis")
            data = ibis.duckdb.connect().create_table("t", df.to_arrow())
        else:
            data = df
        contract = self._contract()
        first = contract.validate_datacontract(data, sample=20, random_seed=7)
        second = contract.validate_datacontract(data, sample=20, random_seed=7)
        assert first.passes == second.passes
        assert first.check_summaries.drop("elapsed").to_dicts() == second.check_summaries.drop("elapsed").to_dicts()
        assert first.failure_cases.to_dicts() == second.failure_cases.to_dicts()

    def test_never_validates_empty_slice_silently_on_ibis(self):
        ibis = pytest.importorskip("ibis")
        con = ibis.duckdb.connect()
        table = con.create_table("t", pl.DataFrame({"a": list(range(30))}).to_arrow())
        contract = self._contract()
        for seed in range(8):
            result = contract.validate_datacontract(table, sample=1, random_seed=seed)
            totals = [
                summary["total_rows"]
                for summary in result.check_summaries.to_dicts()
                if summary["total_rows"] is not None
            ]
            assert any(total > 0 for total in totals) or "sample_fallback" in result.diagnostics
