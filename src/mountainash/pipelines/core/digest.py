# src/mountainash/pipelines/core/digest.py
from __future__ import annotations
import hashlib
import json
from enum import Enum
from typing import Any
from mountainash.pipelines.errors import UnhashableIdentityInput

_NATIVE_FIELDS = {"dataframe", "data"}  # ReadRelNode / SourceRelNode payload fields


def structural_digest(template, target_name: str, bound: set[str]) -> str:
    """Non-executing digest of the target AST and transitive refs; bound source leaves become their binding name."""
    from pydantic import BaseModel
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
    from mountainash.relations.core.relation_nodes.reln_base import RelationNode

    def enc(o: Any) -> Any:
        if isinstance(o, RefRelNode):
            if o.name in bound:
                return {"$bound": o.name}
            if o.name not in template.relations:
                return {"$unbound_ref": o.name}
            return {"$ref": o.name, "node": enc(template.relations[o.name]._node)}
        if isinstance(o, RelationNode):
            out: dict[str, Any] = {"$kind": type(o).__name__}
            for f in type(o).model_fields:  # concrete class fields, not the base annotation
                v = getattr(o, f)
                if f in _NATIVE_FIELDS and v is not None and not isinstance(v, (str, int, float, bool, list, dict)):
                    raise UnhashableIdentityInput(
                        f"unbound native leaf {type(o).__name__}.{f} in template; bind it via inputs"
                    )
                out[f] = enc(v)
            return out
        if isinstance(o, BaseModel):
            return {"$m": type(o).__name__, **{f: enc(getattr(o, f)) for f in type(o).model_fields}}
        if hasattr(o, "_node") and not isinstance(
            o, (str, bytes)
        ):  # expression API wrappers (BooleanExpressionAPI etc.) carry their AST in _node (F4)
            return {"$expr": type(o).__name__, "node": enc(o._node)}
        if isinstance(o, (list, tuple)):
            return [enc(x) for x in o]
        if isinstance(o, dict):
            return {str(k): enc(v) for k, v in o.items()}
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, (str, int, float, bool)) or o is None:
            return o
        raise UnhashableIdentityInput(f"non-structural value in AST: {type(o).__name__}")

    payload = json.dumps(enc(template.relations[target_name]._node), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]
