"""Shared base for backend relation systems: limitations registry hook."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.types import KnownLimitation


class BaseRelationSystem:
    """Mixin carrying the known-limitations table (spec §3.8).

    Keys are ``(operation_key, param_name)``; ``param_name`` may be the
    ``"*"`` wildcard, which is how handler-routed operations (JOIN,
    JOIN_ASOF, CONFORM, REF, SOURCE, READ_RESOURCE) and the
    materialization boundary participate.
    """

    KNOWN_REL_LIMITATIONS: dict[tuple[Any, str], "KnownLimitation"] = {}

    BACKEND_NAME: str = "unknown"

    def __init__(self, dialect: str | None = None) -> None:
        self.dialect = dialect
