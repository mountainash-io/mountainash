"""Base class for Substrait-aligned expression nodes.

This module defines the abstract base class that all Substrait-aligned
expression nodes inherit from. These nodes can be serialized to/from
Substrait's protobuf format.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING
from enum import Enum

from pydantic import BaseModel, ConfigDict



class ExpressionNode(BaseModel, ABC):
    """Base class for all Substrait-aligned expression nodes.

    All expression nodes inherit from this class. Nodes form an AST that can be:
    1. Built by user code via namespaces
    2. Compiled to backend-native expressions via visitors
    3. Serialized to Substrait protobuf for interoperability

    Node types align with Substrait's expression model:
    - LiteralNode: Constant values
    - FieldReferenceNode: Column references
    - ScalarFunctionNode: Function calls (most operations)
    - IfThenNode: Conditional expressions
    - CastNode: Type conversions
    - SingularOrListNode: IN operator / membership tests
    """

    model_config = ConfigDict(
        frozen=True,  # Nodes are immutable
        arbitrary_types_allowed=True,
    )

    # Function identifier - Optional: only ScalarFunctionNode uses this
    # FieldReferenceNode, LiteralNode, CastNode, IfThenNode use their own keys
    function_key: Optional[Enum] = None

    @abstractmethod
    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch pattern.

        Args:
            visitor: The visitor instance

        Returns:
            The result from the visitor's visit method
        """
        ...

    def to_substrait(self) -> Any:
        """Serialize this node to Substrait protobuf.

        Returns:
            Substrait Expression protobuf message

        Note:
            This method will be implemented in Phase 5.
        """
        raise NotImplementedError("Substrait serialization not yet implemented")

    @classmethod
    def from_substrait(cls, expr: Any) -> ExpressionNode:
        """Deserialize from Substrait protobuf.

        Args:
            expr: Substrait Expression protobuf message

        Returns:
            SubstraitNode instance

        Note:
            This method will be implemented in Phase 5.
        """
        raise NotImplementedError("Substrait deserialization not yet implemented")
