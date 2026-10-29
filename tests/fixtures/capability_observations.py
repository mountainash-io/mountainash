"""Test-owned observation validity; never runtime policy or coordinate acquisition."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import (
    Applicability,
    PreparedEnvironment,
    prepare_environment,
)
from mountainash.core.capabilities.capture import Environment


def require_observations(claim: Applicability, environment: Environment) -> PreparedEnvironment:
    domain = claim.prepare()
    prepared = prepare_environment(environment, domain.requirements)
    for kind, name, requires_version in sorted(domain.requirements):
        observation = prepared.values.get((kind, name))
        assert observation is not None, f"required observation missing or unknown: {kind}:{name}"
        if requires_version:
            assert observation.version is not None, f"required version unparseable: {kind}:{name}={observation.raw!r}"
    return prepared
