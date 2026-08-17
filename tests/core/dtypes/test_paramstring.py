"""Unit tests for the restricted AST-validated dtype-repr parser.

Security-relevant surface: ``parse_constructor_repr`` must NEVER evaluate
arbitrary input — only a bounded grammar (bare Name, or Call(Name, args)
whose arguments are Constant / whitelisted-Name / list / tuple). Every
adversarial case below must return None, never raise or execute.

Positive cases cover the Critical-finding fix: a bare ``Name`` used as a
positional/keyword argument (``List(Int64)``, ``Array(Int64, shape=(5,))``)
resolves against the SAME closed namespace, not a wider lookup.
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes._paramstring import parse_constructor_repr


class _Box:
    """Minimal stand-in for a dtype constructor: records its arguments."""

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs


# Closed namespace mirroring the shape of the polars/narwhals whitelists.
_NS = {
    "Datetime": _Box,
    "List": _Box,
    "Array": _Box,
    "Enum": _Box,
    "Int64": "INT64",
    "shape": "SHAPE",
}


class TestPositive:
    def test_bare_name(self):
        assert parse_constructor_repr("Int64", _NS) == "INT64"

    def test_bare_name_arg_resolves_against_namespace(self):
        """The Critical-finding case: Name args must resolve, not be rejected."""
        result = parse_constructor_repr("List(Int64)", _NS)
        assert isinstance(result, _Box)
        assert result.args == ("INT64",)

    def test_name_arg_plus_tuple_of_constants_kwarg(self):
        result = parse_constructor_repr("Array(Int64, shape=(5,))", _NS)
        assert isinstance(result, _Box)
        assert result.args == ("INT64",)
        assert result.kwargs == {"shape": (5,)}

    def test_all_constant_kwargs(self):
        result = parse_constructor_repr(
            "Datetime(time_unit='us', time_zone='UTC')", _NS
        )
        assert isinstance(result, _Box)
        assert result.kwargs == {"time_unit": "us", "time_zone": "UTC"}

    def test_list_arg(self):
        result = parse_constructor_repr("Enum(categories=['a', 'b'])", _NS)
        assert isinstance(result, _Box)
        assert result.kwargs == {"categories": ["a", "b"]}


class TestNegative:
    """Everything outside the bounded grammar returns None — never executes."""

    @pytest.mark.parametrize("s", [
        "os.system('x')",           # attribute access
        "eval('1')",                # arbitrary call
        "Datetime.__init__()",      # method call
        "(lambda: 1)()",            # lambda
        "[x for x in [1, 2]]",      # comprehension (also not a valid expr form)
        "__import__('os')",         # import builtin
        "Datetime(*[1, 2])",        # starred unpacking
        "List(__builtins__)",       # Name outside whitelist in arg position
        "1 + 1",                    # operator expression
        "Datetime.time_unit",       # attribute access as target
    ])
    def test_rejected_returns_none(self, s):
        assert parse_constructor_repr(s, _NS) is None

    def test_unparseable_syntax_returns_none(self):
        assert parse_constructor_repr("not valid python !!!", _NS) is None

    def test_empty_string_returns_none(self):
        assert parse_constructor_repr("", _NS) is None

    def test_unknown_top_level_name_returns_none(self):
        assert parse_constructor_repr("NotInNamespace", _NS) is None
        assert parse_constructor_repr("NotInNamespace(1)", _NS) is None


class TestDoubleStarKwargDrop:
    def test_unpacked_kwargs_are_dropped_not_applied(self):
        """Deliberate, documented behavior: **dict-unpacked keywords are
        dropped (real Polars/Narwhals str() output never emits this form)."""
        result = parse_constructor_repr(
            "Datetime(time_unit='us', **{'time_zone': 'UTC'})", _NS
        )
        assert isinstance(result, _Box)
        assert result.kwargs == {"time_unit": "us"}
        assert "time_zone" not in result.kwargs

    def test_fully_unpacked_kwargs_construct_with_nothing(self):
        """All-keywords-unpacked form drops everything — constructs with zero
        kwargs, never rejects (matches the documented drop, not a raise)."""
        result = parse_constructor_repr("Datetime(**{'a': 1})", _NS)
        assert isinstance(result, _Box)
        assert result.kwargs == {}
