"""All 13 aggregate functions from the scalar aggregate batch must be in the function registry."""
from __future__ import annotations

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE as K,
)
from mountainash.expressions.core.expression_system.function_mapping import (
    FunctionRegistry,
)


EXPECTED_KEYS: set[K] = {
    K.ANY_VALUE,
    K.SUM, K.AVG, K.MIN, K.MAX, K.PRODUCT,
    K.STD_DEV, K.VARIANCE, K.MODE,
    K.CORR, K.MEDIAN, K.QUANTILE,
}


def test_all_thirteen_aggregates_registered():
    FunctionRegistry._init_registry()
    missing = {k for k in EXPECTED_KEYS if k not in FunctionRegistry._functions}
    assert not missing, f"Missing aggregate registrations: {sorted(k.name for k in missing)}"
