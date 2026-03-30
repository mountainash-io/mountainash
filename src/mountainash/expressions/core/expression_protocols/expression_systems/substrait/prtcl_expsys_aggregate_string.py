"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union

from mountainash.core.types import ExpressionT


class SubstraitAggregateStringExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for aggregate string operations.

    Auto-generated from Substrait string extension.
    Function type: aggregate
    """

    def string_agg(self, input: ExpressionT, /, separator: str) -> ExpressionT:
        """Concatenates a column of string values with a separator.

        Substrait: string_agg
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...
