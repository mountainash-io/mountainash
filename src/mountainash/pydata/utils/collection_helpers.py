"""Container emptiness checking."""
from __future__ import annotations
from typing import Any, Mapping, Sequence, Set


def is_empty(obj: Any) -> bool:
    """Check if an object is an empty container.
    Strings are explicitly excluded and never considered empty.
    Returns False for non-containers and None.
    """
    if isinstance(obj, str):
        return False
    elif isinstance(obj, (Mapping, Sequence, Set)):
        return len(obj) == 0
    else:
        return False


__all__ = ["is_empty"]
