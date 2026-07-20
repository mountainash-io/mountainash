"""BackendCapabilityError formatting for CapabilityFact inputs."""
from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def test_error_formats_fact_workaround_and_upstream_ref():
    fact = CapabilityFact(
        operation_key=FK_STR.LPAD,
        param="characters",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.POLARS,
        message="Polars str.lpad() requires a single literal fill character",
        workaround="Use a literal single-character string",
        upstream_ref="PL-STR-01",
        since="2026-07-05",
    )
    err = BackendCapabilityError(
        fact.message, backend="polars", function_key=FK_STR.LPAD, limitation=fact
    )
    text = str(err)
    assert "[polars]" in text
    assert "Workaround: Use a literal single-character string" in text
    assert "Upstream ref: PL-STR-01" in text
    assert err.limitation is fact
