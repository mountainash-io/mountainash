"""Row identity: tiered resolution + keyed gate (spec §7).

Cross-backend keyed-identity validation (validate_keyed_identity against real
data across all backends) lives in cross_backend/test_identity_keyed.py.
"""
import pytest

from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityRequiredError,
)
from mountainash.validation.identity import (
    RowIdentity,
    require_keyed,
    resolve_identity,
)


class TestResolution:
    def test_explicit_natural_key_wins(self):
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.ANY)], primary_key=["id"])
        identity = resolve_identity(natural_key=["code"], spec=spec)
        assert identity == RowIdentity(kind="keyed", key_fields=("code",))

    def test_primary_key_from_spec(self):
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.ANY)], primary_key=["id"])
        assert resolve_identity(spec=spec) == RowIdentity(kind="keyed", key_fields=("id",))

    def test_composite_primary_key(self):
        spec = TypeSpec(fields=[], primary_key=["a", "b"])
        assert resolve_identity(spec=spec).key_fields == ("a", "b")

    def test_row_number_opt_in(self):
        assert resolve_identity(row_identity="row_number") == RowIdentity(kind="row_number")

    def test_default_is_none(self):
        assert resolve_identity() == RowIdentity(kind="none")

    def test_unknown_row_identity_raises(self):
        with pytest.raises(CheckDeclarationError):
            resolve_identity(row_identity="positional")


def test_require_keyed_gates():
    require_keyed(RowIdentity("keyed", ("id",)), feature="pivot_key_fields")  # no raise
    with pytest.raises(IdentityRequiredError, match="pivot_key_fields"):
        require_keyed(RowIdentity("row_number"), feature="pivot_key_fields")
    with pytest.raises(IdentityRequiredError):
        require_keyed(RowIdentity("none"), feature="interpolate_messages")


def test_composite_unique_excludes_any_null_row():
    """Composite uniqueness follows MATCH SIMPLE null exclusion."""
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.validation import ValidationRunner

    frame = pl.DataFrame({"a": [1, 1, 1], "b": [None, None, 2]})
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            unique_keys=[["a", "b"]],
        )
    )

    result = ValidationRunner().validate_relation(frame, plan=plan)

    assert result.check_summaries.filter(pl.col("check_id") == "unique_key__0")[
        "fail_count"
    ].item() == 0
