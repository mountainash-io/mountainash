"""Signature conformance tests — closed-by-default wiring verification.

A1: Protocol vs backend method signatures (arity + names)
A2: Protocol vs visitor call pattern (AST argument count)
A3: Options registry consistency
"""
from __future__ import annotations

import inspect
import re
from typing import get_type_hints
import pytest

from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType

from mountainash.expressions.backends.expression_systems.ibis import (
    IbisExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.narwhals import (
    NarwhalsExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.polars import (
    PolarsExpressionSystem,
)
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitScalarArithmeticExpressionSystemProtocol,
)
import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent.parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from expressions.argument_types._introspection import (
    _CATEGORY_MAP,
    _iter_protocol_classes,
)

BACKEND_LEAF_CLASSES = {
    "polars": PolarsExpressionSystem,
    "ibis": IbisExpressionSystem,
    "narwhals": NarwhalsExpressionSystem,
}


_DIVIDE_SIGNATURE_OWNERS = (
    SubstraitScalarArithmeticExpressionSystemProtocol,
    PolarsExpressionSystem,
    IbisExpressionSystem,
    NarwhalsExpressionSystem,
)


@pytest.mark.parametrize("owner", _DIVIDE_SIGNATURE_OWNERS, ids=lambda cls: cls.__name__)
def test_divide_preserves_legacy_positional_option_order(owner: type) -> None:
    signature = inspect.signature(owner.divide)
    bound = signature.bind(
        object(),
        8.0,
        2.0,
        "SILENT",
        "NAN",
        "IEEE",
        rounding="CEILING",
    )

    assert bound.arguments["overflow"] == "SILENT"
    assert bound.arguments["on_domain_error"] == "NAN"
    assert bound.arguments["on_division_by_zero"] == "IEEE"
    assert bound.arguments["rounding"] == "CEILING"


@pytest.mark.parametrize(
    "system_cls",
    (PolarsExpressionSystem, IbisExpressionSystem, NarwhalsExpressionSystem),
    ids=("polars", "ibis", "narwhals"),
)
def test_divide_invokes_legacy_positional_options_with_keyword_rounding(
    system_cls: type,
) -> None:
    system = system_cls()

    result = system.divide(
        8.0,
        2.0,
        "SILENT",
        "NAN",
        "IEEE",
        rounding="CEILING",
    )

    assert result == 4.0

# ── A1 Exception set ─────────────────────────────────────────────────────
# (protocol_name, method_name, backend_name) → "reason. Since YYYY-MM-DD."
_KNOWN_SIGNATURE_DIVERGENCES: dict[tuple[str, str, str], str] = {
    # median: protocol median(precision, x) vs backends median(x)
    ("SubstraitAggregateArithmeticExpressionSystemProtocol", "median", "polars"):
        "Protocol median(precision, x) vs Polars median(x) — Substrait 2-arg not wired. Since 2026-05-18.",
    ("SubstraitAggregateArithmeticExpressionSystemProtocol", "median", "ibis"):
        "Protocol median(precision, x) vs Ibis median(x) — Substrait 2-arg not wired. Since 2026-05-18.",
    ("SubstraitAggregateArithmeticExpressionSystemProtocol", "median", "narwhals"):
        "Protocol median(precision, x) vs Narwhals median(x) — Substrait 2-arg not wired. Since 2026-05-18.",
    # quantile: protocol quantile(boundaries, precision, n, distribution) vs backends quantile(x, ...)
    ("SubstraitAggregateArithmeticExpressionSystemProtocol", "quantile", "polars"):
        "Protocol quantile(boundaries, precision, n, distribution) vs Polars quantile(x, q, interpolation). Since 2026-05-18.",
    ("SubstraitAggregateArithmeticExpressionSystemProtocol", "quantile", "ibis"):
        "Protocol quantile(boundaries, precision, n, distribution) vs Ibis quantile(x, quantile). Since 2026-05-18.",
    ("SubstraitAggregateArithmeticExpressionSystemProtocol", "quantile", "narwhals"):
        "Protocol quantile(boundaries, precision, n, distribution) vs Narwhals quantile(x, quantile). Since 2026-05-18.",
    # bool_and/bool_or: protocol variadic *a, backends single arg
    ("SubstraitAggregateBooleanExpressionSystemProtocol", "bool_and", "polars"):
        "Protocol bool_and(*a) variadic vs Polars bool_and(x) single-arg. Since 2026-05-18.",
    ("SubstraitAggregateBooleanExpressionSystemProtocol", "bool_and", "ibis"):
        "Protocol bool_and(*a) variadic vs Ibis bool_and(x) single-arg. Since 2026-05-18.",
    ("SubstraitAggregateBooleanExpressionSystemProtocol", "bool_and", "narwhals"):
        "Protocol bool_and(*a) variadic vs Narwhals bool_and(x) single-arg. Since 2026-05-18.",
    ("SubstraitAggregateBooleanExpressionSystemProtocol", "bool_or", "polars"):
        "Protocol bool_or(*a) variadic vs Polars bool_or(x) single-arg. Since 2026-05-18.",
    ("SubstraitAggregateBooleanExpressionSystemProtocol", "bool_or", "ibis"):
        "Protocol bool_or(*a) variadic vs Ibis bool_or(x) single-arg. Since 2026-05-18.",
    ("SubstraitAggregateBooleanExpressionSystemProtocol", "bool_or", "narwhals"):
        "Protocol bool_or(*a) variadic vs Narwhals bool_or(x) single-arg. Since 2026-05-18.",
    # string_agg: protocol string_agg(input, separator, ordering) vs backends string_agg(x)
    ("SubstraitAggregateStringExpressionSystemProtocol", "string_agg", "polars"):
        "Protocol string_agg(input, separator, ordering) 3-arg vs Polars string_agg(x) 1-arg. Since 2026-05-18.",
    ("SubstraitAggregateStringExpressionSystemProtocol", "string_agg", "ibis"):
        "Protocol string_agg(input, separator, ordering) 3-arg vs Ibis string_agg(x) 1-arg. Since 2026-05-18.",
    ("SubstraitAggregateStringExpressionSystemProtocol", "string_agg", "narwhals"):
        "Protocol string_agg(input, separator, ordering) 3-arg vs Narwhals string_agg(x) 1-arg. Since 2026-05-18.",
    # round: protocol round(x, s) vs backends round(x) — s passed as option
    ("SubstraitScalarRoundingExpressionSystemProtocol", "round", "polars"):
        "Protocol round(x, s) vs Polars round(x) — s passed as option. Since 2026-05-18.",
    ("SubstraitScalarRoundingExpressionSystemProtocol", "round", "ibis"):
        "Protocol round(x, s) vs Ibis round(x) — s passed as option. Since 2026-05-18.",
    ("SubstraitScalarRoundingExpressionSystemProtocol", "round", "narwhals"):
        "Protocol round(x, s) vs Narwhals round(x) — s passed as option. Since 2026-05-18.",
    # nth_value: protocol nth_value(x, window_offset) vs backends nth_value(x) — offset via visitor
    ("SubstraitWindowArithmeticExpressionSystemProtocol", "nth_value", "polars"):
        "Protocol nth_value(x, window_offset) vs Polars nth_value(x) — offset injected by visitor. Since 2026-05-18.",
    ("SubstraitWindowArithmeticExpressionSystemProtocol", "nth_value", "ibis"):
        "Protocol nth_value(x, window_offset) vs Ibis nth_value(x) — offset injected by visitor. Since 2026-05-18.",
    ("SubstraitWindowArithmeticExpressionSystemProtocol", "nth_value", "narwhals"):
        "Protocol nth_value(x, window_offset) vs Narwhals nth_value(x) — offset injected by visitor. Since 2026-05-18.",
    # list_sample: protocol list_sample(input, n, with_replacement, seed) vs backends list_sample(input)
    ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "polars"):
        "Protocol list_sample(input, n, with_replacement, seed) 4-arg vs Polars list_sample(input) 1-arg. Since 2026-05-18.",
    ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "ibis"):
        "Protocol list_sample(input, n, with_replacement, seed) 4-arg vs Ibis list_sample(input) 1-arg. Since 2026-05-18.",
    ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "narwhals"):
        "Protocol list_sample(input, n, with_replacement, seed) 4-arg vs Narwhals list_sample(input) 1-arg. Since 2026-05-18.",
}


