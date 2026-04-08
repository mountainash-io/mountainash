from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, TypeVar, Union


from mountainash.core.constants import (
    ExecutionTarget,
    ExtensionRelOperation,
    JoinType,
    ProjectOperation,
    SetType,
    SortField,
)
from ..relation_nodes import (
    AggregateRelNode,
    ExtensionRelNode,
    FetchRelNode,
    FilterRelNode,
    JoinRelNode,
    ProjectRelNode,
    ReadRelNode,
    RelationNode,
    SetRelNode,
    SortRelNode,
)
from .relation_base import RelationBase
from .grouped_relation import GroupedRelation

_T = TypeVar("_T")


"""Relation fluent API, factory functions, and helpers.

This module provides the user-facing Relation class whose chainable methods
build relational AST nodes.  No backend execution happens here -- only AST
construction.  Terminal operations (collect, to_polars, ...) delegate to the
compilation machinery in RelationBase.
"""
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_columns(cols: Any) -> Optional[list[str]]:
    """Normalize column arguments to a list of strings or None.

    - str -> [str]
    - list/tuple -> list
    - None -> None
    """
    if cols is None:
        return None
    if isinstance(cols, str):
        return [cols]
    return list(cols)


def _normalize_sort_fields(
    columns: tuple[Any, ...],
    descending: Union[bool, list[bool]],
) -> list[SortField]:
    """Convert column names and descending flags to SortField objects."""
    cols = list(columns)
    if isinstance(descending, bool):
        desc_list = [descending] * len(cols)
    else:
        desc_list = list(descending)
        if len(desc_list) != len(cols):
            raise ValueError(
                f"Length of descending ({len(desc_list)}) does not match "
                f"number of sort columns ({len(cols)})"
            )
    return [
        SortField(column=c, descending=d)
        for c, d in zip(cols, desc_list)
    ]


def _to_relation_node(other: Any) -> RelationNode:
    """Coerce *other* to a RelationNode.

    - If *other* is a Relation, return its underlying node.
    - Otherwise wrap it in a ReadRelNode (assumes raw data).
    """
    if isinstance(other, Relation):
        return other._node
    return ReadRelNode(dataframe=other)


# ---------------------------------------------------------------------------
# Relation
# ---------------------------------------------------------------------------

