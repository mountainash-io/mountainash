"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitAggregateBooleanExpressionSystemProtocol(Protocol):
    """Protocol for aggregate boolean operations.

    Auto-generated from Substrait boolean extension.
    Function type: aggregate
    """

    def bool_and(self, *a: SupportedExpressions) -> SupportedExpressions:
        """If any value in the input is false, false is returned. If the input is empty or only contains nulls, null is returned. Otherwise, true is returned.


        Substrait: bool_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def bool_or(self, *a: SupportedExpressions) -> SupportedExpressions:
        """If any value in the input is true, true is returned. If the input is empty or only contains nulls, null is returned. Otherwise, false is returned.


        Substrait: bool_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...
