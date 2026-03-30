"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Optional

from mountainash.core.types import ExpressionT


class SubstraitScalarSetExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar set operations.

    Auto-generated from Substrait set extension.
    Function type: scalar
    """

    def index_in(self, needle: ExpressionT , /, *haystack: ExpressionT) -> ExpressionT:
        """Checks the membership of a value in a list of values
Returns the first 0-based index value of some input `needle` if `needle` is equal to any element in `haystack`.  Returns `NULL` if not found.
If `needle` is `NULL`, returns `NULL`.
If `needle` is `NaN`:
  - Returns 0-based index of `NaN` in `input` (default)
  - Returns `NULL` (if `NAN_IS_NOT_NAN` is specified)


        Substrait: index_in
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_set.yaml
        """
        ...