def _resolve_backend_method(
    backend_cls: type, method_name: str
) -> tuple[type, object] | None:
    for cls in type.mro(backend_cls):
        if cls.__name__.endswith("Protocol"):
            continue
        if method_name in cls.__dict__:
            return cls, cls.__dict__[method_name]
    return None


def _get_positional_params(sig: inspect.Signature) -> list[tuple[str, str]]:
    """Extract non-self positional params as (name, kind_str) tuples."""
    result = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            result.append((f"*{pname}", "variadic"))
            continue
        if param.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD):
            continue
        if param.default is not inspect.Parameter.empty:
            ann_str = str(param.annotation)
            if "ExpressionT" not in ann_str and "Expr" not in ann_str:
                continue
        result.append((pname, "positional"))
    return result


def _collect_a1_cases() -> (
    list[tuple[str, str, str, inspect.Signature, inspect.Signature]]
):
    cases = []
    for proto_name, proto_cls in _iter_protocol_classes():
        if proto_name not in _CATEGORY_MAP:
            continue
        for method_name, method in inspect.getmembers(
            proto_cls, predicate=inspect.isfunction
        ):
            if method_name.startswith("_"):
                continue
            proto_sig = inspect.signature(method)
            for backend_name, backend_cls in BACKEND_LEAF_CLASSES.items():
                resolved = _resolve_backend_method(backend_cls, method_name)
                if resolved is None:
                    continue
                defining_cls, backend_method = resolved
                assert not defining_cls.__name__.endswith("Protocol"), (
                    f"MRO resolution returned protocol class {defining_cls.__name__} "
                    f"for {method_name} on {backend_name}"
                )
                backend_sig = inspect.signature(backend_method)
                cases.append(
                    (proto_name, method_name, backend_name, proto_sig, backend_sig)
                )
    return cases


