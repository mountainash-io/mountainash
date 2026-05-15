from __future__ import annotations

import threading
from typing import Any


class ResolverRegistry:
    """Thread-safe registry for pipeline resolver configurations.

    Stores resolver state keyed by (pipeline_name, user_id) tuples,
    allowing concurrent access from multiple threads without data races.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: dict[tuple[str, str], dict[str, Any]] = {}

    def register(self, pipeline_name: str, user_id: str, **kwargs: Any) -> None:
        """Register a resolver configuration for a pipeline+user combination.

        Args:
            pipeline_name: Name of the pipeline
            user_id: User identifier
            **kwargs: Arbitrary configuration data (spec, storage, etc.)
        """
        with self._lock:
            self._store[(pipeline_name, user_id)] = kwargs

    def resolve(self, pipeline_name: str, user_id: str) -> dict[str, Any]:
        """Resolve a configuration for a pipeline+user combination.

        Args:
            pipeline_name: Name of the pipeline
            user_id: User identifier

        Returns:
            A copy of the registered configuration dict

        Raises:
            KeyError: If no resolver is registered for this combination
        """
        with self._lock:
            key = (pipeline_name, user_id)
            if key not in self._store:
                raise KeyError(f"No resolver registered for ({pipeline_name}, {user_id})")
            return dict(self._store[key])

    def unregister(self, pipeline_name: str, user_id: str) -> None:
        """Unregister a resolver configuration.

        Args:
            pipeline_name: Name of the pipeline
            user_id: User identifier
        """
        with self._lock:
            self._store.pop((pipeline_name, user_id), None)


_global_registry = ResolverRegistry()
