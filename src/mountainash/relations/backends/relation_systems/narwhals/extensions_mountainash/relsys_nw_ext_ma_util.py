"""Narwhals implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import narwhals as nw

from mountainash.core.transit import BoundaryKey, transit_call
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
            frame = transit_call(BoundaryKey.NATIVE_LAZY_COLLECT, frame.collect)
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

    def read_resource(self, resource: Any, *, provider_binding: object | str | None = None) -> Any:
        """Load a DataResource into a Narwhals LazyFrame. Native lazy scan for
        local plain CSV/Parquet; Arrow-coerced (lazy-wrapped) fallback for JSON,
        glob, archive, remote."""
        import narwhals as nw
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )

        if provider_binding is not None:
            import polars as pl
            from mountainash.relations.backends.relation_systems.resource_providers import (
                read_provider_arrow,
            )

            return transit_call(
                BoundaryKey.NARWHALS_NATIVE_WRAP,
                nw.from_native,
                pl.from_arrow(read_provider_arrow(resource, provider_binding)).lazy(),
            )
        dialect = resource.to_dialect()
        if resource.data is not None:
            lf = MountainashPolarsExtensionRelationSystem()._read_inline(resource)
            return transit_call(BoundaryKey.NARWHALS_NATIVE_WRAP, nw.from_native, lf)  # stays lazy

        from mountainash.core.io import is_remote
        from mountainash.relations.backends.relation_systems import resource_files as rf

        fmt = MountainashPolarsExtensionRelationSystem._detect_format(resource)
        # Uniform fail-closed (consistency-guarantees) -- see the Polars reader.
        if fmt == "csv":
            rf.ensure_dialect_supported(dialect)
        raw_path = resource.path
        paths = raw_path if isinstance(raw_path, list) else [raw_path]
        all_local = all(not is_remote(p) for p in paths)
        no_glob = all("*" not in p and "?" not in p and "[" not in p for p in paths)
        no_archive = all(not p.lower().endswith((".gz", ".zip")) for p in paths)

        # A native-unsafe CSV dialect (e.g. escape_char) routes to the fallback
        # so it is honoured identically to the other backends.
        native_dialect_ok = fmt != "csv" or rf.dialect_native_safe(dialect)
        if all_local and no_glob and no_archive and fmt in ("csv", "parquet") and native_dialect_ok:
            kwargs = MountainashPolarsExtensionRelationSystem._reader_kwargs(
                resource, fmt, dialect
            )
            scan = nw.scan_csv if fmt == "csv" else nw.scan_parquet
            frames = [scan(p, backend="polars", **(kwargs if fmt == "csv" else {})) for p in paths]
            return frames[0] if len(frames) == 1 else nw.concat(frames, how="vertical")

        # Files fallback: Arrow -> Polars lazy -> Narwhals lazy.
        import polars as pl
        table = rf.parse_resource_to_arrow(resource, dialect=dialect)
        return transit_call(
            BoundaryKey.NARWHALS_NATIVE_WRAP, nw.from_native, pl.from_arrow(table).lazy()
        )

    def empty_frame(self, spec: Any) -> Any:
        """Typed-empty Narwhals LazyFrame (lazy)."""
        import narwhals as nw
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )
        lf = MountainashPolarsExtensionRelationSystem().empty_frame(spec)
        return transit_call(BoundaryKey.NARWHALS_NATIVE_WRAP, nw.from_native, lf)  # stays lazy

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
        if strategy == "nearest" and self._is_pandas(left):
            return self._nearest_forward_wins(left, right, on=on, by=by)
        return left.join_asof(
            right,
            on=on,
            by=by if by else None,
            strategy=strategy,
        )

    @staticmethod
    def _is_pandas(frame: Any) -> bool:
        from narwhals import Implementation
        return getattr(frame, "implementation", None) is Implementation.PANDAS

    def _nearest_forward_wins(
        self, left: Any, right: Any, *, on: str, by: Optional[list[str]]
    ) -> Any:
        """Portable fix (spec §5.3) for the genuine defect: pandas merge_asof
        picks the BACKWARD candidate on an equidistant nearest tie between two
        DIFFERENT-valued candidates, where Polars picks forward. Fixed with a
        dual backward/forward join and a distance comparison.

        Colliding payload names: right payload columns sharing a name with a
        left column are aliased to `{c}_right` up front (mirroring the ibis
        emulation's own convention) -- without this, the `when/then/otherwise`
        alias collides with the identically-named left column already in the
        select list and narwhals raises `DuplicateError`. This is a genuine
        crash fix, kept regardless of the narrower tie-break scope below.

        NOT fixed (declared: NW-REL-05): when the right frame has MULTIPLE
        rows at the SAME matched value (a duplicate-key tie, not a cross-side
        tie), this inherits pandas merge_asof's own first-of-duplicates
        convention on the forward leg and last-of-duplicates on the backward
        leg -- so the winning side's OWN duplicate pick may differ from
        Polars' uniform last-of-tied-group rule. Reproducing that exactly
        needs a within-tie-group row reversal that proved fragile across
        interleaved-by-group inputs in earlier drafts of this plan; the
        narrower, declared-divergence approach is deliberately preferred.
        """
        import narwhals as nw

        by_cols = [by] if isinstance(by, str) else list(by or [])
        left_cols = list(left.columns)
        right_cols = list(right.columns)

        right_payload_raw = [c for c in right_cols if c not in (by_cols + [on])]
        rename_map = {c: (f"{c}_right" if c in left_cols else c) for c in right_payload_raw}
        right_aliased = right.rename(rename_map) if rename_map != {c: c for c in right_payload_raw} else right

        left_id = left.with_row_index("_ma_left_id")
        # Alias the right `on` column before join_asof: narwhals coalesces the
        # shared `on` key into the left's value, so without this the matched
        # right-side key is unrecoverable for a distance comparison.
        right2 = right_aliased.with_columns(nw.col(on).alias("_ma_right_key"))

        back = left_id.join_asof(right2, on=on, by=by_cols or None, strategy="backward")
        fwd = left_id.join_asof(right2, on=on, by=by_cols or None, strategy="forward")
        merged = back.join(fwd, on="_ma_left_id", how="left", suffix="_fwd")

        # Forward wins when it matched and is no farther than the backward
        # candidate (equidistant -> forward, per the normative tie rule).
        fwd_wins = (
            (~merged["_ma_right_key_fwd"].is_null())
            & (
                merged["_ma_right_key"].is_null()
                | (
                    (merged["_ma_right_key_fwd"] - merged[on]).abs()
                    <= (merged["_ma_right_key"] - merged[on]).abs()
                )
            )
        )

        right_payload_out = [rename_map[c] for c in right_payload_raw]
        left_payload = [c for c in left_cols if c not in (by_cols + [on])]

        keep = [merged[on], merged["_ma_left_id"]]
        keep += [merged[c] for c in by_cols]
        keep += [merged[c] for c in left_payload]
        for c in right_payload_out:
            keep.append(
                nw.when(fwd_wins).then(merged[f"{c}_fwd"]).otherwise(merged[c]).alias(c)
            )

        result = merged.select(keep)
        result = result.sort([*by_cols, on, "_ma_left_id"])
        return result.drop("_ma_left_id")
