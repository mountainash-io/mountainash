"""AST-known gates shared by placement preflight and relation dispatch."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry, Enforcement, WILDCARD_PARAM
from mountainash.core.capabilities.predicates import BoundCall, bind_expression_call
from mountainash.core.capabilities.schema import PolicyConsumer
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import ExpressionNode, IfThenNode, LiteralNode, ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL
from mountainash.relations.core.relation_system.relation_mapping.registry import (
    ArgKind, RelationOperationRegistry,
)

if TYPE_CHECKING:
    from mountainash.relations.core.execution.location import ExecutionLocation
    from mountainash.relations.core.execution.preparation import PreparedExecution


def _raise(fact: Any, key: Any, family: Any, *, candidates: tuple = ()) -> None:
    raise BackendCapabilityError(
        fact.message if not candidates else "; ".join(f.message for f in candidates),
        backend=family.value, function_key=key, limitation=fact,
        **({"candidate_fact_keys": tuple(f.fact_key for f in candidates)} if candidates else {}),
    )


def _check_expression(node: ExpressionNode, location: ExecutionLocation, context: Any) -> None:
    family, dialect = location.family, location.dialect
    key = (FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE
           if isinstance(node, IfThenNode) and node.conditions else node.function_key)
    if key is not None:
        fact = CapabilityRegistry.capability_for(
            key, WILDCARD_PARAM, family, dialect, execution_context=context,
        )
        if fact is not None and fact.predicate is None and fact.enforcement is Enforcement.GATE \
                and fact.level is CapabilityLevel.UNSUPPORTED:
            _raise(fact, key, family)
    if isinstance(node, IfThenNode) and node.conditions:
        protocol = ExpressionFunctionRegistry.get(key).protocol_method
        # A chained conditional lowers to one if_then_else call per branch.
        logical_else = node.else_clause
        for condition, branch in reversed(node.conditions):
            bound = bind_expression_call(
                operation_key=key, backend=family, dialect=dialect,
                protocol_method=protocol, arguments=(condition, branch, logical_else), options=None,
            )
            violations = CapabilityRegistry.violations_for(
                bound, phase="raw", execution_context=context,
            )
            if violations:
                ordered = tuple(sorted(violations, key=lambda f: (f.param, f.message)))
                _raise(ordered[0], key, family, candidates=ordered)
            logical_else = IfThenNode(conditions=[(condition, branch)], else_clause=logical_else)
    if isinstance(node, ScalarFunctionNode):
        definition = ExpressionFunctionRegistry.get(key)
        protocol = definition.protocol_method
        if protocol is not None:
            bound = bind_expression_call(
                operation_key=key, backend=family, dialect=dialect,
                protocol_method=protocol, arguments=node.arguments, options=node.options,
            )
            violations = CapabilityRegistry.violations_for(
                bound, phase="raw", execution_context=context,
            )
            if violations:
                ordered = tuple(sorted(violations, key=lambda f: (f.param, f.message)))
                _raise(ordered[0], key, family, candidates=ordered)
            from mountainash.expressions.core.unified_visitor.visitor import _param_name_for, _protocol_sig_params

            parameters = _protocol_sig_params(protocol)
            for index, arg in enumerate(node.arguments):
                name = _param_name_for(parameters, index)
                if name is None:
                    continue
                fact = CapabilityRegistry.capability_for(
                    key, name, family, dialect, execution_context=context,
                )
                if fact is not None and fact.predicate is None and fact.enforcement is Enforcement.GATE \
                        and (fact.level is CapabilityLevel.UNSUPPORTED or (
                            fact.level is CapabilityLevel.LITERAL_ONLY
                            and isinstance(arg, ExpressionNode) and not isinstance(arg, LiteralNode)
                        )):
                    _raise(fact, key, family)
        for name, value in (node.options or {}).items():
            fact = CapabilityRegistry.capability_for(
                key, name, family, dialect,
                option_value=str(value.value if isinstance(value, Enum) else value),
                execution_context=context,
            )
            if fact is not None and fact.predicate is None and fact.enforcement is Enforcement.GATE \
                    and fact.level is CapabilityLevel.UNSUPPORTED:
                _raise(fact, key, family)
    from mountainash.relations.core.unified_visitor.relation_visitor import _expression_children

    for child in _expression_children(node):
        _check_expression(child, location, context)


def check_ast_capabilities(
    node: Any, location: ExecutionLocation, *, execution_context: Any = None,
) -> None:
    """Check only selected, definitely applicable gates visible without native values."""
    if location.family is None or location.dialect is None:
        return
    if execution_context is not None and not execution_context.policy.has_demand(PolicyConsumer.GATE):
        return
    if isinstance(node, ExpressionNode):
        _check_expression(node, location, execution_context)
        return
    key = node.operation_key
    if key is None:
        return
    op = RelationOperationRegistry.get(key)
    family, dialect = location.family, location.dialect
    fact = CapabilityRegistry.capability_for(
        key, WILDCARD_PARAM, family, dialect, execution_context=execution_context,
    )
    if fact is not None and fact.predicate is None and fact.enforcement is Enforcement.GATE \
            and fact.level is CapabilityLevel.UNSUPPORTED:
        _raise(fact, key, family)
    names = tuple(b.field for b in op.args) + tuple(op.options) + op.gate_params
    bindings = {name: getattr(node, name, None) for name in names}
    bound = BoundCall(key, family, dialect, bindings,
                      frozenset(name for name, value in bindings.items() if value is not None))
    violations = CapabilityRegistry.violations_for(
        bound, phase="raw", execution_context=execution_context,
    )
    if violations:
        ordered = tuple(sorted(violations, key=lambda f: (f.param, f.message)))
        _raise(ordered[0], key, family, candidates=ordered)
    for name in names:
        fact = CapabilityRegistry.capability_for(
            key, name, family, dialect, execution_context=execution_context,
        )
        if fact is not None and fact.predicate is None and fact.enforcement is Enforcement.GATE \
                and fact.level is CapabilityLevel.UNSUPPORTED and bindings[name] is not None:
            _raise(fact, key, family)


def preflight_capabilities(prepared: PreparedExecution) -> None:
    """Check all occurrences before any consumer may compile or export a sibling."""
    for key, node in prepared.nodes.items():
        location = prepared.locations[key]
        context = prepared.context_for(location)
        check_ast_capabilities(node, location, execution_context=context)
        if node.operation_key is None:
            continue
        op = RelationOperationRegistry.get(node.operation_key)
        # An operation compiles its own expressions on its selected output
        # system. Earlier source operations retain their own occurrence scope.
        scope = location
        for binding in op.args:
            if binding.kind not in (ArgKind.EXPRESSION, ArgKind.EXPRESSION_LIST):
                continue
            value = getattr(node, binding.field, None)
            values = value if isinstance(value, (tuple, list)) else (value,)
            for item in values:
                expr = item._node if hasattr(item, "_node") else item
                if isinstance(expr, ExpressionNode):
                    check_ast_capabilities(expr, scope, execution_context=prepared.context_for(scope))
