"""Mountainash relation DAG — orchestrator for named, interconnected Relations."""

# lazy_loader (not the eager pattern this package used previously): eagerly
# importing `.dag_relation` here creates a real circular import —
# `relation_base.py` does `from ...dag.errors import RelationDAGRequired`,
# which runs this __init__ first; `dag_relation.py` in turn imports
# `Relation` from the very module (`relation.py`) that is mid-import at that
# point. Deferring attribute resolution breaks the cycle: the `from
# mountainash.relations.dag.errors import ...` submodule import above
# doesn't touch `__getattr__` below, so `dag_relation` (and `dag`) are only
# imported on first attribute access, by which point `relation.py` has
# finished initialising.
import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submod_attrs={
        "dag": ["RelationDAG"],
        "dag_relation": ["DAGRelation"],
        "errors": [
            "DAGError",
            "MissingResourceSchema",
            "RelationDAGRequired",
            "UnknownRelationRef",
            "UnsupportedResourceFormat",
        ],
        "protocol": ["RelationDAGProtocol"],
        "resource_ref": ["ResourceRef"],
        "traversal": ["relation_children", "walk_refs"],
        "validation": ["DAGValidationResult"],
    },
)
