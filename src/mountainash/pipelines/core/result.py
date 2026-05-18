from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class StepMetadata:
    step_name: str
    completed_at: datetime
    record_count: int | None = None
    input_cache_keys: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] | None = None


@dataclass(frozen=True)
class StepResult:
    data: Any
    metadata: StepMetadata
    cache_key: str
