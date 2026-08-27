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
