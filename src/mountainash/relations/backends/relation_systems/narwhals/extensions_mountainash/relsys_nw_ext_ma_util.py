"""Narwhals implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)


class MountainashNarwhalsExtensionRelationSystem(
    MountainashExtensionRelationSystemProtocol[nw.DataFrame | nw.LazyFrame]
):
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
        mask = nw.all_horizontal(*[~nw.col(c).is_nan() for c in subset], ignore_nulls=True)
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
        seed: Optional[int] = None,
    ) -> Any:
        frame = relation
        is_lazy = isinstance(frame, nw.LazyFrame)
        if is_lazy:
            frame = frame.collect()
        if n is not None:
            n = min(n, len(frame))
        sampled = frame.sample(n=n, fraction=fraction, seed=seed)
        return sampled.lazy() if is_lazy else sampled

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

    def unnest(self, relation: Any, /, *, columns: list[str], separator: str) -> Any:
        raise NotImplementedError(
            "unnest is not supported on the Narwhals backend. "
            "Narwhals has no frame-level unnest — requires schema introspection synthesis (Phase 2)."
        )

    def read_resource(self, resource: Any) -> Any:
        """Load a DataResource into a Narwhals LazyFrame. Native lazy scan for
        local plain CSV/Parquet; Arrow-coerced (lazy-wrapped) fallback for JSON,
        glob, archive, remote."""
        import narwhals as nw
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )

        if resource.data is not None:
            lf = MountainashPolarsExtensionRelationSystem()._read_inline(resource)
            return nw.from_native(lf)  # stays lazy

        from mountainash.core.io import is_remote
        from mountainash.relations.backends.relation_systems import resource_files as rf

        fmt = MountainashPolarsExtensionRelationSystem._detect_format(resource)
        # Uniform fail-closed (consistency-guarantees) -- see the Polars reader.
        if fmt == "csv":
            rf.ensure_dialect_supported(resource.dialect)
        raw_path = resource.path
        paths = raw_path if isinstance(raw_path, list) else [raw_path]
        all_local = all(not is_remote(p) for p in paths)
        no_glob = all("*" not in p and "?" not in p and "[" not in p for p in paths)
        no_archive = all(not p.lower().endswith((".gz", ".zip")) for p in paths)

        # A native-unsafe CSV dialect (e.g. escape_char) routes to the fallback so
        # it is honoured identically to the other backends (consistency-guarantees).
        native_dialect_ok = fmt != "csv" or rf.dialect_native_safe(resource.dialect)
        if all_local and no_glob and no_archive and fmt in ("csv", "parquet") and native_dialect_ok:
            kwargs = MountainashPolarsExtensionRelationSystem._reader_kwargs(resource, fmt)
            scan = nw.scan_csv if fmt == "csv" else nw.scan_parquet
            frames = [scan(p, backend="polars", **(kwargs if fmt == "csv" else {})) for p in paths]
            return frames[0] if len(frames) == 1 else nw.concat(frames, how="vertical")

        # Files fallback: Arrow -> Polars lazy -> Narwhals lazy.
        import polars as pl
        table = rf.parse_resource_to_arrow(resource)
        return nw.from_native(pl.from_arrow(table).lazy())

    def empty_frame(self, spec: Any) -> Any:
        """Typed-empty Narwhals LazyFrame (lazy)."""
        import narwhals as nw
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )
        lf = MountainashPolarsExtensionRelationSystem().empty_frame(spec)
        return nw.from_native(lf)  # stays lazy

    def fetch_from_end(self, relation: Any, count: int, /) -> Any:
        return relation.tail(count)

    def join_asof(
        self,
        left: Any,
        right: Any,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> Any:
        return left.join_asof(
            right,
            on=on,
            by=by if by else None,
            strategy=strategy,
        )
