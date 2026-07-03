"""Source relation node — holds Python data for deferred ingress.

This is a leaf node (no input relation). At execution time, the visitor
materializes the Python data into a DataFrame via PydataIngressFactory.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar, Optional

from pydantic import ConfigDict

from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)
from ..reln_base import RelationNode


class SourceRelNode(RelationNode):
    """Leaf node holding Python data for deferred conversion to DataFrame.

    Fields:
        data: The raw Python data (list of dicts, dict of lists, dataclasses, etc.)
        detected_format: The auto-detected data format from PydataIngressFactory.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    _operation_key: ClassVar[Optional[Enum]] = RKEY_MOUNTAINASH_REL.SOURCE

    data: Any
    detected_format: CONST_PYTHON_DATAFORMAT

    def accept(self, visitor: Any) -> Any:
        return visitor.visit(self)
