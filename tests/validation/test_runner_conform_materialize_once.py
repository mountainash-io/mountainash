"""Regression: the runner materialises the conformed plan ONCE per validate.

Item 56 — before the fix, ``ValidationRunner.validate_relation`` kept the
``rel.conform(spec)`` plan lazy and every check re-collected it, so the whole
contract conform re-compiled once *per check* (cost O(checks × contract_fields)).
The runner now collapses the plan to a concrete frame once, up front, so conform
runs exactly once regardless of how many checks execute.

These are closed-by-default guards: if per-check re-collection ever regresses,
``_build_conform_exprs`` is invoked once per check again and the ``== 1``
assertions fail loudly (the call count scales with the number of checks).
"""
import polars as pl

import mountainash as ma
import mountainash.conform.expressions as conform_exprs
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.field import Field
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.validator import Validator
from mountainash.typespec import FieldSpec, TypeSpec
from mountainash.validation import RowRule, ValidationRunner


class WideContract(BaseDataContract):
    a: str = Field(nullable=True)
    b: str = Field(nullable=True)
    c: str = Field(nullable=True)
    d: str = Field(nullable=True)


def _many_rules(n: int) -> RuleRegistry:
    cols = ["a", "b", "c", "d"]
    return RuleRegistry(
        [
            Rule(f"len_{i}", expr=ma.col(cols[i % len(cols)]).str.len_chars().gt(0))
            for i in range(n)
        ]
    )


def _count_conform_builds(monkeypatch) -> "list[int]":
    calls = {"n": 0}
    original = conform_exprs._build_conform_exprs

    def counted(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    # the visitor re-imports this symbol from the source module on each call
    # (function-local ``from mountainash.conform.expressions import ...``), so
    # patching it at the source is what the visitor actually resolves.
    monkeypatch.setattr(conform_exprs, "_build_conform_exprs", counted)
    return calls


def test_conform_compiles_once_regardless_of_check_count(monkeypatch):
    calls = _count_conform_builds(monkeypatch)
    validator = Validator(name="wide", contract=WideContract, rules=_many_rules(12))
    df = pl.DataFrame({c: ["x", "yy", "zzz"] for c in ("a", "b", "c", "d")})

    result = validator.validate(df, context={})

    # one conform node in the plan -> compiled exactly once, not once per check
    assert calls["n"] == 1, (
        f"conform re-compiled {calls['n']}× for 12 checks + 4 field checks — "
        "per-check re-collection has regressed (item 56)"
    )
    assert result.passes is True


def test_conform_once_is_independent_of_check_count(monkeypatch):
    # Same contract, far more checks: the conform build count must NOT scale.
    calls = _count_conform_builds(monkeypatch)
    validator = Validator(name="wide", contract=WideContract, rules=_many_rules(40))
    df = pl.DataFrame({c: ["x", "yy", "zzz"] for c in ("a", "b", "c", "d")})

    validator.validate(df, context={})

    assert calls["n"] == 1, (
        f"conform re-compiled {calls['n']}× — build count scales with checks "
        "(item 56 regression)"
    )


def test_upfront_materialize_failure_honours_isolation_contract():
    """A conform/cast failure in the one-shot materialize must degrade to
    ``status="error"`` for EVERY check (spec §6.5) — never raise out of the
    runner. Item 56 moved materialisation ahead of the per-check loop, so this
    guards that the isolation contract still holds for that upfront collect.
    """
    # spec forces "n" -> integer, but the data is non-numeric: conform's strict
    # cast fails when the plan materialises.
    spec = TypeSpec(fields=[FieldSpec(name="n", type="integer")])
    df = pl.DataFrame({"n": ["not-a-number", "also-bad"]})
    rel = ma.relation(df).conform(spec)
    checks = [
        RowRule(id="n_ge_0", expr=ma.col("n").ge(0)),
        RowRule(id="n_lt_100", expr=ma.col("n").lt(100)),
    ]

    # must NOT raise
    result = ValidationRunner().validate_relation(rel, checks, context={})

    assert result.passes is False
    rows = {r["check_id"]: r for r in result.check_summaries.to_dicts()}
    # every check is present and errored — siblings not dropped
    assert set(rows) == {"n_ge_0", "n_lt_100"}
    assert all(rows[cid]["status"] == "error" for cid in rows)
    assert all(rows[cid]["error"] for cid in rows)
