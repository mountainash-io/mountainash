"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace



class ScalarBooleanExpressionProtocol(Protocol):
    """Protocol for boolean operations.

    Auto-generated from Substrait boolean extension.
    """

    def or_(self, a: SupportedExpressions, /) -> SupportedExpressions:
        """The boolean `or` using Kleene logic.
This function behaves as follows with nulls:

    true or null = true

    null or true = true

    false or null = null

    null or false = null

    null or null = null

In other words, in this context a null value really means "unknown", and an unknown value `or` true is always true.
Behavior for 0 or 1 inputs is as follows:
  or() -> false
  or(x) -> x


        Substrait: or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def and_(self, a: SupportedExpressions, /) -> SupportedExpressions:
        """The boolean `and` using Kleene logic.
This function behaves as follows with nulls:

    true and null = null

    null and true = null

    false and null = false

    null and false = false

    null and null = null

In other words, in this context a null value really means "unknown", and an unknown value `and` false is always false.
Behavior for 0 or 1 inputs is as follows:
  and() -> true
  and(x) -> x


        Substrait: and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def and_not(self, a: SupportedExpressions, b: SupportedExpressions, /) -> SupportedExpressions:
        """The boolean `and` of one value and the negation of the other using Kleene logic.
This function behaves as follows with nulls:

    true and not null = null

    null and not false = null

    false and not null = false

    null and not true = false

    null and not null = null

In other words, in this context a null value really means "unknown", and an unknown value `and not` true is always false, as is false `and not` an unknown value.


        Substrait: and_not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def xor(self, a: SupportedExpressions, b: SupportedExpressions, /) -> SupportedExpressions:
        """The boolean `xor` of two values using Kleene logic.
When a null is encountered in either input, a null is output.


        Substrait: xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def not_(self, a: SupportedExpressions, /) -> SupportedExpressions:
        """The `not` of a boolean value.
When a null is input, a null is output.


        Substrait: not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    # def bool_and(self, a: SupportedExpressions) -> SupportedExpressions:
    #     """If any value in the input is false, false is returned. If the input is empty or only contains nulls, null is returned. Otherwise, true is returned.


    #     Substrait: bool_and
    #     URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
    #     """
    #     ...

    # def bool_or(self, a: SupportedExpressions) -> SupportedExpressions:
    #     """If any value in the input is true, true is returned. If the input is empty or only contains nulls, null is returned. Otherwise, false is returned.


    #     Substrait: bool_or
    #     URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
    #     """
    #     ...


class ScalarBooleanBuilderProtocol(Protocol):
    """Builder protocol for boolean operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def or_(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Boolean OR using Kleene logic.

        Substrait: or
        """
        ...

    def and_(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Boolean AND using Kleene logic.

        Substrait: and
        """
        ...

    def and_not(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Boolean AND of this value and the negation of other.

        Substrait: and_not
        """
        ...

    def xor(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Boolean XOR using Kleene logic.

        Substrait: xor
        """
        ...

    def not_(self) -> "BaseNamespace":
        """Boolean NOT.

        Substrait: not
        """
        ...
