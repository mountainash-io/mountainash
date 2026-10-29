"""Validation error hierarchy — typed-error-hierarchy conformance."""
import pytest

from mountainash.core.errors import MountainashError
from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityInvalidError,
    IdentityRequiredError,
    UnknownCheckTypeError,
    ValidationError,
)


def test_domain_base_roots_to_mountainash_error():
    assert issubclass(ValidationError, MountainashError)


@pytest.mark.parametrize(
    ("leaf", "builtin"),
    [
        (CheckDeclarationError, ValueError),
        (IdentityRequiredError, RuntimeError),
        (IdentityInvalidError, ValueError),
        (UnknownCheckTypeError, TypeError),
    ],
)
def test_leaves_mix_in_builtins(leaf, builtin):
    assert issubclass(leaf, ValidationError)
    assert issubclass(leaf, builtin)
    with pytest.raises(builtin):
        raise leaf("message")


def test_facade_reexports():
    from mountainash import exceptions

    for name in (
        "ValidationError",
        "CheckDeclarationError",
        "IdentityRequiredError",
        "IdentityInvalidError",
        "UnknownCheckTypeError",
    ):
        assert getattr(exceptions, name) is not None
