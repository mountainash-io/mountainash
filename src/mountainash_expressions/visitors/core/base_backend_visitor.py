
from typing import Callable, Any, Optional, List, Literal
import ibis
import ibis.expr.types as ir
from functools import reduce

from abc import ABC, abstractmethod
from .base_visitor import Visitor

class BaseBackendVisitor(Visitor):

    @property
    @abstractmethod
    def _backend_type(self) -> str:
        pass

    @property
    def backend_type(self) -> str:
        return self._backend_type


    @abstractmethod
    def _format_column(self,  column: str, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_literal(self, value: Any, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_list(self, value: Any) -> Any:
        pass
