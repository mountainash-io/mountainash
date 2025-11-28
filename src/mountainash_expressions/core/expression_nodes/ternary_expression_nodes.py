"""Ternary logic expression nodes for three-valued logic operations.

Ternary logic uses three values:
- TRUE (1): Definitely true
- UNKNOWN (0): Cannot determine (typically NULL/missing)
- FALSE (-1): Definitely false

These nodes represent AST nodes for ternary operations that return
integer values (-1, 0, 1) instead of boolean values.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING, Iterable, Optional, Set, FrozenSet
from pydantic import Field

from .base_expression_node import ExpressionNode
from ..constants import (
    CONST_LOGIC_TYPES,
    ENUM_TERNARY_OPERATORS,
    TERNARY_TERMINAL_OPERATORS,
)

if TYPE_CHECKING:
    from ..expression_visitors.ternary_visitor import TernaryExpressionVisitor
    from ...types import SupportedExpressions


# Default UNKNOWN values - just NULL by default
DEFAULT_UNKNOWN_VALUES: FrozenSet[Any] = frozenset({None})


class TernaryExpressionNode(ExpressionNode):
    """
    Base class for ternary logic expression nodes.

    All ternary nodes return integer values (-1, 0, 1) representing
    FALSE, UNKNOWN, and TRUE respectively.
    """

    operator: ENUM_TERNARY_OPERATORS = Field()
    logic_type: CONST_LOGIC_TYPES = Field(default=CONST_LOGIC_TYPES.TERNARY)

    @property
    def is_terminal(self) -> bool:
        """Check if this node is a terminal ternary operator (produces boolean).

        Terminal operators convert ternary values (-1/0/1) to boolean (True/False).
        These are the booleanizers: IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN,
        MAYBE_TRUE, MAYBE_FALSE.

        Returns:
            True if this node produces boolean output, False if it produces
            ternary (-1/0/1) output.
        """
        return self.operator in TERNARY_TERMINAL_OPERATORS

    def accept(self, visitor: TernaryExpressionVisitor) -> SupportedExpressions:
        """Accept a ternary visitor and dispatch to appropriate method."""
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        """Evaluate this node against a DataFrame to get backend expression."""
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class TernaryColumnExpressionNode(TernaryExpressionNode):
    """
    Column reference with sentinel values for UNKNOWN detection.

    This node captures which values should be treated as UNKNOWN
    for this particular column.
    """

    column: str = Field()
    unknown_values: FrozenSet[Any] = Field(default=DEFAULT_UNKNOWN_VALUES)

    def __init__(
        self,
        operator: ENUM_TERNARY_OPERATORS,
        column: str,
        unknown_values: Optional[Set[Any]] = None,
    ):
        super().__init__(
            operator=operator,
            column=column,
            unknown_values=frozenset(unknown_values) if unknown_values else DEFAULT_UNKNOWN_VALUES,
        )


class TernaryComparisonExpressionNode(TernaryExpressionNode):
    """
    Comparison operation that returns ternary value (-1, 0, 1).

    Comparisons involving UNKNOWN values return UNKNOWN (0).
    """

    left: Any = Field()
    right: Any = Field()

    def __init__(
        self,
        operator: ENUM_TERNARY_OPERATORS,
        left: Any,
        right: Any,
    ):
        super().__init__(
            operator=operator,
            left=left,
            right=right,
        )


class TernaryIterableExpressionNode(TernaryExpressionNode):
    """
    N-ary ternary operations (AND, OR, XOR).

    These operations use min/max semantics:
    - AND = minimum of operands
    - OR = maximum of operands
    """

    operands: Iterable[Any] = Field()

    def __init__(
        self,
        operator: ENUM_TERNARY_OPERATORS,
        *operands: Any,
    ):
        super().__init__(
            operator=operator,
            operands=operands,
        )


class TernaryUnaryExpressionNode(TernaryExpressionNode):
    """
    Unary ternary operations (NOT, IS_TRUE, etc.).

    These include:
    - NOT: Sign flip (TRUE↔FALSE, UNKNOWN stays)
    - IS_TRUE, IS_FALSE, IS_UNKNOWN: Convert to boolean
    - MAYBE_TRUE, MAYBE_FALSE, IS_KNOWN: Convert to boolean
    - TO_TERNARY: Convert boolean to ternary
    """

    operand: Any = Field()

    def __init__(
        self,
        operator: ENUM_TERNARY_OPERATORS,
        operand: Any,
    ):
        super().__init__(
            operator=operator,
            operand=operand,
        )


class TernaryConstantExpressionNode(TernaryExpressionNode):
    """
    Constant ternary values (ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN).
    """

    def __init__(self, operator: ENUM_TERNARY_OPERATORS):
        super().__init__(operator=operator)


class TernaryCollectionExpressionNode(TernaryExpressionNode):
    """
    Collection-based ternary operations (IS_IN, IS_NOT_IN).

    Returns UNKNOWN (0) if the element is UNKNOWN.
    """

    operand: Any = Field()
    element: Any = Field()
    container: Any = Field()

    def __init__(
        self,
        operator: ENUM_TERNARY_OPERATORS,
        operand: Any,
        element: Any,
        container: Any,
    ):
        super().__init__(
            operator=operator,
            operand=operand,
            element=element,
            container=container,
        )


# Type alias for all supported ternary expression node types
SupportedTernaryExpressionNodeTypes = (
    TernaryComparisonExpressionNode
    | TernaryIterableExpressionNode
    | TernaryUnaryExpressionNode
    | TernaryConstantExpressionNode
    | TernaryCollectionExpressionNode
    | TernaryColumnExpressionNode
)
