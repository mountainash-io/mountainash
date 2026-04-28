"""Ternary logic operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Provides three-valued logic operations (TRUE=1, UNKNOWN=0, FALSE=-1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode, LiteralNode
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarTernaryAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class MountainAshScalarTernaryAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarTernaryAPIBuilderProtocol):
    """
    Ternary logic operations APIBuilder.

    Provides three-valued logic operations where:
    - TRUE (1): Definitely true
    - UNKNOWN (0): Cannot determine (NULL, missing, or custom sentinel)
    - FALSE (-1): Definitely false

    Ternary Comparisons:
        t_eq, t_ne, t_gt, t_lt, t_ge, t_le: Ternary comparison operators
        t_is_in, t_is_not_in: Ternary collection membership

    Ternary Logic:
        t_and: Ternary AND (minimum semantics)
        t_or: Ternary OR (maximum semantics)
        t_not: Ternary NOT (sign flip)
        t_xor: Ternary XOR (exactly one TRUE)

    Booleanizers:
        is_true: TRUE → True, else → False
        is_false: FALSE → True, else → False
        is_unknown: UNKNOWN → True, else → False
        is_known: TRUE or FALSE → True, UNKNOWN → False
        maybe_true: TRUE or UNKNOWN → True, FALSE → False
        maybe_false: FALSE or UNKNOWN → True, TRUE → False

    Conversion:
        to_ternary: Convert boolean to ternary

    Auto-Coercion:
        When boolean expressions (eq, and_, etc.) are used with ternary
        operations (t_and, t_or, etc.), they are automatically converted
        to ternary via to_ternary().
    """

    # ========================================
    # Boolean → Ternary Coercion Hook
    # ========================================

    def _coerce_if_needed(
        self,
        node: "ExpressionNode",
    ) -> "ExpressionNode":
        """
        Coerce boolean expressions to ternary via to_ternary().

        This hook is called automatically by _to_substrait_node() for all
        arguments passed to ternary operations. Non-ternary nodes (which
        produce boolean True/False) are wrapped with to_ternary() to convert
        to ternary -1/0/1 values for use with ternary logical operators.

        Args:
            node: The expression node to potentially coerce.

        Returns:
            The original node, or a wrapped to_ternary() node for boolean expressions.
        """
        # Only coerce ScalarFunctionNodes that are not already ternary
        if isinstance(node, ScalarFunctionNode) and not node.is_ternary:
            return ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY,
                arguments=[node],
            )
        # Non-ScalarFunctionNode (LiteralNode, FieldReferenceNode) - no coercion
        return node

    # ========================================
    # Sentinel Value Extraction
    # ========================================

    def _extract_unknown_options(self, left_node, right_node=None):
        """Extract unknown_values from FieldReferenceNode operands into options dict."""
        options = {}
        left_unknown = getattr(left_node, "unknown_values", None)
        if left_unknown:
            options["left_unknown"] = frozenset(left_unknown)
        right_unknown = getattr(right_node, "unknown_values", None) if right_node else None
        if right_unknown:
            options["right_unknown"] = frozenset(right_unknown)
        return options

    # ========================================
    # Ternary Comparisons
    # ========================================

    def t_eq(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary equal to. Returns -1/0/1."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_EQ,
            arguments=[self._node, other_node],
            options=self._extract_unknown_options(self._node, other_node),
        )
        return self._build(node)

    def t_ne(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary not equal to. Returns -1/0/1."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NE,
            arguments=[self._node, other_node],
            options=self._extract_unknown_options(self._node, other_node),
        )
        return self._build(node)

    def t_gt(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary greater than. Returns -1/0/1."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GT,
            arguments=[self._node, other_node],
            options=self._extract_unknown_options(self._node, other_node),
        )
        return self._build(node)

    def t_lt(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary less than. Returns -1/0/1."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LT,
            arguments=[self._node, other_node],
            options=self._extract_unknown_options(self._node, other_node),
        )
        return self._build(node)

    def t_ge(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary greater than or equal. Returns -1/0/1."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GE,
            arguments=[self._node, other_node],
            options=self._extract_unknown_options(self._node, other_node),
        )
        return self._build(node)

    def t_le(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary less than or equal. Returns -1/0/1."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LE,
            arguments=[self._node, other_node],
            options=self._extract_unknown_options(self._node, other_node),
        )
        return self._build(node)

    # ========================================
    # Ternary Collection Operations
    # ========================================

    def t_is_in(
        self,
        values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary membership check. Returns -1/0/1.

        `values` may be a Python list/tuple/set (literal collection, baked in
        at build time) or a single expression. When the expression resolves to
        a list-typed column at compile time, each backend compiles the operation
        as per-row `list.contains(element)`; scalar expressions keep today's
        `element == value` semantics.
        """
        left_unknown = getattr(self._node, "unknown_values", None)
        options = {"unknown_values": frozenset(left_unknown)} if left_unknown else {}

        if isinstance(values, (list, tuple, set)):
            # Literal path — wrap in LIST node; visitor will extract raw values.
            literal_nodes: list["ExpressionNode"] = [LiteralNode(value=v) for v in values]
            collection_arg: "ExpressionNode" = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
                arguments=literal_nodes,
            )
        else:
            # Expression path — pass through raw. Visitor compiles normally;
            # the backend distinguishes list-literal vs compiled-Expr arguments
            # via `isinstance` at its own boundary.
            collection_arg = self._to_substrait_node(values)

        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
            arguments=[self._node, collection_arg],
            options=options,
        )
        return self._build(node)

    def t_is_not_in(
        self,
        values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary non-membership check. Returns -1/0/1.

        Mirror of `t_is_in`. See its docstring for `values` semantics.
        """
        left_unknown = getattr(self._node, "unknown_values", None)
        options = {"unknown_values": frozenset(left_unknown)} if left_unknown else {}

        if isinstance(values, (list, tuple, set)):
            literal_nodes: list["ExpressionNode"] = [LiteralNode(value=v) for v in values]
            collection_arg: "ExpressionNode" = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
                arguments=literal_nodes,
            )
        else:
            collection_arg = self._to_substrait_node(values)

        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN,
            arguments=[self._node, collection_arg],
            options=options,
        )
        return self._build(node)

    # ========================================
    # Ternary Logical Operators
    # ========================================

    def t_and(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Ternary AND (minimum semantics).

        Automatically coerces boolean expressions to ternary via to_ternary().

        T ∧ T = T, T ∧ U = U, T ∧ F = F
        U ∧ U = U, U ∧ F = F
        F ∧ F = F
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_AND,
                arguments=[result, operand],
            )
        return self._build(result)

    def t_or(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Ternary OR (maximum semantics).

        Automatically coerces boolean expressions to ternary via to_ternary().

        T ∨ T = T, T ∨ U = T, T ∨ F = T
        U ∨ U = U, U ∨ F = U
        F ∨ F = F
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_OR,
                arguments=[result, operand],
            )
        return self._build(result)

    def t_not(self) -> BaseExpressionAPI:
        """
        Ternary NOT (sign flip).

        Automatically coerces boolean expressions to ternary via to_ternary().

        ¬T = F, ¬U = U, ¬F = T
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NOT,
            arguments=[self._coerce_if_needed(self._node)],
        )
        return self._build(node)

    def t_xor(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Ternary XOR (exactly one TRUE).

        Automatically coerces boolean expressions to ternary via to_ternary().
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR,
                arguments=[result, operand],
            )
        return self._build(result)

    def t_xor_parity(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Ternary XOR parity (odd number of TRUE).

        Automatically coerces boolean expressions to ternary via to_ternary().
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR_PARITY,
                arguments=[result, operand],
            )
        return self._build(result)

    # ========================================
    # Booleanizers
    # ========================================

    def t_is_true(self) -> BaseExpressionAPI:
        """TRUE (1) → True, else → False."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE,
            arguments=[self._node],
        )
        return self._build(node)

    def t_is_false(self) -> BaseExpressionAPI:
        """FALSE (-1) → True, else → False."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE,
            arguments=[self._node],
        )
        return self._build(node)

    def t_is_unknown(self) -> BaseExpressionAPI:
        """UNKNOWN (0) → True, else → False."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN,
            arguments=[self._node],
        )
        return self._build(node)

    def t_is_known(self) -> BaseExpressionAPI:
        """TRUE or FALSE → True, UNKNOWN → False."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN,
            arguments=[self._node],
        )
        return self._build(node)

    def t_maybe_true(self) -> BaseExpressionAPI:
        """TRUE or UNKNOWN → True, FALSE → False."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE,
            arguments=[self._node],
        )
        return self._build(node)

    def t_maybe_false(self) -> BaseExpressionAPI:
        """FALSE or UNKNOWN → True, TRUE → False."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Conversion
    # ========================================

    def to_ternary(self) -> BaseExpressionAPI:
        """Convert boolean expression to ternary (-1/0/1)."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY,
            arguments=[self._node],
        )
        return self._build(node)
