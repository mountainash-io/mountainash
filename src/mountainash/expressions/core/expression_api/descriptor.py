"""Descriptor for binding namespace classes to ExpressionAPI instances."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, overload

if TYPE_CHECKING:
    from .base import BaseExpressionAPI

T = TypeVar("T")


class NamespaceDescriptor(Generic[T]):
    """
    Descriptor that lazily binds a namespace class to an ExpressionAPI instance.

    When accessed on a class, returns the descriptor itself.
    When accessed on an instance, returns a namespace instance bound to that API.

    Example:
        class ExpressionAPI:
            str = NamespaceDescriptor(StringNamespace)

        api = ExpressionAPI(node)
        api.str  # Returns StringNamespace(api)
    """

    def __init__(self, namespace_cls: type[T]) -> None:
        """
        Initialise the descriptor.

        Args:
            namespace_cls: The namespace class to instantiate on access.
        """
        self._namespace_cls = namespace_cls

    @overload
    def __get__(
        self,
        obj: None,
        objtype: type[BaseExpressionAPI] | None = None,
    ) -> NamespaceDescriptor[T]: ...

    @overload
    def __get__(
        self,
        obj: BaseExpressionAPI,
        objtype: type[BaseExpressionAPI] | None = None,
    ) -> T: ...

    def __get__(
        self,
        obj: BaseExpressionAPI | None,
        objtype: type[BaseExpressionAPI] | None = None,
    ) -> T | NamespaceDescriptor[T]:
        """
        Return namespace instance bound to the accessing API instance.

        Args:
            obj: The instance accessing the descriptor (None if class access).
            objtype: The class owning the descriptor.

        Returns:
            Namespace instance if accessed on instance, descriptor if accessed on class.
        """
        if obj is None:
            return self
        return self._namespace_cls(obj)

    def __repr__(self) -> str:
        return f"NamespaceDescriptor({self._namespace_cls.__name__})"
