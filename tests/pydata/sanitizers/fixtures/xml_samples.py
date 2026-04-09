"""
Sample XML data and test fixtures for mountainash-utils-xml testing.

This module provides various XML-related test data samples that can be used
across different test modules.
"""

from typing import Dict, List, Any


# Real-world XML entity examples
REAL_WORLD_SAMPLES = {
    "html_content": {
        "input": "&lt;div class=&quot;content&quot;&gt;Hello &amp; welcome!&lt;/div&gt;",
        "expected": "<div class=\"content\">Hello & welcome!</div>"
    },

    "xml_attributes": {
        "input": {
            "&lt;element&gt;": "&quot;value with &apos;quotes&apos;&quot;",
            "normal_attr": "normal_value"
        },
        "expected": {
            "<element>": "\"value with 'quotes'\"",
            "normal_attr": "normal_value"
        }
    },

    "config_data": {
        "input": {
            "database": {
                "connection_string": "server=localhost&amp;database=test",
                "credentials": {
                    "username": "&lt;admin&gt;",
                    "password": "&quot;secret&amp;safe&quot;"
                }
            },
            "features": ["&lt;feature1&gt;", "&amp;feature2", "normal_feature"]
        },
        "expected": {
            "database": {
                "connection_string": "server=localhost&database=test",
                "credentials": {
                    "username": "<admin>",
                    "password": "\"secret&safe\""
                }
            },
            "features": ["<feature1>", "&feature2", "normal_feature"]
        }
    }
}


# Performance testing data
PERFORMANCE_SAMPLES = {
    "large_string_entities": "&lt;" * 5000 + "content" + "&gt;" * 5000,
    "large_string_expected": "<" * 5000 + "content" + ">" * 5000,

    "large_list_data": ["&lt;item_{}&gt;".format(i) for i in range(1000)],
    "large_list_expected": ["<item_{}>".format(i) for i in range(1000)],

    "deep_nested_structure": {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "level5": ["&lt;deep&gt;", "&amp;nested", "&quot;data&quot;"]
                    }
                }
            }
        }
    },
    "deep_nested_expected": {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "level5": ["<deep>", "&nested", "\"data\""]
                    }
                }
            }
        }
    }
}


# Edge case samples
EDGE_CASE_SAMPLES = {
    "mixed_unicode": {
        "input": "&lt;café&gt; &amp; résumé with 中文 characters",
        "expected": "<café> & résumé with 中文 characters"
    },

    "repeated_entities": {
        "input": "&amp;&amp;&amp; &lt;&lt;&lt; &gt;&gt;&gt;",
        "expected": "&&& <<< >>>"
    },

    "entities_in_numbers": {
        "input": "Price: &lt; $100 &amp; &gt; $50",
        "expected": "Price: < $100 & > $50"
    },

    "empty_containers": {
        "empty_string": "",
        "empty_list": [],
        "empty_dict": {},
        "empty_set": set()
    }
}


# Boundary testing data
BOUNDARY_SAMPLES = {
    "single_entity": {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&apos;": "'",
        "&quot;": "\""
    },

    "entity_combinations": [
        ("&lt;&gt;", "<>"),
        ("&amp;&apos;", "&'"),
        ("&quot;&lt;&amp;&gt;&apos;", "\"<&>'"),
    ],

    "no_entities_special_chars": "This has < & > ' \" but no entities",

    "malformed_entities": [
        "&lt without semicolon",
        "&unknown_entity;",
        "&;",  # Just ampersand and semicolon
        "normal &text; here"
    ]
}


def get_sample_data(category: str) -> Dict[str, Any]:
    """Get sample data by category.

    Args:
        category: The category of sample data to retrieve

    Returns:
        Dictionary containing the requested sample data

    Raises:
        KeyError: If the category doesn't exist
    """
    samples_map = {
        "real_world": REAL_WORLD_SAMPLES,
        "performance": PERFORMANCE_SAMPLES,
        "edge_cases": EDGE_CASE_SAMPLES,
        "boundary": BOUNDARY_SAMPLES
    }

    if category not in samples_map:
        raise KeyError(f"Unknown sample category: {category}")

    return samples_map[category]


def get_all_entity_variations() -> List[tuple]:
    """Get all variations of XML entities for comprehensive testing.

    Returns:
        List of tuples containing (input, expected) pairs
    """
    return [
        # Individual entities
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&amp;", "&"),
        ("&apos;", "'"),
        ("&quot;", "\""),

        # Multiple entities
        ("&lt;&gt;", "<>"),
        ("&amp;&apos;&quot;", "&'\""),
        ("&lt;&amp;&gt;", "<&>"),

        # Entities with text
        ("Hello &lt;world&gt;", "Hello <world>"),
        ("Tom &amp; Jerry", "Tom & Jerry"),
        ("Say &quot;hello&quot;", "Say \"hello\""),
        ("It&apos;s working", "It's working"),

        # No entities (should remain unchanged)
        ("Normal text", "Normal text"),
        ("Text with < > & ' \" chars", "Text with < > & ' \" chars"),
        ("", ""),
    ]
