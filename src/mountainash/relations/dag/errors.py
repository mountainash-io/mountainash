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


class MissingFilesDependency(DAGError, ImportError):
    """The mountainash-files chain is unavailable for a fallback resource read.

    Raised (never a bare ImportError) when reading a resource that needs the
    ``files`` extra — direct import miss OR a transitive dep failing at import
    or during ``parse()``. Subclasses ImportError so ``except ImportError`` and
    ``except DAGError`` both catch it (typed-error-hierarchy builtin-compat).
    """


class UnknownRelationRef(DAGError, KeyError):
    """Raised at compile time when a relation references an upstream name not
    registered in the DAG.

    The ``KeyError`` mixin is required, not decorative: ``execute()`` and the
    ref-resolver cache raised ``KeyError`` before this error existed, so
    existing ``except KeyError`` call sites must keep catching this failure.
    """

    # Render the full sentence message plainly. ``KeyError.__str__`` returns
    # ``repr(args[0])`` (spurious outer quotes around what is a sentence, not a
    # key here); the other DAGError leaves render cleanly via RuntimeError/
    # ValueError, so match them for consistent tracebacks and logs.
    __str__ = Exception.__str__
