"""Protocol for Mountainash extension relation operations not in Substrait."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from mountainash.core.types import RelationT


class MountainashExtensionRelationSystemProtocol(Protocol[RelationT]):
    """Contract for Mountainash-specific relation operations."""

    def drop_nulls(self, relation: RelationT, /, *, subset: Optional[list[str]] = None) -> RelationT: ...

    def drop_nans(self, relation: RelationT, /, *, subset: Optional[list[str]] = None) -> RelationT: ...

    def with_row_index(self, relation: RelationT, /, *, name: str = "index") -> RelationT: ...

    def explode(self, relation: RelationT, /, *, columns: list[str]) -> RelationT: ...

    def sample(
        self,
        relation: RelationT,
        /,
        *,
        n: Optional[int] = None,
        fraction: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> RelationT: ...

    def unpivot(
        self,
        relation: RelationT,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> RelationT: ...

    def pivot(
        self,
        relation: RelationT,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> RelationT: ...

    def top_k(self, relation: RelationT, /, *, k: int, by: str, descending: bool = True) -> RelationT: ...

    def unnest(self, relation: RelationT, /, *, columns: list[str], separator: str) -> RelationT: ...

    def read_resource(self, resource: Any) -> RelationT:
        """Load a DataResource into the backend's native relation type.

        Called by the unified visitor for ResourceReadRelNode materialisation.
        Each backend implements its own file I/O strategy.
        """
        ...

    def empty_frame(self, spec: Any) -> RelationT:
        """Build a typed-empty (0, N) native frame from a TypeSpec.

        Used by the resource-read path to materialise a zero-row resource
        whose source carried no column information, reconstructing the
        declared columns/dtypes from the schema. Accepts ONLY a TypeSpec
        (callers convert raw Frictionless dicts first).
        """
        ...

    def fetch_from_end(self, relation: RelationT, count: int, /) -> RelationT:
        """Fetch the last ``count`` rows (``tail``) — no Substrait FetchRel form.

        Substrait ``FetchRel`` counts from the start (offset/count); fetching
        from the end is a Mountainash convenience with no standard equivalent.
        """
        ...

    def join_asof(
        self,
        left: RelationT,
        right: RelationT,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> RelationT:
        """As-of (nearest-key) join — no Substrait JoinRel form.

        Substrait's ``JoinRel`` join-type enum has no ``ASOF`` member; as-of
        join is a Mountainash addition.
        """
        ...
