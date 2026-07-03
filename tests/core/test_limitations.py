"""Core limitation-enrichment helper (spec §3.8)."""
from __future__ import annotations

import pytest

from mountainash.core.limitations import (
    MATERIALIZE_BOUNDARY,
    WILDCARD_PARAM,
    call_with_limitation_enrichment,
)
from mountainash.core.types import BackendCapabilityError, KnownLimitation

KEY = "op_key"
LIM = KnownLimitation(
    message="known quirk",
    native_errors=(NotImplementedError,),
    workaround="use polars",
)


def _boom():
    raise NotImplementedError("native")


class TestEnrichment:
    def test_named_param_match_enriches(self):
        with pytest.raises(BackendCapabilityError) as exc:
            call_with_limitation_enrichment(
                _boom,
                limitations={(KEY, "tolerance"): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=("tolerance",),
            )
        assert exc.value.limitation is LIM
        assert exc.value.__cause__.__class__ is NotImplementedError

    def test_wildcard_match_enriches_without_named_args(self):
        with pytest.raises(BackendCapabilityError):
            call_with_limitation_enrichment(
                _boom,
                limitations={(KEY, WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=(),
            )

    def test_no_match_reraises_original(self):
        with pytest.raises(NotImplementedError):
            call_with_limitation_enrichment(
                _boom,
                limitations={("other_key", WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=("x",),
            )

    def test_wrong_error_type_reraises_original(self):
        def type_boom():
            raise TypeError("different")

        with pytest.raises(TypeError):
            call_with_limitation_enrichment(
                type_boom,
                limitations={(KEY, WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=(),
            )

    def test_backend_capability_error_passes_through_unwrapped(self):
        inner = BackendCapabilityError(
            "already enriched", backend="polars", function_key=KEY, limitation=LIM
        )

        def raise_bce():
            raise inner

        with pytest.raises(BackendCapabilityError) as exc:
            call_with_limitation_enrichment(
                raise_bce,
                limitations={(KEY, WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=(),
            )
        assert exc.value is inner  # not re-wrapped

    def test_success_passes_value_through(self):
        out = call_with_limitation_enrichment(
            lambda: 42,
            limitations={},
            backend_name="polars",
            operation_key=KEY,
            named_args=(),
        )
        assert out == 42

    def test_materialize_boundary_sentinel_is_hashable_key(self):
        {(MATERIALIZE_BOUNDARY, WILDCARD_PARAM): LIM}
