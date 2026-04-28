"""AST construction tests for string API builders."""
import pytest
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode, IfThenNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING, FKEY_MOUNTAINASH_SCALAR_STRING


class TestStringUnary:
    @pytest.mark.parametrize("method,fkey", [
        ("lower", FKEY_SUBSTRAIT_SCALAR_STRING.LOWER),
        ("upper", FKEY_SUBSTRAIT_SCALAR_STRING.UPPER),
        ("swapcase", FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE),
        ("capitalize", FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE),
        ("title", FKEY_SUBSTRAIT_SCALAR_STRING.TITLE),
        ("initcap", FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP),
        ("char_length", FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH),
        ("bit_length", FKEY_SUBSTRAIT_SCALAR_STRING.BIT_LENGTH),
        ("octet_length", FKEY_SUBSTRAIT_SCALAR_STRING.OCTET_LENGTH),
        ("reverse", FKEY_SUBSTRAIT_SCALAR_STRING.REVERSE),
    ])
    def test_unary_string(self, method, fkey):
        expr = getattr(ma.col("x").str, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestStringTrimming:
    @pytest.mark.parametrize("method,fkey", [
        ("trim", FKEY_SUBSTRAIT_SCALAR_STRING.TRIM),
        ("ltrim", FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
        ("rtrim", FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
    ])
    def test_trim_default(self, method, fkey):
        expr = getattr(ma.col("x").str, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey

    @pytest.mark.parametrize("method,fkey", [
        ("trim", FKEY_SUBSTRAIT_SCALAR_STRING.TRIM),
        ("ltrim", FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
        ("rtrim", FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
    ])
    def test_trim_with_chars(self, method, fkey):
        expr = getattr(ma.col("x").str, method)("xy")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) >= 2


class TestStringPadding:
    @pytest.mark.parametrize("method,fkey", [
        ("lpad", FKEY_SUBSTRAIT_SCALAR_STRING.LPAD),
        ("rpad", FKEY_SUBSTRAIT_SCALAR_STRING.RPAD),
    ])
    def test_padding(self, method, fkey):
        expr = getattr(ma.col("x").str, method)(10, "*")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey

    def test_center(self):
        expr = ma.col("x").str.center(10, "*")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CENTER


class TestStringExtraction:
    def test_substring(self):
        expr = ma.col("x").str.substring(1, 3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING

    @pytest.mark.parametrize("method,fkey", [
        ("left", FKEY_SUBSTRAIT_SCALAR_STRING.LEFT),
        ("right", FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT),
    ])
    def test_left_right(self, method, fkey):
        expr = getattr(ma.col("x").str, method)(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey

    def test_replace_slice(self):
        expr = ma.col("x").str.replace_slice(1, 3, "XY")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE


class TestStringSearch:
    @pytest.mark.parametrize("method,fkey,arg", [
        ("contains", FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, "abc"),
        ("starts_with", FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, "pre"),
        ("ends_with", FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, "suf"),
    ])
    def test_search_method(self, method, fkey, arg):
        expr = getattr(ma.col("x").str, method)(arg)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2

    def test_strpos(self):
        expr = ma.col("x").str.strpos("abc")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS

    def test_count_substring(self):
        expr = ma.col("x").str.count_substring("a")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING


class TestStringManipulation:
    def test_replace(self):
        expr = ma.col("x").str.replace("old", "new")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE

    def test_repeat(self):
        expr = ma.col("x").str.repeat(3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT

    def test_concat(self):
        expr = ma.col("x").str.concat(ma.col("y"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT

    def test_concat_ws(self):
        expr = ma.col("x").str.concat_ws(",", ma.col("y"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT_WS

    @pytest.mark.xfail(reason="builder references FKEY_SUBSTRAIT_SCALAR_STRING.STRING_SPLIT but enum has SPLIT")
    def test_string_split(self):
        expr = ma.col("x").str.string_split(",")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT


class TestStringPattern:
    def test_like(self):
        expr = ma.col("x").str.like("%abc%")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LIKE

    @pytest.mark.xfail(reason="builder references REGEXP_MATCH_SUBSTRING but enum has REGEXP_MATCH")
    def test_regexp_match_substring(self):
        expr = ma.col("x").str.regexp_match_substring(r"\d+")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH

    def test_regexp_replace(self):
        expr = ma.col("x").str.regexp_replace(r"\d+", "NUM")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE

    @pytest.mark.xfail(reason="builder references REGEXP_STRING_SPLIT but enum has REGEXP_SPLIT")
    def test_regexp_string_split(self):
        expr = ma.col("x").str.regexp_string_split(r"\s+")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT

    def test_regex_replace(self):
        # regex_replace delegates to regexp_replace → same fkey
        expr = ma.col("x").str.regex_replace(r"\d+", "NUM")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE

    def test_regex_contains(self):
        # regex_contains routes through the mountainash REGEX_CONTAINS extension
        expr = ma.col("x").str.regex_contains(r"\d+")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS

    def test_regex_match(self):
        # regex_match delegates to regex_contains (with anchored pattern) → REGEX_CONTAINS fkey
        expr = ma.col("x").str.regex_match(r"^\d+$")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS


class TestStringAliases:
    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("to_uppercase", "upper"),
        ("to_lowercase", "lower"),
    ])
    def test_case_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x").str, canonical_method)()._node
        alias = getattr(ma.col("x").str, alias_method)()._node
        assert canonical.function_key == alias.function_key

    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("strip_chars", "trim"),
        ("strip_chars_start", "ltrim"),
        ("strip_chars_end", "rtrim"),
    ])
    def test_strip_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x").str, canonical_method)()._node
        alias = getattr(ma.col("x").str, alias_method)()._node
        assert canonical.function_key == alias.function_key

    @pytest.mark.parametrize("alias_method", ["len_chars", "length", "len"])
    def test_length_alias(self, alias_method):
        canonical = ma.col("x").str.char_length()._node
        alias = getattr(ma.col("x").str, alias_method)()._node
        assert canonical.function_key == alias.function_key

    def test_strip_prefix(self):
        # strip_prefix creates an IfThenNode (conditional AST composition)
        expr = ma.col("x").str.strip_prefix("pre_")
        assert isinstance(expr._node, IfThenNode)

    def test_strip_suffix(self):
        expr = ma.col("x").str.strip_suffix("_suf")
        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.options == {"suffix": "_suf"}
