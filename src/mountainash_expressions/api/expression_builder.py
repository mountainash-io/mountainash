"""
Public API for building expressions with a fluent interface.

This module provides a Polars/Narwhals-style API for building expressions
that compile to backend-native expressions using the ExpressionSystem pattern.

Example:
    >>> import mountainash_expressions as ma
    >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
    >>> backend_expr = expr.compile(df)
    >>> result = df.filter(backend_expr)
"""

from __future__ import annotations
from typing import Any, List, Union

from ..core.constants import (
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_SOURCE_OPERATORS,
    CONST_EXPRESSION_LITERAL_OPERATORS,
    CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS,
    CONST_EXPRESSION_LOGICAL_OPERATORS,
    CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS,
    CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS,
    CONST_EXPRESSION_ARITHMETIC_OPERATORS,
    CONST_EXPRESSION_STRING_OPERATORS,
    CONST_EXPRESSION_PATTERN_OPERATORS,
    CONST_EXPRESSION_CONDITIONAL_OPERATORS,
    CONST_EXPRESSION_TEMPORAL_OPERATORS,
)
from ..core.expression_nodes import (
    ExpressionNode,
    SourceExpressionNode,
    LiteralExpressionNode,
    ComparisonExpressionNode,
    LogicalExpressionNode,
    CollectionExpressionNode,
    UnaryExpressionNode,
    ArithmeticExpressionNode,
    StringExpressionNode,
    PatternExpressionNode,
    ConditionalIfElseExpressionNode,
    TemporalExpressionNode,
)
from ..core.expression_nodes.boolean_expression_nodes import (
    BooleanComparisonExpressionNode,
    BooleanLogicalExpressionNode,
    BooleanCollectionExpressionNode,
    BooleanUnaryExpressionNode,
)
from ..core.expression_visitors import ExpressionVisitorFactory


