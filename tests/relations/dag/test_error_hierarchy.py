"""DAG errors root under MountainashError via a DAGError base, preserving builtins."""
from __future__ import annotations

from mountainash.core.errors import MountainashError
from mountainash.relations.dag.errors import (
    DAGError,
    RelationDAGRequired,
    MissingResourceSchema,
    UnsupportedResourceFormat,
    UnknownRelationRef,
)


def test_dag_base_under_root():
    assert issubclass(DAGError, MountainashError)


def test_dag_base_reexported_from_subsystem():
    # Subsystem-level catch must be reachable: `from mountainash.relations.dag import DAGError`.
    from mountainash.relations.dag import DAGError as ReExported
    assert ReExported is DAGError


def test_all_dag_errors_under_dagerror():
    for cls in (RelationDAGRequired, MissingResourceSchema, UnsupportedResourceFormat, UnknownRelationRef):
        assert issubclass(cls, DAGError)
        assert issubclass(cls, MountainashError)


def test_builtin_compat_preserved():
    # Divergent builtins on the leaves — existing except sites keep working.
    assert issubclass(RelationDAGRequired, RuntimeError)
    assert issubclass(MissingResourceSchema, ValueError)
    assert issubclass(UnsupportedResourceFormat, ValueError)
    assert issubclass(UnknownRelationRef, KeyError)
