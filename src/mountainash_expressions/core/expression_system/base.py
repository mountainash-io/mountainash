"""Base ExpressionSystem interface for backend primitives.

This module defines the abstract interface that all backend-specific
ExpressionSystem implementations must follow. It separates backend
primitives from logic dispatch.
"""

from abc import ABC, abstractmethod
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constants import CONST_VISITOR_BACKENDS
    from ..protocols.core.column import ColumnExpressionProtocol
    from ..protocols.core.literal import LiteralExpressionProtocol

    from ..protocols.boolean.boolean_iterable import BooleanIterableExpressionProtocol, ENUM_BOOLEAN_ITERABLE_OPERATORS
    from ..protocols.boolean.boolean_comparison import BooleanComparisonExpressionProtocol, ENUM_BOOLEAN_COMPARISON_OPERATORS
    from ..protocols.boolean.boolean_collection import BooleanCollectionExpressionProtocol, ENUM_BOOLEAN_COLLECTION_OPERATORS
    from ..protocols.boolean.boolean_constant import BooleanConstantExpressionProtocol, ENUM_BOOLEAN_CONSTANT_OPERATORS
    from ..protocols.boolean.boolean_unary import BooleanUnaryExpressionProtocol, ENUM_BOOLEAN_UNARY_OPERATORS

    from ..protocols.math.arithmetic import ArithmeticExpressionProtocol, ENUM_ARITHMETIC_OPERATORS
    from ..protocols.math.arithmetic_iterable import ArithmeticIterableExpressionProtocol, ENUM_ARITHMETIC_ITERABLE_OPERATORS

    from ..protocols.null.null import NullExpressionProtocol
    from ..protocols.null.null_constant import NullConstantExpressionProtocol
    from ..protocols.null.null_logical import NullLogicalExpressionProtocol



class ExpressionSystem(ColumnExpressionProtocol,
                        LiteralExpressionProtocol,

                        BooleanIterableExpressionProtocol,
                        BooleanComparisonExpressionProtocol,
                        BooleanCollectionExpressionProtocol,
                        BooleanConstantExpressionProtocol,
                        BooleanUnaryExpressionProtocol,

                        ArithmeticExpressionProtocol,
                        ArithmeticIterableExpressionProtocol,
                        NullExpressionProtocol,
                        NullConstantExpressionProtocol,
                        NullLogicalExpressionProtocol
):
    """
    Abstract base class for backend-specific expression systems.

    ExpressionSystem encapsulates all backend-specific operations,
    providing a uniform interface for visitors to use regardless of
    the underlying DataFrame library (Narwhals, Polars, Pandas, Ibis, etc.).

    The visitor pattern uses this interface to build backend-native
    expressions without knowing the specific backend implementation.
    """

    @property
    @abstractmethod
    def backend_type(self) -> "CONST_VISITOR_BACKENDS":
        """Return the backend type constant for this ExpressionSystem."""
        pass


    @abstractmethod
    def is_native_expression(self, expr: Any) -> bool:
        """Return True if the expression is a native expression for this backend."""
        pass

    # ========================================
    # Core Primitives
    # ========================================

    # @abstractmethod
    # def col(self, name: str, **kwargs) -> Any:
    #     """
    #     Create a column reference expression.

    #     Args:
    #         name: Column name
    #         **kwargs: Backend-specific options

    #     Returns:
    #         Backend-native column reference expression
    #     """
    #     pass

    # @abstractmethod
    # def lit(self, value: Any) -> Any:
    #     """
    #     Create a literal value expression.

    #     Args:
    #         value: The literal value (int, float, str, bool, etc.)

    #     Returns:
    #         Backend-native literal expression
    #     """
    #     pass

    # # ========================================
    # # Comparison Operations
    # # ========================================

    # @abstractmethod
    # def eq(self, left: Any, right: Any) -> Any:
    #     """
    #     Equality comparison.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def ne(self, left: Any, right: Any) -> Any:
    #     """
    #     Inequality comparison.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def gt(self, left: Any, right: Any) -> Any:
    #     """
    #     Greater-than comparison.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def lt(self, left: Any, right: Any) -> Any:
    #     """
    #     Less-than comparison.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def ge(self, left: Any, right: Any) -> Any:
    #     """
    #     Greater-than-or-equal comparison.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def le(self, left: Any, right: Any) -> Any:
    #     """
    #     Less-than-or-equal comparison.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # # ========================================
    # # Logical Operations
    # # ========================================

    # @abstractmethod
    # def and_(self, left: Any, right: Any) -> Any:
    #     """
    #     Logical AND operation (binary).

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def or_(self, left: Any, right: Any) -> Any:
    #     """
    #     Logical OR operation (binary).

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # @abstractmethod
    # def not_(self, operand: Any) -> Any:
    #     """
    #     Logical NOT operation (unary).

    #     Args:
    #         operand: Operand to negate

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # # ========================================
    # # Collection Operations
    # # ========================================

    # @abstractmethod
    # def is_in(self, element: Any, collection: List[Any]) -> Any:
    #     """
    #     Membership test (element IN collection).

    #     Args:
    #         element: Element to check
    #         collection: Collection of values

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # # ========================================
    # # Null Operations
    # # ========================================

    # @abstractmethod
    # def is_null(self, operand: Any) -> Any:
    #     """
    #     Check if operand is NULL/None.

    #     Args:
    #         operand: Operand to check

    #     Returns:
    #         Backend-native boolean expression
    #     """
    #     pass

    # # ========================================
    # # Type Operations
    # # ========================================

    # @abstractmethod
    # def cast(self, value: Any, dtype: Any, **kwargs) -> Any:
    #     """
    #     Cast value to specified type.

    #     Args:
    #         value: Value to cast
    #         dtype: Target data type
    #         **kwargs: Backend-specific casting options

    #     Returns:
    #         Backend-native casted expression
    #     """
    #     pass

    # # ========================================
    # # Arithmetic Operations (for numeric expressions)
    # # ========================================

    # @abstractmethod
    # def add(self, left: Any, right: Any) -> Any:
    #     """
    #     Addition operation.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native numeric expression
    #     """
    #     pass

    # @abstractmethod
    # def sub(self, left: Any, right: Any) -> Any:
    #     """
    #     Subtraction operation.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native numeric expression
    #     """
    #     pass

    # @abstractmethod
    # def mul(self, left: Any, right: Any) -> Any:
    #     """
    #     Multiplication operation.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native numeric expression
    #     """
    #     pass

    # @abstractmethod
    # def mod(self, left: Any, right: Any) -> Any:
    #     """
    #     Modulo operation.

    #     Args:
    #         left: Left operand
    #         right: Right operand

    #     Returns:
    #         Backend-native numeric expression
    #     """
    #     pass
