"""DAG-related exceptions.

`DAGError` is the subsystem base under `MountainashError`. The concrete errors
carry divergent builtins (RuntimeError vs ValueError), so each leaf mixes in its
own builtin — preserving every existing `except RuntimeError` / `except ValueError`.
"""
from __future__ import annotations

from mountainash.core.errors import MountainashError


class DAGError(MountainashError):
    """Base for all RelationDAG errors."""


class RelationDAGRequired(DAGError, RuntimeError):
    """Raised when a relation containing a RefRelNode is compiled outside a RelationDAG."""


class MissingResourceSchema(DAGError, ValueError):
    """Raised when DAG.to_package() encounters a relation with no inferable schema."""


class UnsupportedResourceFormat(DAGError, ValueError):
    """Raised when a resource's format/mediatype has no registered reader."""
