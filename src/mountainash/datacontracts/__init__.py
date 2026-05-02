"""mountainash.datacontracts — Data contract validation with pandera."""
from __future__ import annotations

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.datacontracts.rule import Rule, guarded
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor
from mountainash.datacontracts import constraints  # noqa: F401
from mountainash.datacontracts import expressions  # noqa: F401

__all__ = [
    "BaseDataContract",
    "compile_datacontract",
    "constraints",
    "expressions",
    "Rule",
    "guarded",
    "RuleRegistry",
    "Validator",
    "ValidationResult",
    "ValidationResultProcessor",
]
