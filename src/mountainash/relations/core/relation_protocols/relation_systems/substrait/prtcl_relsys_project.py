"""Protocol for Substrait ProjectRel — column selection, addition, removal, and renaming."""

from __future__ import annotations

from typing import Any, Protocol


class SubstraitProjectRelationSystemProtocol(Protocol):
    """Contract for projection operations on relations."""

    def project_select(self, relation: Any, columns: list[Any], /) -> Any: ...

    def project_with_columns(self, relation: Any, expressions: list[Any], /) -> Any: ...

    def project_drop(self, relation: Any, columns: list[Any], /) -> Any: ...

    def project_rename(self, relation: Any, mapping: dict[str, str], /) -> Any: ...
