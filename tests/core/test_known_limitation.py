"""Unit tests for BackendCapabilityError.

The legacy ``KnownLimitation`` dataclass was retired in the capability spine's
Phase 1; the enrichment ``limitation`` payload is now a ``CapabilityFact``
(the spine's MATERIALIZE residue). ``CapabilityFact`` itself is unit-tested in
``test_capability_schema.py``.
"""

import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError


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
        fact = CapabilityFact(
            operation_key="STARTS_WITH",
            param="prefix",
            level=CapabilityLevel.LITERAL_ONLY,
            backend=CONST_BACKEND.NARWHALS,
            message="test",
            workaround="Use a literal",
            upstream_ref="NW-STR-01",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            boundary=Boundary.MATERIALIZE,
            native_errors=(TypeError,),
            since="2026-07-05",
        )
        err = BackendCapabilityError(
            "cannot do this",
            backend="narwhals",
            function_key="STARTS_WITH",
            limitation=fact,
        )
        msg = str(err)
        assert "Workaround: Use a literal" in msg
        assert "Upstream ref: NW-STR-01" in msg

    def test_error_without_workaround(self):
        fact = CapabilityFact(
            operation_key="REPLACE",
            param="substring",
            level=CapabilityLevel.LITERAL_ONLY,
            backend=CONST_BACKEND.POLARS,
            message="test",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            boundary=Boundary.MATERIALIZE,
            native_errors=(TypeError,),
            since="2026-07-05",
        )
        err = BackendCapabilityError(
            "cannot do this",
            backend="polars",
            function_key="REPLACE",
            limitation=fact,
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
