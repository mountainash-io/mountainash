"""Mountainash name extension protocol.

Mountainash Extension: Name
URI: file://extensions/functions_name.yaml

Extensions beyond Substrait standard:
- alias: Rename a column
- prefix: Add prefix to column name
- suffix: Add suffix to column name
- name_to_upper: Convert column name to uppercase
- name_to_lower: Convert column name to lowercase
"""

from __future__ import annotations

from typing import Union, Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.types import SupportedExpressions

class MountainAshNativeAPIBuilderProtocol(Protocol):
    """Backend protocol for Mountainash name operations."""

    def native(
        self,
        expr: SupportedExpressions,
    ) -> BaseExpressionAPI:
        """Rename the expression/column.

        Args:
            input: The expression to rename.
            name: The new name.

        Returns:
            The expression with the new name.
        """
        ...
