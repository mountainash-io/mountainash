"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class SubstraitFieldReferenceAPIBuilderProtocol(Protocol):
    """Protocol for rounding operations.

    Auto-generated from Substrait rounding extension.
    """

    def col(self) -> BaseExpressionAPI:
        """Rounding to the ceiling of the value `x`.


        Substrait: ceil
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...
