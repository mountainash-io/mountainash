"""Regression locks for Ibis/Pandas parameterized backend_type parsing.

These two targets were ALREADY correct at item 54's start (verified
empirically): ibis.dtype() is a full grammar parser, pandas_dtype() is the
official pandas parser. This item deliberately makes NO production change to
them — these tests guard against future upstream drift in libraries we don't
touch, exercised through the same registry.parse_type_string surface the
resolver uses.
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import TypeTarget, registry


class TestIbisRegressionLocks:
    @pytest.mark.parametrize("s", [
        "timestamp('UTC')",          # parameterized temporal
        "decimal(38, 9)",            # parameterized decimal
        "array<int64>",              # parameterized list
    ])
    def test_parameterized_strings_still_parse(self, s):
        assert registry.parse_type_string(s, TypeTarget.IBIS) == s

    def test_garbage_still_rejected(self):
        assert registry.parse_type_string("not a type", TypeTarget.IBIS) is None


class TestPandasRegressionLocks:
    @pytest.mark.parametrize("s", [
        "datetime64[ns, UTC]",       # parameterized temporal w/ tz
        "datetime64[ns]",            # plain temporal
        "category",                  # categorical
        "Int64",                     # pandas nullable int
        "timedelta64[ns]",
    ])
    def test_parameterized_strings_still_parse(self, s):
        assert registry.parse_type_string(s, TypeTarget.PANDAS) == s

    def test_garbage_still_rejected(self):
        assert registry.parse_type_string("not_a_dtype", TypeTarget.PANDAS) is None
