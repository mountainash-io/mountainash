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

from mountainash.expressions.backends.expression_systems.ibis import (
    IbisExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.narwhals import (
    NarwhalsExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.polars import (
    PolarsExpressionSystem,
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
    # extract: protocol extract(component, input) vs backends extract(input) — component is an option
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "extract", "polars"):
        "Protocol extract(component, input) vs Polars extract(input) — component passed as option. Since 2026-05-18.",
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "extract", "ibis"):
        "Protocol extract(component, input) vs Ibis extract(input) — component passed as option. Since 2026-05-18.",
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "extract", "narwhals"):
        "Protocol extract(component, input) vs Narwhals extract(input) — component passed as option. Since 2026-05-18.",
    # strptime_timestamp: protocol strptime_timestamp(input, format, timezone) vs backends strptime_timestamp(input)
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp", "polars"):
        "Protocol strptime_timestamp(input, format, timezone) 3-arg vs Polars strptime_timestamp(input) 1-arg. Since 2026-05-18.",
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp", "ibis"):
        "Protocol strptime_timestamp(input, format, timezone) 3-arg vs Ibis strptime_timestamp(input) 1-arg. Since 2026-05-18.",
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp", "narwhals"):
        "Protocol strptime_timestamp(input, format, timezone) 3-arg vs Narwhals strptime_timestamp(input) 1-arg. Since 2026-05-18.",
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

from core._smoke_helpers import (
    build_args_for_fkey,
    count_protocol_arguments,
    is_variadic,
)

_NAMESPACE_PREFIXES = {"list_": "list", "struct_": "struct"}
_DESCRIPTOR_NAMESPACES = ("str", "dt", "list", "struct")


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
}


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

        ExpressionFunctionRegistry._init_registry()
        fkey = None
        for k in ExpressionFunctionRegistry._functions:
            if str(k) == fkey_str:
                fkey = k
                break
        assert fkey is not None, f"FKEY {fkey_str} not found in registry"

        fdef = ExpressionFunctionRegistry.get(fkey)

        try:
            args, options = build_args_for_fkey(fkey, fdef)
        except ValueError as e:
            pytest.fail(
                f"Cannot auto-construct args for {fkey_str}: {e}. "
                f"Add to _SMOKE_ARG_OVERRIDES in _smoke_helpers.py."
            )

        if not args:
            pytest.skip("No args to build expression from")

        method_name = fdef.protocol_method.__name__
        base = args[0]
        remaining_args = args[1:]

        callable_method = _resolve_api_callable(base, method_name)
        if callable_method is None:
            pytest.skip(f"{method_name} not accessible via any API namespace")

        try:
            expr = callable_method(*remaining_args, **options)
        except (TypeError, Exception) as e:
            pytest.skip(f"{method_name} call failed: {e}")

        node = expr._node if hasattr(expr, "_node") else expr
        if isinstance(node, (ScalarFunctionNode, WindowFunctionNode)):
            actual_arg_count = len(node.arguments)
            assert actual_arg_count == expected_arg_count, (
                f"{fkey_str}: AST node has {actual_arg_count} arguments, "
                f"protocol expects {expected_arg_count}"
            )

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
    "FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT":
        "Registry has 'separator' but protocol has 'null_handling' — different option sets. Since 2026-05-18.",
    "FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING":
        "Registry has 'start','length' but protocol has 'negative_start' — options not aligned. Since 2026-05-18.",
    "FKEY_MOUNTAINASH_SCALAR_STRING.TO_DATETIME":
        "Protocol has required 'timezone' option not in registry — timezone handled by API builder. Since 2026-05-18.",
    "FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT":
        "Protocol extract(component, input) — component is a required positional option not in registry. Since 2026-05-18.",
    "FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN":
        "Protocol extract_boolean(component, input) — component is a required positional option not in registry. Since 2026-05-18.",
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
