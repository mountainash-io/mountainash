"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union

from mountainash.core.types import ExpressionT


class SubstraitScalarBooleanExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for boolean operations.

    Auto-generated from Substrait boolean extension.
    """


    def and_(self, *args: ExpressionT) -> ExpressionT:
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

    def or_(self, *args: ExpressionT) -> ExpressionT:
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


    def not_(self, a: ExpressionT, /) -> ExpressionT:
        """The `not` of a boolean value.
When a null is input, a null is output.


        Substrait: not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def xor(self, a: ExpressionT, b: ExpressionT, /) -> ExpressionT:
        """The boolean `xor` of two values using Kleene logic.
When a null is encountered in either input, a null is output.


        Substrait: xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...


    def and_not(self, a: ExpressionT, b: ExpressionT, /) -> ExpressionT:
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
