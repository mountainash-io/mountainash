from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EmptyPolicy(Enum):
    WARN = "warn"
    FAIL = "fail"
    SILENT = "silent"


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    backoff_rate: float = 2.0
    initial_delay_seconds: float = 1.0
