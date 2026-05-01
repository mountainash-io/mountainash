"""Validator — unified validation orchestrator."""
from __future__ import annotations

from typing import Any, Callable

import polars as pl
import pandera.polars as pa

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor


def _compile_contract_with_rules(
    contract: type[BaseDataContract],
    rules: list[Rule],
) -> type[BaseDataContract]:
    """Create an ephemeral subclass with compiled rules as @dataframe_check methods."""
    check_methods: dict[str, Any] = {}
    for rule in rules:
        def make_check(r: Rule) -> Any:
            def check_fn(cls: Any, data: pa.PolarsData) -> pl.LazyFrame:
                compiled_expr = r.expr.compile(data.lazyframe)
                return data.lazyframe.select(compiled_expr)
            return pa.dataframe_check(name=r.id)(check_fn)
        check_methods[f"_check_{rule.id}"] = make_check(rule)

    return type(
        f"{contract.__name__}_WithRules",
        (contract,),
        check_methods,
    )


class Validator:
    """Unified validation orchestrator binding contract + rules + data."""

    def __init__(
        self,
        *,
        name: str,
        contract: type[BaseDataContract],
        rules: RuleRegistry | None = None,
        natural_key: list[str] | None = None,
        prepare: Callable[[Any], Any] | None = None,
    ) -> None:
        self.name = name
        self.contract = contract
        self.rules = rules
        self.natural_key = natural_key
        self.prepare = prepare

    def _resolve_contract(self, context: dict[str, Any] | None) -> type[BaseDataContract]:
        if self.rules is None:
            return self.contract
        resolved = self.rules.resolve(context=context)
        if not resolved:
            return self.contract
        return _compile_contract_with_rules(self.contract, resolved)

    def _prepare_data(self, data: Any) -> Any:
        if self.prepare is not None:
            return self.prepare(data)
        return data

    def validate(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
    ) -> ValidationResult:
        """Full validation — collects all errors."""
        prepared = self._prepare_data(data)
        active_contract = self._resolve_contract(context)

        try:
            active_contract.validate_datacontract(
                prepared, head=head, tail=tail, sample=sample, random_seed=random_seed,
            )
            return ValidationResult(
                passes=True,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
            )
        except pa.errors.SchemaErrors as e:
            processor = ValidationResultProcessor(e.failure_cases)
            return ValidationResult(
                passes=False,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
                processor=processor,
                message=str(e),
            )

    def validate_quick(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
    ) -> ValidationResult:
        """Quick validation — fails on first error."""
        prepared = self._prepare_data(data)
        active_contract = self._resolve_contract(context)

        try:
            active_contract.validate_datacontract_quick(
                prepared, head=head, tail=tail, sample=sample, random_seed=random_seed,
            )
            return ValidationResult(
                passes=True,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
            )
        except pa.errors.SchemaError as e:
            fc = getattr(e, "failure_cases", None)
            processor = ValidationResultProcessor(fc) if fc is not None else None
            return ValidationResult(
                passes=False,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
                processor=processor,
                message=str(e),
            )
