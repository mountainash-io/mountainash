"""Dtype errors root under MountainashError; ValueError carried on the shared base."""
from __future__ import annotations

from mountainash.core.errors import MountainashError
from mountainash.core.dtypes.errors import (
    DtypeError,
    UnknownDtypeError,
    DtypeMappingError,
)


def test_base_carries_builtin_and_root():
    assert issubclass(DtypeError, MountainashError)
    assert issubclass(DtypeError, ValueError)


def test_base_reexported_from_subsystem():
    # Subsystem-level catch must be reachable: `from mountainash.core.dtypes import DtypeError`.
    from mountainash.core.dtypes import DtypeError as ReExported
    assert ReExported is DtypeError


def test_children_inherit_transitively():
    for cls in (UnknownDtypeError, DtypeMappingError):
        assert issubclass(cls, DtypeError)
        assert issubclass(cls, MountainashError)
        assert issubclass(cls, ValueError)  # backward-compat for existing except ValueError