class Relation(RelationBase):
    """Fluent builder for relational query plans.

    Every chainable method returns a new Relation wrapping a new AST node
    whose ``input`` is the current node.  No execution occurs until a
    terminal operation is called.
    """

    # --- Projection ---

    def select(self, *columns: Any) -> Relation:
        """Select columns."""
        return Relation(
            ProjectRelNode(
                input=self._node,
                expressions=list(columns),
                operation=ProjectOperation.SELECT,
            )
        )

    def with_columns(self, *expressions: Any) -> Relation:
        """Add or overwrite columns."""
        return Relation(
            ProjectRelNode(
                input=self._node,
                expressions=list(expressions),
                operation=ProjectOperation.WITH_COLUMNS,
            )
        )

    def drop(self, *columns: Any) -> Relation:
        """Drop columns."""
        return Relation(
            ProjectRelNode(
                input=self._node,
                expressions=list(columns),
                operation=ProjectOperation.DROP,
            )
        )

    def rename(self, mapping: dict[str, str]) -> Relation:
        """Rename columns according to *mapping*."""
        return Relation(
            ProjectRelNode(
                input=self._node,
                expressions=[],
                operation=ProjectOperation.RENAME,
                rename_mapping=mapping,
            )
        )

    # --- Filtering ---

    def filter(self, *predicates: Any) -> Relation:
        """Filter rows.  Multiple predicates produce chained FilterRelNodes."""
        result = self
        for pred in predicates:
            result = Relation(
                FilterRelNode(input=result._node, predicate=pred)
            )
        return result

    # --- Sorting ---

    def sort(
        self,
        *by: Any,
        descending: Union[bool, list[bool]] = False,
    ) -> Relation:
        """Sort rows."""
        sort_fields = _normalize_sort_fields(by, descending)
        return Relation(
            SortRelNode(input=self._node, sort_fields=sort_fields)
        )

    # --- Fetch (head / tail / slice) ---

    def head(self, n: int = 5) -> Relation:
        """Return the first *n* rows."""
        return Relation(
            FetchRelNode(input=self._node, count=n, from_end=False)
        )

    def tail(self, n: int = 5) -> Relation:
        """Return the last *n* rows."""
        return Relation(
            FetchRelNode(input=self._node, count=n, from_end=True)
        )

    def slice(self, offset: int, length: Optional[int] = None) -> Relation:
        """Return a slice starting at *offset*."""
        return Relation(
            FetchRelNode(input=self._node, offset=offset, count=length)
        )

    # --- Joins ---

    def join(
        self,
        other: Any,
        *,
        on: Optional[Union[str, list[str]]] = None,
        left_on: Optional[Union[str, list[str]]] = None,
        right_on: Optional[Union[str, list[str]]] = None,
        how: str = "inner",
        suffix: str = "_right",
        execute_on: Optional[ExecutionTarget] = None,
    ) -> Relation:
        """Join with another relation or raw data."""
        return Relation(
            JoinRelNode(
                left=self._node,
                right=_to_relation_node(other),
                join_type=JoinType(how),
                on=_normalize_columns(on),
                left_on=_normalize_columns(left_on),
                right_on=_normalize_columns(right_on),
                suffix=suffix,
                execute_on=execute_on,
            )
        )

    def join_asof(
        self,
        other: Any,
        *,
        on: Optional[Union[str, list[str]]] = None,
        by: Optional[Union[str, list[str]]] = None,
        strategy: str = "backward",
        tolerance: Any = None,
    ) -> Relation:
        """Asof join with another relation or raw data."""
        return Relation(
            JoinRelNode(
                left=self._node,
                right=_to_relation_node(other),
                join_type=JoinType.ASOF,
                on=_normalize_columns(on),
                strategy=strategy,
                tolerance=tolerance,
            )
        )

    # --- Aggregation ---

    def group_by(self, *keys: Any) -> GroupedRelation:
        """Group rows by *keys*, returning a GroupedRelation."""
        return GroupedRelation(self._node, list(keys))

    def unique(
        self,
        *columns: Any,
        subset: Optional[list[str]] = None,
        keep: str = "any",
    ) -> Relation:
        """Return distinct rows.  Implemented as an aggregate with no measures."""
        keys = list(columns) if columns else (subset or [])
        return Relation(
            AggregateRelNode(input=self._node, keys=keys, measures=[])
        )

    # --- Extension operations ---

    def drop_nulls(self, *, subset: Optional[list[str]] = None) -> Relation:
        """Drop rows containing null values."""
        options: dict[str, Any] = {}
        if subset is not None:
            options["subset"] = subset
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.DROP_NULLS,
                options=options,
            )
        )

    def with_row_index(self, *, name: str = "index") -> Relation:
        """Add a row-index column."""
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.WITH_ROW_INDEX,
                options={"name": name},
            )
        )

    def explode(self, *columns: Any) -> Relation:
        """Explode list columns into rows."""
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.EXPLODE,
                options={"columns": list(columns)},
            )
        )

    def sample(
        self,
        *,
        n: Optional[int] = None,
        fraction: Optional[float] = None,
    ) -> Relation:
        """Sample rows."""
        options: dict[str, Any] = {}
        if n is not None:
            options["n"] = n
        if fraction is not None:
            options["fraction"] = fraction
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.SAMPLE,
                options=options,
            )
        )

    def unpivot(
        self,
        *,
        on: Union[str, list[str]],
        index: Optional[Union[str, list[str]]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> Relation:
        """Unpivot (melt) from wide to long format."""
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.UNPIVOT,
                options={
                    "on": _normalize_columns(on),
                    "index": _normalize_columns(index),
                    "variable_name": variable_name,
                    "value_name": value_name,
                },
            )
        )

    def pivot(
        self,
        *,
        on: Union[str, list[str]],
        index: Optional[Union[str, list[str]]] = None,
        values: Optional[Union[str, list[str]]] = None,
        aggregate_function: str = "first",
    ) -> Relation:
        """Pivot from long to wide format."""
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.PIVOT,
                options={
                    "on": _normalize_columns(on),
                    "index": _normalize_columns(index),
                    "values": _normalize_columns(values),
                    "aggregate_function": aggregate_function,
                },
            )
        )

    def top_k(
        self,
        k: int,
        *,
        by: Union[str, list[str]],
        descending: bool = True,
    ) -> Relation:
        """Return the top *k* rows ordered by *by*."""
        return Relation(
            ExtensionRelNode(
                input=self._node,
                operation=ExtensionRelOperation.TOP_K,
                options={
                    "k": k,
                    "by": _normalize_columns(by),
                    "descending": descending,
                },
            )
        )

    # --- Pipe ---

    def pipe(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Apply an arbitrary function to this Relation."""
        return func(self, *args, **kwargs)

    # --- Terminal operations ---

    def collect(self) -> Any:
        """Execute the plan and return the native backend result."""
        return self._compile_and_execute()

    def item(self, column: str, row: int = 0) -> Any:
        """Extract a single cell value as a Python scalar with strict semantics.

        The relation is materialised via the existing ``to_polars()`` terminal,
        and the cell is extracted via Polars' ``Series`` scalar accessor
        (which handles native → Python conversion for datetime, decimal, etc.).

        Args:
            column: Column name to extract. Must exist in the result.
            row: Row index; must satisfy ``0 <= row < number_of_rows``.
                Defaults to ``0``. Negative indexing is **not** supported.

        Returns:
            The cell value as a Python scalar.

        Raises:
            KeyError: if ``column`` is not present in the result.
            IndexError: if ``row < 0``, if ``row >= number_of_rows``, or if
                the relation is empty.
            RelationDAGRequired: if the relation contains a ``RefRelNode`` and
                is compiled standalone.
        """
        df = self.to_polars()

        if column not in df.columns:
            raise KeyError(column)

        n = len(df)
        if row < 0 or row >= n:
            raise IndexError(
                f"row {row} out of range for relation with {n} row(s) "
                f"in column {column!r}"
            )

        return df[column][row]

    def count_rows(self) -> int:
        """Execute the relation and return the number of rows as a Python int.

        Implemented as a thin composition: wraps ``self._node`` in an
        ``AggregateRelNode`` with a single ``count_records()`` measure, compiles
        via the standard visitor pipeline, and extracts the single scalar
        from the single-row result. No per-backend dispatch — all backend
        variance lives inside the ``count_records`` aggregate implementations.

        Returns:
            Row count as a Python ``int``. Returns ``0`` for an empty relation.

        Raises:
            RelationDAGRequired: if the relation contains a ``RefRelNode`` and
                is compiled standalone instead of inside
                ``RelationDAG.collect()``.
        """
        import mountainash as ma

        counted = Relation(
            AggregateRelNode(
                input=self._node,
                keys=[],
                measures=[ma.count_records().alias("__count_rows__")],
            )
        )
        return int(counted.item("__count_rows__"))

    # ------------------------------------------------------------------
    # Scalar aggregate terminals
    #
    # Each method is a thin composition over the corresponding aggregate
    # expression function. The pattern is identical to ``count_rows()``:
    # wrap ``self._node`` in an AggregateRelNode with empty keys, compile
    # via the existing visitor pipeline, extract via ``.item(...)``.
    # ------------------------------------------------------------------

    def _scalar_aggregate(self, agg_expr: Any) -> Any:
        """Internal helper: aggregate the relation to one row, extract scalar."""
        aggregated = Relation(
            AggregateRelNode(
                input=self._node,
                keys=[],
                measures=[agg_expr.alias("__value__")],
            )
        )
        return aggregated.item("__value__")

    def sum(self, col: str) -> Any:
        """Return the sum of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).sum())

    def avg(self, col: str) -> Any:
        """Return the arithmetic mean of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).avg())

    def mean(self, col: str) -> Any:
        """Short alias for :meth:`avg`."""
        return self.avg(col)

    def min(self, col: str) -> Any:
        """Return the minimum value in ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).min())

    def max(self, col: str) -> Any:
        """Return the maximum value in ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).max())

    def product(self, col: str) -> Any:
        """Return the product of values in ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).product())

    def std_dev(self, col: str) -> Any:
        """Return the standard deviation of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).std_dev())

    def variance(self, col: str) -> Any:
        """Return the variance of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).variance())

    def any_value(self, col: str) -> Any:
        """Return one representative value from ``col`` as a Python scalar.

        Note: nondeterministic — different backends may return different
        representatives across runs.
        """
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).any_value())

    def to_polars(self) -> Any:
        """Execute and return a Polars DataFrame."""
        from mountainash.core.types import is_polars_dataframe, is_polars_lazyframe

        result = self._compile_and_execute()
        if is_polars_dataframe(result):
            return result
        if is_polars_lazyframe(result):
            return result.collect()
        # Fallback for other backends
        import polars as pl
        return pl.from_pandas(result.to_pandas())

    def to_pandas(self) -> Any:
        """Execute and return a Pandas DataFrame."""
        result = self._compile_and_execute()
        if hasattr(result, "to_pandas"):
            return result.to_pandas()
        return result

    def to_dict(self) -> dict[str, list[Any]]:
        """Execute and return a dict of column name -> list of values."""
        return self.to_polars().to_dict(as_series=False)

    def to_dicts(self) -> list[dict[str, Any]]:
        """Execute and return a list of row dicts."""
        return self.to_polars().to_dicts()

    def to_tuples(self) -> list[tuple]:
        """Execute the plan and return rows as a list of tuples."""
        df = self.to_polars()
        return df.rows()

    def to_dataclasses(self, cls: type[_T]) -> list[_T]:
        """Execute the plan and return rows as a list of dataclass instances.

        Args:
            cls: The dataclass type to instantiate for each row.

        Returns:
            List of dataclass instances.
        """
        rows = self.to_dicts()
        return [cls(**row) for row in rows]

    def to_pydantic(self, cls: type[_T]) -> list[_T]:
        """Execute the plan and return rows as a list of Pydantic model instances.

        Uses model_validate for Pydantic models (proper validation),
        falls back to direct construction for other types.

        Args:
            cls: The Pydantic model class to instantiate for each row.

        Returns:
            List of Pydantic model instances.
        """
        rows = self.to_dicts()
        if hasattr(cls, "model_validate"):
            return [cls.model_validate(row) for row in rows]
        return [cls(**row) for row in rows]

    # --- Introspection ---

    @property
    def columns(self) -> list[str]:
        """Execute and return column names."""
        result = self._compile_and_execute()
        return list(result.columns)


