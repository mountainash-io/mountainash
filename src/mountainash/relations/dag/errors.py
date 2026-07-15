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


class ResourceSchemaCastError(DAGError, ValueError):
    """Raised when applying a resource's declared schema dtypes to its inline
    data fails at read time.

    The inline-read path (`_read_inline`) casts null-inferred columns to the
    dtype declared in `resource.table_schema` (see item 53). Casting a
    `pl.Null` column succeeds for every dtype the type resolver produces today;
    this error surfaces the rare failure with the resource name and the
    offending `{column: dtype}` map, rather than a bare Polars error or a
    silent null-cast (`strict=False` is never used — Test Integrity).

    `ValueError` mixin matches the sibling data-level DAG errors
    (`UnsupportedResourceFormat`, `MissingResourceSchema`).
    """

    def __init__(self, resource: str, casts: dict) -> None:
        self.resource = resource
        self.casts = casts
        super().__init__(
            f"Failed to apply declared schema dtypes to inline resource "
            f"{resource!r}: casts={ {k: str(v) for k, v in casts.items()} }"
        )
