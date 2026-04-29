"""AST-level tests for Tier 3 .str namespace operations."""

from __future__ import annotations

import mountainash as ma
from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import (
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_STRING,
)


def _get_node(expr):
    """Extract the underlying AST node from an expression."""
    return expr._node


class TestToTimeAST:
    def test_to_time_creates_scalar_function_node(self):
        expr = ma.col("t").str.to_time("%H:%M:%S")
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME
        assert node.options == {"format": "%H:%M:%S"}

    def test_to_time_different_format(self):
        expr = ma.col("t").str.to_time("%I:%M %p")
        node = _get_node(expr)
        assert node.options["format"] == "%I:%M %p"


class TestToIntegerAST:
    def test_to_integer_default_base(self):
        expr = ma.col("s").str.to_integer()
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.TO_INTEGER
        assert node.options == {"base": 10}

    def test_to_integer_custom_base(self):
        expr = ma.col("s").str.to_integer(base=16)
        node = _get_node(expr)
        assert node.options == {"base": 16}


class TestJsonDecodeAST:
    def test_json_decode_creates_node(self):
        import polars as pl

        expr = ma.col("j").str.json_decode(pl.Utf8)
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE
        assert node.options["dtype"] == pl.Utf8

    def test_json_decode_none_dtype(self):
        expr = ma.col("j").str.json_decode()
        node = _get_node(expr)
        assert node.options == {"dtype": None}


class TestJsonPathMatchAST:
    def test_json_path_match_creates_node(self):
        expr = ma.col("j").str.json_path_match("$.name")
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH
        assert node.options == {"json_path": "$.name"}


class TestEncodeAST:
    def test_encode_hex(self):
        expr = ma.col("s").str.encode("hex")
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE
        assert node.options == {"encoding": "hex"}

    def test_encode_base64(self):
        expr = ma.col("s").str.encode("base64")
        node = _get_node(expr)
        assert node.options == {"encoding": "base64"}


class TestDecodeAST:
    def test_decode_hex(self):
        expr = ma.col("s").str.decode("hex")
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.DECODE
        assert node.options == {"encoding": "hex", "strict": True}

    def test_decode_not_strict(self):
        expr = ma.col("s").str.decode("base64", strict=False)
        node = _get_node(expr)
        assert node.options == {"encoding": "base64", "strict": False}


class TestExtractGroupsAST:
    def test_extract_groups_creates_node(self):
        expr = ma.col("s").str.extract_groups(r"(?P<a>\w+)-(?P<b>\w+)")
        node = _get_node(expr)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS
        assert node.options == {"pattern": r"(?P<a>\w+)-(?P<b>\w+)"}
