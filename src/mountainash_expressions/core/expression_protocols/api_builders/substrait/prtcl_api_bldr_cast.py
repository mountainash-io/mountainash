"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, Union, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class CaseFailureBehaviour(Enum):
    THROW = "throw"
    NULL = "null"


class SubstraitCastAPIBuilderProtocol(Protocol):
    """Builder protocol for type casting operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def cast(
        self,
        dtype: Union[str, type, Any],
        *,
        failure_behavior: Optional[CaseFailureBehaviour] = CaseFailureBehaviour.THROW
    ) -> BaseExpressionAPI:
        """Cast to the specified data type.

        Substrait: cast
        """
        ...
