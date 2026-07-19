"""RelationOperationRegistry — the relations analog of ExpressionFunctionRegistry.

Every relation operation has one row keyed by its RKEY enum member, carrying
Substrait metadata, the protocol method it dispatches to, and a declarative
argument-binding spec (the relations analog of arguments-vs-options:
INPUT/INPUT_LIST fields are visited child relations, EXPRESSION/EXPRESSION_LIST
fields compile via the expression visitor, LITERAL fields pass through raw).

Registration-time validation (spec §3.5): a bad definition fails at first
registry init, not at dispatch.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class ArgKind(Enum):
    """How a bound node field is resolved into a positional argument."""

    INPUT = auto()            # child relation node -> visitor.visit(...)
    INPUT_LIST = auto()       # list of child nodes -> [visitor.visit(n) for n in ...]
    EXPRESSION = auto()       # expression field -> visitor.compile_expression(...)
    EXPRESSION_LIST = auto()  # list field -> compile each element
    LITERAL = auto()          # raw value, passed through


@dataclass(frozen=True)
class ArgBinding:
    field: str
    kind: ArgKind


@dataclass(frozen=True)
class RelationOperationDef:
    """One relation operation's registry row (spec §3.5)."""

    operation_key: Enum
    node_type: Optional[type] = None       # None only for non-node-dispatched ops
    substrait_rel: Optional[str] = None    # Substrait Rel message name; None = no direct 1:1 mapping
    lowers_to: Optional[str] = None        # Substrait Rel this op transforms into (no direct message)
    substrait_op: Optional[str] = None     # message-level variant, e.g. "SET_OP_UNION_DISTINCT"
    extension_uri: Optional[str] = None
    is_extension: bool = False
    protocol_method: Optional[Callable] = None
    args: tuple = ()                       # tuple[ArgBinding, ...] — ordered positional binding
    options: tuple = ()                    # node fields passed raw as kwargs
    options_field: Optional[str] = None    # dict field spread as **kwargs (ExtensionRelNode.options)
    handler: Optional[Callable] = None     # custom compile override: (node, visitor) -> Any

    def get_signature(self) -> Optional[inspect.Signature]:
        if self.protocol_method is None:
            return None
        return inspect.signature(self.protocol_method)


def classify_relation_def(d: "RelationOperationDef") -> str | None:
    """Return the serialization class of a def, or None if its metadata is invalid.

    Exactly one of three valid states (spec §5.4):
      - "direct":    substrait_rel set; lowers_to None; not an extension.
      - "lowered":   lowers_to set; substrait_rel None; not an extension.
      - "extension": both None; is_extension True with an extension_uri.
    """
    if d.is_extension:
        if d.substrait_rel is None and d.lowers_to is None and d.extension_uri is not None:
            return "extension"
        return None
    # non-extension: must carry no extension_uri, and exactly one of rel/lowers_to
    if d.extension_uri is not None:
        return None
    if d.substrait_rel is not None and d.lowers_to is None:
        return "direct"
    if d.substrait_rel is None and d.lowers_to is not None:
        return "lowered"
    return None


def _validate_def(d: RelationOperationDef) -> None:
    if d.protocol_method is None and d.handler is None:
        raise ValueError(
            f"{d.operation_key}: definition needs a protocol_method or handler"
        )
    if classify_relation_def(d) is None:
        raise ValueError(
            f"RelationOperationDef {d.operation_key} has invalid serialization "
            f"classification: substrait_rel={d.substrait_rel!r}, lowers_to={d.lowers_to!r}, "
            f"is_extension={d.is_extension!r}, extension_uri={d.extension_uri!r}. "
            f"Must be exactly one of direct / lowered / extension (spec §5.4)."
        )
    if d.node_type is None:
        return  # metadata-only row (EMPTY_FRAME) — nothing to bind
    model_fields = getattr(d.node_type, "model_fields", {})
    for b in d.args:
        if b.field not in model_fields:
            raise ValueError(
                f"{d.operation_key}: bound field {b.field!r} does not exist "
                f"on {d.node_type.__name__}"
            )
    for f_name in d.options:
        if f_name not in model_fields:
            raise ValueError(
                f"{d.operation_key}: option field {f_name!r} does not exist "
                f"on {d.node_type.__name__}"
            )
    if d.options_field is not None and d.options_field not in model_fields:
        raise ValueError(
            f"{d.operation_key}: options_field {d.options_field!r} does not "
            f"exist on {d.node_type.__name__}"
        )
    if d.handler is not None:
        return  # handler owns the calling convention
    sig = d.get_signature()
    assert sig is not None
    params = list(sig.parameters.values())[1:]  # drop self
    positional = [
        p for p in params
        if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if len(positional) != len(d.args):
        raise ValueError(
            f"{d.operation_key}: {len(d.args)} bound positional args but "
            f"{d.protocol_method.__name__} takes {len(positional)}"
        )
    kw_only = {p.name for p in params if p.kind is inspect.Parameter.KEYWORD_ONLY}
    unknown = set(d.options) - kw_only
    if unknown:
        raise ValueError(
            f"{d.operation_key}: options {sorted(unknown)} are not "
            f"keyword-only params of {d.protocol_method.__name__}"
        )


class RelationOperationRegistry:
    """Class-level singleton mirroring ExpressionFunctionRegistry."""

    _operations: Dict[Enum, RelationOperationDef] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, d: RelationOperationDef) -> None:
        if d.operation_key in cls._operations:
            raise ValueError(
                f"relation operation already registered for {d.operation_key}"
            )
        _validate_def(d)
        cls._operations[d.operation_key] = d

    @classmethod
    def get(cls, operation_key: Enum) -> RelationOperationDef:
        cls._init_registry()
        if operation_key not in cls._operations:
            raise KeyError(
                f"No relation operation registered for {operation_key}. "
                f"Available: {[k.name for k in cls._operations]}"
            )
        return cls._operations[operation_key]

    @classmethod
    def list_all(cls) -> List[Enum]:
        cls._init_registry()
        return list(cls._operations.keys())

    @classmethod
    def _init_registry(cls) -> None:
        if not cls._initialized:
            cls._initialized = True
            from .definitions import register_all_relation_operations
            register_all_relation_operations()

    @classmethod
    def reset(cls) -> None:
        """Test hook."""
        cls._operations.clear()
        cls._initialized = False
