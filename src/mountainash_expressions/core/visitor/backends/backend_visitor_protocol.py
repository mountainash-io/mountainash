from typing import Protocol

from ...constants import CONST_VISITOR_BACKENDS


class BackendVisitorProtocol(Protocol):
    """Protocol for expression nodes"""
    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:...
