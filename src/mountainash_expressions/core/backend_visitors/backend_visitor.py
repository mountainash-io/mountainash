
from typing import Any
from abc import ABC, abstractmethod
from ...constants import CONST_VISITOR_BACKENDS

class BackendVisitor(ABC):

    @property
    @abstractmethod
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        pass



    @abstractmethod
    def _col(self,  column: str) -> Any:
        pass

    @abstractmethod
    def _lit(self, value: Any) -> Any:
        pass

    @abstractmethod
    def _as_list(self, value: Any) -> Any:
        pass

    @abstractmethod
    def _as_set(self, value: Any) -> Any:
        pass


    @abstractmethod
    def _is_reserved_unknown_flag(self, value: Any) -> Any:
        pass

    @abstractmethod
    def _is_null(self, value: Any) -> Any:
        pass

    @abstractmethod
    def _not_null(self, value: Any) -> Any:
        pass