# ---------------------------------------------------------------------------
# Module-level factory functions
# ---------------------------------------------------------------------------

def _is_python_data(data: Any) -> bool:
    """Check if data is a Python data structure suitable for PydataIngress.

    Returns True for list, dict, dataclass instances, and Pydantic model
    instances — the primary types that PydataIngressFactory can detect and
    convert.  Returns False for everything else (DataFrames, strings,
    tuples, sets, opaque objects) which should go through ReadRelNode.
    """
    if isinstance(data, (list, dict)):
        return True
    # Dataclass and Pydantic model instances
    if hasattr(data, "__dataclass_fields__") or hasattr(data, "__pydantic_core_schema__"):
        return True
    return False


def relation(data: Any) -> Relation:
    """Create a Relation from a DataFrame or Python data.

    - DataFrames (Polars, Pandas, Ibis, etc.) and other opaque objects
      produce a ReadRelNode.
    - Python data structures (list, dict, dataclass, Pydantic model, etc.)
      produce a SourceRelNode for deferred ingress via PydataIngress.
    """
    if _is_python_data(data):
        from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory
        from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
        from ..relation_nodes import SourceRelNode

        detected = PydataIngressFactory._get_strategy_key(data)
        if detected is None:
            detected = CONST_PYTHON_DATAFORMAT.UNKNOWN

        return Relation(SourceRelNode(data=data, detected_format=detected))

    return Relation(ReadRelNode(dataframe=data))


def concat(relations: Sequence[Relation]) -> Relation:
    """Concatenate multiple Relations via UNION ALL."""
    nodes = [r._node for r in relations]
    return Relation(SetRelNode(inputs=nodes, set_type=SetType.UNION_ALL))
