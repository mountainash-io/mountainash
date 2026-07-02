"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Literal, Protocol

# Runtime (not TYPE_CHECKING) import: tests/core/test_signature_conformance.py
# resolves this protocol's annotations via typing.get_type_hints(), which needs
# these names in the module's runtime namespace. (TCH002 would push them into a
# type-checking block and break that introspection.)
from mountainash.core.dtypes import MountainashDtype, NativeDtype  # noqa: TCH002
from mountainash.core.types import ExpressionT


class SubstraitCastExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for type casting operations.

    Auto-generated from Substrait cast extension.
    """

    def cast(
        self,
        x: ExpressionT,
        /,
        dtype: MountainashDtype | NativeDtype,
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT:
        """Cast expression to a target data type.

        Substrait: cast
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/cast.yaml

        Args:
            x: The expression to cast.
            dtype: The target data type.
            failure_behavior: How to handle cast failures — universally a
                literal on every backend, so it is an option, not a visited
                argument (see principle: arguments-vs-options.md):
                - "throw": Raise an error on invalid conversion (default)
                - "null": Return NULL on invalid conversion
        """
        ...
