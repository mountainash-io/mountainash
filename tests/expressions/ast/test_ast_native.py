"""AST construction tests for native expression API builder."""
import pytest
import mountainash.expressions as ma


class TestNativeMethod:
    def test_native_wraps_expression(self):
        expr = ma.native("raw_backend_expr")
        assert expr._node is not None
