"""Mountainash's checked cast operation builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.dtypes import DecimalDtype, MountainashDtype, parse_cast_target
from mountainash.expressions.core.expression_nodes import CastNode, ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NAME,
    FKEY_MOUNTAINASH_SCALAR_VALUE,
)
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash.prtcl_api_bldr_ext_ma_cast import (
    CaseFailureBehaviour,
    MountainAshCastAPIBuilderProtocol,
    NumericRounding,
)
from ..api_builder_base import BaseExpressionAPIBuilder

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshCastAPIBuilder(BaseExpressionAPIBuilder, MountainAshCastAPIBuilderProtocol):
    """Construct checked Mountainash casts, retaining standard casts for other targets."""

    def cast(
        self,
        dtype: Any,
        failure_behavior: CaseFailureBehaviour | str = "throw",
        *,
        rounding: NumericRounding | str = "TIE_TO_EVEN",
    ) -> BaseExpressionAPI:
        target = parse_cast_target(dtype)
        if isinstance(failure_behavior, CaseFailureBehaviour):
            failure_behavior = failure_behavior.value
        if not isinstance(failure_behavior, str) or failure_behavior not in {"throw", "null"}:
            raise ValueError("failure_behavior must be 'throw' or 'null'")
        if isinstance(rounding, NumericRounding):
            rounding = rounding.value
        if not isinstance(rounding, str) or rounding not in {"TIE_TO_EVEN", "TIE_AWAY_FROM_ZERO"}:
            raise ValueError("rounding must be 'TIE_TO_EVEN' or 'TIE_AWAY_FROM_ZERO'")

        numeric_target = isinstance(target, DecimalDtype) or (
            isinstance(target, MountainashDtype)
            and target in (MountainashDtype.LEXICAL_INTEGER, MountainashDtype.LEXICAL_DECIMAL)
        )
        if numeric_target:
            wrappers = []
            argument = self._node
            naming_functions = {
                FKEY_MOUNTAINASH_NAME.ALIAS,
                FKEY_MOUNTAINASH_NAME.PREFIX,
                FKEY_MOUNTAINASH_NAME.SUFFIX,
                FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER,
                FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER,
            }
            while (
                isinstance(argument, ScalarFunctionNode)
                and argument.function_key in naming_functions
            ):
                wrappers.append(argument)
                argument = argument.arguments[0]
            node = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_VALUE.NUMERIC_CAST,
                arguments=[argument],
                options={"dtype": target, "rounding": rounding, "failure_behavior": failure_behavior},
            )
            for wrapper in reversed(wrappers):
                node = wrapper.model_copy(update={"arguments": [node]})
        else:
            if rounding != "TIE_TO_EVEN":
                raise ValueError("rounding is only supported for numeric casts")
            node = CastNode(input=self._node, target_type=target, failure_behavior=failure_behavior)
        return self._build(node)
