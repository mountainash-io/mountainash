"""Protocol for Substrait JoinRel — joining two relations."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from mountainash.core.constants import JoinType


class SubstraitJoinRelationSystemProtocol(Protocol):
    """Contract for joining relations."""

    def join(
        self,
        left: Any,
        right: Any,
        *,
        join_type: JoinType,
        on: Optional[list[str]],
        left_on: Optional[list[str]],
        right_on: Optional[list[str]],
        suffix: str,
    ) -> Any: ...

    def join_asof(
        self,
        left: Any,
        right: Any,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> Any: ...
