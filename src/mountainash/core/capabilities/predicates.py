"""Predicate engine for compound capability facts (spec 2026-07-28, backlog 66b).

Bound-call interface and conservative, witnessed domain comparison.
Deliberately import-free of the expression visitor at module level: the lazy
import in bind_expression_call mirrors registry._definition_for and avoids a
core -> expressions import cycle.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, TYPE_CHECKING, cast

from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate, _operand_key

if TYPE_CHECKING:
    from mountainash.core.capabilities.schema import ValueClass
    from mountainash.core.dtypes.metadata import OperandType

OPERAND_TYPES_ROOT = "__operand_types__"


@dataclass(frozen=True)
class BoundCall:
    """A bound operation call (§5). Not hashable (bindings is a Mapping)."""

    operation_key: Any
    backend: Any  # CONST_BACKEND
    dialect: str | None
    bindings: Mapping[str, Any]  # param name -> bound value or AST node
    supplied: frozenset[str]  # params the caller actually passed
    operand_types: Mapping[str, OperandType] | None = None

    def __post_init__(self) -> None:
        if OPERAND_TYPES_ROOT in self.bindings or OPERAND_TYPES_ROOT in self.supplied:
            raise ValueError(f"{OPERAND_TYPES_ROOT} is reserved compiler metadata")


def _unwrap_literal(value: Any) -> Any:
    from mountainash.expressions.core.expression_nodes import LiteralNode

    return value.value if isinstance(value, LiteralNode) else value


def bind_expression_call(*, operation_key, backend, dialect, protocol_method, arguments, options) -> BoundCall:
    from mountainash.expressions.core.unified_visitor.visitor import (
        _param_name_for,
        _protocol_sig_params,
    )

    sig_params = _protocol_sig_params(protocol_method)
    var_positional_name = next((p.name for p in sig_params if p.kind is inspect.Parameter.VAR_POSITIONAL), None)
    bindings: dict[str, Any] = {}
    supplied: set[str] = set()
    for i, arg in enumerate(arguments):
        name = _param_name_for(sig_params, i)
        if name is None:
            continue
        supplied.add(name)
        if name == var_positional_name:
            bindings.setdefault(name, [])
            bindings[name].append(arg)
        else:
            bindings[name] = arg
    for option_name, option_value in (options or {}).items():
        bindings[option_name] = option_value
        supplied.add(option_name)
    # Defaults are applied to bindings (§5) but stay out of supplied.
    for p in sig_params:
        if p.name not in supplied and p.default is not inspect.Parameter.empty:
            bindings[p.name] = p.default
    if var_positional_name is not None and isinstance(bindings.get(var_positional_name), list):
        bindings[var_positional_name] = tuple(bindings[var_positional_name])
    return BoundCall(
        operation_key=operation_key,
        backend=backend,
        dialect=dialect,
        bindings=bindings,
        supplied=frozenset(supplied),
    )


def _declared_fields(value: Any) -> set[str] | None:
    if hasattr(value, "model_fields"):  # Pydantic v2
        return set(value.model_fields)
    if hasattr(value, "__fields__"):  # Pydantic v1
        return set(value.__fields__)
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name for f in fields(value)}
    return None


def _resolve_segment(value: Any, seg: str, path: str) -> Any:
    if isinstance(value, Mapping):
        if seg in value:
            return value[seg]
        raise ValueError(f"predicate path {path!r}: mapping has no key {seg!r}")
    if isinstance(value, Enum):
        if seg in ("name", "value"):
            return getattr(value, seg)
        raise ValueError(f"predicate path {path!r}: enum {type(value).__name__} has no attribute {seg!r}")
    declared = _declared_fields(value)
    if declared is not None:
        if seg not in declared:
            raise ValueError(f"predicate path {path!r}: {type(value).__name__} has no declared field {seg!r}")
        return getattr(value, seg)  # declared field only: no user code runs
    raise ValueError(
        f"predicate path {path!r}: cannot traverse {seg!r} through "
        f"{type(value).__name__} (not a mapping, enum, or declared model)"
    )


def resolve_path(
    bindings: Mapping[str, Any], path: str, *, operand_types: Mapping[str, OperandType] | None = None
) -> Any:
    segments = path.split(".")
    head = segments[0]
    if head == OPERAND_TYPES_ROOT:
        from mountainash.core.dtypes.metadata import OperandType

        operand, field = _metadata_path(path)
        if operand_types is None or operand not in operand_types:
            raise ValueError(f"predicate path {path!r}: operand metadata is unresolved")
        descriptor = operand_types[operand]
        if type(descriptor) is not OperandType:
            raise ValueError(f"predicate path {path!r}: expected OperandType")
        return getattr(descriptor, field)
    if head not in bindings:
        raise ValueError(f"predicate path {path!r}: parameter {head!r} is not bound")
    value = _unwrap_literal(bindings[head])  # unwrap LiteralNode at the root
    for seg in segments[1:]:
        if value is None:
            raise ValueError(f"predicate path {path!r}: cannot traverse {seg!r} through None")
        value = _resolve_segment(value, seg, path)
    return value


def evaluate_clause(
    clause: Clause,
    bindings: Mapping[str, Any],
    supplied: frozenset[str],
    *,
    operand_types: Mapping[str, OperandType] | None = None,
) -> bool:
    from mountainash.expressions.core.expression_nodes import ExpressionNode, LiteralNode

    root = clause.path.split(".")[0]
    if clause.op is ClauseOp.IS_LITERAL:
        return isinstance(bindings.get(root), LiteralNode)
    value = resolve_path(bindings, clause.path, operand_types=operand_types)
    if clause.op is ClauseOp.IS_NULL:
        return value is None
    if clause.op is ClauseOp.IS_SET:
        return value is not None
    # A dynamic (non-literal) expression makes value-comparing clauses False (§4.4).
    if isinstance(value, ExpressionNode):
        return False
    if clause.op is ClauseOp.MATCHES_CLASS:
        from mountainash.core.capabilities.value_classes import matches

        return isinstance(value, str) and matches(clause.operand, value)
    if clause.op is ClauseOp.EQ:
        return value == clause.operand
    if clause.op is ClauseOp.IN:
        return value in clause.operand
    raise ValueError(f"unknown ClauseOp {clause.op!r}")


def predicate_holds(
    predicate: Predicate,
    bindings: Mapping[str, Any],
    supplied: frozenset[str],
    *,
    operand_types: Mapping[str, OperandType] | None = None,
) -> bool:
    # Validate every referenced descriptor before a false raw clause can short-circuit.
    for clause in predicate.clauses:
        if clause.path.split(".")[0] == OPERAND_TYPES_ROOT:
            resolve_path(bindings, clause.path, operand_types=operand_types)
    return all(evaluate_clause(c, bindings, supplied, operand_types=operand_types) for c in predicate.clauses)


def _metadata_path(path: str) -> tuple[str, str]:
    parts = path.split(".")
    if (
        len(parts) != 3
        or parts[0] != OPERAND_TYPES_ROOT
        or not parts[1]
        or parts[2] not in ("logical_kind", "storage_kind", "nullable")
    ):
        raise ValueError(f"invalid operand metadata predicate path {path!r}")
    return parts[1], parts[2]


def metadata_arguments(predicate: Predicate) -> frozenset[str]:
    return frozenset(_metadata_path(c.path)[0] for c in predicate.clauses if c.path.split(".")[0] == OPERAND_TYPES_ROOT)


def validate_metadata_predicate(predicate: Predicate, protocol_method: Any) -> None:
    from mountainash.core.dtypes.metadata import LOGICAL_KINDS, STORAGE_KINDS

    parameters = inspect.signature(protocol_method).parameters if protocol_method else {}
    for clause in predicate.clauses:
        if clause.path.split(".")[0] != OPERAND_TYPES_ROOT:
            continue
        operand, field = _metadata_path(clause.path)
        parameter = parameters.get(operand)
        if parameter is None or "ExpressionT" not in str(parameter.annotation):
            raise ValueError(f"metadata operand {operand!r} is not an expression parameter")
        if clause.op in (ClauseOp.IS_NULL, ClauseOp.IS_SET):
            continue
        if clause.op not in (ClauseOp.EQ, ClauseOp.IN):
            raise ValueError(f"unsupported metadata selector {clause.op}")
        values = cast("frozenset[str | int]", clause.operand) if clause.op is ClauseOp.IN else (clause.operand,)
        for value in values:
            value_type = type(value)
            if field == "nullable":
                valid = value is None or value_type is bool
            else:
                choices = LOGICAL_KINDS if field == "logical_kind" else STORAGE_KINDS
                valid = value_type is str and value in choices
            if not valid:
                raise ValueError(f"invalid metadata selector {clause.path!r}: {value!r}")


class DomainRelation(Enum):
    """How confidently two predicate domains relate."""

    DISJOINT = "disjoint"
    OVERLAP = "overlap"
    NOT_PROVEN = "not_proven"


@dataclass(frozen=True)
class DomainComparison:
    """Immutable result of comparing two predicate applicability domains."""

    relation: DomainRelation
    witness: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if type(self.relation) is not DomainRelation:
            raise TypeError("domain comparison requires a DomainRelation")
        if self.witness is not None:
            if not isinstance(self.witness, Mapping):
                raise TypeError("domain comparison witness requires a mapping or None")
            object.__setattr__(self, "witness", MappingProxyType(dict(self.witness)))


_DISJOINT = DomainComparison(DomainRelation.DISJOINT)
_NOT_PROVEN = DomainComparison(DomainRelation.NOT_PROVEN)
_UNKNOWN = object()


def _is_raw_path(path: str) -> bool:
    return "." not in path and path != OPERAND_TYPES_ROOT


def _value_satisfies(clause: Clause, value: Any) -> bool:
    if clause.op is ClauseOp.IS_NULL:
        return value is None
    if clause.op is ClauseOp.IS_SET:
        return value is not None
    if clause.op is ClauseOp.EQ:
        return value == clause.operand
    if clause.op is ClauseOp.IN:
        return value in clause.operand
    if clause.op is ClauseOp.MATCHES_CLASS:
        from mountainash.core.capabilities.value_classes import matches

        return isinstance(value, str) and matches(clause.operand, value)
    raise ValueError(f"unsupported value-domain clause {clause.op!r}")


def _path_witness(clauses: tuple[Clause, ...]) -> Any:
    """Return a concrete satisfying value, or `_UNKNOWN`/`_DISJOINT`."""
    if any(c.op is ClauseOp.IS_NULL for c in clauses):
        return None if all(_value_satisfies(c, None) for c in clauses) else _DISJOINT

    finite = tuple(c for c in clauses if c.op in (ClauseOp.EQ, ClauseOp.IN))
    if finite:
        first = finite[0]
        candidates = (
            (first.operand,)
            if first.op is ClauseOp.EQ
            else tuple(sorted(cast("frozenset[str | int]", first.operand), key=_operand_key))
        )
        for candidate in candidates:
            if all(_value_satisfies(clause, candidate) for clause in clauses):
                return candidate
        return _DISJOINT

    classes = tuple(cast("ValueClass", c.operand) for c in clauses if c.op is ClauseOp.MATCHES_CLASS)
    if classes:
        from mountainash.core.capabilities.value_classes import REPRESENTATIVE_SLICES

        for value_class in classes:
            for candidate in REPRESENTATIVE_SLICES[value_class]:
                if all(_value_satisfies(clause, candidate) for clause in clauses):
                    return candidate
        return _UNKNOWN

    # The only remaining constraint is IS_SET, which accepts any non-null scalar.
    return ""


def _comparison_clauses(
    left: Predicate | None,
    right: Predicate | None,
) -> tuple[dict[str, list[Clause]], set[str], bool]:
    paths: dict[str, list[Clause]] = {}
    literal_roots: set[str] = set()
    uncertain = False
    for predicate in (left, right):
        if predicate is None:
            continue
        for clause in predicate.clauses:
            root = clause.path.split(".", 1)[0]
            if clause.op is ClauseOp.IS_LITERAL:
                literal_roots.add(root)
                uncertain |= root == OPERAND_TYPES_ROOT
                continue
            paths.setdefault(clause.path, []).append(clause)
            uncertain |= not _is_raw_path(clause.path)
    return paths, literal_roots, uncertain


def compare_domains(
    left: Predicate | None,
    right: Predicate | None,
) -> DomainComparison:
    """Compare conjunctions without assuming relations absent from the DSL.

    A contradiction on a resolved path proves `DISJOINT`.  `OVERLAP` requires
    a concrete binding witness, so nested and operand-metadata selectors remain
    `NOT_PROVEN` unless a same-path contradiction has already decided the
    comparison.
    """
    paths, literal_roots, uncertain = _comparison_clauses(left, right)
    bindings: dict[str, Any] = {}
    unknown = uncertain
    for path, clauses in paths.items():
        value = _path_witness(tuple(clauses))
        if value is _DISJOINT:
            return _DISJOINT
        if value is _UNKNOWN:
            unknown = True
            continue
        if _is_raw_path(path):
            bindings[path] = value
    if unknown:
        return _NOT_PROVEN

    if literal_roots:
        from mountainash.expressions.core.expression_nodes import LiteralNode

        for root in literal_roots:
            bindings[root] = LiteralNode(value=bindings.get(root))
    supplied = frozenset(bindings)
    if left is not None and not predicate_holds(left, bindings, supplied):
        return _NOT_PROVEN
    if right is not None and not predicate_holds(right, bindings, supplied):
        return _NOT_PROVEN
    return DomainComparison(DomainRelation.OVERLAP, bindings)