_A1_CASES = _collect_a1_cases()


class TestProtocolVsBackendSignatures:
    """A1: Every backend method must match its protocol's signature."""

    @pytest.mark.parametrize(
        ("proto_name", "method_name", "backend_name", "proto_sig", "backend_sig"),
        _A1_CASES,
        ids=[f"{p}/{m}/{b}" for p, m, b, _, _ in _A1_CASES],
    )
    def test_signature_matches(
        self,
        proto_name: str,
        method_name: str,
        backend_name: str,
        proto_sig: inspect.Signature,
        backend_sig: inspect.Signature,
    ) -> None:
        key = (proto_name, method_name, backend_name)
        if key in _KNOWN_SIGNATURE_DIVERGENCES:
            pytest.xfail(_KNOWN_SIGNATURE_DIVERGENCES[key])

        proto_params = _get_positional_params(proto_sig)
        backend_params = _get_positional_params(backend_sig)

        proto_variadic = any(k == "variadic" for _, k in proto_params)
        backend_variadic = any(k == "variadic" for _, k in backend_params)

        if proto_variadic:
            if not backend_variadic:
                assert len(backend_params) >= 2, (
                    f"{proto_name}.{method_name} on {backend_name}: "
                    f"protocol is variadic but backend has {len(backend_params)} "
                    f"fixed params (need >= 2)"
                )
            return

        assert len(proto_params) == len(backend_params), (
            f"{proto_name}.{method_name} on {backend_name}: "
            f"protocol has {len(proto_params)} positional params "
            f"{[n for n, _ in proto_params]}, "
            f"backend has {len(backend_params)} "
            f"{[n for n, _ in backend_params]}"
        )

    def test_no_stale_divergence_entries(self) -> None:
        all_keys = {(p, m, b) for p, m, b, _, _ in _A1_CASES}
        for key in _KNOWN_SIGNATURE_DIVERGENCES:
            assert key in all_keys, (
                f"Stale _KNOWN_SIGNATURE_DIVERGENCES entry: {key} — "
                f"protocol/method/backend combo no longer exists"
            )

    def test_divergences_still_diverge(self) -> None:
        """Every exception must still actually diverge — if fixed, remove it."""
        for proto_name, method_name, backend_name, proto_sig, backend_sig in _A1_CASES:
            key = (proto_name, method_name, backend_name)
            if key not in _KNOWN_SIGNATURE_DIVERGENCES:
                continue
            proto_params = _get_positional_params(proto_sig)
            backend_params = _get_positional_params(backend_sig)
            proto_variadic = any(k == "variadic" for _, k in proto_params)
            if proto_variadic:
                continue
            assert len(proto_params) != len(backend_params), (
                f"Stale divergence: {key} — signatures now match! "
                f"Remove from _KNOWN_SIGNATURE_DIVERGENCES."
            )

    def test_every_divergence_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_SIGNATURE_DIVERGENCES.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_SIGNATURE_DIVERGENCES[{key}] missing 'Since YYYY-MM-DD': "
                f"{reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_SIGNATURE_DIVERGENCES[{key}] has no date: {reason!r}"
            )


# ── A2: Protocol vs Visitor Call Pattern ─────────────────────────────────

