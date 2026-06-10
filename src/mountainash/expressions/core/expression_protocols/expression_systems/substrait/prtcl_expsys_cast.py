"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from mountainash.core.types import ExpressionT

if TYPE_CHECKING:
    from mountainash.core.dtypes import MountainashDtype, NativeDtype


class SubstraitCastExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for type casting operations.

    Auto-generated from Substrait cast extension.
    """

    def cast(self, x: ExpressionT, /, dtype: "MountainashDtype | NativeDtype") -> ExpressionT:
        """Cast expression to a target data type.

        Substrait: cast
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/cast.yaml
        """
        ...
