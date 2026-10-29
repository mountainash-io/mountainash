# tests/expressions/ast/test_typed_nodes.py
import polars as pl
import pytest
from pydantic import ValidationError

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D, NativeDtype, UnknownDtypeError
from mountainash.expressions.core.expression_nodes.substrait.exn_cast import CastNode
from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode


class TestCastNodeTyping:
    def test_canonical_target(self):
        node = ma.col("x").cast("i64")._node
        assert node.target_type is D.I64

    def test_python_type_target(self):
        node = ma.col("x").cast(int)._node
        assert node.target_type is D.I64

    def test_native_target_wrapped(self):
        node = ma.col("x").cast(pl.Datetime("us", "UTC"))._node
        assert isinstance(node.target_type, NativeDtype)
        assert node.target_type.value == pl.Datetime("us", "UTC")

    def test_invalid_dtype_fails_at_build_time(self):
        with pytest.raises(UnknownDtypeError, match="i65"):
            ma.col("x").cast("i65")


class TestLiteralNodeTyping:
    def test_native_marker_is_flag(self):
        node = ma.native(pl.col("x") * 2)._node
        assert node.is_native is True
        assert node.dtype is None

    def test_default_not_native(self):
        assert LiteralNode(value=42).is_native is False

    def test_dtype_accepts_enum(self):
        assert LiteralNode(value=1, dtype=D.I32).dtype is D.I32

    def test_dtype_rejects_arbitrary_string(self):
        with pytest.raises(ValidationError):
            LiteralNode(value=1, dtype="native")
