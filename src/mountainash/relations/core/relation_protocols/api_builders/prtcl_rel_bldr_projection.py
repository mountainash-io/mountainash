"""Protocol for the relation projection builder."""

from __future__ import annotations

from typing import Any, Protocol


class RelationProjectionBuilderProtocol(Protocol):
    """Contract for projection operations on relations."""

    def select(self, *columns: Any) -> Any: ...
    def with_columns(self, *expressions: Any) -> Any: ...
    def drop(self, *columns: Any) -> Any: ...
    def rename(self, mapping: dict[str, str]) -> Any: ...
