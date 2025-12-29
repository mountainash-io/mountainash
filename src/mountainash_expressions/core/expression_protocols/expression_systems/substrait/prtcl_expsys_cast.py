"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions


class SubstraitCastExpressionSystemProtocol(Protocol):
    """Protocol for type casting operations.

    Auto-generated from Substrait cast extension.
    """

    def cast(self, x: SupportedExpressions, /, dtype: Any) -> SupportedExpressions:
        """Cast expression to a target data type.

        Substrait: cast
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/cast.yaml
        """
        ...
