"""Pipeline orchestration errors."""

from __future__ import annotations

from mountainash.core.errors import MountainashError


class PipelineError(MountainashError):
    """Base for macro-orchestration errors."""


class UnitFailed(PipelineError): ...


class NonRetryable(PipelineError): ...


class AmbiguousWrite(NonRetryable): ...


class UnsupportedValueKind(PipelineError, TypeError): ...


class IncompleteCoverage(PipelineError, ValueError): ...


class EmptyUnitOutput(UnitFailed): ...


class UnhashableIdentityInput(PipelineError, TypeError): ...


class IncompatibleResume(PipelineError): ...
