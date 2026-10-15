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
