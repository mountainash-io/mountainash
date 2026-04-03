"""Tests for mountainash.pydata.utils.collection_helpers."""
from __future__ import annotations

import pytest

from mountainash.pydata.utils.collection_helpers import is_empty


# ---------------------------------------------------------------------------
# Parametrized: empty containers → True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("obj", [
    [],
    {},
    set(),
    (),
])
def test_empty_containers_return_true(obj: object) -> None:
    assert is_empty(obj) is True


# ---------------------------------------------------------------------------
# Parametrized: non-containers and special values → False
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("obj", [
    object(),
    "hello",
    "",
    0,
    None,
    False,
    True,
])
def test_non_containers_return_false(obj: object) -> None:
    assert is_empty(obj) is False


# ---------------------------------------------------------------------------
# Parametrized: nonempty containers → False
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("obj", [
    [1],
    {"a": 1},
    {1},
    (1,),
])
def test_nonempty_containers_return_false(obj: object) -> None:
    assert is_empty(obj) is False


# ---------------------------------------------------------------------------
# Individual: list
# ---------------------------------------------------------------------------

def test_empty_list() -> None:
    assert is_empty([]) is True


def test_nonempty_list() -> None:
    assert is_empty([1, 2, 3]) is False


# ---------------------------------------------------------------------------
# Individual: dict
# ---------------------------------------------------------------------------

def test_empty_dict() -> None:
    assert is_empty({}) is True


def test_nonempty_dict() -> None:
    assert is_empty({"key": "value"}) is False


# ---------------------------------------------------------------------------
# Individual: set
# ---------------------------------------------------------------------------

def test_empty_set() -> None:
    assert is_empty(set()) is True


def test_nonempty_set() -> None:
    assert is_empty({1, 2}) is False


# ---------------------------------------------------------------------------
# Individual: tuple
# ---------------------------------------------------------------------------

def test_empty_tuple() -> None:
    assert is_empty(()) is True


def test_nonempty_tuple() -> None:
    assert is_empty((1, 2)) is False


# ---------------------------------------------------------------------------
# Strings: never empty, including empty string
# ---------------------------------------------------------------------------

def test_empty_string_not_empty() -> None:
    assert is_empty("") is False


def test_nonempty_string_not_empty() -> None:
    assert is_empty("abc") is False


# ---------------------------------------------------------------------------
# Non-containers always False
# ---------------------------------------------------------------------------

def test_none_not_empty() -> None:
    assert is_empty(None) is False


def test_zero_not_empty() -> None:
    assert is_empty(0) is False


def test_one_not_empty() -> None:
    assert is_empty(1) is False


def test_true_not_empty() -> None:
    assert is_empty(True) is False


def test_false_not_empty() -> None:
    assert is_empty(False) is False


def test_object_not_empty() -> None:
    assert is_empty(object()) is False


# ---------------------------------------------------------------------------
# Nested empty containers: [[]] is not empty (it contains one element)
# ---------------------------------------------------------------------------

def test_nested_empty_list_is_not_empty() -> None:
    assert is_empty([[]]) is False


# ---------------------------------------------------------------------------
# Edge cases: custom sequence class not recognized by isinstance check
# ---------------------------------------------------------------------------

class CustomSeq:
    """A sequence-like class that does NOT inherit from Sequence."""

    def __len__(self) -> int:
        return 0

    def __getitem__(self, index: int) -> int:
        raise IndexError(index)


def test_custom_sequence_not_recognized() -> None:
    # CustomSeq does not inherit from collections.abc.Sequence, so is_empty
    # falls through to the else branch and returns False.
    assert is_empty(CustomSeq()) is False


# ---------------------------------------------------------------------------
# Edge cases: range
# ---------------------------------------------------------------------------

def test_empty_range() -> None:
    assert is_empty(range(0)) is True


def test_nonempty_range() -> None:
    assert is_empty(range(5)) is False


# ---------------------------------------------------------------------------
# Edge cases: bytes and bytearray
# ---------------------------------------------------------------------------

def test_empty_bytes() -> None:
    assert is_empty(b"") is True


def test_nonempty_bytes() -> None:
    assert is_empty(b"abc") is False


def test_empty_bytearray() -> None:
    assert is_empty(bytearray()) is True


def test_nonempty_bytearray() -> None:
    assert is_empty(bytearray(b"abc")) is False
