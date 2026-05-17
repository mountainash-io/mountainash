"""Polars implementation of Mountainash extension relation operations."""

from __future__ import annotations

import io
from typing import Any, Optional

import polars as pl

from mountainash.relations.dag.errors import UnsupportedResourceFormat

from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)


class MountainashPolarsExtensionRelationSystem(MountainashExtensionRelationSystemProtocol):
    """Mountainash-specific relation operations on Polars LazyFrames."""

    def drop_nulls(
        self, relation: pl.LazyFrame, /, *, subset: Optional[list[str]] = None
    ) -> pl.LazyFrame:
        if subset:
            return relation.drop_nulls(subset=subset)
        return relation.drop_nulls()

    def drop_nans(
        self, relation: pl.LazyFrame, /, *, subset: Optional[list[str]] = None
    ) -> pl.LazyFrame:
        if subset:
            return relation.drop_nans(subset=subset)
        return relation.drop_nans()

    def with_row_index(
        self, relation: pl.LazyFrame, /, *, name: str = "index"
    ) -> pl.LazyFrame:
        return relation.with_row_index(name=name)

    def explode(self, relation: pl.LazyFrame, /, *, columns: list[str]) -> pl.LazyFrame:
        return relation.explode(columns)

    def sample(
        self,
        relation: pl.LazyFrame,
        /,
        *,
        n: Optional[int] = None,
        fraction: Optional[float] = None,
    ) -> pl.LazyFrame:
        # LazyFrame does not support .sample() directly — collect, sample, re-lazy.
        return relation.collect().sample(n=n, fraction=fraction).lazy()

    def unpivot(
        self,
        relation: pl.LazyFrame,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> pl.LazyFrame:
        return relation.unpivot(
            on=on,
            index=index,
            variable_name=variable_name,
            value_name=value_name,
        )

    def pivot(
        self,
        relation: pl.LazyFrame,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> pl.LazyFrame:
        # Pivot requires eager DataFrame — collect, pivot, re-lazy.
        return (
            relation.collect()
            .pivot(
                on=on,
                index=index,
                values=values,
                aggregate_function=aggregate_function,
            )
            .lazy()
        )

    def top_k(
        self, relation: pl.LazyFrame, /, *, k: int, by: str, descending: bool = True
    ) -> pl.LazyFrame:
        return relation.sort(by, descending=descending).head(k)

    def unnest(
        self, relation: pl.LazyFrame, /, *, columns: list[str], separator: str
    ) -> pl.LazyFrame:
        return relation.unnest(columns, separator=separator if separator else None)

    # ------------------------------------------------------------------
    # read_resource — load a DataResource into a Polars LazyFrame
    # ------------------------------------------------------------------

    def read_resource(self, resource: Any) -> pl.LazyFrame:
        """Load a DataResource into a Polars LazyFrame."""
        if resource.data is not None:
            return self._read_inline(resource)
        fmt = self._detect_format(resource)
        raw_path = resource.path
        assert raw_path is not None, f"DataResource '{resource.name}' has no path"
        paths: list[str] = raw_path if isinstance(raw_path, list) else [raw_path]
        readers = {
            "csv": self._read_csv,
            "json": self._read_json,
            "parquet": self._read_parquet,
        }
        reader = readers.get(fmt)
        if reader is None:
            raise UnsupportedResourceFormat(
                f"no reader for format {fmt!r} (resource {resource.name!r})"
            )
        kwargs = self._reader_kwargs(resource, fmt)
        frames = [reader(p, kwargs) for p in paths]
        if len(frames) == 1:
            return frames[0]
        return pl.concat(frames, how="vertical")

    @staticmethod
    def _detect_format(resource: Any) -> str:
        if resource.format:
            return resource.format.lower()
        if resource.mediatype:
            mt = resource.mediatype.lower()
            if "csv" in mt:
                return "csv"
            if "json" in mt:
                return "json"
            if "parquet" in mt:
                return "parquet"
        if isinstance(resource.path, str) and "." in resource.path:
            return resource.path.rsplit(".", 1)[-1].lower()
        if isinstance(resource.path, list) and resource.path and "." in resource.path[0]:
            return resource.path[0].rsplit(".", 1)[-1].lower()
        raise UnsupportedResourceFormat(
            f"cannot detect format for resource {resource.name!r}"
        )

    @staticmethod
    def _reader_kwargs(resource: Any, fmt: str) -> dict[str, Any]:
        if fmt == "csv" and resource.dialect:
            return resource.dialect.to_polars_read_csv_kwargs()
        return {}

    @staticmethod
    def _read_csv(path: str, kwargs: dict[str, Any]) -> pl.LazyFrame:
        from mountainash.core.io import is_remote, facade_read_bytes

        if is_remote(path):
            return pl.read_csv(io.BytesIO(facade_read_bytes(path)), **kwargs).lazy()
        return pl.scan_csv(path, **kwargs)

    @staticmethod
    def _read_json(path: str, kwargs: dict[str, Any]) -> pl.LazyFrame:
        from mountainash.core.io import is_remote, facade_read_bytes

        if is_remote(path):
            raw = facade_read_bytes(path)
        else:
            with open(path, "rb") as f:
                raw = f.read()
        return pl.read_json(io.BytesIO(raw), **kwargs).lazy()

    @staticmethod
    def _read_parquet(path: str, kwargs: dict[str, Any]) -> pl.LazyFrame:
        from mountainash.core.io import is_remote, facade_read_bytes

        if is_remote(path):
            return pl.read_parquet(io.BytesIO(facade_read_bytes(path)), **kwargs).lazy()
        return pl.scan_parquet(path, **kwargs)

    @staticmethod
    def _read_inline(resource: Any) -> pl.LazyFrame:
        from mountainash.pydata.ingress.pydata_ingress import PydataIngress

        df = PydataIngress.convert(resource.data)
        return df.lazy()
