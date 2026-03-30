"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol

from mountainash.core.types import ExpressionT

class SubstraitFieldReferenceExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for rounding operations.

    Auto-generated from Substrait rounding extension.
    """

    def col(self, x: ExpressionT, /) -> ExpressionT:
        """Rounding to the ceiling of the value `x`.


        Substrait: ceil
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...
