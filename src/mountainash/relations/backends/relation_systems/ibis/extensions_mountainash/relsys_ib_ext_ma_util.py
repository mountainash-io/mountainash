"""Ibis implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import ibis
import ibis.expr.types as ir

from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)
from mountainash.relations.backends.relation_systems.ibis._sqlite_compat import (
    ensure_sqlite_nat_adapter,
)


class MountainashIbisExtensionRelationSystem(MountainashExtensionRelationSystemProtocol[ir.Table]):
    """Mountainash-specific relation operations for the Ibis backend."""

    def drop_nulls(self, relation: ir.Table, /, *, subset: Optional[list[str]] = None) -> ir.Table:
        return relation.drop_null(subset)

    def drop_nans(
        self, relation: ir.Table, /, *, subset: Optional[list[str]] = None
    ) -> ir.Table:
        if subset is None:
            schema = relation.schema()
            subset = [
                name for name, dtype in schema.items()
                if dtype.is_floating()
            ]
        if not subset:
            return relation
        import functools
        import operator
        predicates = [~relation[c].isnan() for c in subset]
        combined = functools.reduce(operator.and_, predicates)
        return relation.filter(combined)

    def with_row_index(self, relation: ir.Table, /, *, name: str = "index") -> ir.Table:
        return relation.mutate(**{name: ibis.row_number()})

    def explode(self, relation: ir.Table, /, *, columns: list[str]) -> ir.Table:
        result = relation
        for col in columns:
            result = result.unnest(col)
        return result

    def sample(
        self,
        relation: ir.Table,
        /,
        *,
        n: Optional[int] = None,
        fraction: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> ir.Table:
        if fraction is not None:
            return relation.sample(fraction, method="row", seed=seed)
        if n is not None:
            total = transit_call(BoundaryKey.IBIS_SCALAR_EXECUTE, relation.count().execute)
            frac = min(n / total, 1.0) if total > 0 else 1.0
            return relation.sample(frac, method="row", seed=seed)
        raise ValueError("Either n or fraction must be specified for sample().")

    def unpivot(
        self,
        relation: ir.Table,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> ir.Table:
        from ibis import selectors as s

        return relation.pivot_longer(
            s.cols(*on),
            names_to=variable_name,
            values_to=value_name,
        )

    def pivot(
        self,
        relation: ir.Table,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> ir.Table:
        kwargs: dict[str, Any] = {
            "on": on,
            "names_from": on,
            "values_agg": aggregate_function,
        }
        if index is not None:
            kwargs["index"] = index
        if values is not None:
            kwargs["values_from"] = values
        return relation.pivot_wider(**kwargs)

    def top_k(
        self, relation: ir.Table, /, *, k: int, by: list[str], descending: bool = True
    ) -> ir.Table:
        order_keys = [ibis.desc(col) if descending else col for col in by]
        return relation.order_by(order_keys).limit(k)

    def unnest(
        self, relation: ir.Table, /, *, columns: list[str], separator: str
    ) -> ir.Table:
        result = relation
        for col in columns:
            struct_col = result[col]
            field_names = struct_col.type().names
            prefix = f"{col}{separator}" if separator else ""
            result = result.mutate(
                **{f"{prefix}{field}": struct_col[field] for field in field_names}
            )
            result = result.drop(col)
        return result

    def read_resource(self, resource: Any, *, provider_binding: object | str | None = None) -> ir.Table:
        """Load a DataResource into an Ibis table. Native engine reads for local
        plain CSV/Parquet (default dialect); Arrow-coerced fallback (no pandas)
        for JSON, glob, archive, remote, and non-default-dialect CSV -- uniform
        with the other backends (spec §A.6)."""
        dialect = resource.to_dialect()
        if provider_binding is not None:
            from mountainash.relations.backends.relation_systems.resource_providers import (
                read_provider_arrow,
            )

            return transit_call(
                BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER,
                ibis.memtable,
                read_provider_arrow(resource, provider_binding),
            )
        if resource.data is not None:
            from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
                MountainashPolarsExtensionRelationSystem,
            )
            lf = MountainashPolarsExtensionRelationSystem()._read_inline(resource)
            ensure_sqlite_nat_adapter()
            arrow = transit_call(BoundaryKey.NON_PANDAS_ARROW_TERMINAL, lf.collect().to_arrow)
            return transit_call(BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER, ibis.memtable, arrow)

        fmt = self._detect_format_name(resource)
        raw_path = resource.path
        assert raw_path is not None, f"DataResource '{resource.name}' has no path"
        paths = raw_path if isinstance(raw_path, list) else [raw_path]

        from mountainash.core.io import is_remote
        from mountainash.relations.backends.relation_systems import resource_files as rf

        if fmt == "csv":
            rf.ensure_dialect_supported(dialect)
        all_local = all(not is_remote(p) for p in paths)
        no_glob = all("*" not in p and "?" not in p and "[" not in p for p in paths)
        no_archive = all(not p.lower().endswith((".gz", ".zip")) for p in paths)
        con = ibis.get_backend()
        # NATIVE only for local plain CSV/Parquet. CSV also requires a default
        # dialect (con.read_csv ignores our dialect). JSON is fallback-routed
        # for parity even though con.read_json exists.
        native = {"csv": "read_csv", "parquet": "read_parquet"}.get(fmt)
        native_ok = (
            all_local and no_glob and no_archive and native
            and hasattr(con, native)
            and (fmt != "csv" or rf.dialect_is_default(dialect))
        )
        if native_ok:
            return getattr(con, native)(paths if len(paths) > 1 else paths[0])

        # Fallback: mountainash-files -> Arrow -> memtable (no pandas). The files
        # reader honours the full CSV dialect via CsvSpec (>=26.7.1).
        ensure_sqlite_nat_adapter()
        return transit_call(
            BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER,
            ibis.memtable,
            rf.parse_resource_to_arrow(resource, dialect=dialect),
        )

    @staticmethod
    def _detect_format_name(resource: Any) -> str:
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )
        return MountainashPolarsExtensionRelationSystem._detect_format(resource)

    def empty_frame(self, spec: Any) -> ir.Table:
        """Typed-empty Ibis table via Arrow (no pandas)."""
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )
        lf = MountainashPolarsExtensionRelationSystem().empty_frame(spec)
        arrow = transit_call(BoundaryKey.NON_PANDAS_ARROW_TERMINAL, lf.collect().to_arrow)
        return transit_call(BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER, ibis.memtable, arrow)

    def fetch_from_end(self, relation: ir.Table, count: int, /) -> ir.Table:
        # Ibis does not have a native .tail() method.
        # Materialise the total row count and compute the offset.
        n = transit_call(BoundaryKey.IBIS_SCALAR_EXECUTE, relation.count().execute)
        offset = max(0, n - count)
        return relation.limit(count, offset=offset)

    def join_asof(
        self,
        left: ir.Table,
        right: ir.Table,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> ir.Table:
        # backward has a native ASOF JOIN translation on duckdb and polars;
        # sqlite has none, and forward/nearest have no native direction
        # control anywhere -- those route through the emulation.
        if strategy == "backward" and self.dialect in ("ibis-duckdb", "ibis-polars"):
            return self._native_asof(left, right, on=on, by=by, tolerance=tolerance)
        return self._emulate_asof(
            left, right, on=on, by=by, strategy=strategy, tolerance=tolerance
        )

    def _native_asof(
        self,
        left: ir.Table,
        right: ir.Table,
        *,
        on: str,
        by: Optional[list[str]],
        tolerance: Any,
    ) -> ir.Table:
        """Native asof_join for `backward` on ibis-duckdb/ibis-polars, with `by`
        translated to predicates (ibis 12 has no `by` parameter) and
        Polars-parity schema (the `{on}_right` column ibis 12.0.0's asof_join
        always emits is dropped -- a pre-existing leak in the current
        codebase, only caught because this plan's tests do full-row Polars-
        oracle equality).

        Two DECLARED (not fixed) divergences from Polars on ibis-duckdb:
        IB-REL-16 (duplicate-right-key ties under backward pick the FIRST row,
        not the LAST) and IB-REL-17 (row order for interleaved `by` groups is
        grouped-by-value, not left-input-preserving). Neither is a value-
        correctness defect -- every matched row is a valid at-or-before match,
        just not necessarily THE SAME one Polars happens to pick among equals.

        One genuine bug IS fixed here, not declared: without an explicit
        secondary sort key, duplicate-LEFT-row order on ibis-duckdb is
        NONDETERMINISTIC (probe-confirmed: varied across 20 fresh-connection
        reps) -- the `_ma_left_id` tiebreak pins this deterministically (and,
        as a side effect, correctly, since duplicate-left-row cases have no
        by-group-interleaving ambiguity). `ibis.row_number()` has no
        translation on ibis-polars (IB-REL-01), and isn't needed there: it
        delegates directly to real Polars' own `join_asof`, which already
        preserves left input order natively and stably with no `order_by` at
        all (probe-confirmed: 20/20 identical reps, including interleaved
        groups) -- adding one there would only break that.
        """
        by_cols = list(by) if by else []
        if self.dialect == "ibis-duckdb":
            left_id = left.mutate(_ma_left_id=ibis.row_number())
            predicates = [left_id[c] == right[c] for c in by_cols]
            result = left_id.asof_join(right, on=on, predicates=predicates, tolerance=tolerance)
            on_right = f"{on}_right"
            drop = [c for c in ([on_right] + [f"{c}_right" for c in by_cols]) if c in result.columns]
            if drop:
                result = result.drop(*drop)
            return result.order_by([*by_cols, on, "_ma_left_id"]).drop("_ma_left_id")

        predicates = [left[c] == right[c] for c in by_cols]
        result = left.asof_join(right, on=on, predicates=predicates, tolerance=tolerance)
        on_right = f"{on}_right"
        drop = [c for c in ([on_right] + [f"{c}_right" for c in by_cols]) if c in result.columns]
        if drop:
            result = result.drop(*drop)
        return result

    def _emulate_asof(
        self,
        left: ir.Table,
        right: ir.Table,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> ir.Table:
        """Emulate an asof join as an Ibis relational expression (spec §5.2)
        for forward/nearest (any SQL dialect) and every strategy on
        ibis-sqlite. Probe-verified (scripts/probes/probe_asof_emulation.py)
        against the Polars oracle for VALUE correctness on every case.

        Composition: presort both inputs by `[by, on]`, assign a row_number
        identity to each, inner-join on the strategy's directional predicate
        (none for `nearest`, ranked purely by distance), rank per left row
        (forward: smallest qualifying key, ties broken by smallest id;
        backward: largest qualifying key, ties broken by largest id; nearest:
        distance then right id descending -- reproduces both "forward wins a
        genuine cross-side tie" and "last wins a same-value duplicate tie"),
        filter rank 0 (0-based), left-keep join, drop internal/collision
        columns.

        DECLARED (not fixed): IB-REL-17 -- the final `order_by([by, on, id])`
        groups rows by `by` value, diverging from Polars' left-input-order
        preservation when groups interleave. Values are always correct.

        Temporal keys: a `datetime.timedelta` tolerance is converted to
        seconds before comparison. Raises BackendCapabilityError for temporal
        on-columns combined with nearest/tolerance on ibis-sqlite (IB-REL-14):
        `IntervalColumn` has no `.abs()`, and `.delta(unit="second")` has no
        sqlite translation (OperationNotDefinedError). Plain forward/backward
        over temporal keys need no distance and work fine on both dialects.
        """
        from datetime import timedelta

        from mountainash.core.types import BackendCapabilityError
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL,
        )

        left_cols = list(left.columns)
        right_cols = list(right.columns)
        by_cols = list(by) if by else []

        is_temporal = left[on].type().is_temporal()
        if self.dialect == "ibis-sqlite" and is_temporal and (
            strategy == "nearest" or tolerance is not None
        ):
            raise BackendCapabilityError(
                "ibis-sqlite has no TimestampDelta translation "
                "(OperationNotDefinedError); temporal join_asof nearest/tolerance "
                "distance cannot be computed on this dialect. Use ibis-duckdb, "
                "polars, or narwhals for temporal nearest/tolerance asof joins.",
                backend="ibis",
                function_key=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
            )

        if is_temporal and isinstance(tolerance, timedelta):
            tolerance = tolerance.total_seconds()

        def _distance(a, b):
            if is_temporal:
                return a.delta(b, unit="second").abs()
            return (a - b).abs()

        left_sorted = left.order_by([*by_cols, on])
        right_sorted = right.order_by([*by_cols, on])
        left_id = left_sorted.mutate(_ma_left_id=ibis.row_number())
        right_id = right_sorted.mutate(_ma_right_id=ibis.row_number())

        if strategy == "forward":
            pred = right_id[on] >= left_id[on]
        elif strategy == "backward":
            pred = right_id[on] <= left_id[on]
        else:  # nearest: no directional filter, ranked purely by distance below
            pred = ibis.literal(True)
        for col in by_cols:
            pred = pred & (right_id[col] == left_id[col])
        if tolerance is not None:
            pred = pred & (_distance(right_id[on], left_id[on]) <= tolerance)

        cand = left_id.join(right_id, pred)
        on_right = f"{on}_right" if on in left_cols else on

        if strategy == "forward":
            rank_order = [cand[on_right], cand["_ma_right_id"]]
        elif strategy == "backward":
            rank_order = [ibis.desc(cand[on_right]), ibis.desc(cand["_ma_right_id"])]
        else:
            rank_order = [_distance(cand[on_right], cand[on]), ibis.desc(cand["_ma_right_id"])]

        ranked = cand.mutate(
            _ma_rank=ibis.row_number().over(
                ibis.window(group_by="_ma_left_id", order_by=rank_order)
            )
        )
        right_out_cols = [c if c not in left_cols else f"{c}_right" for c in right_cols]
        best = ranked.filter(ranked["_ma_rank"] == 0).select("_ma_left_id", *right_out_cols)

        result = left_id.left_join(best, "_ma_left_id")
        drop_cols = {"_ma_left_id_right", on_right} | {f"{c}_right" for c in by_cols}
        result = result.drop(*[c for c in drop_cols if c in result.columns])
        result = result.order_by([*by_cols, on, "_ma_left_id"])
        public = [c for c in result.columns if c != "_ma_left_id"]
        return result.select(*public)
