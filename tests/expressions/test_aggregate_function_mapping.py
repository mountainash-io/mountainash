"""All 13 aggregate functions from the scalar aggregate batch must be in the function registry."""
from __future__ import annotations

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE as K,
)
from mountainash.expressions.core.expression_system.function_mapping import (
    FunctionRegistry as ExpressionFunctionRegistry,
)


EXPECTED_KEYS = {
    K.ANY_VALUE,
    K.SUM, K.AVG, K.MIN, K.MAX, K.PRODUCT,
    K.STD_DEV, K.VARIANCE, K.MODE,
    K.CORR, K.MEDIAN, K.QUANTILE,
}


def test_all_thirteen_aggregates_registered():
    ExpressionFunctionRegistry._init_registry()
    registered = set(ExpressionFunctionRegistry._functions.keys())
    missing = EXPECTED_KEYS - registered
    assert not missing, f"Missing aggregate registrations: {sorted(k.name for k in missing)}"
