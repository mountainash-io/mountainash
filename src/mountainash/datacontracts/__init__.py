"""mountainash.datacontracts — native data contract declaration layer."""
from __future__ import annotations

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.compiler import (
    compile_datacontract,
    constraint_checks,
    contract_from_typespec,
)
from mountainash.datacontracts.field import Field
from mountainash.datacontracts.plan import PlanResult, ValidationPlan
from mountainash.datacontracts.rule import Rule, guarded
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor
from mountainash.datacontracts import constraints  # noqa: F401
from mountainash.datacontracts import expressions  # noqa: F401

__all__ = [
    "BaseDataContract",
    "Field",
    "compile_datacontract",
    "constraint_checks",
    "contract_from_typespec",
    "constraints",
    "expressions",
    "PlanResult",
    "ValidationPlan",
    "Rule",
    "guarded",
    "RuleRegistry",
    "Validator",
    "ValidationResult",
    "ValidationResultProcessor",
]
