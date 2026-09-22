"""Cross-backend keyed-identity validation (spec §7).

``validate_keyed_identity`` reads key columns by name from a prepared
``ResolvedLogicalSnapshot`` (spec section 15, Task 7 step 5) -- it never
calls ``Relation.to_polars()`` -- so results are identical across every
backend with no per-backend xfails.
"""
import pytest

import mountainash as ma
from mountainash.relations.core.materialization import MaterializationScope
from mountainash.validation.errors import IdentityInvalidError
from mountainash.validation.identity import RowIdentity, validate_keyed_identity
from mountainash.validation.prepared import prepare_validation_input

from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestKeyedValidation:
    def _snapshot(self, data, backend_name, backend_factory):
        from mountainash.core.capabilities.policy import _new_execution_context
        frame = backend_factory.create(data, backend_name)
        execution_context = _new_execution_context(frame)
        rel = ma.relation(frame)
        with MaterializationScope() as scope:
            prepared = prepare_validation_input(
                rel, scope=scope, execution_context=execution_context,
            )
        return prepared.logical_snapshot

    def test_valid_key_returns_zero_diagnostics(self, backend_name, backend_factory):
        snapshot = self._snapshot({"id": [1, 2, 3], "v": [10, 20, 30]}, backend_name, backend_factory)
        diags = validate_keyed_identity(snapshot, RowIdentity("keyed", ("id",)))
        assert diags == {
            "null_key_rows": 0,
            "unknown_key_rows": 0,
            "duplicate_key_tuples": 0,
        }, f"[{backend_name}]"

    def test_missing_key_field_raises(self, backend_name, backend_factory):
        snapshot = self._snapshot({"v": [1]}, backend_name, backend_factory)
        with pytest.raises(IdentityInvalidError, match="missing"):
            validate_keyed_identity(snapshot, RowIdentity("keyed", ("id",)))

    def test_null_key_raises_by_default(self, backend_name, backend_factory):
        snapshot = self._snapshot({"id": [1, None, 3], "v": [1, 2, 3]}, backend_name, backend_factory)
        with pytest.raises(IdentityInvalidError):
            validate_keyed_identity(snapshot, RowIdentity("keyed", ("id",)))

    def test_duplicate_key_raises_by_default(self, backend_name, backend_factory):
        snapshot = self._snapshot({"id": [1, 1, 3], "v": [1, 2, 3]}, backend_name, backend_factory)
        with pytest.raises(IdentityInvalidError):
            validate_keyed_identity(snapshot, RowIdentity("keyed", ("id",)))

    def test_allow_imperfect_key_downgrades_to_diagnostics(self, backend_name, backend_factory):
        snapshot = self._snapshot({"id": [1, 1, None], "v": [1, 2, 3]}, backend_name, backend_factory)
        diags = validate_keyed_identity(
            snapshot, RowIdentity("keyed", ("id",)), allow_imperfect_key=True
        )
        assert diags["null_key_rows"] == 1, f"[{backend_name}]"
        assert diags["duplicate_key_tuples"] == 1, f"[{backend_name}]"
