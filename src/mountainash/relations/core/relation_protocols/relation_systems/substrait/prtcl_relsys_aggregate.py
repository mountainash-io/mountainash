"""Protocol for Substrait AggregateRel — grouping and aggregation."""

from __future__ import annotations

from typing import Protocol, Sequence, Union

from mountainash.core.types import ExpressionT, RelationT


class SubstraitAggregateRelationSystemProtocol(Protocol[RelationT, ExpressionT]):
    """Contract for aggregation operations on relations."""

    def aggregate(
        self,
        relation: RelationT,
        keys: Sequence[Union[ExpressionT, str]],
        measures: list[ExpressionT],
        /,
    ) -> RelationT: ...

    def distinct(
        self, relation: RelationT, columns: Sequence[Union[ExpressionT, str]], /
    ) -> RelationT: ...
