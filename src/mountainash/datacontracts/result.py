"""Back-compat import path: canonical result types live in mountainash.validation."""
from mountainash.validation.result import (  # noqa: F401
    CheckSummary,
    DAGValidationResult,
    ValidationResult,
)

__all__ = ["CheckSummary", "DAGValidationResult", "ValidationResult"]
