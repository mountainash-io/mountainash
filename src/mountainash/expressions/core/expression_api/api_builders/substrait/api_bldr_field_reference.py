"""Field reference APIBuilder.

Substrait-aligned implementation for column references.
"""

from __future__ import annotations


from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_protocols.api_builders.substrait import SubstraitFieldReferenceAPIBuilderProtocol




class SubstraitFieldReferenceAPIBuilder(BaseExpressionAPIBuilder, SubstraitFieldReferenceAPIBuilderProtocol):
    """
    Field reference APIBuilder (Substrait-aligned).

    Provides column reference operations. Most users won't
    access this directly - use col() entrypoint instead.
    """
    pass  # FieldReference is typically created via col() entrypoint
