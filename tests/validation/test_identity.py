"""Row identity: tiered resolution + keyed validation (spec §7)."""
import pytest

import mountainash as ma
from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityInvalidError,
    IdentityRequiredError,
)
from mountainash.validation.identity import (
    RowIdentity,
    require_keyed,
    resolve_identity,
    validate_keyed_identity,
)

from fixtures.backend_registry import ALL_BACKENDS


class TestResolution:
    def test_explicit_natural_key_wins(self):
        spec = TypeSpec(fields=[FieldSpec(name="id")], primary_key="id")
        identity = resolve_identity(natural_key=["code"], spec=spec)
        assert identity == RowIdentity(kind="keyed", key_fields=("code",))

    def test_primary_key_from_spec(self):
        spec = TypeSpec(fields=[FieldSpec(name="id")], primary_key="id")
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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestKeyedValidation:
    def _rel(self, data, backend_name, backend_factory):
        return ma.relation(backend_factory.create(data, backend_name))

    def test_valid_key_returns_zero_diagnostics(self, backend_name, backend_factory):
        rel = self._rel({"id": [1, 2, 3], "v": [10, 20, 30]}, backend_name, backend_factory)
        diags = validate_keyed_identity(rel, RowIdentity("keyed", ("id",)))
        assert diags == {"null_key_rows": 0, "duplicate_key_tuples": 0}, f"[{backend_name}]"

    def test_missing_key_field_raises(self, backend_name, backend_factory):
        rel = self._rel({"v": [1]}, backend_name, backend_factory)
        with pytest.raises(IdentityInvalidError, match="missing"):
            validate_keyed_identity(rel, RowIdentity("keyed", ("id",)))

    def test_null_key_raises_by_default(self, backend_name, backend_factory):
        rel = self._rel({"id": [1, None, 3], "v": [1, 2, 3]}, backend_name, backend_factory)
        with pytest.raises(IdentityInvalidError):
            validate_keyed_identity(rel, RowIdentity("keyed", ("id",)))

    def test_duplicate_key_raises_by_default(self, backend_name, backend_factory):
        rel = self._rel({"id": [1, 1, 3], "v": [1, 2, 3]}, backend_name, backend_factory)
        with pytest.raises(IdentityInvalidError):
            validate_keyed_identity(rel, RowIdentity("keyed", ("id",)))

    def test_allow_imperfect_key_downgrades_to_diagnostics(self, backend_name, backend_factory):
        rel = self._rel({"id": [1, 1, None], "v": [1, 2, 3]}, backend_name, backend_factory)
        diags = validate_keyed_identity(
            rel, RowIdentity("keyed", ("id",)), allow_imperfect_key=True
        )
        assert diags["null_key_rows"] == 1, f"[{backend_name}]"
        assert diags["duplicate_key_tuples"] == 1, f"[{backend_name}]"


def test_require_keyed_gates():
    require_keyed(RowIdentity("keyed", ("id",)), feature="pivot_key_fields")  # no raise
    with pytest.raises(IdentityRequiredError, match="pivot_key_fields"):
        require_keyed(RowIdentity("row_number"), feature="pivot_key_fields")
    with pytest.raises(IdentityRequiredError):
        require_keyed(RowIdentity("none"), feature="interpolate_messages")
