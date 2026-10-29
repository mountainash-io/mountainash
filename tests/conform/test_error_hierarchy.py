"""ConformError family roots under MountainashError."""
from __future__ import annotations

import pytest

from mountainash.core.errors import MountainashError
from mountainash.conform.errors import (
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldsMismatchError,
    NoMatchingFieldsError,
    ConformTransformError,
    SchemaDriftError,
    UnresolvedSourceTypeError,
    IncompatibleSourceTypeError,
)

ALL = [
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldsMismatchError,
    NoMatchingFieldsError,
    ConformTransformError,
    SchemaDriftError,
    UnresolvedSourceTypeError,
    IncompatibleSourceTypeError,
]


@pytest.mark.parametrize("cls", ALL)
def test_conform_errors_root_under_mountainash(cls):
    assert issubclass(cls, MountainashError)


def test_conform_error_message_preserved():
    err = MissingFieldsError(missing_fields=["a"], fields_match="exact")
    assert "spec fields not found" in str(err)
