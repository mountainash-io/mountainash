"""Literal APIBuilder.

Substrait-aligned implementation for literal values.
"""

from __future__ import annotations


from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_protocols.api_builders.substrait import SubstraitLiteralAPIBuilderProtocol




class SubstraitLiteralAPIBuilder(BaseExpressionAPIBuilder, SubstraitLiteralAPIBuilderProtocol):
    """
    Literal APIBuilder (Substrait-aligned).

    Provides literal value operations. Most users won't
    access this directly - use lit() entrypoint instead.
    """
    pass  # Literals are typically created via lit() entrypoint
