"""Narwhals implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import narwhals as nw


from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)



def _temporary_name(occupied: set[str]) -> str:
    """Use case-invariant identifiers across native Unicode name resolvers."""
    index = 0
    while (name := f"__{index}") in occupied:
        index += 1
    occupied.add(name)
    return name


def _quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _as_duckdb(relation: Any) -> Any:
    if relation.implementation is nw.Implementation.DUCKDB:
        return relation.to_native()
    if relation.implementation is nw.Implementation.SQLFRAME:
        native = relation.to_native()
        if native.session._is_duckdb:
            return native.session._conn.sql(native.sql(dialect="duckdb", optimize=False))
    return None


def _sample_seed(seed: Optional[int]) -> Optional[int]:
    if seed is not None:
        from operator import index

        seed = index(seed)
        if seed < 0:
            raise ValueError("expected non-negative integer")
    return seed


def _duckdb_sample(native: Any, *, n: Optional[int], fraction: Optional[float], seed: Optional[int]) -> Any:
    seed = _sample_seed(seed)
    columns = native.columns
    occupied = set(columns)
    indexed = native
    order = "random()"
    if seed is not None:
        from duckdb import ConstantExpression

        index = _quote_identifier(_temporary_name(occupied))
        indexed = native.project(f"*, row_number() OVER () - 1 AS {index}")
        literal = str(ConstantExpression(str(seed)))
        order = f"md5({index}::VARCHAR || ':' || {literal}), {index}"
    if n is not None:
        chosen = indexed.order(order).limit(min(n, 2**63 - 1))
    else:
        rank = _quote_identifier(_temporary_name(occupied))
        total = _quote_identifier(_temporary_name(occupied))
        chosen = indexed.project(
            f"*, row_number() OVER (ORDER BY {order}) AS {rank}, count(*) OVER () AS {total}"
        ).filter(
            f"{rank} <= floor({total} * CAST({fraction!r} AS DOUBLE))"
        ).order(rank)
    return chosen.project(", ".join(_quote_identifier(name) for name in columns))


def _spark_sample(relation: Any, *, n: Optional[int], fraction: Optional[float], seed: Optional[int]) -> Any:
    native = relation.to_native()
    F = relation._compliant_frame._F
    Window = relation._compliant_frame._Window
    seed = _sample_seed(seed)
    normalized_seed = None if seed is None else (seed + 2**63) % 2**64 - 2**63
    occupied = set(native.columns)
    key = _temporary_name(occupied)
    keyed = native.withColumn(key, F.rand(normalized_seed))
    if n is not None and n <= 2**31 - 1:
        return keyed.orderBy(F.col(key)).limit(n).drop(key)
    rank = _temporary_name(occupied)
    ranked = keyed.withColumn(
        rank, F.count(F.lit(1)).over(
            Window.orderBy(F.col(key)).rowsBetween(Window.unboundedPreceding, Window.currentRow)
        )
    )
    helpers = [key, rank]
    if n is not None:
        threshold = F.lit(min(n, 2**63 - 1))
    else:
        total = _temporary_name(occupied)
        ranked = ranked.withColumn(
            total, F.count(F.lit(1)).over(
                Window.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
            )
        )
        threshold = F.floor(F.col(total).cast("double") * F.lit(fraction).cast("double"))
        helpers.append(total)
    return ranked.filter(F.col(rank) <= threshold).orderBy(F.col(rank)).drop(*helpers)


def _spark_position(
    relation: Any, *, offset: int = 0, count: Optional[int], from_end: bool = False,
) -> Any:
    native = relation.to_native()
    F = relation._compliant_frame._F
    Window = relation._compliant_frame._Window
    occupied = set(native.columns)
    position = _temporary_name(occupied)
    rank = _temporary_name(occupied)
    ranked = native.withColumn(position, F.monotonically_increasing_id()).withColumn(
        rank, F.count(F.lit(1)).over(
            Window.orderBy(F.col(position)).rowsBetween(Window.unboundedPreceding, Window.currentRow)
        )
    )
    helpers = [position, rank]
    if from_end:
        total = _temporary_name(occupied)
        ranked = ranked.withColumn(
            total, F.count(F.lit(1)).over(
                Window.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
            )
        )
        threshold = F.greatest(F.col(total) - F.lit(min(count, 2**63 - 1)), F.lit(0))
        condition = F.col(rank) > threshold
        helpers.append(total)
    else:
        end = 2**63 - 1 if count is None else min(offset + count, 2**63 - 1)
        condition = (F.col(rank) > min(offset, 2**63 - 1)) & (F.col(rank) <= end)
    return ranked.filter(condition).orderBy(F.col(rank)).drop(*helpers)


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
        # Narwhals pins empty_as_null=True; Polars (the reference) defaults to
        # False, so a row whose lists are all empty yields no row. Non-List
        # columns (e.g. pandas object) keep native explode's own error.
        schema = relation.collect_schema()
        if all(isinstance(schema[c], nw.List) for c in columns):
            all_empty = nw.all_horizontal(
                *[(nw.col(c).list.len() == 0).fill_null(False) for c in columns],
                ignore_nulls=False,
            )
            relation = relation.filter(~all_empty)
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
        is_lazy = isinstance(relation, nw.LazyFrame)
        if is_lazy and relation.implementation.is_polars():
            from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
                MountainashPolarsExtensionRelationSystem,
            )

            sampled = MountainashPolarsExtensionRelationSystem().sample(
                relation.to_native(), n=n, fraction=fraction, seed=seed
            )
            return nw.from_native(sampled)
        if is_lazy:
            native = relation.to_native()
            duckdb_relation = _as_duckdb(relation)
            if duckdb_relation is not None:
                return nw.from_native(_duckdb_sample(duckdb_relation, n=n, fraction=fraction, seed=seed))
            implementation = relation.implementation
            if implementation in {
                nw.Implementation.PYSPARK, nw.Implementation.PYSPARK_CONNECT, nw.Implementation.SQLFRAME,
            }:
                return nw.from_native(_spark_sample(relation, n=n, fraction=fraction, seed=seed))
            if implementation is nw.Implementation.DASK:
                def sample_partition(frame):
                    count = min(n, len(frame)) if n is not None else None
                    return nw.from_native(frame).sample(n=count, fraction=fraction, seed=seed).to_native()
                sampled = native.repartition(npartitions=1).map_partitions(
                    sample_partition, meta=native, clear_divisions=True,
                )
                return nw.from_native(sampled)
            # Some eager providers expose a LazyFrame API wrapper, not a lazy engine.
            frame = nw.from_native(native, eager_only=True)
        else:
            frame = relation
        if n is not None:
            n = min(n, len(frame))
        return frame.sample(n=n, fraction=fraction, seed=seed)

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
        raise BackendCapabilityError(
            "Narwhals does not support frame-level unnest.",
            backend=self.BACKEND_NAME,
            function_key=RKEY_MOUNTAINASH_REL.UNNEST,
        )

    def _native_scan_for(self, resource: Any, dialect: Any) -> bool:
        from mountainash.relations.backends.relation_systems import resource_files as rf
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )

        fmt = MountainashPolarsExtensionRelationSystem._detect_format(resource)
        return rf.polars_native_scan_supported(resource, fmt, dialect)

    def read_resource(self, resource: Any) -> Any:
        """Load a DataResource into a Narwhals LazyFrame. Native lazy scan for
        local plain CSV/Parquet; Arrow-coerced (lazy-wrapped) fallback for JSON,
        glob, archive, remote."""
        from mountainash.core.lowering_reuse import DEFERRED_ONLY, OCCURRENCE

        self._resource_lowering = OCCURRENCE
        import narwhals as nw
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )

        dialect = resource.to_dialect()
        if resource.data is not None:
            reader = MountainashPolarsExtensionRelationSystem()
            lf = reader._read_inline(resource)
            self._resource_lowering = reader._resource_lowering
            return nw.from_native(lf)  # stays lazy

        from mountainash.relations.backends.relation_systems import resource_files as rf

        fmt = MountainashPolarsExtensionRelationSystem._detect_format(resource)
        raw_path = resource.path
        paths = raw_path if isinstance(raw_path, list) else [raw_path]
        if self._native_scan_for(resource, dialect):
            self._resource_lowering = DEFERRED_ONLY
            kwargs = MountainashPolarsExtensionRelationSystem._reader_kwargs(
                resource, fmt, dialect
            )
            scan = nw.scan_csv if fmt == "csv" else nw.scan_parquet
            frames = [scan(p, backend="polars", **(kwargs if fmt == "csv" else {})) for p in paths]
            return frames[0] if len(frames) == 1 else nw.concat(frames, how="vertical")

        # Files fallback: Arrow -> Polars lazy -> Narwhals lazy.
        import polars as pl
        table = rf.parse_resource_to_arrow(resource, dialect=dialect)
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
        if not isinstance(relation, nw.LazyFrame):
            return relation.tail(count)
        native = _as_duckdb(relation)
        if native is not None:
            columns = native.columns
            occupied = set(columns)
            index = _quote_identifier(_temporary_name(occupied))
            total = _quote_identifier(_temporary_name(occupied))
            return nw.from_native(native.project(
                f"*, row_number() OVER () AS {index}, count(*) OVER () AS {total}"
            ).filter(
                f"{index} > greatest({total} - {min(count, 2**63 - 1)}, 0)"
            ).order(index).project(", ".join(_quote_identifier(name) for name in columns)))
        if relation.implementation is nw.Implementation.DASK:
            return nw.from_native(relation.to_native().repartition(npartitions=1).tail(count, compute=False))
        if relation.implementation in {
            nw.Implementation.PYSPARK, nw.Implementation.PYSPARK_CONNECT, nw.Implementation.SQLFRAME,
        }:
            return nw.from_native(_spark_position(relation, count=count, from_end=True))
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
        if tolerance is not None:
            raise BackendCapabilityError(
                "Narwhals join_asof does not expose a tolerance argument.",
                backend="narwhals",
                function_key=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
            )
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

        keep = [merged[c] for c in left_cols] + [merged["_ma_left_id"]]
        for c in right_payload_out:
            keep.append(
                nw.when(fwd_wins).then(merged[f"{c}_fwd"]).otherwise(merged[c]).alias(c)
            )

        result = merged.select(keep)
        result = result.sort([*by_cols, on, "_ma_left_id"])
        return result.drop("_ma_left_id")
