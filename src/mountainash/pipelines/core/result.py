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


def infer_record_count(data: Any) -> int | None:
    """Record-count inference shared by runners.

    An explicit integer ``record_count`` attribute wins — reference types
    (handles to externally stored data) opt in this way; then list length,
    arrow ``num_rows``, polars ``height``.
    """
    explicit = getattr(data, "record_count", None)
    if isinstance(explicit, int):
        return explicit
    if isinstance(data, list):
        return len(data)
    if hasattr(data, "num_rows"):
        return data.num_rows
    if hasattr(data, "height"):
        return data.height
    return None
