"""Narwhals implementation of Substrait SortRel."""

from __future__ import annotations

from mountainash.core.constants import SortField


class SubstraitNarwhalsSortRelationSystem:
    """Sort operations on Narwhals DataFrames."""

    def sort(self, relation: object, sort_fields: list[SortField], /) -> object:
        # Narwhals sort supports ``by`` and ``descending`` but not ``nulls_last``.
        return relation.sort(  # type: ignore[union-attr]
            by=[sf.column for sf in sort_fields],
            descending=[sf.descending for sf in sort_fields],
        )
