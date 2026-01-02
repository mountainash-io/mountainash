"""Field reference APIBuilder.

Substrait-aligned implementation for column references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_FIELD_REFERENCE
from mountainash_expressions.core.expression_nodes import FieldReferenceNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.substrait import SubstraitFieldReferenceAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class SubstraitFieldReferenceAPIBuilder(BaseExpressionAPIBuilder, SubstraitFieldReferenceAPIBuilderProtocol):
    """
    Field reference APIBuilder (Substrait-aligned).

    Provides column reference operations. Most users won't
    access this directly - use col() entrypoint instead.
    """
    pass  # FieldReference is typically created via col() entrypoint
