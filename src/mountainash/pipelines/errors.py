"""Pipeline orchestration errors."""
from __future__ import annotations

from mountainash.core.errors import MountainashError


class StepEmptyError(MountainashError):
    """Raised when a pipeline step returns empty data under a non-empty policy."""


class InvalidStorageKeyError(MountainashError, ValueError):
    """Raised when a step name or cache key cannot be used as a storage path component."""
