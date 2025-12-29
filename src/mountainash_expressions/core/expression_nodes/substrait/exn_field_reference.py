"""Field reference node for column access.

Corresponds to Substrait's FieldReference message.
"""

from __future__ import annotations
from typing import Any, Optional, Set

from .exn_base import ExpressionNode


class FieldReferenceNode(ExpressionNode):
    """A reference to a column/field in a DataFrame.

    Represents access to a column by name. Corresponds to Substrait's
    FieldReference expression type using direct reference by name.

    Attributes:
        field: The column name to reference
        unknown_values: Optional set of values to treat as UNKNOWN for ternary logic.
                       This enables configurable NULL-like behavior for sentinel values.

    Examples:
        >>> FieldReferenceNode(field="age")
        >>> FieldReferenceNode(field="score", unknown_values={-99999})
    """

    field: str
    unknown_values: Optional[Set[Any]] = None

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_field_reference(self)
