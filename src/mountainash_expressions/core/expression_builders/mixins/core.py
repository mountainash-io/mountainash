

from __future__ import annotations
from typing import Any, List, Union, TYPE_CHECKING

from mountainash_expressions.core.expression_builders.base_expression_builder import ExpressionBuilder

from ..base_expression_builder import ExpressionBuilder
if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode


from ...protocols import (
    ColumnBuilderProtocol,
    LiteralBuilderProtocol,
    NativeBuilderProtocol,
    ConditionalBuilderProtocol,
    NullConstantBuilderProtocol
)

class CoreExpressionBuilder(ExpressionBuilder,
                            ColumnBuilderProtocol,
                            LiteralBuilderProtocol):


    def col(self,  **kwargs) -> ExpressionBuilder: ...

    def lit(self) -> ExpressionBuilder: ...

    # def native(self) -> ExpressionBuilder: ...


    # def when( self, condition: SupportedExpressions, consequence: SupportedExpressions, alternative: SupportedExpressions ) -> Any: ...
    # def null_if(self, operand: SupportedExpressions, expr: SupportedExpressions) -> SupportedExpressions: ...
    # def if_(self, condition: ExpressionNode, consequence: ExpressionNode, alternative: ExpressionNode) -> SupportedExpressions: ...



    # def always_null(self) -> ExpressionBuilder: ...




def col(name: str) -> ExpressionBuilder:
    """
    Create a column reference expression.

    This is the primary entry point for building expressions.

    Args:
        name: Column name
        logic_type: Logic system to use (BOOLEAN or TERNARY)

    Returns:
        ExpressionBuilder for chaining operations

    Example:
        >>> expr = col("age").gt(30)
        >>> expr = col("name").eq("Alice")
    """
    # For columns, we can just store the string directly
    # The visitor's _process_operand() will handle converting it
    node = ColumnExpressionNode(ENUM_COLUMN_OPERATORS.LIT, value)
    return ExpressionBuilder(name)


def lit(value: Any) -> ExpressionBuilder:
    """
    Create a literal value expression.

    Args:
        value: Literal value (int, float, str, bool, etc.)
        logic_type: Logic system to use (BOOLEAN or TERNARY)

    Returns:
        ExpressionBuilder for chaining operations

    Example:
        >>> expr = lit(42)
        >>> expr = lit("hello")
    """
    # Create a proper LiteralExpressionNode
    node = LiteralExpressionNode(ENUM_LITERAL_OPERATORS.LIT, value)
    return ExpressionBuilder(node)
