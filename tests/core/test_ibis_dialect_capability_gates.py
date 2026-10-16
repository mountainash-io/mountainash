"""Exercise the real Ibis visitor's declared gates without optional SQL drivers.

These are compiler-boundary policy tests, not remote execution qualification.
The input schema and target dialect are explicit, as at relation compilation;
no backend implementation, capability record or lowering method is mocked.
"""

from __future__ import annotations

import ibis
import pytest

import mountainash as ma
from mountainash.core.capabilities import BackendIdentity
from mountainash.core.capabilities.policy import _CapabilityTarget, _prepare_capability_context
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

_CASES = (
    ("ibis-mysql", "decimal"),
    ("ibis-singlestoredb", "decimal"),
    ("ibis-exasol", "decimal"),
    ("ibis-exasol", "regex"),
)


def _compile(dialect, kind, version, policy):
    table = ibis.table({"value": "string"}, name="source")
    context = _prepare_capability_context(
        policy,
        _CapabilityTarget(BackendIdentity(CONST_BACKEND.IBIS, dialect), table),
        package_versions={"ibis-framework": version},
    )
    system = get_expression_system(CONST_BACKEND.IBIS)(
        dialect=dialect, execution_context=context,
    )
    visitor = UnifiedExpressionVisitor(system, execution_context=context, input_data=table)
    expression = (
        ma.col("value").cast(ma.DecimalDtype(12, 2), rounding="half_to_even")
        if kind == "decimal"
        else ma.col("value").str.regex_contains("^a")
    )
    return table.select(visitor.visit(expression.node).name("result")).result


@pytest.mark.parametrize("dialect,kind", _CASES)
@pytest.mark.parametrize("policy", [ma.CapabilityPolicy.checked(), ma.CapabilityPolicy.native_debugging()])
def test_qualified_missing_translator_is_refused(dialect, kind, policy):
    with pytest.raises(BackendCapabilityError) as error:
        _compile(dialect, kind, "12.0.0", policy)
    assert error.value.function_key.name == ("DECIMAL_CAST" if kind == "decimal" else "REGEX_CONTAINS")
    assert error.value.backend == "ibis"


@pytest.mark.parametrize("dialect,kind", _CASES)
@pytest.mark.parametrize(
    "version,policy",
    [
        ("12.0.1", ma.CapabilityPolicy.checked()),
        (None, ma.CapabilityPolicy.checked()),
        ("12.0.0", ma.CapabilityPolicy.trusted()),
    ],
)
def test_unqualified_or_unselected_gate_preserves_native_lowering(dialect, kind, version, policy):
    compiled = _compile(dialect, kind, version, policy)
    assert compiled.type() == (ibis.dtype("decimal(12, 2)") if kind == "decimal" else ibis.dtype("boolean"))


def _postgres_visitor(policy, versions=("12.0.0", "29.0.1", "16.15")):
    """Supply observations explicitly; do not pretend an unbound table is a driver."""
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.applicability import prepare_environment
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate
    from mountainash.core.capabilities.policy import _ExecutionContext

    CapabilityRegistry.ensure_loaded()
    table = ibis.table({"value": "string", "pattern": "string"}, name="source")
    coordinates = (("package", "ibis-framework"), ("package", "sqlglot"), ("engine", "postgres"))
    observations = Environment(tuple(
        EnvironmentCoordinate(kind, name, version) for (kind, name), version in zip(coordinates, versions)
    ))
    context = _ExecutionContext(
        policy, _CapabilityTarget(BackendIdentity(CONST_BACKEND.IBIS, "ibis-postgres"), table),
        observations, prepare_environment(observations, frozenset((kind, name, True) for kind, name in coordinates)),
    )
    system = get_expression_system(CONST_BACKEND.IBIS)(dialect="ibis-postgres", execution_context=context)
    visitor = UnifiedExpressionVisitor(system, execution_context=context, input_data=table)
    return visitor, table


def _postgres_regex(shape, policy, versions=("12.0.0", "29.0.1", "16.15"), *, sensitive=False):
    visitor, table = _postgres_visitor(policy, versions)
    pattern = {
        "column": ma.col("pattern"), "computed": ma.col("pattern") + ma.lit("$"),
        "computed-constant": ma.lit("^AU") + ma.lit("$"),
        "native-column": ma.native(table.pattern), "native-computed": ma.native(table.pattern + "$"),
        "deferred": ma.native(ibis._["pattern"]), "literal": "^AU$",
        "literal-expression": ma.lit("^AU$"), "native-literal": ma.native(ibis.literal("^AU$")),
    }[shape]
    expression = ma.col("value").str.regex_contains(pattern, case_sensitive=sensitive)
    compiled = table.select(visitor.visit(expression.node).name("result")).result
    return compiled, table


@pytest.mark.parametrize("shape", [
    "column", "computed", "computed-constant", "native-column", "native-computed", "deferred",
])
@pytest.mark.parametrize("policy", [ma.CapabilityPolicy.checked(), ma.CapabilityPolicy.native_debugging()])
def test_postgres_dynamic_insensitive_regex_is_refused(shape, policy):
    with pytest.raises(BackendCapabilityError) as error:
        _postgres_regex(shape, policy)
    assert error.value.function_key.name == "REGEX_CONTAINS"
    assert error.value.backend == "ibis"


