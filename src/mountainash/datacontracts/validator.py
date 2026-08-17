"""Validator — orchestrates prepare -> slice once -> resolve -> ValidationRunner.

No Pandera. validate_quick() is validate() with fail_fast=True: identical
result shapes by construction (spec §6.5, item 18 subsumed).
"""
from __future__ import annotations

import inspect
import random
from typing import TYPE_CHECKING, Any, Callable

import polars as pl

from mountainash.validation.checks import classify
from mountainash.validation.errors import CheckDeclarationError
from mountainash.validation.identity import resolve_identity
from mountainash.validation.result import (
    CheckSummary,
    ValidationResult,
    summaries_frame,
)
from mountainash.validation.runner import ValidationRunner

if TYPE_CHECKING:
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.datacontracts.registry import RuleRegistry


class Validator:
    """Unified validation orchestrator binding contract + rules + data."""

    def __init__(
        self,
        *,
        name: str,
        contract: "type[BaseDataContract]",
        rules: "RuleRegistry | None" = None,
        natural_key: "list[str] | None" = None,
        prepare: "Callable[..., Any] | None" = None,
    ) -> None:
        self.name = name
        self.contract = contract
        self.rules = rules
        self.natural_key = natural_key
        self.prepare = prepare

    # -- pipeline pieces ------------------------------------------------------

    def _prepare_data(self, data: Any, context: "dict[str, Any] | None") -> Any:
        """17 P6: prepare(data) or prepare(data, context=...) by signature."""
        if self.prepare is None:
            return data
        signature = inspect.signature(self.prepare)
        if "context" in signature.parameters:
            return self.prepare(data, context=context)
        return self.prepare(data)

    @staticmethod
    def _to_polars_frame(rel: Any) -> pl.DataFrame:
        materialised = rel.to_polars()
        if isinstance(materialised, pl.LazyFrame):
            materialised = materialised.collect()
        return materialised
    @classmethod
    def _slice(
        cls,
        rel: Any,
        *,
        head: int | None,
        tail: int | None,
        sample: int | None,
        random_seed: int | None,
    ) -> tuple[Any, dict[str, Any]]:
        """Apply slicing once, keeping seeded sampling on the source backend."""
        diagnostics: dict[str, Any] = {}
        if head is not None:
            rel = rel.head(head)
        if tail is not None:
            rel = rel.tail(tail)
        if sample is not None:
            effective_seed = (
                random_seed if random_seed is not None else random.randrange(2**31)
            )
            sampled = rel.sample(n=sample, seed=effective_seed)
            if sampled.count_rows() == 0 and rel.count_rows() > 0:
                rel = rel.limit(sample)
                diagnostics["sample_fallback"] = {
                    "reason": "sampled slice was empty on non-empty input",
                    "requested_sample": sample,
                    "random_seed": random_seed,
                    "fallback": f"limit({sample})",
                }
            else:
                rel = sampled
        return rel, diagnostics

    # -- public API -----------------------------------------------------------

    def validate(
        self,
        data: Any,
        *,
        context: "dict[str, Any] | None" = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
        row_identity: str | None = None,
        allow_imperfect_key: bool = False,
        failure_sample: int | None = None,
    ) -> ValidationResult:
        """Full validation — collects all check results."""
        return self._run(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed, fail_fast=False, row_identity=row_identity,
            allow_imperfect_key=allow_imperfect_key, failure_sample=failure_sample,
        )

    def validate_quick(
        self,
        data: Any,
        *,
        context: "dict[str, Any] | None" = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
        row_identity: str | None = None,
        allow_imperfect_key: bool = False,
        failure_sample: int | None = None,
    ) -> ValidationResult:
        """Quick validation — same runner, fail_fast=True. Identical shapes."""
        return self._run(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed, fail_fast=True, row_identity=row_identity,
            allow_imperfect_key=allow_imperfect_key, failure_sample=failure_sample,
        )

    def _run(
        self, data: Any, *, context: "dict[str, Any] | None",
        head: int | None, tail: int | None, sample: int | None,
        random_seed: int | None, fail_fast: bool, row_identity: str | None,
        allow_imperfect_key: bool, failure_sample: int | None,
    ) -> ValidationResult:
        import mountainash as ma
        from mountainash.datacontracts.result_processor import ValidationResultProcessor
        from mountainash.relations import Relation

        # --- declaration phase (spec §9.4): strictly BEFORE any data is
        # touched — a bad gate, predicate, as_of, contextual builder, or
        # duplicate id must surface before prepare's side effects run
        spec = self.contract.to_typespec()
        natural_key = self.natural_key or getattr(self.contract.Config, "natural_key", None)
        identity = resolve_identity(
            natural_key=natural_key, spec=spec, row_identity=row_identity
        )

        checks: list[Any] = list(self.contract.to_checks())
        skipped: list[CheckSummary] = []
        if self.rules is not None:
            resolved = self.rules.resolve_detailed(context=context)
            checks.extend(classify(rule) for rule in resolved.included)
            skipped = [
                CheckSummary(
                    check_id=entry.rule.id,
                    check_kind=None,  # unknowable without materialising the expression
                    status="skipped",
                    diagnostic=entry.reason,
                )
                for entry in resolved.excluded
            ]

        # contract checks + resolved rules share one id namespace (spec §9.4)
        seen_ids: set[str] = set()
        for check in checks:
            if check.id in seen_ids:
                raise CheckDeclarationError(
                    f"duplicate check id {check.id!r} across contract checks "
                    "and resolved rules"
                )
            seen_ids.add(check.id)

        # --- data phase
        prepared = self._prepare_data(data, context)
        rel = prepared if isinstance(prepared, Relation) else ma.relation(prepared)
        rel, slice_diagnostics = self._slice(
            rel, head=head, tail=tail, sample=sample, random_seed=random_seed
        )

        if getattr(self.contract.Config, "coerce", True):
            rel = rel.conform(spec)

        result = ValidationRunner().validate_relation(
            rel,
            checks,
            identity=identity,
            allow_imperfect_key=allow_imperfect_key,
            context=context or {},
            fail_fast=fail_fast,
            failure_sample=failure_sample,
            validator_name=self.name,
            datacontract_name=self.contract.contract_name(),
        )
        if slice_diagnostics:
            result.diagnostics.update(slice_diagnostics)
        if skipped:
            # skipped summaries are visibility only: appended to the frame,
            # never part of the runner's pass computation (they cannot fail)
            result.check_summaries = pl.concat(
                [result.check_summaries, summaries_frame(skipped)]
            )

        if not result.passes:
            result.processor = ValidationResultProcessor(
                result.failure_cases,
                source_data=self._to_polars_frame(rel),
                identity=identity,
                check_summaries=result.check_summaries,
                validator_name=self.name,
            )
        return result
