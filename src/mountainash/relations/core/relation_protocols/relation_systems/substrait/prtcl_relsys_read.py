"""Protocol for Substrait ReadRel — scanning a data source into a relation."""

from __future__ import annotations

from typing import Any, Protocol

from mountainash.core.types import RelationT


class SubstraitReadRelationSystemProtocol(Protocol[RelationT]):
    """Contract for reading / scanning a data source into a relation."""

    def read(self, dataframe: Any, /) -> RelationT: ...