@pytest.mark.parametrize("shape,sensitive", [
    ("literal", False), ("literal-expression", False), ("native-literal", False),
    ("column", True), ("native-column", True),
])
def test_postgres_regex_supported_neighbors_retain_native_compilation(shape, sensitive):
    compiled, table = _postgres_regex(shape, ma.CapabilityPolicy.checked(), sensitive=sensitive)
    pattern = table.pattern if "column" in shape else ibis.literal("(?i)^AU$")
    native = table.select(table.value.re_search(pattern).name("result")).result
    assert ibis.to_sql(compiled, dialect="postgres") == ibis.to_sql(native, dialect="postgres")


@pytest.mark.parametrize("coordinate,value", [
    (0, "12.0.1"), (1, "29.0.2"), (2, "16.16"), (0, None), (1, None), (2, None),
])
def test_postgres_unqualified_stack_skips_native_inspection(monkeypatch, coordinate, value):
    versions = ["12.0.0", "29.0.1", "16.15"]
    versions[coordinate] = value
    _assert_postgres_bypass_without_inspection(monkeypatch, ma.CapabilityPolicy.checked(), tuple(versions))


@pytest.mark.parametrize("mode", ["trusted", "excluded-semantics"])
def test_postgres_unselected_policy_skips_native_inspection(monkeypatch, mode):
    from mountainash.core.capabilities.schema import CapabilityIssueClass

    policy = (ma.CapabilityPolicy.trusted() if mode == "trusted" else ma.CapabilityPolicy.checked(
        protection=frozenset({CapabilityIssueClass.AVAILABILITY}),
    ))
    _assert_postgres_bypass_without_inspection(monkeypatch, policy, ("12.0.0", "29.0.1", "16.15"))


def _assert_postgres_bypass_without_inspection(monkeypatch, policy, versions):
    from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem

    def forbidden_inspection(self, value):
        raise AssertionError("inactive protection inspected a native argument")

    monkeypatch.setattr(IbisBaseExpressionSystem, "native_argument_form", forbidden_inspection)
    compiled, table = _postgres_regex("native-column", policy, versions)
    native = table.select(table.value.re_search(ibis.literal("(?i)") + table.pattern).name("result")).result
    assert ibis.to_sql(compiled, dialect="postgres") == ibis.to_sql(native, dialect="postgres")


def _postgres_decimal(policy, versions=("12.0.0", "29.0.1", "16.15"), *,
                      failure_behavior="null", rounding="half_to_even"):
    visitor, table = _postgres_visitor(policy, versions)
    expression = ma.col("value").cast(
        ma.DecimalDtype(5, 2), rounding=rounding, failure_behavior=failure_behavior,
    )
    return table.select(visitor.visit(expression.node).name("result")).result


@pytest.mark.parametrize("rounding", ["half_to_even", "half_away_from_zero", "to_zero"])
@pytest.mark.parametrize("policy", [ma.CapabilityPolicy.checked(), ma.CapabilityPolicy.native_debugging()])
def test_postgres_null_on_invalid_decimal_is_refused(rounding, policy):
    # Prevent reaching strict native TryCast lowering when null-on-invalid was requested.
    with pytest.raises(BackendCapabilityError) as error:
        _postgres_decimal(policy, rounding=rounding)
    assert error.value.function_key.name == "DECIMAL_CAST"
    assert error.value.backend == "ibis"


@pytest.mark.parametrize("rounding", ["half_to_even", "half_away_from_zero", "to_zero"])
def test_postgres_strict_decimal_remains_available(rounding):
    compiled = _postgres_decimal(
        ma.CapabilityPolicy.checked(), failure_behavior="throw", rounding=rounding,
    )
    assert compiled.type() == ibis.dtype("decimal(5, 2)")


@pytest.mark.parametrize("coordinate,value", [
    (0, "12.0.1"), (1, "29.0.2"), (2, "16.16"), (0, None), (1, None), (2, None),
])
def test_postgres_decimal_unqualified_stack_retains_native_lowering(coordinate, value):
    versions = ["12.0.0", "29.0.1", "16.15"]
    versions[coordinate] = value
    compiled = _postgres_decimal(ma.CapabilityPolicy.checked(), tuple(versions))
    assert compiled.type() == ibis.dtype("decimal(5, 2)")


@pytest.mark.parametrize("mode", ["trusted", "excluded-semantics"])
def test_postgres_decimal_unselected_protection_retains_native_lowering(mode):
    from mountainash.core.capabilities.schema import CapabilityIssueClass

    policy = (ma.CapabilityPolicy.trusted() if mode == "trusted" else ma.CapabilityPolicy.checked(
        protection=frozenset({CapabilityIssueClass.AVAILABILITY}),
    ))
    compiled = _postgres_decimal(policy)
    assert compiled.type() == ibis.dtype("decimal(5, 2)")
