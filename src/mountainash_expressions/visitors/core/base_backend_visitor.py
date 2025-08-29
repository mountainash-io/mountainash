
from typing import Callable, Any, Optional, List, Literal
import ibis
import ibis.expr.types as ir
from functools import reduce

from abc import ABC, abstractmethod


class BaseBackendVisitor(ABC):

    @abstractmethod
    def _format_column(self,  column: str, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_literal(self, value: Any, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_list(self, value: Any) -> Any:
        pass
