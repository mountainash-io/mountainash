"""Protocol for Mountainash extension relation operations not in Substrait."""

from __future__ import annotations

from typing import Any, Optional, Protocol


class MountainashExtensionRelationSystemProtocol(Protocol):
    """Contract for Mountainash-specific relation operations."""

    def drop_nulls(self, relation: Any, /, *, subset: Optional[list[str]] = None) -> Any: ...

    def drop_nans(self, relation: Any, /, *, subset: Optional[list[str]] = None) -> Any: ...

    def with_row_index(self, relation: Any, /, *, name: str = "index") -> Any: ...

    def explode(self, relation: Any, /, *, columns: list[str]) -> Any: ...

    def sample(
        self, relation: Any, /, *, n: Optional[int] = None, fraction: Optional[float] = None
    ) -> Any: ...

    def unpivot(
        self,
        relation: Any,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> Any: ...

    def pivot(
        self,
        relation: Any,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> Any: ...

    def top_k(self, relation: Any, /, *, k: int, by: str, descending: bool = True) -> Any: ...

    def read_resource(self, resource: Any) -> Any:
        """Load a DataResource into the backend's native relation type.

        Called by the unified visitor for ResourceReadRelNode materialisation.
        Each backend implements its own file I/O strategy.
        """
        ...
