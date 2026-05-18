from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParamSpec:
    """Declares one parameter a pipeline step accepts."""
    name: str
    type: type
    required: bool = True
    default: Any = None
