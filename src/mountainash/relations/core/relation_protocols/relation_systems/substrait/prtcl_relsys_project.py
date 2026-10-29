"""Protocol for Substrait ProjectRel — column selection, addition, removal, and renaming."""

from __future__ import annotations

from typing import Protocol, Union

from mountainash.core.types import ExpressionT, RelationT


class SubstraitProjectRelationSystemProtocol(Protocol[RelationT, ExpressionT]):
    """Contract for projection operations on relations."""

    def project_select(
        self, relation: RelationT, columns: list[Union[ExpressionT, str]], /
    ) -> RelationT: ...

    def project_with_columns(
        self, relation: RelationT, expressions: list[ExpressionT], /
    ) -> RelationT: ...

    def project_drop(
        self, relation: RelationT, columns: list[Union[ExpressionT, str]], /
    ) -> RelationT: ...

    def project_rename(
        self, relation: RelationT, mapping: dict[str, str], /
    ) -> RelationT: ...
