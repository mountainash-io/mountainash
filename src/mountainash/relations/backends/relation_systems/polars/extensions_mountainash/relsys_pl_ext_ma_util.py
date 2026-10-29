"""Polars implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import polars as pl


from mountainash.relations.dag.errors import (
    ResourceSchemaCastError,
    UnsupportedResourceFormat,
)

from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)

def _declared_polars_schema(resource: Any) -> Optional[dict[str, Any]]:
    """Resolve a resource's schema to a Polars {name: dtype} map.

    Raw Frictionless mappings stay on the direct adapter path. References and
    schema declarations resolve through ``resource.to_table_schema()`` so the
    descriptor codec remains the single resolution boundary.
    """
    table_schema = resource.table_schema
    if table_schema is None:
        return None
    from mountainash.typespec.spec import TableSchema

    if isinstance(table_schema, TableSchema):
        spec = table_schema
    elif isinstance(table_schema, dict):
        from mountainash.typespec.frictionless import table_schema_from_frictionless

        spec = table_schema_from_frictionless(table_schema)
    else:
        spec = resource.to_table_schema()
        if spec is None:
            return None

    from mountainash.typespec.converters import to_polars_schema

    return to_polars_schema(spec)


class MountainashPolarsExtensionRelationSystem(MountainashExtensionRelationSystemProtocol[pl.LazyFrame]):
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
        seed: Optional[int] = None,
    ) -> pl.LazyFrame:
        names = relation.collect_schema().names()
        index_name = "_ma_sample_index"
        while index_name in names:
            index_name = "_" + index_name
        count = min(n, 2**63 - 1) if n is not None else (pl.len() * fraction).cast(pl.UInt64)
        # Gather every column with the same native random indices, including
        # Object columns which cannot be placed inside a struct expression.
        indexed = relation.with_columns(
            pl.int_range(pl.len()).shuffle(seed=seed).alias(index_name)
        )
        return indexed.select(
            pl.exclude(index_name).gather(pl.col(index_name).head(count))
        )

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

    def _native_scan_for(self, resource: Any, dialect: Any) -> bool:
        from mountainash.relations.backends.relation_systems import resource_files as rf

        return rf.polars_native_scan_supported(resource, self._detect_format(resource), dialect)

    def read_resource(self, resource: Any, *, location: Any = None) -> pl.LazyFrame:
        """Load a DataResource into a Polars LazyFrame."""
        from mountainash.core.lowering_reuse import DEFERRED_ONLY, OCCURRENCE

        self._resource_lowering = OCCURRENCE
        dialect = resource.to_dialect()
        if resource.data is not None:
            return self._read_inline(resource)
        fmt = self._detect_format(resource)
        assert resource.path is not None, f"DataResource '{resource.name}' has no path"

        from mountainash.relations.backends.relation_systems import resource_files as rf

        # Keep schema-phase eligibility identical to this reader's actual lazy
        # route; all other formats and path forms use the eager files fallback.
        # The decision also yields the effective (confined) paths: computed once.
        paths = rf.polars_native_scan_paths(resource, fmt, dialect)
        if paths is not None:
            self._resource_lowering = DEFERRED_ONLY
            return self._native_local_scan(fmt, paths, resource, dialect)
        return pl.from_arrow(
            rf.parse_resource_to_arrow(resource, dialect=dialect)
        ).lazy()

    def _native_local_scan(
        self, fmt: str, paths: list[str], resource: Any, dialect: Any,
    ) -> pl.LazyFrame:
        # Eligibility excludes authored globs; the descriptor base stays literal.
        kwargs = {**self._reader_kwargs(resource, fmt, dialect), "glob": False}
        if fmt == "csv":
            frames = [pl.scan_csv(p, **kwargs) for p in paths]
        else:
            frames = [pl.scan_parquet(p, glob=False) for p in paths]
        return frames[0] if len(frames) == 1 else pl.concat(frames, how="vertical")


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
    def _reader_kwargs(resource: Any, fmt: str, dialect: Any) -> dict[str, Any]:
        if fmt == "csv" and dialect is not None:
            return dialect.to_polars_read_csv_kwargs()
        return {}

    def empty_frame(self, spec: Any) -> pl.LazyFrame:
        """Typed-empty LazyFrame with the schema's declared columns/dtypes."""
        from mountainash.typespec.converters import to_polars_schema

        return pl.DataFrame(schema=to_polars_schema(spec)).lazy()

    def _read_inline(self, resource: Any) -> pl.LazyFrame:
        from mountainash.pydata.ingress.pydata_ingress import PydataIngress

        df, self._resource_lowering = PydataIngress._convert_for_compilation(resource.data)

        # Restore the declared dtype of columns Polars could not type from the
        # inline data (an all-null OR zero-row column infers pl.Null). Cast
        # ONLY those null-inferred columns to the declared dtype (Null-only
        # policy, item 53 §3.3): typed columns are never touched, so no
        # strict-cast regression is possible for data that diverges from its
        # schema.
        declared = _declared_polars_schema(resource)
        if declared:
            casts = {
                name: dt
                for name, dt in declared.items()
                if name in df.columns and df.schema[name] == pl.Null
            }
            if casts:
                try:
                    df = df.cast(casts)
                except pl.exceptions.PolarsError as e:
                    raise ResourceSchemaCastError(resource.name, casts) from e
        return df.lazy()

    def fetch_from_end(self, relation: pl.LazyFrame, count: int, /) -> pl.LazyFrame:
        return relation.tail(count)

    def join_asof(
        self,
        left: pl.LazyFrame,
        right: pl.LazyFrame,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> pl.LazyFrame:
        return left.join_asof(
            right,
            on=on,
            by=by if by else None,
            strategy=strategy,
            tolerance=tolerance,
        )