class ExpressionBuilder:
    """
    Fluent API builder for expressions.

    This class provides a chainable interface for building expressions
    that follows the Polars/Narwhals pattern. Under the hood, it builds
    an ExpressionNode AST that can be compiled to any backend.

    Example:
        >>> expr = ExpressionBuilder.col("age").gt(30)
        >>> backend_expr = expr.compile(df)
    """

    def __init__(self, node: Union[ExpressionNode, Any], logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN):
        """
        Initialize with an ExpressionNode or raw value.

        Args:
            node: The underlying expression node or raw value (string, int, etc.)
            logic_type: Logic system to use (BOOLEAN or TERNARY)
        """
        self._node = node
        self._logic_type = logic_type

    @property
    def node(self) -> Union[ExpressionNode, Any]:
        """Get the underlying expression node or raw value."""
        return self._node

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Get the logic type."""
        return self._logic_type

    # ========================================
    # Helper Methods
    # ========================================

    def _to_node(self, other: Union[ExpressionBuilder, Any]) -> Any:
        """
        Convert value to node representation.

        Args:
            other: ExpressionBuilder, ExpressionNode, or raw value

        Returns:
            Node representation (ExpressionNode or raw value)

        Note:
            Raw values (strings, ints, etc.) are kept as-is.
            The visitor's _process_operand() will handle converting them.
        """
        if isinstance(other, ExpressionBuilder):
            return other._node
        else:
            # Keep raw values as-is (visitor will handle them)
            return other

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Equal to (==).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """
        other_node = self._to_node(other)
        node = BooleanComparisonExpressionNode(
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def ne(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Not equal to (!=).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """
        other_node = self._to_node(other)
        node = BooleanComparisonExpressionNode(
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def gt(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Greater than (>).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """
        other_node = self._to_node(other)
        node = BooleanComparisonExpressionNode(
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.GT,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def lt(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Less than (<).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """
        other_node = self._to_node(other)
        node = BooleanComparisonExpressionNode(
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.LT,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def ge(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Greater than or equal (>=).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """
        other_node = self._to_node(other)
        node = BooleanComparisonExpressionNode(
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.GE,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def le(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Less than or equal (<=).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """
        other_node = self._to_node(other)
        node = BooleanComparisonExpressionNode(
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.LE,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Logical Operations
    # ========================================

    def and_(self, *others: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Logical AND operation.

        Args:
            *others: One or more expressions to AND with this one

        Returns:
            New ExpressionBuilder with logical AND node
        """
        operands = [self._node] + [self._to_node(other) for other in others]
        node = BooleanLogicalExpressionNode(
            CONST_EXPRESSION_LOGICAL_OPERATORS.AND,
            operands
        )
        return ExpressionBuilder(node, self._logic_type)

    def or_(self, *others: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Logical OR operation.

        Args:
            *others: One or more expressions to OR with this one

        Returns:
            New ExpressionBuilder with logical OR node
        """
        operands = [self._node] + [self._to_node(other) for other in others]
        node = BooleanLogicalExpressionNode(
            CONST_EXPRESSION_LOGICAL_OPERATORS.OR,
            operands
        )
        return ExpressionBuilder(node, self._logic_type)

    def not_(self) -> ExpressionBuilder:
        """
        Logical NOT operation (negation).

        Returns:
            New ExpressionBuilder with logical NOT node
        """
        node = BooleanLogicalExpressionNode(
            CONST_EXPRESSION_LOGICAL_OPERATORS.NOT,
            [self._node]
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(self, values: List[Any]) -> ExpressionBuilder:
        """
        Check if value is in a list (IN operation).

        Args:
            values: List of values to check membership

        Returns:
            New ExpressionBuilder with collection IN node
        """
        node = BooleanCollectionExpressionNode(
            CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS.IN,
            self._node,
            values
        )
        return ExpressionBuilder(node, self._logic_type)

    def is_not_in(self, values: List[Any]) -> ExpressionBuilder:
        """
        Check if value is not in a list (NOT IN operation).

        Args:
            values: List of values to check exclusion

        Returns:
            New ExpressionBuilder with collection NOT IN node
        """
        node = BooleanCollectionExpressionNode(
            CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS.NOT_IN,
            self._node,
            values
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Null Operations
    # ========================================

    def is_null(self) -> ExpressionBuilder:
        """
        Check if value is NULL.

        Returns:
            New ExpressionBuilder with IS NULL node
        """
        node = BooleanUnaryExpressionNode(
            CONST_EXPRESSION_SOURCE_OPERATORS.IS_NULL,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def is_not_null(self) -> ExpressionBuilder:
        """
        Check if value is not NULL.

        Returns:
            New ExpressionBuilder with IS NOT NULL node
        """
        node = BooleanUnaryExpressionNode(
            CONST_EXPRESSION_SOURCE_OPERATORS.IS_NOT_NULL,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Addition: self + other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic addition node

        Example:
            >>> ma.col("price").add(ma.col("tax"))
            >>> ma.col("price").add(10)
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def subtract(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Subtraction: self - other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic subtraction node

        Example:
            >>> ma.col("total").subtract(ma.col("discount"))
            >>> ma.col("total").subtract(5)
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.SUBTRACT,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def multiply(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Multiplication: self * other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic multiplication node

        Example:
            >>> ma.col("price").multiply(ma.col("quantity"))
            >>> ma.col("price").multiply(1.1)
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.MULTIPLY,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def divide(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Division: self / other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic division node

        Example:
            >>> ma.col("total").divide(ma.col("count"))
            >>> ma.col("total").divide(2)
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.DIVIDE,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def modulo(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Modulo: self % other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic modulo node

        Example:
            >>> ma.col("number").modulo(10)
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.MODULO,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def power(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Exponentiation: self ** other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic power node

        Example:
            >>> ma.col("base").power(2)
            >>> ma.col("base").power(ma.col("exponent"))
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.POWER,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def floor_divide(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Floor division: self // other

        Args:
            other: ExpressionBuilder, numeric value, or column expression

        Returns:
            New ExpressionBuilder with arithmetic floor division node

        Example:
            >>> ma.col("total").floor_divide(3)
        """
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.FLOOR_DIVIDE,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # String Operations
    # ========================================

    def str_upper(self) -> ExpressionBuilder:
        """Convert string to uppercase."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.UPPER, self._node)
        return ExpressionBuilder(node, self._logic_type)

    def str_lower(self) -> ExpressionBuilder:
        """Convert string to lowercase."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.LOWER, self._node)
        return ExpressionBuilder(node, self._logic_type)

    def str_trim(self) -> ExpressionBuilder:
        """Trim whitespace from both sides."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.TRIM, self._node)
        return ExpressionBuilder(node, self._logic_type)

    def str_length(self) -> ExpressionBuilder:
        """Get string length."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.LENGTH, self._node)
        return ExpressionBuilder(node, self._logic_type)

    def str_contains(self, substring: str) -> ExpressionBuilder:
        """Check if string contains substring (returns boolean)."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.CONTAINS, self._node, substring)
        return ExpressionBuilder(node, self._logic_type)

    def str_starts_with(self, prefix: str) -> ExpressionBuilder:
        """Check if string starts with prefix (returns boolean)."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.STARTS_WITH, self._node, prefix)
        return ExpressionBuilder(node, self._logic_type)

    def str_ends_with(self, suffix: str) -> ExpressionBuilder:
        """Check if string ends with suffix (returns boolean)."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.ENDS_WITH, self._node, suffix)
        return ExpressionBuilder(node, self._logic_type)

    def str_replace(self, old: str, new: str) -> ExpressionBuilder:
        """Replace substring."""
        node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.REPLACE, self._node, old, new)
        return ExpressionBuilder(node, self._logic_type)

    def str_substring(self, start: int, length: int = None) -> ExpressionBuilder:
        """Extract substring."""
        if length is None:
            node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.SUBSTRING, self._node, start)
        else:
            node = StringExpressionNode(CONST_EXPRESSION_STRING_OPERATORS.SUBSTRING, self._node, start, length)
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def like(self, pattern: str) -> ExpressionBuilder:
        """
        SQL LIKE pattern matching (% and _ wildcards).

        Args:
            pattern: Pattern with % (any chars) and _ (single char) wildcards

        Returns:
            Boolean expression indicating if string matches pattern

        Example:
            >>> ma.col("name").like("John%")  # Starts with "John"
            >>> ma.col("email").like("%@%.com")  # Contains @ and ends with .com
        """
        node = PatternExpressionNode(CONST_EXPRESSION_PATTERN_OPERATORS.LIKE, self._node, pattern)
        return ExpressionBuilder(node, self._logic_type)

    def regex_match(self, pattern: str) -> ExpressionBuilder:
        r"""
        Check if string fully matches regex pattern.

        Args:
            pattern: Regular expression pattern

        Returns:
            Boolean expression indicating if string matches pattern

        Example:
            >>> ma.col("phone").regex_match(r"^\d{3}-\d{3}-\d{4}$")
        """
        node = PatternExpressionNode(CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_MATCH, self._node, pattern)
        return ExpressionBuilder(node, self._logic_type)

    def regex_contains(self, pattern: str) -> ExpressionBuilder:
        r"""
        Check if string contains regex pattern.

        Args:
            pattern: Regular expression pattern

        Returns:
            Boolean expression indicating if string contains pattern

        Example:
            >>> ma.col("text").regex_contains(r"\d+")  # Contains digits
        """
        node = PatternExpressionNode(CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_CONTAINS, self._node, pattern)
        return ExpressionBuilder(node, self._logic_type)

    def regex_replace(self, pattern: str, replacement: str) -> ExpressionBuilder:
        r"""
        Replace text matching regex pattern.

        Args:
            pattern: Regular expression pattern
            replacement: Replacement string

        Returns:
            String expression with replacements applied

        Example:
            >>> ma.col("text").regex_replace(r"\d+", "X")  # Replace digits with X
        """
        node = PatternExpressionNode(CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_REPLACE, self._node, pattern, replacement)
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Conditional Operations
    # ========================================

    def fill_null(self, value: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Replace null values with specified value.

        Args:
            value: Value to use for nulls

        Returns:
            Expression with nulls replaced

        Example:
            >>> ma.col("score").fill_null(0)
        """
        value_node = self._to_node(value)
        node = ConditionalIfElseExpressionNode(
            CONST_EXPRESSION_CONDITIONAL_OPERATORS.FILL_NULL,
            condition=self._node,
            consequence=value_node
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Temporal Operations
    # ========================================

    def dt_year(self) -> ExpressionBuilder:
        """
        Extract year from datetime.

        Returns:
            Expression with year extracted

        Example:
            >>> ma.col("date").dt_year()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.YEAR,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_month(self) -> ExpressionBuilder:
        """
        Extract month from datetime.

        Returns:
            Expression with month extracted

        Example:
            >>> ma.col("date").dt_month()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.MONTH,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_day(self) -> ExpressionBuilder:
        """
        Extract day from datetime.

        Returns:
            Expression with day extracted

        Example:
            >>> ma.col("date").dt_day()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.DAY,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_hour(self) -> ExpressionBuilder:
        """
        Extract hour from datetime.

        Returns:
            Expression with hour extracted

        Example:
            >>> ma.col("timestamp").dt_hour()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.HOUR,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_minute(self) -> ExpressionBuilder:
        """
        Extract minute from datetime.

        Returns:
            Expression with minute extracted

        Example:
            >>> ma.col("timestamp").dt_minute()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.MINUTE,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_second(self) -> ExpressionBuilder:
        """
        Extract second from datetime.

        Returns:
            Expression with second extracted

        Example:
            >>> ma.col("timestamp").dt_second()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.SECOND,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_weekday(self) -> ExpressionBuilder:
        """
        Extract day of week from datetime (0=Monday, 6=Sunday).

        Returns:
            Expression with weekday extracted

        Example:
            >>> ma.col("date").dt_weekday()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.WEEKDAY,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_week(self) -> ExpressionBuilder:
        """
        Extract week number from datetime.

        Returns:
            Expression with week number extracted

        Example:
            >>> ma.col("date").dt_week()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.WEEK,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_quarter(self) -> ExpressionBuilder:
        """
        Extract quarter from datetime (1-4).

        Returns:
            Expression with quarter extracted

        Example:
            >>> ma.col("date").dt_quarter()
        """
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.QUARTER,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_add_days(self, days: Union[ExpressionBuilder, int]) -> ExpressionBuilder:
        """
        Add days to a date.

        Args:
            days: Number of days to add

        Returns:
            Expression with days added

        Example:
            >>> ma.col("date").dt_add_days(7)
        """
        days_node = self._to_node(days)
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_DAYS,
            self._node,
            days_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_add_months(self, months: Union[ExpressionBuilder, int]) -> ExpressionBuilder:
        """
        Add months to a date.

        Args:
            months: Number of months to add

        Returns:
            Expression with months added

        Example:
            >>> ma.col("date").dt_add_months(3)
        """
        months_node = self._to_node(months)
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_MONTHS,
            self._node,
            months_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_add_years(self, years: Union[ExpressionBuilder, int]) -> ExpressionBuilder:
        """
        Add years to a date.

        Args:
            years: Number of years to add

        Returns:
            Expression with years added

        Example:
            >>> ma.col("date").dt_add_years(1)
        """
        years_node = self._to_node(years)
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_YEARS,
            self._node,
            years_node
        )
        return ExpressionBuilder(node, self._logic_type)

    def dt_diff_days(self, other_date: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Calculate difference in days between this date and another date.

        Args:
            other_date: Date to subtract from this date

        Returns:
            Expression with difference in days (self - other_date)

        Example:
            >>> ma.col("end_date").dt_diff_days(ma.col("start_date"))
        """
        other_node = self._to_node(other_date)
        node = TemporalExpressionNode(
            CONST_EXPRESSION_TEMPORAL_OPERATORS.DIFF_DAYS,
            self._node,
            other_node
        )
        return ExpressionBuilder(node, self._logic_type)

    # ========================================
    # Compilation
    # ========================================

    def compile(self, dataframe: Any, logic_type: CONST_LOGIC_TYPES = None, use_universal: bool = True) -> Any:
        """
        Compile expression to backend-native expression.

        This is the key method that converts the ExpressionNode AST
        into a backend-specific expression (nw.Expr, pl.Expr, ir.Expr).

        Args:
            dataframe: DataFrame to auto-detect backend from
            logic_type: Override logic type (defaults to builder's logic_type)
            use_universal: Use universal visitor with ExpressionSystem (default True)

        Returns:
            Backend-native expression (nw.Expr, pl.Expr, or ir.Expr)

        Example:
            >>> expr = col("age").gt(30)
            >>> backend_expr = expr.compile(df)
            >>> result = df.filter(backend_expr)
        """
        logic = logic_type or self._logic_type

        # Get appropriate visitor for backend
        visitor = ExpressionVisitorFactory.get_visitor_for_backend(
            dataframe,
            logic,
            use_universal=use_universal
        )

        # Compile the node using visitor
        if isinstance(self._node, ExpressionNode):
            # ExpressionNode - use visitor pattern
            return self._node.accept(visitor)
        else:
            # Raw value (string, int, etc.) - process directly through visitor
            return visitor._process_operand(self._node)

    # ========================================
    # Python Magic Methods (for convenience)
    # ========================================

    def __and__(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """Support & operator for AND."""
        return self.and_(other)

    def __or__(self, other: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """Support | operator for OR."""
        return self.or_(other)

    def __invert__(self) -> ExpressionBuilder:
        """Support ~ operator for NOT."""
        return self.not_()

    def __eq__(self, other: Any) -> ExpressionBuilder:
        """Support == operator."""
        return self.eq(other)

    def __ne__(self, other: Any) -> ExpressionBuilder:
        """Support != operator."""
        return self.ne(other)

    def __gt__(self, other: Any) -> ExpressionBuilder:
        """Support > operator."""
        return self.gt(other)

    def __lt__(self, other: Any) -> ExpressionBuilder:
        """Support < operator."""
        return self.lt(other)

    def __ge__(self, other: Any) -> ExpressionBuilder:
        """Support >= operator."""
        return self.ge(other)

    def __le__(self, other: Any) -> ExpressionBuilder:
        """Support <= operator."""
        return self.le(other)

    # Arithmetic operators
    def __add__(self, other: Any) -> ExpressionBuilder:
        """Support + operator for addition."""
        return self.add(other)

    def __sub__(self, other: Any) -> ExpressionBuilder:
        """Support - operator for subtraction."""
        return self.subtract(other)

    def __mul__(self, other: Any) -> ExpressionBuilder:
        """Support * operator for multiplication."""
        return self.multiply(other)

    def __truediv__(self, other: Any) -> ExpressionBuilder:
        """Support / operator for division."""
        return self.divide(other)

    def __mod__(self, other: Any) -> ExpressionBuilder:
        """Support % operator for modulo."""
        return self.modulo(other)

    def __pow__(self, other: Any) -> ExpressionBuilder:
        """Support ** operator for exponentiation."""
        return self.power(other)

    def __floordiv__(self, other: Any) -> ExpressionBuilder:
        """Support // operator for floor division."""
        return self.floor_divide(other)

    # Reverse arithmetic operators (for when left operand is not ExpressionBuilder)
    def __radd__(self, other: Any) -> ExpressionBuilder:
        """Support other + self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __rsub__(self, other: Any) -> ExpressionBuilder:
        """Support other - self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.SUBTRACT,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __rmul__(self, other: Any) -> ExpressionBuilder:
        """Support other * self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.MULTIPLY,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __rtruediv__(self, other: Any) -> ExpressionBuilder:
        """Support other / self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.DIVIDE,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __rmod__(self, other: Any) -> ExpressionBuilder:
        """Support other % self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.MODULO,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __rpow__(self, other: Any) -> ExpressionBuilder:
        """Support other ** self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.POWER,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __rfloordiv__(self, other: Any) -> ExpressionBuilder:
        """Support other // self."""
        other_node = self._to_node(other)
        node = ArithmeticExpressionNode(
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.FLOOR_DIVIDE,
            other_node,
            self._node
        )
        return ExpressionBuilder(node, self._logic_type)

    def __repr__(self) -> str:
        """String representation."""
        return f"ExpressionBuilder({self._node})"
