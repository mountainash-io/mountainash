"""Tests for the MountainashError root and its top-level export."""
from __future__ import annotations


def test_root_is_exception_subclass():
    from mountainash.core.errors import MountainashError
    assert issubclass(MountainashError, Exception)


def test_root_has_no_custom_init():
    # Bare marker: constructing it behaves exactly like Exception.
    from mountainash.core.errors import MountainashError
    err = MountainashError("boom")
    assert err.args == ("boom",)
    assert str(err) == "boom"


def test_root_exported_at_top_level():
    import mountainash as ma
    from mountainash.core.errors import MountainashError
    assert ma.MountainashError is MountainashError


def test_backend_capability_error_under_root():
    from mountainash.core.errors import MountainashError
    from mountainash.core.types import BackendCapabilityError
    assert issubclass(BackendCapabilityError, MountainashError)


def test_schema_validation_error_under_root():
    from mountainash.core.errors import MountainashError
    from mountainash.typespec.validation import SchemaValidationError
    assert issubclass(SchemaValidationError, MountainashError)
