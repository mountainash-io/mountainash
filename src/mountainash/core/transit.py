"""Closed transit policy registry, trace capture, and the ``transit_call()`` wrapper.

Every production call that can produce a pandas value routes through
``transit_call()`` with a literal :class:`BoundaryKey`. The wrapper enforces
the registered :class:`TransitClass` policy for that boundary unconditionally,
and — only while a :class:`ConversionTrace` is active via
``capture_conversion_trace()`` — records a :class:`ConversionRecord` for
test-time verification. Without an active trace, no record, identity, or
context object is allocated.

See ``mountainash-central/04.planning/mountainash/superpowers/specs/
2026-08-27-pandas-transit-elimination-design.md`` sections 6 and 12 for the
governing design.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

from mountainash.core.errors import BackendConversionError

T = TypeVar("T")

_UNSET: Any = object()


class TransitClass(Enum):
    """Policy classification for a conversion boundary.

    The first four members are permitted, each under its own rule (spec
    section 6.2). ``INTERNAL_EXECUTION_TRANSIT`` is always prohibited.
    ``NON_PANDAS_OPERATION`` is an audit-only disposition for a route that
    must never observe a pandas result.
    """

    EXPLICIT_PANDAS_INPUT = auto()
    EXPLICIT_PANDAS_EGRESS = auto()
    RESULT_DIAGNOSTIC_VIEW = auto()
    SEMANTICS_PRESERVING_ADAPTER = auto()
    INTERNAL_EXECUTION_TRANSIT = auto()
    NON_PANDAS_OPERATION = auto()


class RouteKey(Enum):
    """Named conversion route a boundary belongs to."""

    NATIVE_MATERIALIZATION = auto()
    EXPLICIT_POLARS_EGRESS = auto()
    EXPLICIT_PANDAS_EGRESS = auto()
    DIAGNOSTIC_POLARS_VIEW = auto()
    CROSS_FAMILY_COERCION = auto()
    NARWHALS_DIALECT_COERCION = auto()
    RESOURCE_READ = auto()
    SCHEMA_INSPECTION = auto()
    PYDATA_INGRESS = auto()
    PYDATA_EGRESS = auto()
    RESULT_PROCESSING = auto()
    IBIS_SCALAR_TERMINAL = auto()
    LOGICAL_SNAPSHOT_CAPTURE = auto()
    LOGICAL_SNAPSHOT_POLARS_OUTPUT = auto()
    LOGICAL_SNAPSHOT_PANDAS_OUTPUT = auto()


class BoundaryKey(Enum):
    """Every literal boundary a production call site can declare.

    A boundary key has exactly one :class:`BoundarySpec` in
    ``BOUNDARY_REGISTRY``. Later tasks add members here and a matching
    registry entry in the same commit that wires their call site.
    """

    POLARS_LAZY_COLLECT = auto()
    NARWHALS_LAZY_COLLECT = auto()
    NARWHALS_NATIVE_UNWRAP_PANDAS = auto()
    NARWHALS_NATIVE_UNWRAP_NON_PANDAS = auto()
    IBIS_NATIVE_CACHE = auto()
    IBIS_INTERNAL_EXECUTE = auto()
    IBIS_TO_ARROW_EGRESS = auto()
    ARROW_TO_POLARS_EGRESS = auto()
    PANDAS_TO_POLARS_EGRESS = auto()
    NARWHALS_TO_POLARS_EGRESS = auto()
    POLARS_TO_PANDAS_EGRESS = auto()
    NARWHALS_TO_PANDAS_EGRESS = auto()
    IBIS_TO_PANDAS_EGRESS = auto()
    ARROW_TO_PANDAS_EGRESS = auto()
    NARWHALS_FROM_DICT_ADAPTER = auto()
    NARWHALS_FROM_DICTS_ADAPTER = auto()
    ARROW_TO_IBIS_ADAPTER = auto()
    NARWHALS_DIALECT_TO_PANDAS = auto()
    NARWHALS_DIALECT_TO_POLARS = auto()
    NARWHALS_DIALECT_TO_ARROW = auto()
    RELATION_TO_POLARS_TERMINAL = auto()
    NATIVE_LAZY_COLLECT = auto()
    NARWHALS_NATIVE_WRAP = auto()
    NON_PANDAS_ARROW_TERMINAL = auto()
    IBIS_CONSTRUCTOR_ADAPTER = auto()
    IBIS_SCALAR_EXECUTE = auto()
    DAG_PROTOTYPE_ADAPTER = auto()
    PYDATA_EXPLICIT_PANDAS_INPUT = auto()
    PYDATA_EXPLICIT_PANDAS_EGRESS = auto()
    PIPELINE_STEP_EXECUTOR = auto()
    RESULT_PROCESSOR_POLARS_MATERIALIZE = auto()
    NARWHALS_SCHEMA_UNWRAP = auto()
    DIAGNOSTIC_VIEW_FROM_PANDAS = auto()
    DIAGNOSTIC_VIEW_FROM_ARROW = auto()
    LOGICAL_SNAPSHOT_IBIS_TO_ARROW = auto()
    LOGICAL_SNAPSHOT_NARWHALS_TO_ARROW = auto()
    LOGICAL_SNAPSHOT_PANDAS_TO_POLARS = auto()
    LOGICAL_SNAPSHOT_ARROW_TO_POLARS = auto()
    LOGICAL_SNAPSHOT_POLARS_TO_PANDAS = auto()
    LOGICAL_SNAPSHOT_ARROW_TO_PANDAS = auto()
    LOGICAL_SNAPSHOT_PANDAS_FRAME_ASSEMBLY = auto()
    LOGICAL_SNAPSHOT_POLARS_DISPATCH = auto()
    LOGICAL_SNAPSHOT_PANDAS_DISPATCH = auto()


@dataclass(frozen=True)
class BoundarySpec:
    """Immutable policy declaration for one :class:`BoundaryKey`."""

    owner: str
    consumer: str
    route: RouteKey
    step: int
    transit_class: TransitClass
    source_families: frozenset[str]
    source_dialects: frozenset[str | None]
    destination_families: frozenset[str]
    destination_dialects: frozenset[str | None]
    reason: str
    since: date


_SINCE_2026_08_27 = date(2026, 8, 27)
_MATERIALIZATION_OWNER = "mountainash.relations.core.materialization"
_LOGICAL_SNAPSHOT_OWNER = "mountainash.relations.core.logical_snapshot"

BOUNDARY_REGISTRY: dict[BoundaryKey, BoundarySpec] = {
    BoundaryKey.POLARS_LAZY_COLLECT: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="native relation collection",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars"}),
        source_dialects=frozenset({"polars"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "Polars LazyFrame.collect() stays a native Polars eager frame; "
            "no cross-family conversion occurs."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_LAZY_COLLECT: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="native relation collection",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-lazy"}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset({"narwhals-polars", "narwhals-pyarrow"}),
        reason=(
            "Narwhals LazyFrame.collect() stays within the underlying "
            "non-pandas backend detected at runtime; no cross-family "
            "conversion occurs."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_NATIVE_UNWRAP_PANDAS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="pandas-selected narwhals native unwrap",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_INPUT,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-pandas"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"narwhals-pandas"}),
        reason=(
            "A Narwhals frame wrapping a selected pandas backend unwraps to "
            "its native pandas value; pandas is the declared source identity."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_NATIVE_UNWRAP_NON_PANDAS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="non-pandas narwhals native unwrap",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-polars", "narwhals-pyarrow"}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset({"narwhals-polars", "narwhals-pyarrow"}),
        reason=(
            "A Narwhals frame wrapping a non-pandas backend unwraps to its "
            "native Polars or PyArrow value; no pandas transit occurs."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.IBIS_NATIVE_CACHE: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="ibis validation-source native cache",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"ibis"}),
        source_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        destination_families=frozenset({"ibis"}),
        destination_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        reason=(
            "Table.cache() eagerly materializes within the same Ibis backend "
            "and dialect; no cross-family conversion occurs."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.IBIS_INTERNAL_EXECUTE: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="prohibited ibis internal execute",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.INTERNAL_EXECUTION_TRANSIT,
        source_families=frozenset({"ibis"}),
        source_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"narwhals-pandas"}),
        reason=(
            "Ibis Table.execute() converts a successful result to pandas "
            "before relation wrapping, silently changing backend identity "
            "and null/NaN semantics. Permanently prohibited; the "
            "specification stays registered only for the negative synthetic "
            "proof once production call sites stop using it."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.IBIS_TO_ARROW_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit Polars egress from Ibis",
        route=RouteKey.EXPLICIT_POLARS_EGRESS,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"ibis"}),
        source_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        destination_families=frozenset({"pyarrow"}),
        destination_dialects=frozenset({"pyarrow"}),
        reason=(
            "Ibis Table.to_pyarrow() is the Arrow-preserving first step of "
            "explicit_polars_egress(); Arrow keeps date32/temporal types a "
            "pandas round-trip would widen (spec 4.4)."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.ARROW_TO_POLARS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit Polars egress from Arrow",
        route=RouteKey.EXPLICIT_POLARS_EGRESS,
        step=2,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"pyarrow"}),
        source_dialects=frozenset({"pyarrow"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "pl.from_arrow() converts a PyArrow table to Polars, whether "
            "chained after IBIS_TO_ARROW_EGRESS or from a direct PyArrow "
            "source; never touches pandas."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.PANDAS_TO_POLARS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit Polars egress from a pandas-selected source",
        route=RouteKey.EXPLICIT_POLARS_EGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_INPUT,
        source_families=frozenset({"pandas"}),
        source_dialects=frozenset({"pandas", "narwhals-pandas"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "pl.from_pandas() converts a declared pandas-selected source to "
            "Polars; the source identity is pandas, not an internal "
            "conversion detail."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_TO_POLARS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit Polars egress from Narwhals",
        route=RouteKey.EXPLICIT_POLARS_EGRESS,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-polars", "narwhals-pandas", "narwhals-pyarrow"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "Narwhals DataFrame.to_polars() is narwhals' own declared "
            "conversion API; its destination is always Polars regardless of "
            "the wrapped backend."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.POLARS_TO_PANDAS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit pandas egress from Polars",
        route=RouteKey.EXPLICIT_PANDAS_EGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"polars"}),
        source_dialects=frozenset({"polars"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason="A declared, user-visible pandas terminal via Polars' own to_pandas().",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_TO_PANDAS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit pandas egress from Narwhals",
        route=RouteKey.EXPLICIT_PANDAS_EGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-polars", "narwhals-pyarrow"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason=(
            "A declared, user-visible pandas terminal via Narwhals' own "
            "to_pandas() for a non-pandas-selected source."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.IBIS_TO_PANDAS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit pandas egress from Ibis",
        route=RouteKey.EXPLICIT_PANDAS_EGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"ibis"}),
        source_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason=(
            "A declared, user-visible pandas terminal via Ibis Table's own "
            "to_pandas() -- called directly, never through "
            "explicit_polars_egress()."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.ARROW_TO_PANDAS_EGRESS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="explicit pandas egress from PyArrow",
        route=RouteKey.EXPLICIT_PANDAS_EGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"pyarrow"}),
        source_dialects=frozenset({"pyarrow"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason="A declared, user-visible pandas terminal via PyArrow Table.to_pandas().",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_FROM_DICT_ADAPTER: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="cross-type join column-mapping adapter",
        route=RouteKey.CROSS_FAMILY_COERCION,
        step=1,
        transit_class=TransitClass.SEMANTICS_PRESERVING_ADAPTER,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset(
            {"narwhals-pandas", "narwhals-polars", "narwhals-pyarrow"}
        ),
        reason=(
            "nw.from_dict(data, backend=target_namespace) builds a "
            "destination-native Narwhals frame from a column mapping; "
            "replaces the pd.DataFrame() fallback (spec 4.3/9)."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_FROM_DICTS_ADAPTER: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="cross-type join row-mapping adapter",
        route=RouteKey.CROSS_FAMILY_COERCION,
        step=1,
        transit_class=TransitClass.SEMANTICS_PRESERVING_ADAPTER,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset(
            {"narwhals-pandas", "narwhals-polars", "narwhals-pyarrow"}
        ),
        reason=(
            "nw.from_dicts(rows, backend=target_namespace) builds a "
            "destination-native Narwhals frame from a sequence of row "
            "mappings; replaces the pd.DataFrame() fallback (spec 4.3/9)."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.ARROW_TO_IBIS_ADAPTER: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="cross-type join Ibis construction from Arrow",
        route=RouteKey.CROSS_FAMILY_COERCION,
        step=2,
        transit_class=TransitClass.SEMANTICS_PRESERVING_ADAPTER,
        source_families=frozenset({"pyarrow"}),
        source_dialects=frozenset({"pyarrow"}),
        destination_families=frozenset({"ibis"}),
        destination_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        reason=(
            "ibis.memtable(arrow_table) after converting a dict/row-mapping "
            "operand to Arrow first; avoids Ibis's own internal pandas "
            "construction from a raw dict/list (spec 4.4)."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_DIALECT_TO_PANDAS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="same-family Narwhals dialect coercion to pandas",
        route=RouteKey.NARWHALS_DIALECT_COERCION,
        step=1,
        transit_class=TransitClass.SEMANTICS_PRESERVING_ADAPTER,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-polars", "narwhals-pyarrow"}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset({"narwhals-pandas"}),
        reason=(
            "Narwhals DataFrame.to_pandas() when the join/union target's "
            "own dialect is narwhals-pandas; a declared same-family dialect "
            "match, not an internal execution transit."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_DIALECT_TO_POLARS: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="same-family Narwhals dialect coercion to polars",
        route=RouteKey.NARWHALS_DIALECT_COERCION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-pandas", "narwhals-pyarrow"}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset({"narwhals-polars"}),
        reason="Narwhals DataFrame.to_polars() to match the target's narwhals-polars dialect.",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_DIALECT_TO_ARROW: BoundarySpec(
        owner=_MATERIALIZATION_OWNER,
        consumer="same-family Narwhals dialect coercion to pyarrow",
        route=RouteKey.NARWHALS_DIALECT_COERCION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-pandas", "narwhals-polars"}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset({"narwhals-pyarrow"}),
        reason="Narwhals DataFrame.to_arrow() to match the target's narwhals-pyarrow dialect.",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.RELATION_TO_POLARS_TERMINAL: BoundarySpec(
        owner="mountainash.relations.core.relation_api.relation",
        consumer="Relation terminal/intermediate Polars materialization",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars", "narwhals", "ibis", "pyarrow"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "A declared Polars-producing terminal or intermediate call on a "
            "Relation, egress/ingress converter, validator, or processor; "
            "its result is never pandas by contract."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NATIVE_LAZY_COLLECT: BoundarySpec(
        owner="mountainash.relations.core.relation_api.relation",
        consumer="native lazy-frame or relation materialization outside the shared session",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars", "narwhals"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"polars", "narwhals"}),
        destination_dialects=frozenset({None}),
        reason=(
            "Native materialization of a Polars/Narwhals lazy frame or a "
            "Mountainash relation whose declared terminal never itself "
            "constructs pandas."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_NATIVE_WRAP: BoundarySpec(
        owner=(
            "mountainash.relations.backends.relation_systems.narwhals."
            "extensions_mountainash.relsys_nw_ext_ma_util"
        ),
        consumer="narwhals wrap of an arbitrary native value for reading, inspection, or coercion",
        route=RouteKey.RESOURCE_READ,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars", "pandas", "pyarrow", "narwhals"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"narwhals"}),
        destination_dialects=frozenset({None}),
        reason=(
            "Wraps an arbitrary native value into a Narwhals frame for "
            "inspection, resource reading, or adapter ingestion; the wrap "
            "call itself never constructs pandas."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NON_PANDAS_ARROW_TERMINAL: BoundarySpec(
        owner="mountainash.relations.core.relation_api.relation",
        consumer="declared PyArrow-producing terminal",
        route=RouteKey.PYDATA_EGRESS,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars", "narwhals", "ibis"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"pyarrow"}),
        destination_dialects=frozenset({"pyarrow"}),
        reason="A declared PyArrow-producing terminal; never pandas.",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER: BoundarySpec(
        owner=(
            "mountainash.relations.backends.relation_systems.ibis."
            "extensions_mountainash.relsys_ib_ext_ma_util"
        ),
        consumer="declared Ibis table construction from Arrow or resource-native input",
        route=RouteKey.RESOURCE_READ,
        step=1,
        transit_class=TransitClass.SEMANTICS_PRESERVING_ADAPTER,
        source_families=frozenset({"pyarrow", "polars", "narwhals", "pandas"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"ibis"}),
        destination_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        reason="Declared Ibis table construction from Arrow or resource-native input.",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.IBIS_SCALAR_EXECUTE: BoundarySpec(
        owner=(
            "mountainash.relations.backends.relation_systems.ibis."
            "extensions_mountainash.relsys_ib_ext_ma_util"
        ),
        consumer="Ibis scalar/count execution",
        route=RouteKey.IBIS_SCALAR_TERMINAL,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"ibis"}),
        source_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        destination_families=frozenset({"python"}),
        destination_dialects=frozenset({None}),
        reason=(
            "Ibis scalar/count execution; the result is a Python scalar, "
            "never a pandas frame."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.DAG_PROTOTYPE_ADAPTER: BoundarySpec(
        owner="mountainash.relations.dag.materialization",
        consumer="DAG cross-dialect anchor prototype construction",
        route=RouteKey.RESOURCE_READ,
        step=1,
        transit_class=TransitClass.SEMANTICS_PRESERVING_ADAPTER,
        source_families=frozenset({"pandas", "polars", "pyarrow"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"narwhals", "ibis"}),
        destination_dialects=frozenset({None}),
        reason=(
            "Wraps an empty native placeholder (Polars/PyArrow/pandas) into "
            "Narwhals or Ibis for the DAG's declared cross-dialect prototype "
            "adapter."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.PYDATA_EXPLICIT_PANDAS_INPUT: BoundarySpec(
        owner="mountainash.pydata.ingress.ingress_from_series",
        consumer="explicit pandas-selected pydata ingress source",
        route=RouteKey.PYDATA_INGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_INPUT,
        source_families=frozenset({"python", "pandas"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"pandas", "polars"}),
        destination_dialects=frozenset({None}),
        reason=(
            "pd.DataFrame()/pl.from_pandas(): a declared pandas-selected "
            "source or destination construction for pydata ingress."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.PYDATA_EXPLICIT_PANDAS_EGRESS: BoundarySpec(
        owner="mountainash.pydata.egress.egress_pydata_from_polars",
        consumer="explicit user-visible pandas pydata egress terminal",
        route=RouteKey.PYDATA_EGRESS,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"polars"}),
        source_dialects=frozenset({"polars"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason="A declared, user-visible pandas terminal.",
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.PIPELINE_STEP_EXECUTOR: BoundarySpec(
        owner="mountainash.pipelines.integration.relation",
        consumer="pipeline-step executor invocation",
        route=RouteKey.NATIVE_MATERIALIZATION,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"python"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"python"}),
        destination_dialects=frozenset({None}),
        reason=(
            "node.executor.execute(...) is a pipeline-step executor call, "
            "unrelated to Ibis Table.execute() or any backend conversion; "
            "syntactically risky-named only."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.RESULT_PROCESSOR_POLARS_MATERIALIZE: BoundarySpec(
        owner="mountainash.datacontracts.result_processor",
        consumer="ValidationResultProcessor internal Polars diagnostic materialization",
        route=RouteKey.RESULT_PROCESSING,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars"}),
        source_dialects=frozenset({"polars"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "ValidationResultProcessor's internal frame source and every "
            "produced diagnostic are Polars-only by contract; the "
            "collect()/to_polars() calls that build and filter them never "
            "touch pandas."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.NARWHALS_SCHEMA_UNWRAP: BoundarySpec(
        owner="mountainash.typespec.source_shape",
        consumer="narwhals frame unwrap for schema/metadata inspection",
        route=RouteKey.SCHEMA_INSPECTION,
        step=1,
        transit_class=TransitClass.RESULT_DIAGNOSTIC_VIEW,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"pandas", "polars", "narwhals", "pyarrow"}),
        destination_dialects=frozenset({None}),
        reason=(
            "Unwraps a Narwhals frame to its native value for schema/dtype "
            "inspection only; the unwrapped value (including a pandas "
            "DataFrame when the source is pandas-backed) never escapes as "
            "data, only as SourceShape metadata."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.DIAGNOSTIC_VIEW_FROM_PANDAS: BoundarySpec(
        owner="mountainash.relations.core.materialization",
        consumer="diagnostic Polars view built from a pandas-selected native value",
        route=RouteKey.DIAGNOSTIC_POLARS_VIEW,
        step=1,
        transit_class=TransitClass.RESULT_DIAGNOSTIC_VIEW,
        source_families=frozenset({"pandas"}),
        source_dialects=frozenset({"pandas", "narwhals-pandas"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "diagnostic_polars_view() wraps a pandas-selected native value "
            "for read-only diagnostic/result transport only (spec 6.2's "
            "RESULT_DIAGNOSTIC_VIEW class); never returned to execution, "
            "stored in a relation leaf, or cached in a DAG resolver."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.DIAGNOSTIC_VIEW_FROM_ARROW: BoundarySpec(
        owner="mountainash.relations.core.materialization",
        consumer="diagnostic Polars view built via a to_arrow()/to_pyarrow() terminal",
        route=RouteKey.DIAGNOSTIC_POLARS_VIEW,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"ibis", "pyarrow", "narwhals"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "diagnostic_polars_view()'s Arrow-preserving fallback: whichever "
            "of to_pyarrow()/to_arrow() the native value declares, routed "
            "through pl.from_arrow(); never pandas."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_IBIS_TO_ARROW: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical terminal snapshot capture from Ibis",
        route=RouteKey.LOGICAL_SNAPSHOT_CAPTURE,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"ibis"}),
        source_dialects=frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
        destination_families=frozenset({"pyarrow"}),
        destination_dialects=frozenset({"pyarrow"}),
        reason=(
            "logical_terminal_snapshot()'s Ibis adapter reads the cached "
            "table once via to_pyarrow() to build the shared physical "
            "snapshot every logical structured consumer resolves against; "
            "never to_pandas()."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_NARWHALS_TO_ARROW: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical terminal snapshot capture from Narwhals",
        route=RouteKey.LOGICAL_SNAPSHOT_CAPTURE,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"narwhals"}),
        source_dialects=frozenset({"narwhals-polars", "narwhals-pandas", "narwhals-pyarrow"}),
        destination_families=frozenset({"pyarrow"}),
        destination_dialects=frozenset({"pyarrow"}),
        reason=(
            "logical_terminal_snapshot()'s Narwhals adapter normalizes "
            "every supported dialect through its own to_arrow() so the "
            "snapshot's physical columns are one uniform representation."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_POLARS_DISPATCH: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot Polars output family dispatch",
        route=RouteKey.LOGICAL_SNAPSHOT_POLARS_OUTPUT,
        step=1,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"polars", "pandas", "pyarrow", "narwhals", "ibis"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "resolved_snapshot_to_polars() dispatches to the resolved "
            "snapshot's own source-family adapter; the dispatch itself "
            "never touches pandas -- only the per-family conversion legs "
            "it calls into (LOGICAL_SNAPSHOT_PANDAS_TO_POLARS/"
            "LOGICAL_SNAPSHOT_ARROW_TO_POLARS) may."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_TO_POLARS: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot Polars output from a pandas-selected source",
        route=RouteKey.LOGICAL_SNAPSHOT_POLARS_OUTPUT,
        step=2,
        transit_class=TransitClass.EXPLICIT_PANDAS_INPUT,
        source_families=frozenset({"pandas"}),
        source_dialects=frozenset({"pandas"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "resolved_snapshot_to_polars() converts an untagged pandas "
            "column via pl.from_pandas() when reconstructing Polars output "
            "for a pandas-family logical snapshot; the source identity is "
            "pandas, not an internal conversion detail."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_ARROW_TO_POLARS: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot Polars output from an Arrow-captured source",
        route=RouteKey.LOGICAL_SNAPSHOT_POLARS_OUTPUT,
        step=2,
        transit_class=TransitClass.NON_PANDAS_OPERATION,
        source_families=frozenset({"pyarrow"}),
        source_dialects=frozenset({"pyarrow"}),
        destination_families=frozenset({"polars"}),
        destination_dialects=frozenset({"polars"}),
        reason=(
            "resolved_snapshot_to_polars() converts an untagged Arrow "
            "column via pl.from_arrow() when reconstructing Polars output "
            "for a PyArrow, Narwhals, or Ibis logical snapshot (all three "
            "capture Arrow-native columns); never touches pandas."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_DISPATCH: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot pandas output family dispatch",
        route=RouteKey.LOGICAL_SNAPSHOT_PANDAS_OUTPUT,
        step=1,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"polars", "pandas", "pyarrow", "narwhals", "ibis"}),
        source_dialects=frozenset({None}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason=(
            "resolved_snapshot_to_pandas() dispatches to the resolved "
            "snapshot's own source-family adapter; a declared, "
            "user-visible pandas terminal regardless of which per-family "
            "conversion leg the adapter calls into."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_POLARS_TO_PANDAS: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot pandas output from a Polars-selected source",
        route=RouteKey.LOGICAL_SNAPSHOT_PANDAS_OUTPUT,
        step=2,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"polars"}),
        source_dialects=frozenset({"polars"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason=(
            "resolved_snapshot_to_pandas() converts an untagged Polars "
            "column via its own to_pandas() when reconstructing a declared "
            "pandas terminal for a Polars logical snapshot."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_ARROW_TO_PANDAS: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot pandas output from an Arrow-captured source",
        route=RouteKey.LOGICAL_SNAPSHOT_PANDAS_OUTPUT,
        step=2,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"pyarrow"}),
        source_dialects=frozenset({"pyarrow"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason=(
            "resolved_snapshot_to_pandas() converts an untagged Arrow "
            "column via its own to_pandas() when reconstructing a declared "
            "pandas terminal for a PyArrow, Narwhals, or Ibis logical "
            "snapshot."
        ),
        since=_SINCE_2026_08_27,
    ),
    BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_FRAME_ASSEMBLY: BoundarySpec(
        owner=_LOGICAL_SNAPSHOT_OWNER,
        consumer="logical snapshot pandas output frame assembly",
        route=RouteKey.LOGICAL_SNAPSHOT_PANDAS_OUTPUT,
        step=3,
        transit_class=TransitClass.EXPLICIT_PANDAS_EGRESS,
        source_families=frozenset({"pandas"}),
        source_dialects=frozenset({"pandas"}),
        destination_families=frozenset({"pandas"}),
        destination_dialects=frozenset({"pandas"}),
        reason=(
            "resolved_snapshot_to_pandas() builds each decoded transported "
            "column as an object-dtype pandas Series and assembles the "
            "final pandas DataFrame from already-pandas-native columns; a "
            "declared, user-visible pandas terminal."
        ),
        since=_SINCE_2026_08_27,
    ),
}

_PANDAS_PERMITTED_CLASSES = frozenset(
    {
        TransitClass.EXPLICIT_PANDAS_INPUT,
        TransitClass.EXPLICIT_PANDAS_EGRESS,
        TransitClass.RESULT_DIAGNOSTIC_VIEW,
        TransitClass.SEMANTICS_PRESERVING_ADAPTER,
    }
)


@dataclass(frozen=True)
class ConversionRecord:
    """One observed ``transit_call()`` invocation, captured only while traced."""

    boundary_key: BoundaryKey
    route: RouteKey
    transit_class: TransitClass
    consumer: str
    source_type: str | None
    result_type: str


@dataclass
class ConversionTrace:
    """Ordered record of every ``transit_call()`` invocation during a proof."""

    records: list[ConversionRecord] = field(default_factory=list)


_ACTIVE_TRACE: ContextVar[ConversionTrace | None] = ContextVar(
    "_ACTIVE_TRACE", default=None
)


@contextmanager
def capture_conversion_trace() -> Iterator[ConversionTrace]:
    """Activate a :class:`ConversionTrace` for the duration of the block."""
    trace = ConversionTrace()
    token = _ACTIVE_TRACE.set(trace)
    try:
        yield trace
    finally:
        _ACTIVE_TRACE.reset(token)


def _is_pandas_value(value: Any) -> bool:
    value_type = type(value)
    return value_type.__module__.startswith("pandas") and value_type.__name__ in {
        "DataFrame",
        "Series",
        "Index",
    }


def _qualified_type(value: Any) -> str:
    value_type = type(value)
    module = value_type.__module__
    name = value_type.__qualname__
    return name if module == "builtins" else f"{module}.{name}"


def transit_call(
    key: BoundaryKey,
    fn: Callable[..., T],
    /,
    *args: Any,
    trace_source: Any = _UNSET,
    **kwargs: Any,
) -> T:
    """Invoke ``fn`` under the transit policy registered for ``key``.

    Always enforces the boundary's pandas policy, whether or not a trace is
    active. Only records a :class:`ConversionRecord` when a trace is active
    (see ``capture_conversion_trace()``).
    """
    spec = BOUNDARY_REGISTRY[key]
    result = fn(*args, **kwargs)

    if _is_pandas_value(result) and spec.transit_class not in _PANDAS_PERMITTED_CLASSES:
        source_type = (
            _qualified_type(trace_source)
            if trace_source is not _UNSET
            else _qualified_type(result)
        )
        raise BackendConversionError(
            f"{key.name} is classified {spec.transit_class.name} and must "
            "not produce a pandas result",
            boundary_key=key,
            source_family=None,
            source_dialect=None,
            destination_family="pandas",
            destination_dialect="pandas",
            source_type=source_type,
            route=spec.route.name,
            reason=spec.reason,
        )

    trace = _ACTIVE_TRACE.get()
    if trace is not None:
        trace_source_type = (
            _qualified_type(trace_source) if trace_source is not _UNSET else None
        )
        trace.records.append(
            ConversionRecord(
                boundary_key=key,
                route=spec.route,
                transit_class=spec.transit_class,
                consumer=spec.consumer,
                source_type=trace_source_type,
                result_type=_qualified_type(result),
            )
        )

    return result
