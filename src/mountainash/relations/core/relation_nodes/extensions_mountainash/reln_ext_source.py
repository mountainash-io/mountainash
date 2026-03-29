"""Source relation node — holds Python data for deferred ingress.

This is a leaf node (no input relation). At execution time, the visitor
materializes the Python data into a DataFrame via PydataIngressFactory.
"""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
from ..reln_base import RelationNode


class SourceRelNode(RelationNode):
    """Leaf node holding Python data for deferred conversion to DataFrame.

    Fields:
        data: The raw Python data (list of dicts, dict of lists, dataclasses, etc.)
        detected_format: The auto-detected data format from PydataIngressFactory.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    data: Any
    detected_format: CONST_PYTHON_DATAFORMAT

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_source_rel(self)
