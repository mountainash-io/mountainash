"""ValidationResult — outcome of a validation run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.datacontracts.result_processor import ValidationResultProcessor


@dataclass
class ValidationResult:
    """Result of a Validator.validate() or Validator.validate_quick() call."""

    passes: bool
    validator_name: str
    datacontract_name: str | None = None
    processor: Optional[ValidationResultProcessor] = None
    message: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
