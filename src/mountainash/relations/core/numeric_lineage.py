"""Execution-scoped numeric identity through existing relation operations."""
from __future__ import annotations

from types import MappingProxyType

from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes.errors import LexicalNumericUseError
from mountainash.expressions.core.expression_nodes import FieldReferenceNode
from mountainash.expressions.core.output_names import resolve_output_names
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL as RM,
    RKEY_SUBSTRAIT_REL as RS,
)
from mountainash.relations.core.structured_lineage import (
    _expression_node, _join_name_maps, _named_values, _relation_output_names,
)


def has_lexical(shape):
    return shape is not None and (
        shape.canonical_type in {D.LEXICAL_INTEGER, D.LEXICAL_DECIMAL}
        or has_lexical(shape.item_shape)
        or any(has_lexical(child) for _, child in shape.struct_fields)
    )


def project_numeric_types(expressions, incoming, context, input_names, *, keep=False):
    """Use the expression visitor's semantic resolver and shared naming rules."""
    result = dict(incoming) if keep else {}
    names = None
    for expression in expressions:
        node = _expression_node(expression)
        if isinstance(node, str):
            node = FieldReferenceNode(field=node)
        if not incoming and context.semantic_shape(node) is None:
            continue
        output = resolve_output_names(node)
        if output.kind == "expansion":
            if names is None:
                names = tuple(input_names() if callable(input_names) else input_names)
            output = resolve_output_names(node, input_names=names)
        if output.names is None or any(name is None for name in output.names):
            if any(has_lexical(shape) for shape in incoming.values()):
                raise LexicalNumericUseError("Cannot prove numeric identity through an opaque projection")
            result.clear()
            continue
        for index, name in enumerate(output.names):
            shape = context.semantic_shape(node, input_names=names, output_index=index)
            result.pop(name, None)
            if shape is not None:
                result[name] = shape
    return MappingProxyType(result)


def propagate_numeric_types(node, child_maps, context, *, output_names_resolver=None):
    """Derive one output map, rejecting unproven lexical consumers before dispatch."""
    incoming = child_maps[0] if child_maps else {}
    key = node.operation_key
    if key in {RS.READ, RM.SOURCE, RM.READ_RESOURCE, RM.EMPTY_FRAME, RM.REF, RM.CONFORM}:
        return MappingProxyType({})
    if key in {RS.PROJECT_SELECT, RS.PROJECT_WITH_COLUMNS, RS.AGGREGATE}:
        if key is RS.AGGREGATE:
            from mountainash.relations.core.aggregate_names import normalize_aggregate
            keys, measures = normalize_aggregate(node.keys, node.measures)
            expressions = [*keys, *measures]
        else:
            expressions = node.expressions
        return project_numeric_types(
            expressions, incoming, context,
            lambda: _relation_output_names(node.input, output_names_resolver),
            keep=key is RS.PROJECT_WITH_COLUMNS,
        )
    if not any(child_maps):
        if key is RS.FILTER and context is not None:
            if has_lexical(context.semantic_shape(_expression_node(node.predicate))):
                raise LexicalNumericUseError("A lexical numeric value is not a boolean predicate")
        return MappingProxyType({})
    if key is RS.PROJECT_RENAME:
        renames = node.rename_mapping or {}
        return MappingProxyType({renames.get(name, name): shape for name, shape in incoming.items()})
    if key is RS.PROJECT_DROP:
        dropped = _named_values(node.expressions)
        return MappingProxyType({name: shape for name, shape in incoming.items() if name not in dropped})
    if key in {RS.JOIN, RM.JOIN_ASOF}:
        left, right = child_maps
        left_keys = node.on or node.left_on or ()
        right_keys = node.on or node.right_on or ()
        for left_key, right_key in zip(left_keys, right_keys):
            lshape, rshape = left.get(left_key), right.get(right_key)
            if has_lexical(lshape) or has_lexical(rshape):
                if key is RM.JOIN_ASOF or lshape != rshape:
                    raise LexicalNumericUseError("Join keys require compatible validated numeric domains or explicit conversion")
        for name in getattr(node, "by", ()) or ():
            if (has_lexical(left.get(name)) or has_lexical(right.get(name))) and left.get(name) != right.get(name):
                raise LexicalNumericUseError("Join grouping keys have incompatible numeric domains")
        maps = _join_name_maps(node, child_maps, output_names_resolver=output_names_resolver)
        return MappingProxyType({
            final: child[name] for child, names in zip(child_maps, maps) for name, final in names.items()
        })
    if key in {RS.UNION_ALL, RS.UNION_DISTINCT}:
        names = set().union(*(child.keys() for child in child_maps))
        result = {}
        for name in names:
            shapes = [child.get(name) for child in child_maps]
            if any(has_lexical(shape) for shape in shapes) and any(shape != shapes[0] for shape in shapes[1:]):
                raise LexicalNumericUseError("Union requires compatible validated numeric domains or explicit conversion")
            if all(shape == shapes[0] for shape in shapes[1:]) and shapes[0] is not None:
                result[name] = shapes[0]
        return MappingProxyType(result)
    if key in {RS.SORT, RM.TOP_K}:
        for name in _named_values(vars(node)):
            if has_lexical(incoming.get(name)):
                raise LexicalNumericUseError("Numeric ordering of lexical values requires explicit numeric conversion")
        return MappingProxyType(dict(incoming))
    if key is RS.FILTER:
        predicate = _expression_node(node.predicate)
        if has_lexical(context.semantic_shape(predicate)):
            raise LexicalNumericUseError("A lexical numeric value is not a boolean predicate")
        return MappingProxyType(dict(incoming))
    if key in {RS.FETCH, RS.DISTINCT, RM.DROP_NULLS, RM.SAMPLE, RM.FETCH_FROM_END}:
        return MappingProxyType(dict(incoming))
    if key is RM.WITH_ROW_INDEX:
        result = dict(incoming)
        result.pop((getattr(node, "options", {}) or {}).get("name", "index"), None)
        return MappingProxyType(result)
    if key in {RM.UNNEST, RM.EXPLODE}:
        selected = _named_values(getattr(node, "options", {}))
        result = dict(incoming)
        for name in selected:
            shape = result.get(name)
            if shape is None:
                continue
            if key is RM.UNNEST and shape.struct_fields:
                result.pop(name)
                result.update((child_name, child) for child_name, child in shape.struct_fields)
            elif key is RM.EXPLODE and shape.item_shape is not None:
                result[name] = shape.item_shape
            elif has_lexical(shape):
                raise LexicalNumericUseError("This container operation needs explicit numeric conversion")
        return MappingProxyType(result)
    if any(has_lexical(shape) for child in child_maps for shape in child.values()):
        raise LexicalNumericUseError(f"Numeric identity is not established for {key}")
    return MappingProxyType({})
