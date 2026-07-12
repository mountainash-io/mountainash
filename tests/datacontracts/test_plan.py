"""ValidationPlan: sequential multi-validator orchestration (spec §9.5)."""
import polars as pl
import pytest

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.field import Field
from mountainash.datacontracts.plan import PlanResult, ValidationPlan
from mountainash.datacontracts.validator import Validator


class BatchContract(BaseDataContract):
    batch_id: str = Field(nullable=False)

    class Config:
        coerce = False


class AccountContract(BaseDataContract):
    account_id: int = Field(nullable=False, ge=1)

    class Config:
        coerce = False


def _plan(batch_df, accounts_df, **kwargs):
    return ValidationPlan(
        name="report-batch",
        steps=[
            ("batch", Validator(name="batch", contract=BatchContract), batch_df),
            ("accounts", Validator(name="accounts", contract=AccountContract), accounts_df),
        ],
        **kwargs,
    )


def test_all_steps_pass():
    result = _plan(
        pl.DataFrame({"batch_id": ["b1"]}),
        pl.DataFrame({"account_id": [1, 2]}),
    ).execute()
    assert isinstance(result, PlanResult)
    assert result.passes
    assert set(result.results) == {"batch", "accounts"}
    assert result.summary.columns == ["step", "passes", "fail_count", "elapsed"]
    assert result.summary["passes"].to_list() == [True, True]


def test_failing_step_reported_individually():
    result = _plan(
        pl.DataFrame({"batch_id": ["b1"]}),
        pl.DataFrame({"account_id": [0]}),  # fails ge=1
    ).execute()
    assert result.passes is False
    assert result.results["batch"].passes is True
    assert result.results["accounts"].passes is False
    by_step = dict(zip(result.summary["step"].to_list(), result.summary["fail_count"].to_list()))
    assert by_step["accounts"] == 1


def test_fail_fast_stops_at_first_failing_step():
    result = _plan(
        pl.DataFrame({"batch_id": [None]}),   # fails not_null
        pl.DataFrame({"account_id": [1]}),
        fail_fast=True,
    ).execute()
    assert result.passes is False
    assert list(result.results) == ["batch"]  # accounts never ran
    assert result.summary.height == 1


def test_context_flows_to_every_validator():
    plan = _plan(
        pl.DataFrame({"batch_id": ["b1"]}),
        pl.DataFrame({"account_id": [1]}),
        context={"batch_id": "2026010100001"},
    )
    result = plan.execute()
    assert result.results["batch"].context == {"batch_id": "2026010100001"}
    assert result.results["accounts"].context == {"batch_id": "2026010100001"}


def test_duplicate_step_names_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        ValidationPlan(
            name="p",
            steps=[
                ("s", Validator(name="a", contract=BatchContract), None),
                ("s", Validator(name="b", contract=BatchContract), None),
            ],
        )
