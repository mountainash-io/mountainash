"""Validator over the native runner: prepare/slice/context/rules/coerce."""
import polars as pl
import pytest

import mountainash as ma
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.field import Field
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.validator import Validator


class PersonContract(BaseDataContract):
    name: str
    age: int = Field(ge=0)

    class Config:
        coerce = False  # tests drive conform explicitly


class DatedPersonContract(PersonContract):
    """PersonContract plus the column the as-of contextual rule reads.

    Exact-mode conform requires the contract to declare every input column;
    a contextual rule's ``fields`` metadata is execution metadata, not a
    schema extension.
    """

    extract_date: str


def _rules():
    return RuleRegistry([
        Rule("age_under_150", expr=ma.col("age").lt(150)),
    ])


class TestFlow:
    def test_contract_and_rules_run_together(self):
        validator = Validator(name="people", contract=PersonContract, rules=_rules())
        df = pl.DataFrame({"name": ["a"], "age": [200]})
        result = validator.validate(df)
        ids = result.check_summaries["check_id"].to_list()
        assert "age_range" in ids
        assert "age_under_150" in ids
        assert result.passes is False  # 200 >= 150

    def test_context_flows_to_registry_and_result(self):
        rules = _rules()
        rules.exclude("age_under_150", when={"region": "test"})
        validator = Validator(name="people", contract=PersonContract, rules=rules)
        df = pl.DataFrame({"name": ["a"], "age": [200]})
        result = validator.validate(df, context={"region": "test"})
        # excluded rule surfaces as a skipped summary — visible, never run (spec §8/§9.6)
        skipped = result.check_summaries.filter(pl.col("status") == "skipped")
        assert skipped["check_id"].to_list() == ["age_under_150"]
        assert skipped["diagnostic"][0].startswith("excluded:")
        assert "age_under_150" not in result.failure_cases["check_id"].to_list()
        assert result.passes is True  # skipped never blocks; age_range passes (200 >= 0)
        assert result.context == {"region": "test"}  # 17 P3: one dict, both uses

    def test_only_when_gate_skips_with_reason(self):
        rules = _rules()
        rules.only_when("age_under_150", when={"batch_tier": {"C", "P"}})
        validator = Validator(name="people", contract=PersonContract, rules=rules)
        df = pl.DataFrame({"name": ["a"], "age": [200]})
        result = validator.validate(df, context={"batch_tier": "N"})
        skipped = result.check_summaries.filter(pl.col("status") == "skipped")
        assert skipped["check_id"].to_list() == ["age_under_150"]
        assert skipped["diagnostic"][0].startswith("not applicable:")
        included = validator.validate(df, context={"batch_tier": "C"})
        assert included.passes is False  # 200 >= 150: the gated rule ran and failed

    def test_declaration_errors_raise_before_prepare_runs(self):
        """spec §9.4: a broken gate surfaces before prepare's side effects."""
        from mountainash.validation.errors import CheckDeclarationError

        prepared = []

        def spy_prepare(data):
            prepared.append(True)
            return data

        rules = _rules()
        rules.exclude("age_under_150", when={"version": lambda v: v.boom})  # raising predicate
        validator = Validator(
            name="people", contract=PersonContract, rules=rules, prepare=spy_prepare
        )
        with pytest.raises(CheckDeclarationError):
            validator.validate(pl.DataFrame({"name": ["a"], "age": [1]}),
                               context={"version": "0300"})
        assert prepared == []  # declaration phase failed before any data was touched

    def test_duplicate_check_id_across_contract_and_rules_raises(self):
        from mountainash.validation.errors import CheckDeclarationError

        rules = RuleRegistry([Rule("age_range", expr=ma.col("age").ge(0))])  # collides with Field check id
        validator = Validator(name="people", contract=PersonContract, rules=rules)
        with pytest.raises(CheckDeclarationError, match="duplicate check id"):
            validator.validate(pl.DataFrame({"name": ["a"], "age": [1]}))

    def test_as_of_contextual_rule_is_deterministic_end_to_end(self):
        """spec §6.5: same data + same pinned as_of -> identical results, twice."""
        from datetime import datetime, timezone

        from mountainash.datacontracts.rule import ContextualRule
        from mountainash.validation.checks import require_as_of

        rules = RuleRegistry([ContextualRule(
            "not_future",
            build=lambda ctx: ma.col("extract_date")
                .str.to_datetime("%Y-%m-%dT%H:%M:%S")
                .le(ma.lit(require_as_of(ctx).replace(tzinfo=None))),
            fields=["extract_date"],
        )])
        validator = Validator(name="people", contract=DatedPersonContract, rules=rules)
        df = pl.DataFrame({
            "name": ["a", "b"], "age": [1, 2],
            "extract_date": ["2026-07-01T00:00:00", "2026-08-01T00:00:00"],
        })
        as_of = datetime(2026, 7, 10, tzinfo=timezone.utc)
        first = validator.validate(df, context={"as_of": as_of})
        second = validator.validate(df, context={"as_of": as_of})
        for result in (first, second):
            assert result.passes is False  # the August row is in the future
            row = result.check_summaries.filter(pl.col("check_id") == "not_future")
            assert row["fail_count"][0] == 1
        assert first.failure_cases.equals(second.failure_cases)

    def test_prepare_plain_signature(self):
        validator = Validator(
            name="people", contract=PersonContract,
            prepare=lambda data: data.with_columns(pl.col("age") + 1),
        )
        result = validator.validate(pl.DataFrame({"name": ["a"], "age": [-1]}))
        assert result.passes  # -1 + 1 = 0 passes age__ge

    def test_prepare_context_signature(self):
        def prepare(data, context=None):
            offset = (context or {}).get("offset", 0)
            return data.with_columns(pl.col("age") + offset)

        validator = Validator(name="people", contract=PersonContract, prepare=prepare)
        result = validator.validate(
            pl.DataFrame({"name": ["a"], "age": [-5]}), context={"offset": 5}
        )
        assert result.passes  # 17 P6: prepare(data, context=...)

    def test_slice_head_applies_once(self):
        validator = Validator(name="people", contract=PersonContract)
        df = pl.DataFrame({"name": ["a", "b"], "age": [1, -1]})
        result = validator.validate(df, head=1)
        assert result.passes  # the failing row was sliced away
        assert result.check_summaries["total_rows"][0] == 1

    def test_quick_same_shape_fewer_rows(self):
        validator = Validator(name="people", contract=PersonContract, rules=_rules())
        df = pl.DataFrame({"name": ["a"], "age": [-1]})
        full = validator.validate(df)
        quick = validator.validate_quick(df)
        assert list(full.check_summaries.columns) == list(quick.check_summaries.columns)
        assert list(full.failure_cases.columns) == list(quick.failure_cases.columns)

    def test_processor_attached_on_failure_with_sliced_source(self):
        validator = Validator(
            name="people", contract=PersonContract, natural_key=["name"]
        )
        df = pl.DataFrame({"name": ["a", "b"], "age": [1, -1]})
        result = validator.validate(df)
        assert result.processor is not None
        assert result.processor.passed() is False
        passing = validator.validate(pl.DataFrame({"name": ["a"], "age": [1]}))
        assert passing.processor is None


class CoercingContract(BaseDataContract):
    age: int = Field(ge=0)

    class Config:
        coerce = True


def test_coerce_conforms_before_checks():
    # string "5" conforms to int 5 before the ge check runs (vision Phase 2 seed)
    result = CoercingContract.validate_datacontract(pl.DataFrame({"age": ["5"]}))
    assert result.passes
