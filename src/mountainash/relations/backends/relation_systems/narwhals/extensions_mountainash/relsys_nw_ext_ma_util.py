"""Narwhals implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional


class MountainashNarwhalsExtensionRelationSystem:
    """Mountainash-specific relation operations on Narwhals DataFrames."""

    def drop_nulls(
        self, relation: Any, /, *, subset: Optional[list[str]] = None
    ) -> Any:
        if subset:
            return relation.drop_nulls(subset=subset)
        return relation.drop_nulls()

    def drop_nans(
        self, relation: Any, /, *, subset: Optional[list[str]] = None
    ) -> Any:
        import narwhals as nw
        if subset is None:
            schema = relation.schema
            subset = [
                name for name, dtype in schema.items()
                if dtype in (nw.Float32, nw.Float64)
            ]
        if not subset:
            return relation
        mask = nw.all_horizontal(*[~nw.col(c).is_nan() for c in subset])
        return relation.filter(mask)

    def with_row_index(self, relation: Any, /, *, name: str = "index") -> Any:
        return relation.with_row_index(name=name)

    def explode(self, relation: Any, /, *, columns: list[str]) -> Any:
        return relation.explode(columns)

    def sample(
        self,
        relation: Any,
        /,
        *,
        n: Optional[int] = None,
        fraction: Optional[float] = None,
    ) -> Any:
        return relation.sample(n=n, fraction=fraction)

    def unpivot(
        self,
        relation: Any,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> Any:
        return relation.unpivot(
            on=on,
            index=index,
            variable_name=variable_name,
            value_name=value_name,
        )

    def pivot(
        self,
        relation: Any,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> Any:
        return relation.pivot(
            on=on,
            index=index,
            values=values,
            aggregate_function=aggregate_function,
        )

    def top_k(
        self, relation: Any, /, *, k: int, by: str, descending: bool = True
    ) -> Any:
        return relation.sort(by, descending=descending).head(k)
