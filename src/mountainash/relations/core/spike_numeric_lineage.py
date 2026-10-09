"""Disposable scalar semantic map on the existing relation metadata channel."""
from mountainash.core.dtypes.spike_numeric import NumericDtype
from mountainash.expressions.core.expression_nodes import FieldReferenceNode, CastNode, ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
from mountainash.expressions.core.expression_system.function_keys.spike_numeric import FKEY_MOUNTAINASH_SPIKE_NUMERIC as K
from mountainash.expressions.core.output_names import resolve_output_names
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL as S, RKEY_MOUNTAINASH_REL as M


class LexicalNumericUseError(ValueError):
    pass


def lexical(dtype):
    return isinstance(dtype, NumericDtype) and dtype.kind.startswith("lexical_")


def expression_dtype(expr, incoming):
    from mountainash.relations.core.unified_visitor.relation_visitor import _expression_children
    expr = getattr(expr, "node", expr)
    if isinstance(expr, FieldReferenceNode):
        if expr.field == "*" or expr.field.startswith("^"):
            if any(lexical(dtype) for dtype in incoming.values()):
                raise LexicalNumericUseError("spike requires named projections for lexical numeric fields")
        return incoming.get(expr.field)
    children = [expression_dtype(child, incoming) for child in _expression_children(expr)]
    if isinstance(expr, CastNode):
        return expr.target_type
    if isinstance(expr, ScalarFunctionNode):
        if expr.function_key is K.CAST:
            return expr.options["dtype"]
        if expr.function_key is FKEY_MOUNTAINASH_NAME.ALIAS:
            return children[0]
    if any(lexical(dtype) for dtype in children):
        raise LexicalNumericUseError("lexical numeric operation requires an explicit numeric cast, or STRING cast for text semantics")
    return None


def propagate_numeric(node, child_maps):
    incoming = dict(child_maps[0]) if child_maps else {}
    key = node.operation_key
    if key is M.CONFORM:
        from mountainash.typespec import TypeSpec
        spec = TypeSpec.from_frictionless(node.spec) if isinstance(node.spec, dict) else node.spec
        declared = {field.name: field.dtype for field in spec.fields if field.dtype is not None}
        # The spike only claims exact/open conform with default coercion policy.
        if spec.fields_match == "open":
            for field in spec.fields:
                incoming.pop(field.source_name, None)
                incoming.pop(field.name, None)
            incoming.update(declared)
            return incoming
        return declared
    if key in {S.PROJECT_SELECT, S.PROJECT_WITH_COLUMNS}:
        output = dict(incoming) if key is S.PROJECT_WITH_COLUMNS else {}
        for expr in node.expressions:
            dtype = expression_dtype(expr, incoming)
            name = resolve_output_names(expr).scalar_name
            if name is None:
                if incoming:
                    raise LexicalNumericUseError("spike numeric lineage requires a named single-output projection")
                continue
            output.pop(name, None)
            if isinstance(dtype, NumericDtype):
                output[name] = dtype
        return output
    if key is S.PROJECT_RENAME:
        return {node.rename_mapping.get(name, name): dtype for name, dtype in incoming.items()}
    if key is S.PROJECT_DROP:
        names = {getattr(getattr(expr, "node", expr), "field", None) for expr in node.expressions}
        return {name: dtype for name, dtype in incoming.items() if name not in names}
    if key is S.SORT:
        for field in node.sort_fields:
            if lexical(incoming.get(field.column)):
                raise LexicalNumericUseError(f"sorting lexical numeric field {field.column!r} requires explicit conversion")
        return incoming
    if key is S.FILTER:
        dtype = expression_dtype(node.condition, incoming)
        if lexical(dtype):
            raise LexicalNumericUseError("lexical numeric filter requires explicit conversion")
        return incoming
    if key in {S.FETCH, M.FETCH_FROM_END, M.WITH_ROW_INDEX, M.SAMPLE}:
        return incoming
    if any(lexical(dtype) for values in child_maps for dtype in values.values()):
        raise LexicalNumericUseError(f"numeric spike has not classified relation operation {key}")
    return {}
