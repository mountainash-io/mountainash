"""Tests for Validator — unified validation orchestrator."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa
import mountainash as ma

from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.rule import Rule, guarded
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
