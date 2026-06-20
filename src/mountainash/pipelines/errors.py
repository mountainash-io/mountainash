"""Pipeline orchestration errors."""
from __future__ import annotations

from mountainash.core.errors import MountainashError


class StepEmptyError(MountainashError):
    """Raised when a pipeline step returns empty data under a non-empty policy."""
