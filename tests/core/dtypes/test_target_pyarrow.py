"""PyArrow parse_type_string — parameterized backend_type fidelity (item 54, gap 1).

PyArrow's str() format is bracket/paren grammar (timestamp[us, tz=UTC],
decimal128(38, 10)) — a distinct, bounded family parsed via regex after
pa.type_for_alias fails. Recursive list<...>/struct<...> strings are
explicitly out of scope and must stay None (never a silent partial parse).
"""
from __future__ import annotations

import pyarrow as pa
import pytest

from mountainash.core.dtypes import target_pyarrow


class TestParameterizedRoundTrip:
    @pytest.mark.parametrize("s,expected", [
        ("timestamp[us, tz=UTC]", pa.timestamp("us", tz="UTC")),
        ("timestamp[ns]", pa.timestamp("ns")),
        ("decimal128(38, 10)", pa.decimal128(38, 10)),
        ("decimal256(38, 10)", pa.decimal256(38, 10)),
        ("duration[ms]", pa.duration("ms")),
        ("time64[ns]", pa.time64("ns")),
        ("time32[s]", pa.time32("s")),
    ])
    def test_parameterized_repr_round_trips(self, s, expected):
        assert target_pyarrow.parse_type_string(s) == expected

    def test_bare_name_via_alias_unchanged(self):
        assert target_pyarrow.parse_type_string("int64") == pa.int64()
        assert target_pyarrow.parse_type_string("string") == pa.string()


class TestSemanticallyInvalidReturnsNone:
    """Syntactically-valid-but-semantically-invalid strings match their regex
    but must return None (never leak a raw Arrow constructor ValueError) so
    the resolver raises the typed InvalidBackendTypeError instead."""

    @pytest.mark.parametrize("s", [
        "timestamp[badunit]",
        "decimal128(999, 10)",
        "decimal256(999, 10)",
        "time64[badunit]",
        "time32[badunit]",
        "duration[badunit]",
    ])
    def test_semantically_invalid_returns_none(self, s):
        assert target_pyarrow.parse_type_string(s) is None


class TestOutOfScopeStaysNone:
    @pytest.mark.parametrize("s", [
        "list<item: int64>",     # recursive list grammar — out of scope
        "struct<a: int64>",      # recursive struct grammar — out of scope
        "fixed_size_list<item: int64>[2]",
    ])
    def test_recursive_grammar_returns_none(self, s):
        """Asserted explicitly: a silent partial parse would be worse than
        None (canonical fallback handles the container honestly)."""
        assert target_pyarrow.parse_type_string(s) is None

    def test_garbage_returns_none(self):
        assert target_pyarrow.parse_type_string("not_a_type") is None
        assert target_pyarrow.parse_type_string("timestamp[us, tz=UTC") is None
