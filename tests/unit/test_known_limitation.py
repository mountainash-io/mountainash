"""Unit tests for KnownLimitation and BackendCapabilityError."""

import pytest
from mountainash.core.types import KnownLimitation, BackendCapabilityError


class TestKnownLimitation:
    def test_frozen_dataclass(self):
        lim = KnownLimitation(
            message="test limitation",
            native_errors=(TypeError,),
        )
        assert lim.message == "test limitation"
        assert lim.native_errors == (TypeError,)
        assert lim.upstream_issue is None
        assert lim.workaround is None

    def test_with_all_fields(self):
        lim = KnownLimitation(
            message="test",
            native_errors=(TypeError, ValueError),
            upstream_issue="https://github.com/pola-rs/polars/issues/123",
            workaround="Use a literal value",
        )
        assert lim.upstream_issue == "https://github.com/pola-rs/polars/issues/123"
        assert lim.workaround == "Use a literal value"

    def test_immutable(self):
        lim = KnownLimitation(message="test", native_errors=(TypeError,))
        with pytest.raises(AttributeError):
            lim.message = "changed"


class TestBackendCapabilityError:
    def test_basic_error(self):
        err = BackendCapabilityError(
            "cannot do this",
            backend="polars",
            function_key="CONTAINS",
        )
        assert "[polars]" in str(err)
        assert "cannot do this" in str(err)
        assert err.backend == "polars"
        assert err.function_key == "CONTAINS"
        assert err.limitation is None

    def test_error_with_limitation(self):
        lim = KnownLimitation(
            message="test",
            native_errors=(TypeError,),
            workaround="Use a literal",
            upstream_issue="https://github.com/example/issue/1",
        )
        err = BackendCapabilityError(
            "cannot do this",
            backend="narwhals",
            function_key="STARTS_WITH",
            limitation=lim,
        )
        msg = str(err)
        assert "Workaround: Use a literal" in msg
        assert "Upstream: https://github.com/example/issue/1" in msg

    def test_error_without_workaround(self):
        lim = KnownLimitation(
            message="test",
            native_errors=(TypeError,),
        )
        err = BackendCapabilityError(
            "cannot do this",
            backend="polars",
            function_key="REPLACE",
            limitation=lim,
        )
        msg = str(err)
        assert "Workaround" not in msg
        assert "Upstream" not in msg

    def test_is_exception(self):
        err = BackendCapabilityError(
            "test", backend="polars", function_key="CONTAINS"
        )
        assert isinstance(err, Exception)
        with pytest.raises(BackendCapabilityError):
            raise err
