from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING

from mountainash.pipelines.core.capabilities import ResolvedPredicates, StepCapabilities
from mountainash.pipelines.core.policies import EmptyPolicy, RetryConfig

if TYPE_CHECKING:
    from datetime import timedelta


@dataclass
class StepContext:
    predicates: ResolvedPredicates
    pipeline_storage: Any | None
    storage_facade: Any | None
    config: dict[str, Any]
    step_name: str
    workflow_id: str | None


@dataclass(frozen=True)
class StepDefinition:
    name: str
    fn: Callable
    depends_on: list[str] = field(default_factory=list)
    capabilities: StepCapabilities = field(default_factory=StepCapabilities)
    retry: RetryConfig | None = None
    cache_ttl: timedelta | None = None
    empty_policy: EmptyPolicy = EmptyPolicy.WARN


def step(
    name: str,
    *,
    depends_on: list[str] | None = None,
    pushdown: StepCapabilities | None = None,
    retry: RetryConfig | None = None,
    cache_ttl: timedelta | None = None,
    empty_policy: EmptyPolicy = EmptyPolicy.WARN,
) -> Callable:
    def decorator(fn: Callable) -> Callable:
        defn = StepDefinition(
            name=name,
            fn=fn,
            depends_on=depends_on or [],
            capabilities=pushdown or StepCapabilities(),
            retry=retry,
            cache_ttl=cache_ttl,
            empty_policy=empty_policy,
        )

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        wrapper._step_definition = defn
        return wrapper

    return decorator
