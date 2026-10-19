"""Validator — orchestrates prepare -> slice once -> resolve -> ValidationRunner.

No Pandera. validate_quick() is validate() with fail_fast=True: identical
result shapes by construction (spec §6.5, item 18 subsumed).
"""
from __future__ import annotations

import inspect
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

import polars as pl


from mountainash.validation.checks import classify
from mountainash.validation.errors import CheckDeclarationError
from mountainash.validation.identity import resolve_identity
from mountainash.validation.plan import _freeze_check
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
    """Unified validation orchestrator binding contract + rules + data.

    The contract's schema, checks, natural key, ``Config.coerce`` and name are
    acquired at construction; later edits to the contract affect only Validators
    built afterwards.

    Input is conformed to the contract's TypeSpec before any check runs, so a
    column read by a rule but absent from the contract (a support column) is
    rejected under the default ``fields_match="exact"``. Declare the column in
    the contract, or set ``fields_match="open"`` on its TypeSpec to retain it
    (see :class:`~mountainash.typespec.spec.TypeSpec` for all six modes). A rule
    that cannot run reports an ``error`` summary with unavailable counts and
    other checks still execute; a shared conform failure is distinct from a
    rule-local failure.
    """

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

        # Acquire the contract's declarations once. Later edits to the
        # authoring contract affect only Validators constructed afterwards.
        # Callbacks, registries and the contract class itself are not copied.
        self._contract_spec = deepcopy(contract.to_typespec())
        self._contract_checks = tuple(
            _freeze_check(check) for check in contract.to_checks()
        )
        self._contract_natural_key = deepcopy(
            natural_key or getattr(contract.Config, "natural_key", None)
        )
        self._contract_coerce = bool(getattr(contract.Config, "coerce", True))
        self._contract_name = contract.contract_name()

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
    def _slice(
        rel: Any,
        *,
        head: int | None,
        tail: int | None,
        sample: int | None,
        random_seed: int | None,
    ) -> Any:
        """Choose the sample once on its source backend for this validation run."""
        if head is not None:
            rel = rel.head(head)
        if tail is not None:
            rel = rel.tail(tail)
        if sample is not None:
            rel = rel.sample(n=sample, seed=random_seed).snapshot()
        return rel

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
        spec = self._contract_spec
        identity = resolve_identity(
            natural_key=self._contract_natural_key,
            spec=spec,
            row_identity=row_identity,
        )

        checks: list[Any] = list(self._contract_checks)
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

        prepared = self._prepare_data(data, context)
        # Resource descriptors have their own ordinary-read conformance. A
        # validator owns the single conformance plan for this validation run,
        # so copy resource leaves with that built-in pass disabled first.
        rel = (
            prepared._without_resource_schema_conform()
            if isinstance(prepared, Relation)
            else ma.relation(prepared)
        )
        with ma.materialization_scope():
            rel = self._slice(
                rel, head=head, tail=tail, sample=sample, random_seed=random_seed
            )

            rel = rel.conform(
                spec,
                apply_value_transforms=self._contract_coerce,
            )

            result = ValidationRunner().validate_relation(
                rel,
                checks,
                identity=identity,
                allow_imperfect_key=allow_imperfect_key,
                context=context or {},
                fail_fast=fail_fast,
                failure_sample=failure_sample,
                validator_name=self.name,
                datacontract_name=self._contract_name,
            )
            if skipped:
                # Skipped summaries are visibility only, not pass computation.
                result.check_summaries = pl.concat(
                    [result.check_summaries, summaries_frame(skipped)]
                )

            if not result.passes:
                result.processor = ValidationResultProcessor(
                    result.failure_cases,
                    source_data=result._materialized_source,
                    identity=identity,
                    check_summaries=result.check_summaries,
                    validator_name=self.name,
                )
            return result
