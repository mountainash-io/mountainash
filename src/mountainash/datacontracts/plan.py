"""ValidationPlan — sequential multi-validator orchestration (spec §9.5).

The non-DAG orchestration peer to RelationDAG.validate(): same runner,
same ValidationResult per step (17 P2). Parallel execution deferred.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from mountainash.datacontracts.validator import Validator
    from mountainash.validation.result import ValidationResult

_SUMMARY_SCHEMA = {
    "step": pl.String,
    "passes": pl.Boolean,
    "fail_count": pl.Int64,
    "elapsed": pl.Float64,
}


@dataclass
class PlanResult:
    passes: bool
    results: "dict[str, ValidationResult]"
    summary: pl.DataFrame  # step, passes, fail_count, elapsed


class ValidationPlan:
    """Named sequence of (step_name, validator, data) validations."""

    def __init__(
        self,
        *,
        name: str,
        steps: "list[tuple[str, Validator, Any]]",
        context: "dict[str, Any] | None" = None,
        fail_fast: bool = False,
    ) -> None:
        self.name = name
        self.steps = list(steps)
        self.context = context
        self.fail_fast = fail_fast
        if not self.steps:
            raise ValueError("ValidationPlan requires at least one step")
        seen: set[str] = set()
        for step_name, _validator, _data in self.steps:
            if step_name in seen:
                raise ValueError(f"duplicate step name: {step_name!r}")
            seen.add(step_name)

    def execute(self) -> PlanResult:
        results: "dict[str, ValidationResult]" = {}
        rows: list[dict[str, Any]] = []
        for step_name, validator, data in self.steps:
            start = time.perf_counter()
            result = validator.validate(data, context=self.context)
            elapsed = time.perf_counter() - start
            results[step_name] = result
            fail_count = result.check_summaries["fail_count"].sum()
            rows.append(
                {
                    "step": step_name,
                    "passes": result.passes,
                    "fail_count": int(fail_count) if fail_count is not None else 0,
                    "elapsed": elapsed,
                }
            )
            if self.fail_fast and not result.passes:
                break
        summary = pl.DataFrame(rows, schema=_SUMMARY_SCHEMA)
        return PlanResult(
            passes=all(r.passes for r in results.values()),
            results=results,
            summary=summary,
        )
