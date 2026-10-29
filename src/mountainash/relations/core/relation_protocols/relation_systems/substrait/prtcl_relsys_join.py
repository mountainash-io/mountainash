"""Protocol for Substrait JoinRel — joining two relations."""

from __future__ import annotations

from typing import Optional, Protocol

from mountainash.core.constants import JoinType
from mountainash.core.types import RelationT


class SubstraitJoinRelationSystemProtocol(Protocol[RelationT]):
    """Contract for joining relations."""

    def join(
        self,
        left: RelationT,
        right: RelationT,
        *,
        join_type: JoinType,
        on: Optional[list[str]],
        left_on: Optional[list[str]],
        right_on: Optional[list[str]],
        suffix: str,
    ) -> RelationT: ...
