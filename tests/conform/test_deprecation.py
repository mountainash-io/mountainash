"""Tests for keep_unmapped deprecation transition behavior."""
from __future__ import annotations

import warnings
import pytest
import polars as pl
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestDeprecationTruthTable:
    def _make_df(self):
        return pl.DataFrame({"keep": ["a", "b"], "extra": [1, 2]})

    def test_absent_none_no_warning(self):
        """keep_unmapped absent, fields_match=None → no deprecation warning."""
        df = self._make_df()
        spec = TypeSpec(fields=[FieldSpec(name="keep", type=UniversalType.STRING)])
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            # Should not raise DeprecationWarning
            ma.relation(df).conform(spec).to_polars()

    def test_keep_unmapped_false_warns(self):
        """keep_unmapped=False → DeprecationWarning."""
        df = self._make_df()
        spec = TypeSpec(fields=[FieldSpec(name="keep", type=UniversalType.STRING)])
        with pytest.warns(DeprecationWarning, match="keep_unmapped"):
            ma.relation(df).conform(spec, keep_unmapped=False).to_polars()

    def test_keep_unmapped_true_warns(self):
        """keep_unmapped=True → DeprecationWarning."""
        df = self._make_df()
        spec = TypeSpec(fields=[FieldSpec(name="keep", type=UniversalType.STRING)])
        with pytest.warns(DeprecationWarning, match="keep_unmapped"):
            result = ma.relation(df).conform(spec, keep_unmapped=True).to_polars()
        assert "extra" in result.columns  # open behavior

    def test_keep_unmapped_true_with_explicit_fields_match_raises(self):
        """keep_unmapped=True + explicit fields_match → ValueError."""
        df = self._make_df()
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
            fields_match="partial",
        )
        with pytest.raises(ValueError, match="[Cc]onflicting"):
            ma.relation(df).conform(spec, keep_unmapped=True)

    def test_keep_unmapped_false_with_none_gives_partial(self):
        """keep_unmapped=False, fields_match=None → partial (drops extras)."""
        df = self._make_df()
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = ma.relation(df).conform(spec, keep_unmapped=False).to_polars()
        assert "extra" not in result.columns
