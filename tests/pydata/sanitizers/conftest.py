"""Shared test fixtures for XML sanitizer tests."""
from __future__ import annotations

import pytest
from typing import Dict, Any


@pytest.fixture
def xml_entity_samples() -> Dict[str, Any]:
    """Provide comprehensive XML entity test data samples.

    Returns:
        Dictionary containing various XML entity test cases for different data types.
    """
    return {
        # String samples
        "basic_entities": "&lt;&gt;&amp;&apos;&quot;",
        "basic_entities_expected": "<>&'\"",
        "mixed_content": "Hello &lt;world&gt; &amp; welcome",
        "mixed_content_expected": "Hello <world> & welcome",
        "no_entities": "Plain text without entities",
        "empty_string": "",

        # List samples
        "simple_list": ["&lt;item1&gt;", "&amp;item2", "normal_item"],
        "simple_list_expected": ["<item1>", "&item2", "normal_item"],
        "nested_list": ["&lt;", ["&gt;", "&amp;"], "normal"],
        "nested_list_expected": ["<", [">", "&"], "normal"],
        "empty_list": [],

        # Dictionary samples
        "simple_dict": {"&lt;key&gt;": "&amp;value", "normal": "text"},
        "simple_dict_expected": {"<key>": "&value", "normal": "text"},
        "nested_dict": {
            "&lt;parent&gt;": {
                "&amp;child": "&quot;nested&quot;",
                "normal": "value"
            }
        },
        "nested_dict_expected": {
            "<parent>": {
                "&child": "\"nested\"",
                "normal": "value"
            }
        },
        "empty_dict": {},

        # Set samples
        "simple_set": {"&lt;item&gt;", "&amp;data", "normal"},
        "simple_set_expected": {"<item>", "&data", "normal"},
        "empty_set": set(),

        # Mixed type samples
        "complex_nested": {
            "string": "&lt;test&gt;",
            "list": ["&amp;item1", "&lt;item2&gt;"],
            "dict": {"&quot;key&quot;": "&apos;value&apos;"},
            "number": 123,
            "none_value": None
        },
        "complex_nested_expected": {
            "string": "<test>",
            "list": ["&item1", "<item2>"],
            "dict": {"\"key\"": "'value'"},
            "number": 123,
            "none_value": None
        }
    }


@pytest.fixture
def xml_entities_mapping() -> Dict[str, str]:
    """Provide the standard XML entity mapping.

    Returns:
        Dictionary mapping XML entities to their character equivalents.
    """
    return {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&apos;": "'",
        "&quot;": "\""
    }


@pytest.fixture
def edge_case_data() -> Dict[str, Any]:
    """Provide edge case test data.

    Returns:
        Dictionary containing edge case scenarios for testing.
    """
    return {
        # Large data scenarios
        "large_string": "&lt;" * 1000 + "content" + "&gt;" * 1000,
        "large_string_expected": "<" * 1000 + "content" + ">" * 1000,
        "large_list": ["&lt;item&gt;" for _ in range(100)],
        "large_list_expected": ["<item>" for _ in range(100)],

        # Unicode and special characters
        "unicode_string": "&lt;ïñtërñâtîöñâl&gt; text with ümlauts",
        "unicode_string_expected": "<ïñtërñâtîöñâl> text with ümlauts",

        # Boundary cases
        "only_entities": "&lt;&gt;&amp;&apos;&quot;",
        "only_entities_expected": "<>&'\"",
        "no_matching_entities": "normal text with & and < and >",

        # Mixed with other data types
        "mixed_types": [123, None, "&lt;string&gt;", {"key": "&amp;value"}],
        "mixed_types_expected": [123, None, "<string>", {"key": "&value"}]
    }


@pytest.fixture
def error_case_data() -> Dict[str, Any]:
    """Provide data for testing error conditions.

    Returns:
        Dictionary containing test cases that should trigger errors.
    """
    return {
        # Unhashable set items (should raise TypeError)
        "unhashable_set_content": [["&lt;list&gt;"], {"&amp;dict": "value"}],

        # Malformed but processable data
        "partial_entities": "&lt incomplete entity",
        "mixed_valid_invalid": "&lt;valid&gt; &invalid; &amp;also_valid"
    }
