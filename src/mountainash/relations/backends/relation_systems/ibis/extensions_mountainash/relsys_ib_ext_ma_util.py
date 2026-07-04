"""Ibis implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import ibis
import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
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
        self, relation: ir.Table, /, *, n: Optional[int] = None, fraction: Optional[float] = None
    ) -> ir.Table:
        if fraction is not None:
            return relation.sample(fraction)
        if n is not None:
            total = relation.count().execute()
            frac = min(n / total, 1.0) if total > 0 else 1.0
            return relation.sample(frac)
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

    def read_resource(self, resource: Any) -> ir.Table:
        """Load a DataResource into an Ibis table. Native engine reads for local
        plain CSV/Parquet (default dialect); Arrow-coerced fallback (no pandas)
        for JSON, glob, archive, remote, and non-default-dialect CSV -- uniform
        with the other backends (spec §A.6)."""
        if resource.data is not None:
            from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
                MountainashPolarsExtensionRelationSystem,
            )
            lf = MountainashPolarsExtensionRelationSystem()._read_inline(resource)
            return ibis.memtable(lf.collect().to_arrow())

        fmt = self._detect_format_name(resource)
        raw_path = resource.path
        paths = raw_path if isinstance(raw_path, list) else [raw_path]

        from mountainash.core.io import is_remote
        from mountainash.relations.backends.relation_systems import resource_files as rf

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
            and (fmt != "csv" or rf.dialect_is_default(resource.dialect))
        )
        if native_ok:
            return getattr(con, native)(paths if len(paths) > 1 else paths[0])

        # Fallback: mountainash-files -> Arrow -> memtable (no pandas). The files
        # reader honours the full CSV dialect via CsvSpec (>=26.7.1).
        return ibis.memtable(rf.parse_resource_to_arrow(resource))

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
        return ibis.memtable(lf.collect().to_arrow())
