"""Generic keyed-registry plumbing shared across mountainash subsystems.

One primitive replaces the four hand-rolled dict+decorator registries:
the expression backend registry (``expsys_base``), the relation backend
registry (``relsys_base``), the relation visit registry
(``visit_registry``), and the optimisation-pass registry
(``optimisation_registry``).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class KeyedRegistry(Generic[K, V]):
    """Dict-backed registry with decorator registration and lazy init.

    Args:
        kind: Human-readable name used in error messages
            (e.g. ``"expression system"``).
        initializer: Optional zero-arg callable invoked lazily before the
            first read (the ``_initialized`` idiom). Re-armed by ``reset()``.
        validator: Optional ``(key, value) -> None`` hook run before every
            registration; raise to block it (e.g. protected node types).
        multi: When True, values accumulate per key in lists and
            ``entries()`` preserves global insertion order (used by the
            optimisation-pass registry). Duplicate-key errors are disabled.
    """

    def __init__(
        self,
        kind: str,
        *,
        initializer: Optional[Callable[[], None]] = None,
        validator: Optional[Callable[[K, V], None]] = None,
        multi: bool = False,
    ) -> None:
        self._kind = kind
        self._initializer = initializer
        self._validator = validator
        self._multi = multi
        self._initialized = initializer is None
        self._store: Dict[K, Any] = {}
        self._entries: List[Tuple[K, V]] = []

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._initialized = True
            assert self._initializer is not None
            self._initializer()

    def register(self, key: K, value: V) -> V:
        """Register *value* under *key*; returns *value* (decorator-friendly).

        Raises:
            ValueError: On duplicate key (single-value mode only).
        """
        if self._validator is not None:
            self._validator(key, value)
        if self._multi:
            self._store.setdefault(key, []).append(value)
            self._entries.append((key, value))
            return value
        if key in self._store:
            raise ValueError(
                f"{self._kind} already registered for key {key!r}"
            )
        self._store[key] = value
        self._entries.append((key, value))
        return value

    def decorator(self, key: K) -> Callable[[V], V]:
        """Decorator form: ``@registry.decorator(key)``."""
        def _decorator(value: V) -> V:
            return self.register(key, value)
        return _decorator

    def get(self, key: K) -> Any:
        """Look up *key*; raises ``KeyError`` listing available keys."""
        self._ensure_initialized()
        if key not in self._store:
            raise KeyError(
                f"No {self._kind} registered for key {key!r}. "
                f"Available: {list(self._store.keys())}"
            )
        return self._store[key]

    def get_optional(self, key: K) -> Optional[Any]:
        """Look up *key*; returns ``None`` on a miss."""
        self._ensure_initialized()
        return self._store.get(key)

    def unregister(self, key: K) -> None:
        """Remove *key* if present (idempotent)."""
        self._store.pop(key, None)
        self._entries = [(k, v) for (k, v) in self._entries if k != key]

    def list_keys(self) -> List[K]:
        self._ensure_initialized()
        return list(self._store.keys())

    def entries(self) -> List[Tuple[K, V]]:
        """All registrations in global insertion order."""
        self._ensure_initialized()
        return list(self._entries)

    def reset(self) -> None:
        """Test hook: clear everything and re-arm the lazy initializer."""
        self._store.clear()
        self._entries.clear()
        self._initialized = self._initializer is None
