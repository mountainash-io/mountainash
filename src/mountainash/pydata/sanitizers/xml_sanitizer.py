"""XML entity restoration functions for the pydata sanitizers pipeline.

Provides utilities for restoring XML special characters (entities) in
strings, lists, dicts, and sets, plus an XSD validation stub.
"""
from __future__ import annotations

from typing import List, Dict, Set, Any

from upath import UPath

__all__ = [
    "restore_special_characters",
    "validate_file_xsd",
]


def _restore_special_characters_str(value: str) -> str:
    """Restores XML special characters in a string.

    Replaces encoded characters like &lt; with the original characters.

    Args:
        value: The string to restore.

    Returns:
        The string with XML entities converted to characters.

    Example:
        text = _restore_special_characters_str("A &lt; B")
        # text = "A < B"
    """
    special_chars: list[str] = ["&lt;", "&gt;", "&amp;", "&apos;", "&quot;"]

    # Check if string contains any encoded entities
    if any(char in value for char in special_chars):

        special_chars_dict: dict[str, str] = {
            "&lt;": "<",
            "&gt;": ">",
            "&amp;": "&",
            "&apos;": "'",
            "&quot;": "\""
        }

        for encoded, char in special_chars_dict.items():
            value = value.replace(encoded, char)

    return value


def _restore_special_characters_list(value: List[Any]) -> List[Any]:
    """Restores XML entities in each element of a list.

    Args:
        value: The list of values.

    Returns:
        The list with special characters restored in each element.

    Example:
        data = ["A &lt; B", "C &gt; D"]
        fixed = _restore_special_characters_list(data)
    """
    return [restore_special_characters(value=v) for v in value]


def _restore_special_characters_dict(value: Dict[str, Any]) -> Dict[Any, Any]:
    """Restores XML entities in keys and values of a dictionary.

    Iterates through the dictionary and restores XML special characters in both
    the keys and values.

    Args:
        value: The dictionary to process.

    Returns:
        The dictionary with special characters restored in keys and values.

    Example:
        data = {"A &lt; B": "C &gt; D"}
        fixed = _restore_special_characters_dict(data)
    """
    return {
        restore_special_characters(value=k): restore_special_characters(value=v)
        for k, v in value.items()
    }


def _restore_special_characters_set(value: Set[Any]) -> Set[Any]:
    """Restores XML entities in each element of a set.

    Args:
        value: The set to process.

    Returns:
        The set with special characters restored in each element.

    Example:
        data = {"A &lt; B", "C &gt; D"}
        fixed = _restore_special_characters_set(data)
    """
    new_set = set()
    for k in value:
        restored: Any = restore_special_characters(value=k)
        try:
            hash(restored)  # Check if the item is hashable
            new_set.add(restored)
        except TypeError:
            raise TypeError(f"Set item {restored} is not hashable. The set was not valid")
    return new_set


def restore_special_characters(value: Any) -> Any:
    """Restores XML special characters in a value.

    Detects the type of the input value and calls the
    appropriate restoration helper function.

    Supported types are str, list, dict and set.
    Other types are returned unchanged.

    Args:
        value: The value to process.

    Returns:
        The value with XML entities converted to characters.

    Example:
        text = restore_special_characters("A &lt; B")
        data = {"key": "val &amp;"}
        restore_special_characters(data)
    """
    if isinstance(value, str):
        return _restore_special_characters_str(value)
    elif isinstance(value, list):
        return _restore_special_characters_list(value)
    elif isinstance(value, dict):
        return _restore_special_characters_dict(value)
    elif isinstance(value, set):
        return _restore_special_characters_set(value)
    else:
        return value


def validate_file_xsd(file_path: UPath | str, xsd_path: UPath | str) -> bool:
    """Validate an XML file against an XSD schema (stub — not yet implemented).

    Args:
        file_path: Path to the XML file to validate.
        xsd_path: Path to the XSD schema file.

    Returns:
        True if valid, False otherwise. Currently always returns None (stub).
    """
    pass
