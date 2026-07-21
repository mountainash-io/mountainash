"""Value-aware capability gating for scalar-function options."""

import pytest

from expressions.argument_types.conftest import make_df
from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import (
    FieldReferenceNode,
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_system.expsys_base import (
    get_expression_system,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


_TEST_DIALECT = "polars"
_UNSUPPORTED_OPTION_VALUE = "__UNIT_TEST_UNSUPPORTED__"


@pytest.fixture(autouse=True)
def _isolate_registry():
    snap = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _abs_node_with_options(options):
    return ScalarFunctionNode(
        function_key=FK_ARITH.ABS,
        arguments=[FieldReferenceNode(field="v")],
        options=options,
    )


def _compile_node(node, df, backend):
    identity = identify_backend_identity(df)
    assert identity.family is CONST_BACKEND(backend)
    system_cls = get_expression_system(identity.family)
    visitor = UnifiedExpressionVisitor(system_cls(dialect=_TEST_DIALECT))
    return visitor.visit(node)


def test_declared_unsupported_option_raises_before_dispatch():
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_ARITH.ABS,
                param="overflow",
                option_value=_UNSUPPORTED_OPTION_VALUE,
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect=_TEST_DIALECT,
                message="polars abs has no checked overflow",
                since="2026-07-21",
                condition=(
                    "options['overflow'] == '__UNIT_TEST_UNSUPPORTED__'"
                ),
            ),
        ],
    )
    df = make_df({"v": [1]}, "polars")
    node = _abs_node_with_options({"overflow": _UNSUPPORTED_OPTION_VALUE})

    with pytest.raises(BackendCapabilityError):
        _compile_node(node, df, "polars")
