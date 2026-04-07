"""DAG-related exceptions."""


class RelationDAGRequired(RuntimeError):
    """Raised when a relation containing a RefRelNode is compiled outside a RelationDAG."""


class MissingResourceSchema(ValueError):
    """Raised when DAG.to_package() encounters a relation with no inferable schema."""


class UnsupportedResourceFormat(ValueError):
    """Raised when a resource's format/mediatype has no registered reader."""
