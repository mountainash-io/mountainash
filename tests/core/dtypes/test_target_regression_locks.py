"""Invalid backend type strings must not acquire a fallback dtype."""
from __future__ import annotations


from mountainash.core.dtypes import TypeTarget, registry


class TestIbisRegressionLocks:
    def test_garbage_still_rejected(self):
        assert registry.parse_type_string("not a type", TypeTarget.IBIS) is None


class TestPandasRegressionLocks:
    def test_garbage_still_rejected(self):
        assert registry.parse_type_string("not_a_dtype", TypeTarget.PANDAS) is None
