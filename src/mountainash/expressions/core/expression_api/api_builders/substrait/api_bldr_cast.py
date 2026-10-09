"""Cast operations APIBuilder.

Substrait-aligned implementation using CastNode.
Implements CastBuilderProtocol for type casting operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_nodes import CastNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import SubstraitCastAPIBuilderProtocol, CaseFailureBehaviour


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class SubstraitCastAPIBuilder(BaseExpressionAPIBuilder, SubstraitCastAPIBuilderProtocol):
    """
    Cast operations APIBuilder (Substrait-aligned).

    Provides type casting operations.

    Methods:
        cast: Cast to a target data type
    """

    def cast(
        self,
        dtype: Union[str, type, Any],
        *,
        failure_behavior: Optional[CaseFailureBehaviour] = CaseFailureBehaviour.THROW,
        rounding: str = "TIE_TO_EVEN",
    ) -> BaseExpressionAPI:
        """
        Cast to the specified data type.

        Substrait: cast

        Args:
            dtype: The target data type. Can be:
                - A string type name (e.g., "i32", "i64", "f64", "string", "date")
                - A Python type (e.g., int, float, str)
                - A backend-specific type
            failure_behavior: How to handle cast failures:
                - "throw": Raise an error on invalid conversion (default)
                - "null": Return NULL on invalid conversion

        Returns:
            New ExpressionAPI with cast node.

        Examples:
            >>> col("price").cast("f64")  # Cast to float64
            >>> col("count").cast(int)    # Cast to integer
            >>> col("date_str").cast("date", failure_behavior="null")  # Safe cast
        """
        from mountainash.core.dtypes import parse_cast_target
        from mountainash.core.dtypes.spike_numeric import NumericDtype
        if isinstance(dtype, NumericDtype):
            from ..extensions_mountainash.api_bldr_ext_ma_spike_numeric import numeric_cast_node
            fb = failure_behavior.value if isinstance(failure_behavior, CaseFailureBehaviour) else failure_behavior
            return self._build(numeric_cast_node(self._node, dtype, rounding, fb))
        if rounding != "TIE_TO_EVEN":
            raise ValueError("spike rounding option requires a portable numeric target")

        target_type = parse_cast_target(dtype)

        # Convert enum to string value if needed
        fb = failure_behavior.value if isinstance(failure_behavior, CaseFailureBehaviour) else failure_behavior
        node = CastNode(
            input=self._node,
            target_type=target_type,
            failure_behavior=fb,
        )
        return self._build(node)
