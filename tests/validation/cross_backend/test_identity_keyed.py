"""Cross-backend keyed-identity validation (spec §7).

`validate_keyed_identity` is backend-agnostic (filter / group_by / count_rows);
it produces identical results on every backend, so these run across the full
matrix with no per-backend xfails.
"""
import pytest

import mountainash as ma
from mountainash.validation.errors import IdentityInvalidError
from mountainash.validation.identity import RowIdentity, validate_keyed_identity

from fixtures.backend_registry import ALL_BACKENDS


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
