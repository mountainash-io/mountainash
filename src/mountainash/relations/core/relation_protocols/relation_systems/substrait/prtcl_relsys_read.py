"""Protocol for Substrait ReadRel — scanning a data source into a relation."""

from __future__ import annotations

from typing import Any, Protocol


class SubstraitReadRelationSystemProtocol(Protocol):
    """Contract for reading / scanning a data source into a relation."""

    def read(self, dataframe: Any, /) -> Any: ...
