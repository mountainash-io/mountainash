"""Disposable numeric extension: existing ScalarFunctionNode, not a new AST."""
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import MountainashExtension
from mountainash.expressions.core.expression_system.function_keys.spike_numeric import FKEY_MOUNTAINASH_SPIKE_NUMERIC as K
from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionDef, ExpressionFunctionRegistry
from mountainash.expressions.core.expression_system.function_mapping.output_rules import PROPAGATE_FIRST
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash.prtcl_expsys_ext_ma_spike_numeric import SpikeNumericProtocol


def numeric_cast_node(node, dtype, rounding="TIE_TO_EVEN", failure_behavior="throw", preserve=False):
    if rounding not in {"TIE_TO_EVEN", "TIE_AWAY_FROM_ZERO"}:
        raise ValueError("unsupported numeric rounding policy")
    if failure_behavior not in {"throw", "null"}:
        raise ValueError("failure_behavior must be throw or null")
    ExpressionFunctionRegistry.register(ExpressionFunctionDef(
        function_key=K.CAST,
        substrait_uri=MountainashExtension.VALUE,
        substrait_name="numeric_cast",
        is_extension=True,
        protocol_method=SpikeNumericProtocol.numeric_cast,
        options=("dtype", "rounding", "failure_behavior", "preserve"),
        projection_rule=PROPAGATE_FIRST,
    ))
    return ScalarFunctionNode(function_key=K.CAST, arguments=[node], options={
        "dtype": dtype, "rounding": rounding, "failure_behavior": failure_behavior, "preserve": preserve,
    })
