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


def _declared_polars_schema(table_schema: Any) -> Optional[dict[str, Any]]:
    """Resolve a resource's ``table_schema`` to a Polars {name: dtype} map.

    ``table_schema`` may be a raw Frictionless dict or an already-built
    ``TypeSpec`` (``DataResource.table_schema`` is ``Optional[Any]``). Reuses
    the same resolver ``empty_frame`` uses (``to_polars_schema`` ->
    ``_resolve_field_native``): ``ANY`` -> ``STRING``, honours unparameterised
    ``backend_type``. Keys on the field *output* name, so ``rename_from`` never
    enters this path. Returns ``None`` for a missing or unknown-shaped schema
    (read un-cast — do not guess); a genuinely malformed dict lets
    ``typespec_from_frictionless`` raise (no swallow wrapper — item 53 §8.2).
    """
    if table_schema is None:
        return None
    from mountainash.typespec.spec import TypeSpec

    if isinstance(table_schema, TypeSpec):
        spec = table_schema
    elif isinstance(table_schema, dict):
        from mountainash.typespec.frictionless import typespec_from_frictionless

        spec = typespec_from_frictionless(table_schema)
    else:
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
        # LazyFrame does not support .sample() directly — collect, sample, re-lazy.
        frame = relation.collect()
        if n is not None:
            n = min(n, frame.height)
        return frame.sample(n=n, fraction=fraction, seed=seed).lazy()

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

        from mountainash.core.io import is_remote
        from mountainash.relations.backends.relation_systems import resource_files as rf

        # Uniform fail-closed: an unmappable dialect field raises here on EVERY
        # backend, so a native Polars scan never silently reads a dialect the
        # Ibis fallback would reject (consistency-guarantees).
        if fmt == "csv":
            rf.ensure_dialect_supported(resource.dialect)

        all_local = all(not is_remote(p) for p in paths)
        no_glob = all("*" not in p and "?" not in p and "[" not in p for p in paths)
        no_archive = all(not p.lower().endswith((".gz", ".zip")) for p in paths)
        # Native local scan handles local plain CSV (incl. native-safe dialect
        # kwargs) + Parquet lazily. Glob/archive/remote/JSON -> files fallback.
        # A CSV dialect with a native-unsafe field (e.g. escape_char, which has no
        # correct pl.scan_csv target) also routes to the fallback so it is honoured
        # identically to Ibis (consistency-guarantees), not read natively-and-wrong.
        native_dialect_ok = fmt != "csv" or rf.dialect_native_safe(resource.dialect)
        if all_local and no_glob and no_archive and fmt in ("csv", "parquet") and native_dialect_ok:
            return self._native_local_scan(fmt, paths, resource)
        return pl.from_arrow(rf.parse_resource_to_arrow(resource)).lazy()

    def _native_local_scan(self, fmt: str, paths: list[str], resource: Any) -> pl.LazyFrame:
        kwargs = self._reader_kwargs(resource, fmt)
        if fmt == "csv":
            frames = [pl.scan_csv(p, **kwargs) for p in paths]
        else:
            frames = [pl.scan_parquet(p) for p in paths]
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
    def _reader_kwargs(resource: Any, fmt: str) -> dict[str, Any]:
        if fmt == "csv" and resource.dialect:
            return resource.dialect.to_polars_read_csv_kwargs()
        return {}

    def empty_frame(self, spec: Any) -> pl.LazyFrame:
        """Typed-empty LazyFrame with the schema's declared columns/dtypes."""
        from mountainash.typespec.converters import to_polars_schema

        return pl.DataFrame(schema=to_polars_schema(spec)).lazy()

    @staticmethod
    def _read_inline(resource: Any) -> pl.LazyFrame:
        from mountainash.pydata.ingress.pydata_ingress import PydataIngress

        df = PydataIngress.convert(resource.data)  # eager pl.DataFrame

        # Restore the declared dtype of columns Polars could not type from the
        # inline data (an all-null OR zero-row column infers pl.Null). Cast
        # ONLY those null-inferred columns to the declared dtype (Null-only
        # policy, item 53 §3.3): typed columns are never touched, so no
        # strict-cast regression is possible for data that diverges from its
        # schema.
        declared = _declared_polars_schema(resource.table_schema)
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
