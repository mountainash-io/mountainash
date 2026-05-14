from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mountainash.pipelines.core.capabilities import ResolvedPredicates


@dataclass(frozen=True)
class StepMetadata:
    step_name: str
    completed_at: datetime
    record_count: int | None = None
    input_cache_keys: dict[str, str] = field(default_factory=dict)
    resolved_predicates: ResolvedPredicates | None = None


@dataclass(frozen=True)
class StepResult:
    data: Any
    metadata: StepMetadata
    cache_key: str