import mountainash as ma
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import (
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_window_function import (
    WindowFunctionNode,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_cast import CastNode
from mountainash.expressions.core.expression_nodes.substrait.exn_ifthen import IfThenNode

from core._smoke_helpers import (
    build_args_for_fkey,
    count_protocol_arguments,
    is_variadic,
)


def _init_a2_local_builders() -> dict:
    """A2-only expression factories, never shared with test_api_reachability.py
    or test_compile_smoke.py. Keeping these local (not added to
    _smoke_helpers.py's shared _init_smoke_expr_builders()) is deliberate:
    several of these FKEYs (e.g. FIELD/GET/TO_ARRAY/TRUNCATE/OFFSET_BY/NTILE)
    currently have _KNOWN_SMOKE_FAILURES park entries in test_compile_smoke.py
    describing the exact "missing required arg" TypeError the generic
    resolver hits — sharing a correctly-parameterized builder would silently
    resolve those compile-smoke cases too, and for
    FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY specifically that resolution
    surfaces a genuine, undeclared backend capability gap (ibis/narwhals/
    pandas lack array.to_array()) requiring a real CapabilityFact in the
    production capability spine — out of scope for a test-harness-only
    change. Keeping the overlay A2-local avoids all of that cross-suite
    ripple. Since 2026-08-11."""
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_CATEGORICAL,
        FKEY_MOUNTAINASH_SCALAR_DATETIME,
        FKEY_MOUNTAINASH_SCALAR_LIST,
        FKEY_MOUNTAINASH_SCALAR_STRUCT,
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL,
        FKEY_MOUNTAINASH_SCALAR_TERNARY,
        FKEY_MOUNTAINASH_WINDOW,
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
        FKEY_SUBSTRAIT_SCALAR_DATETIME,
        FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC,
        SUBSTRAIT_ARITHMETIC_WINDOW,
    )

    c = ma.col("a")
    s = ma.col("c")
    b = ma.col("e")

    return {
        FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_UNKNOWN: lambda: ma.always_unknown(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_TRUE: lambda: ma.always_true(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_FALSE: lambda: ma.always_false(),
        # protocol_method name (is_true_ternary/is_unknown/maybe_true/...)
        # doesn't match the real public accessor (t_is_true/t_is_unknown/
        # t_maybe_true/...); not reachable via _resolve_api_callable.
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE: lambda: c.t_is_true(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE: lambda: c.t_is_false(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN: lambda: c.t_is_unknown(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN: lambda: c.t_is_known(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE: lambda: c.t_maybe_true(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE: lambda: c.t_maybe_false(),
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS: lambda: ma.count_records(),
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR: lambda: ma.corr(c, b),
        # Namespace collision: the generic resolver finds list.median first.
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN: lambda: ma.median(0, c),
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE: lambda: ma.quantile([0.5], 2, 1, "LINEAR"),
        SUBSTRAIT_ARITHMETIC_WINDOW.NTILE: lambda: c.ntile(4).over("b"),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY: lambda: ma.today(),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW: lambda: ma.now(),
        # Name collision: "round"/"ceil"/"floor" already resolve to the flat
        # numeric-rounding builder (FKEY_SUBSTRAIT_SCALAR_ROUNDING); these are
        # the datetime-namespaced ops, only reachable via .dt.<name>().
        FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND: lambda: c.dt.round(unit="1d"),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL: lambda: c.dt.ceil(unit="1d"),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR: lambda: c.dt.floor(unit="1d"),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE: lambda: c.dt.truncate(unit="1d"),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY: lambda: c.dt.offset_by(offset="1d"),
        FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD: lambda: c.struct.field("x"),
        FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST: lambda: c.struct.cast(
            fields=(FieldSpec(name="id", type=UniversalType.INTEGER),), field_name="x"
        ),
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT: lambda: c.geo.parse_geopoint(
            format="default", source_representation="lexical", field_name="x"
        ),
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON: lambda: c.geo.parse_geojson(
            format="default", field_name="x"
        ),
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON: lambda: c.geo.serialize_geojson(
            format="default", field_name="x"
        ),
        FKEY_MOUNTAINASH_SCALAR_LIST.PARSE: lambda: s.str.parse_list(field_name="x"),
        FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS: lambda: c.list.cast_items(
            item_object_fields=(FieldSpec(name="id", type=UniversalType.INTEGER),), field_name="x"
        ),
        FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST: lambda: c.cat.cast(
            value_type="integer", categories=(1, 2), ordered=True, field_name="x"
        ),
        FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB: lambda: c.log(base=10),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE: lambda: s.str.to_date("%Y-%m-%d"),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP: lambda: s.str.to_datetime("%Y-%m-%d"),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT: lambda: c.dt.extract("YEAR"),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN: lambda: c.dt.extract_boolean("IS_LEAP_YEAR"),
        SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK: lambda: c.percent_rank().over("b"),
        SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST: lambda: c.cume_dist().over("b"),
        # Constructs successfully but always 0-ary (order_by_col unreachable
        # via the public builder) — proves the _KNOWN_CALL_PATTERN_MISMATCHES
        # entries above are genuine mismatches, not construction failures.
        SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER: lambda: c.row_number().over("b"),
        SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK: lambda: c.dense_rank().over("b"),
        SUBSTRAIT_ARITHMETIC_WINDOW.RANK: lambda: c.rank(method="min").over("b"),
        FKEY_MOUNTAINASH_WINDOW.RANK_MAX: lambda: c.rank(method="max").over("b"),
        FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE: lambda: c.rank(method="average").over("b"),
    }


_A2_LOCAL_BUILDERS = _init_a2_local_builders()

_NAMESPACE_PREFIXES = {"list_": "list", "struct_": "struct"}
_DESCRIPTOR_NAMESPACES = ("str", "dt", "list", "struct", "geo")


def _resolve_api_callable(
    base: ma.Expression, method_name: str
) -> object | None:
    """Find a callable for method_name across all expression namespaces."""
    # Try flat namespaces first (comparison, arithmetic, boolean, etc.)
    try:
        return getattr(base, method_name)
    except AttributeError:
        pass

    # Try descriptor namespaces with prefix stripping (list_sum -> .list.sum)
    for prefix, ns_name in _NAMESPACE_PREFIXES.items():
        if method_name.startswith(prefix):
            stripped = method_name[len(prefix) :]
            try:
                ns = getattr(base, ns_name)
                return getattr(ns, stripped)
            except AttributeError:
                pass

    # Try descriptor namespaces without prefix stripping (upper -> .str.upper)
    for ns_name in _DESCRIPTOR_NAMESPACES:
        try:
            ns = getattr(base, ns_name)
            return getattr(ns, method_name)
        except AttributeError:
            continue

    return None


def _collect_a2_cases() -> list[tuple[str, int]]:
    ExpressionFunctionRegistry._init_registry()
    cases = []
    for fkey, fdef in ExpressionFunctionRegistry._functions.items():
        if is_variadic(fdef):
            continue
        if fdef.protocol_method is None:
            continue
        arg_count = count_protocol_arguments(fdef)
        cases.append((str(fkey), arg_count))
    return cases


_A2_CASES = _collect_a2_cases()

# (fkey_str) → "reason. Since YYYY-MM-DD."
_KNOWN_CALL_PATTERN_MISMATCHES: dict[str, str] = {
    "SUBSTRAIT_ARITHMETIC_WINDOW.LEAD":
        "Protocol lead(x) has 1 ExpressionT arg, but API builder adds LiteralNode offset (n=1) "
        "making 2 AST args. Since 2026-05-18.",
    "SUBSTRAIT_ARITHMETIC_WINDOW.LAG":
        "Protocol lag(x) has 1 ExpressionT arg, but API builder adds LiteralNode offset (n=1) "
        "making 2 AST args. Since 2026-05-18.",
    "SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER":
        "Protocol row_number(*, order_by_col=None) declares an optional ExpressionT kwarg, "
        "but SubstraitWindowArithmeticAPIBuilder.row_number() never exposes it — the "
        "constructed AST always has 0 arguments. Since 2026-08-11.",
    "SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK":
        "Protocol dense_rank(*, order_by_col=None) declares an optional ExpressionT kwarg, "
        "unreachable via the public builder — AST always has 0 arguments. Since 2026-08-11.",
    "SUBSTRAIT_ARITHMETIC_WINDOW.RANK":
        "Protocol rank(*, order_by_col=None) declares an optional ExpressionT kwarg, "
        "unreachable via the public builder — AST always has 0 arguments. Since 2026-08-11.",
    "FKEY_MOUNTAINASH_WINDOW.RANK_MAX":
        "Protocol rank(*, order_by_col=None) declares an optional ExpressionT kwarg, "
        "unreachable via the public builder — AST always has 0 arguments. Since 2026-08-11.",
    "FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE":
        "Protocol rank(*, order_by_col=None) declares an optional ExpressionT kwarg, "
        "unreachable via the public builder — AST always has 0 arguments. Since 2026-08-11.",
}

# (fkey_str) → "reason. Since YYYY-MM-DD."
# Escape hatch for A2 arg-count verification: an entry here means the FKEY's
# expression truly cannot be constructed with the correct identity via any
# current public API surface.
_KNOWN_UNVERIFIABLE_CALL_PATTERNS: dict[str, str] = {}


class _A2ConstructionError(Exception):
    """Raised when an FKEY's expression cannot be constructed at all."""


class _A2ValidationError(Exception):
    """Raised when a constructed node fails identity or arity validation."""


def _construct_a2_expr(fkey: object, fdef: object) -> object:
    """Build a real expression for fkey: A2-local builder first, generic
    namespace-scanning resolver as fallback. Raises _A2ConstructionError if
    no path can construct anything at all."""
    if fkey in _A2_LOCAL_BUILDERS:
        return _A2_LOCAL_BUILDERS[fkey]()

    try:
        args, options = build_args_for_fkey(fkey, fdef)
    except ValueError as e:
        raise _A2ConstructionError(
            f"Cannot auto-construct args for {fkey}: {e}. Add to "
            f"_SMOKE_ARG_OVERRIDES in _smoke_helpers.py or to "
            f"_A2_LOCAL_BUILDERS in this file, or add a dated entry to "
            f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS."
        ) from e

    if not args:
        raise _A2ConstructionError(
            f"{fkey}: no args to build a receiver from and no "
            f"_A2_LOCAL_BUILDERS entry. Add one, or add a dated entry to "
            f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS."
        )

    method_name = fdef.protocol_method.__name__
    callable_method = _resolve_api_callable(args[0], method_name)
    if callable_method is None:
        raise _A2ConstructionError(
            f"{fkey}: {method_name} not accessible via any API namespace and "
            f"no _A2_LOCAL_BUILDERS entry. Add one, or add a dated entry to "
            f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS."
        )

    try:
        return callable_method(*args[1:], **options)
    except TypeError as e:
        raise _A2ConstructionError(
            f"{fkey}: {method_name} call failed: {e}. Add an "
            f"_A2_LOCAL_BUILDERS entry, or a dated entry to "
            f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS."
        ) from e


def _validate_a2_node(fkey: object, fkey_str: str, node: object, expected_arg_count: int) -> None:
    """Check a constructed node's identity and arity against the protocol.
    Raises _A2ValidationError on any mismatch or unhandled node shape."""
    if isinstance(node, (ScalarFunctionNode, WindowFunctionNode)):
        if node.function_key != fkey:
            raise _A2ValidationError(
                f"{fkey_str}: constructed node has function_key "
                f"{node.function_key}, expected {fkey} — the resolved callable "
                f"emits a different operation than the one under test "
                f"(namespace/name collision)"
            )
        actual_arg_count = len(node.arguments)
        if actual_arg_count != expected_arg_count:
            raise _A2ValidationError(
                f"{fkey_str}: AST node has {actual_arg_count} arguments, "
                f"protocol expects {expected_arg_count}"
            )
        return
    if isinstance(node, CastNode):
        # CastNode carries a single `input` field, not an `.arguments` list —
        # its arity is structurally always 1.
        if expected_arg_count != 1:
            raise _A2ValidationError(
                f"{fkey_str}: CastNode is always 1-ary, protocol expects "
                f"{expected_arg_count}"
            )
        return
    if isinstance(node, IfThenNode):
        # IfThenNode has no flat `.arguments`; its ExpressionT-equivalent slot
        # count is 2 per (condition, result) pair plus the else clause.
        actual_arg_count = 2 * len(node.conditions) + 1
        if actual_arg_count != expected_arg_count:
            raise _A2ValidationError(
                f"{fkey_str}: IfThenNode has {actual_arg_count} "
                f"condition/result/else slots, protocol expects "
                f"{expected_arg_count}"
            )
        return
    raise _A2ValidationError(
        f"{fkey_str}: unhandled node type {type(node).__name__} — extend "
        f"_validate_a2_node's dispatch to verify its arity, or add a dated "
        f"entry to _KNOWN_UNVERIFIABLE_CALL_PATTERNS."
    )


def _resolve_fkey_by_str(fkey_str: str) -> object:
    ExpressionFunctionRegistry._init_registry()
    for k in ExpressionFunctionRegistry._functions:
        if str(k) == fkey_str:
            return k
    raise AssertionError(f"FKEY {fkey_str} not found in registry")


class TestProtocolVsVisitorCallPattern:
    """A2: The AST node's argument count must match the protocol's argument count."""

    @pytest.mark.parametrize(
        ("fkey_str", "expected_arg_count"),
        _A2_CASES,
        ids=[fk for fk, _ in _A2_CASES],
    )
    def test_ast_arg_count_matches_protocol(
        self, fkey_str: str, expected_arg_count: int
    ) -> None:
        if fkey_str in _KNOWN_CALL_PATTERN_MISMATCHES:
            pytest.xfail(_KNOWN_CALL_PATTERN_MISMATCHES[fkey_str])

        fkey = _resolve_fkey_by_str(fkey_str)
        fdef = ExpressionFunctionRegistry.get(fkey)

        try:
            expr = _construct_a2_expr(fkey, fdef)
        except _A2ConstructionError as e:
            if fkey_str in _KNOWN_UNVERIFIABLE_CALL_PATTERNS:
                pytest.xfail(_KNOWN_UNVERIFIABLE_CALL_PATTERNS[fkey_str])
            pytest.fail(str(e))

        node = expr._node if hasattr(expr, "_node") else expr
        try:
            _validate_a2_node(fkey, fkey_str, node, expected_arg_count)
        except _A2ValidationError as e:
            if fkey_str in _KNOWN_UNVERIFIABLE_CALL_PATTERNS:
                pytest.xfail(_KNOWN_UNVERIFIABLE_CALL_PATTERNS[fkey_str])
            pytest.fail(str(e))

    def test_no_stale_call_pattern_entries(self) -> None:
        all_fkeys = {fk for fk, _ in _A2_CASES}
        for key in _KNOWN_CALL_PATTERN_MISMATCHES:
            assert key in all_fkeys, (
                f"Stale _KNOWN_CALL_PATTERN_MISMATCHES entry: {key}"
            )

    def test_every_mismatch_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_CALL_PATTERN_MISMATCHES.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_CALL_PATTERN_MISMATCHES[{key}] missing date: {reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_CALL_PATTERN_MISMATCHES[{key}] has no date: {reason!r}"
            )

    def test_call_pattern_mismatches_still_mismatch(self) -> None:
        """Every _KNOWN_CALL_PATTERN_MISMATCHES entry must still actually
        mismatch — if the AST now emits the protocol-expected arg count,
        remove the exemption."""
        for fkey_str, expected_arg_count in _A2_CASES:
            if fkey_str not in _KNOWN_CALL_PATTERN_MISMATCHES:
                continue
            fkey = _resolve_fkey_by_str(fkey_str)
            fdef = ExpressionFunctionRegistry.get(fkey)
            try:
                expr = _construct_a2_expr(fkey, fdef)
            except _A2ConstructionError as e:
                pytest.fail(
                    f"{fkey_str}: _KNOWN_CALL_PATTERN_MISMATCHES entries must "
                    f"still construct successfully (the mismatch is in arity, "
                    f"not constructibility): {e}"
                )
            node = expr._node if hasattr(expr, "_node") else expr
            try:
                _validate_a2_node(fkey, fkey_str, node, expected_arg_count)
            except _A2ValidationError:
                continue  # still mismatches — exemption still valid
            pytest.fail(
                f"Stale mismatch entry: {fkey_str} — now constructs with the "
                f"correct identity and arity. Remove from "
                f"_KNOWN_CALL_PATTERN_MISMATCHES."
            )

    def test_no_stale_unverifiable_call_pattern_entries(self) -> None:
        all_fkeys = {fk for fk, _ in _A2_CASES}
        for key in _KNOWN_UNVERIFIABLE_CALL_PATTERNS:
            assert key in all_fkeys, (
                f"Stale _KNOWN_UNVERIFIABLE_CALL_PATTERNS entry: {key}"
            )

    def test_every_unverifiable_call_pattern_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_UNVERIFIABLE_CALL_PATTERNS.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS[{key}] missing "
                f"'Since YYYY-MM-DD': {reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS[{key}] has no date: {reason!r}"
            )

    def test_unverifiable_call_patterns_still_unverifiable(self) -> None:
        """Every exemption must still actually be unconstructible-or-invalid —
        if the A2-local overlay or generic resolution now covers it with the
        correct identity and arity, remove it."""
        for fkey_str, expected_arg_count in _A2_CASES:
            if fkey_str not in _KNOWN_UNVERIFIABLE_CALL_PATTERNS:
                continue
            fkey = _resolve_fkey_by_str(fkey_str)
            fdef = ExpressionFunctionRegistry.get(fkey)
            try:
                expr = _construct_a2_expr(fkey, fdef)
            except _A2ConstructionError:
                continue  # still unconstructible — exemption still valid
            node = expr._node if hasattr(expr, "_node") else expr
            try:
                _validate_a2_node(fkey, fkey_str, node, expected_arg_count)
            except _A2ValidationError:
                continue  # still invalid — exemption still valid
            pytest.fail(
                f"Stale exemption: {fkey_str} now constructs successfully "
                f"with the correct identity and arity. Remove from "
                f"_KNOWN_UNVERIFIABLE_CALL_PATTERNS."
            )


# ── A3: Options Registry Consistency ─────────────────────────────────────


def _collect_a3_cases() -> list[tuple[str, tuple[str, ...], list[str], list[str]]]:
    """Collect (fkey_str, registered_options, protocol_option_params, required_protocol_options).

    Protocol option params are identified by _classify_annotation returning
    "option" or "unclassified", or by being KEYWORD_ONLY.
    Required options are those without a default value.
    """
    from expressions.argument_types._introspection import _classify_annotation

    ExpressionFunctionRegistry._init_registry()
    cases = []
    for fkey, fdef in ExpressionFunctionRegistry._functions.items():
        if fdef.protocol_method is None:
            continue
        sig = inspect.signature(fdef.protocol_method)
        hints = get_type_hints(fdef.protocol_method)
        option_params = []
        required_options = []
        for pname, param in sig.parameters.items():
            if pname == "self":
                continue
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                continue
            is_option = False
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                is_option = True
            else:
                ann = hints.get(pname, param.annotation)
                if _classify_annotation(ann) in ("option", "unclassified"):
                    is_option = True
            if is_option:
                option_params.append(pname)
                if param.default is inspect.Parameter.empty:
                    required_options.append(pname)
        cases.append((str(fkey), fdef.options, option_params, required_options))
    return cases


_A3_CASES = _collect_a3_cases()

# (fkey_str) → "reason. Since YYYY-MM-DD."
_KNOWN_OPTIONS_DRIFT: dict[str, str] = {
    "FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING":
        "Registry has 'start','length' but protocol has 'negative_start' — options not aligned. Since 2026-05-18.",
    "FKEY_MOUNTAINASH_NAME.ALIAS":
        "Protocol has required 'name' kwarg not in registry — handled by API builder directly. Since 2026-05-18.",
    "FKEY_MOUNTAINASH_NAME.PREFIX":
        "Protocol has required 'prefix' kwarg not in registry — handled by API builder directly. Since 2026-05-18.",
    "FKEY_MOUNTAINASH_NAME.SUFFIX":
        "Protocol has required 'suffix' kwarg not in registry — handled by API builder directly. Since 2026-05-18.",
}


class TestOptionsRegistryConsistency:
    """A3: ExpressionFunctionDef.options must match protocol option params."""

    @pytest.mark.parametrize(
        ("fkey_str", "registered_options", "protocol_options", "required_options"),
        _A3_CASES,
        ids=[fk for fk, _, _, _ in _A3_CASES],
    )
    def test_registered_options_exist_in_protocol(
        self,
        fkey_str: str,
        registered_options: tuple[str, ...],
        protocol_options: list[str],
        required_options: list[str],
    ) -> None:
        """Every option in the registry must correspond to a protocol param."""
        if fkey_str in _KNOWN_OPTIONS_DRIFT:
            pytest.xfail(_KNOWN_OPTIONS_DRIFT[fkey_str])

        registered = set(registered_options)
        protocol = set(protocol_options)

        extra = registered - protocol
        assert not extra, (
            f"{fkey_str}: options {extra} in registry but not in protocol. "
            f"Registry: {registered}, Protocol: {protocol}"
        )

    @pytest.mark.parametrize(
        ("fkey_str", "registered_options", "protocol_options", "required_options"),
        _A3_CASES,
        ids=[fk for fk, _, _, _ in _A3_CASES],
    )
    def test_required_protocol_options_registered(
        self,
        fkey_str: str,
        registered_options: tuple[str, ...],
        protocol_options: list[str],
        required_options: list[str],
    ) -> None:
        """Required protocol options (no default) must be in the registry."""
        if fkey_str in _KNOWN_OPTIONS_DRIFT:
            pytest.xfail(_KNOWN_OPTIONS_DRIFT[fkey_str])

        registered = set(registered_options)
        missing_required = set(required_options) - registered
        assert not missing_required, (
            f"{fkey_str}: required options {missing_required} in protocol but "
            f"not in registry. Registry: {registered}, Required: {set(required_options)}"
        )

    def test_drift_entries_still_drift(self) -> None:
        """Every exception must still actually drift — if fixed, remove it."""
        from expressions.argument_types._introspection import _classify_annotation

        for fkey_str, registered_options, protocol_options, required_options in _A3_CASES:
            if fkey_str not in _KNOWN_OPTIONS_DRIFT:
                continue
            registered = set(registered_options)
            protocol = set(protocol_options)
            extra = registered - protocol
            missing_required = set(required_options) - registered
            assert extra or missing_required, (
                f"Stale drift: {fkey_str} — options now match! "
                f"Remove from _KNOWN_OPTIONS_DRIFT."
            )

    def test_no_stale_options_drift_entries(self) -> None:
        all_fkeys = {fk for fk, _, _, _ in _A3_CASES}
        for key in _KNOWN_OPTIONS_DRIFT:
            assert key in all_fkeys, (
                f"Stale _KNOWN_OPTIONS_DRIFT entry: {key}"
            )

    def test_every_drift_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_OPTIONS_DRIFT.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_OPTIONS_DRIFT[{key}] missing date: {reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_OPTIONS_DRIFT[{key}] has no date: {reason!r}"
            )


# ── A4: Options Keyword-Bindable Guard ───────────────────────────────────


def _collect_a4_cases() -> list[tuple[str, tuple[str, ...], object]]:
    """Collect (fkey_str, registered_options, protocol_method) for option binding."""
    ExpressionFunctionRegistry._init_registry()
    return [
        (str(fkey), fdef.options, fdef.protocol_method)
        for fkey, fdef in ExpressionFunctionRegistry._functions.items()
        if fdef.protocol_method is not None and fdef.options
    ]


_A4_CASES = _collect_a4_cases()


class TestOptionsAreKeywordBindable:
    """A4: every registered option must be bindable as a keyword.

    The visitor dispatches options as keywords (`method(*compiled_args,
    **options)`, unified_visitor/visitor.py). An option declared
    POSITIONAL_ONLY on the protocol method therefore raises TypeError at
    compile time for every call that passes it -- the op is unwireable, and
    nothing detects that until a user calls it.

    This is the class behind item 62 PR-A: to_timezone declared
    `(self, x, timezone, /)` and had no ExpressionFunctionDef, so the two
    defects masked each other.
    """

    @pytest.mark.parametrize(
        ("fkey_str", "registered_options", "protocol_method"),
        _A4_CASES,
        ids=[fk for fk, _, _ in _A4_CASES],
    )
    def test_registered_option_is_keyword_bindable(
        self,
        fkey_str: str,
        registered_options: tuple[str, ...],
        protocol_method: object,
    ) -> None:
        sig = inspect.signature(protocol_method)
        positional_only = {
            name
            for name, p in sig.parameters.items()
            if p.kind == inspect.Parameter.POSITIONAL_ONLY
        }
        offenders = sorted(set(registered_options) & positional_only)
        assert not offenders, (
            f"{fkey_str}: option(s) {offenders} are POSITIONAL_ONLY on "
            f"{protocol_method.__qualname__}, but the visitor dispatches "
            f"options as keywords. Move the '/' so they are "
            f"POSITIONAL_OR_KEYWORD. Signature: {sig}"
        )


def test_no_option_bearing_def_escapes_the_a4_guard() -> None:
    """A4's collector skips protocol_method=None; nothing may hide there.

    Without this, a def registered with options but no protocol_method is
    silently absent from _A4_CASES -- a positional-only option would go
    undetected, which is the exact silent-inertness this guard exists to
    prevent (closed-by-default-verification).
    """
    ExpressionFunctionRegistry._init_registry()
    unbound = sorted(
        str(fkey)
        for fkey, fdef in ExpressionFunctionRegistry._functions.items()
        if fdef.options and fdef.protocol_method is None
    )
    assert not unbound, (
        f"defs registered with options but no protocol_method: {unbound}. "
        "These are invisible to the A4 keyword-bindability guard -- either "
        "wire protocol_method or drop the options."
    )

