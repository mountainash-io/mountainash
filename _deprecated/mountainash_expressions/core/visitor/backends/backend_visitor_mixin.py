
from typing import Any
from abc import ABC, abstractmethod
from ...constants import CONST_VISITOR_BACKENDS

class BackendVisitorMixin(ABC):

    @property
    @abstractmethod
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        pass


    @abstractmethod
    def _format_column(self,  column: str, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_literal(self, value: Any, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_list(self, value: Any) -> Any:
        pass
