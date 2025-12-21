"""Ibis ScalarBooleanExpressionProtocol implementation.

Implements boolean logical operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_boolean import (
        ScalarBooleanExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


class IbisScalarBooleanSystem(IbisBaseExpressionSystem):
    """Ibis implementation of ScalarBooleanExpressionProtocol.

    Implements 5 boolean methods using Kleene (three-valued) logic:
    - and_: Boolean AND (returns false if any false, null if any null and no false)
    - or_: Boolean OR (returns true if any true, null if any null and no true)
    - not_: Boolean NOT (negation)
    - xor: Boolean XOR (exclusive or)
    - and_not: Boolean AND of first value with negation of second
    """

    def and_(self, *args: SupportedExpressions) -> SupportedExpressions:
        """Boolean AND using Kleene logic.

        Behavior with nulls:
        - true and null = null
        - false and null = false
        - null and null = null

        For 0 inputs: returns true
        For 1 input: returns that input
        """
        if len(args) == 0:
            return ibis.literal(True)
        if len(args) == 1:
            return args[0]

        result = args[0]
        for arg in args[1:]:
            result = result & arg
        return result

    def or_(self, *args: SupportedExpressions) -> SupportedExpressions:
        """Boolean OR using Kleene logic.

        Behavior with nulls:
        - true or null = true
        - false or null = null
        - null or null = null

        For 0 inputs: returns false
        For 1 input: returns that input
        """
        if len(args) == 0:
            return ibis.literal(False)
        if len(args) == 1:
            return args[0]

        result = args[0]
        for arg in args[1:]:
            result = result | arg
        return result

    def not_(self, a: SupportedExpressions, /) -> SupportedExpressions:
        """Boolean NOT.

        Returns null if input is null.
        """
        return ~a

    def xor(self, a: SupportedExpressions, b: SupportedExpressions, /) -> SupportedExpressions:
        """Boolean XOR using Kleene logic.

        Returns null if either input is null.
        """
        return a ^ b

    def and_not(self, a: SupportedExpressions, b: SupportedExpressions, /) -> SupportedExpressions:
        """Boolean AND of first value with negation of second.

        Equivalent to: a AND (NOT b)

        Behavior with nulls:
        - true and not null = null
        - false and not null = false
        - null and not true = false
        - null and not false = null
        """
        return a & (~b)
