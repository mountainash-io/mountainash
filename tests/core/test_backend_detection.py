"""Tests for core-level backend detection (moved from expsys_base)."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.backend_detection import identify_backend, _BACKEND_ALIASES


class TestIdentifyBackendCore:
    def test_string_alias(self):
        assert identify_backend("pl") is CONST_BACKEND.POLARS
        assert identify_backend("narwhals") is CONST_BACKEND.NARWHALS

    def test_enum_passthrough(self):
        assert identify_backend(CONST_BACKEND.IBIS) is CONST_BACKEND.IBIS

    def test_polars_dataframe(self):
        assert identify_backend(pl.DataFrame({"a": [1]})) is CONST_BACKEND.POLARS

    def test_unknown_string_raises(self):
        with pytest.raises(ValueError, match="Unknown backend identifier"):
            identify_backend("spark")

    def test_aliases_cover_all_short_names(self):
        assert {"pl", "ir", "nw", "pd"} <= set(_BACKEND_ALIASES)


class TestCompatReExport:
    def test_expsys_base_still_exports_identify_backend(self):
        from mountainash.expressions.core.expression_system.expsys_base import (
            identify_backend as legacy,
        )
        from mountainash.core.backend_detection import identify_backend as canonical
        assert legacy is canonical
