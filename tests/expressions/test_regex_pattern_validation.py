"""The anchored regex_match wrapper still requires a literal pattern."""
from __future__ import annotations

import pytest

import mountainash as ma


def test_regex_match_rejects_expression_pattern():
    """Expression-pattern support in regex_contains does not expand regex_match."""
    with pytest.raises(TypeError):
        ma.col("name").str.regex_match(ma.col("regex_col"))
