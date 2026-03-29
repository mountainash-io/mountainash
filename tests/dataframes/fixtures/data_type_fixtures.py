"""Data type variety fixtures for comprehensive type testing.

This module provides fixtures with comprehensive coverage of different data types,
null handling patterns, and type conversion scenarios commonly encountered in
data processing pipelines.
"""

import pytest
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal, getcontext
from uuid import UUID, uuid4
from pathlib import Path
from enum import Enum
import json
from typing import Dict, List, Any, Optional, Union
import math
import random
# import numpy as np  # Commented out - not in base requirements
import polars as pl
import pandas as pd
import pyarrow as pa


class StatusEnum(Enum):
    """Sample enum for testing enum handling."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


@pytest.fixture(scope="session")
def comprehensive_data_types():
    """Complete data type coverage with realistic values and edge cases."""

    # Set high precision for decimal calculations
    getcontext().prec = 28

    base_date = date(2024, 1, 15)
    base_datetime = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)
    base_time = time(14, 30, 15, 789012)

    return {
        # Numeric Types
        "integers": [
            1, 42, 0, -17, 999999, -999999,
            2**31 - 1,  # Max 32-bit signed int
            -2**31,     # Min 32-bit signed int
            None, 2**63 - 1  # Max 64-bit signed int
        ],

        "floats": [
            0.0, 1.5, -3.14159, 2.718281828, 1e10, 1e-10,
            float('inf'), float('-inf'), float('nan'), None
        ],

        "decimals": [
            Decimal('0.00'), Decimal('123.45'), Decimal('-987.65'),
            Decimal('0.123456789123456789'),  # High precision
            Decimal('999999999.99'), Decimal('1E-15'),
            None, Decimal('3.141592653589793238462643383279')  # Pi with high precision
        ],

        # String Types
        "strings": [
            "Hello World", "", "   ", "Single word",
            "Multi\\nLine\\nString", "Tab\\tSeparated",
            "Unicode: 🚀 Café naïve résumé", "Very long string " * 50,
            None, "Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?"
        ],

        "text_large": [
            "Short",
            "Medium length text with some content that spans multiple words and sentences.",
            " ".join(["Lorem"] * 100),  # 100 words
            " ".join(["Ipsum"] * 1000),  # 1000 words
            None, "", "🌟" * 100  # 100 emoji
        ],

        # Date and Time Types
        "dates": [
            base_date,
            base_date - timedelta(days=365),  # One year ago
            base_date + timedelta(days=365),  # One year from now
            date(2000, 2, 29),  # Leap year
            date(1970, 1, 1),   # Unix epoch
            None,
            date(2038, 1, 19),  # Near 32-bit timestamp limit
            date(1900, 1, 1),   # Century boundary
            date(2100, 2, 28)   # Non-leap century year
        ],

        "datetimes": [
            base_datetime,
            base_datetime.replace(tzinfo=None),  # Naive datetime
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc),  # Y2K
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),  # Unix epoch
            datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc),  # 32-bit limit
            None,
            datetime.now(timezone.utc),  # Current time
            datetime(2024, 3, 10, 2, 30, 0),  # DST transition
            datetime(2024, 12, 31, 23, 59, 59, 999999)  # End of year
        ],

        "times": [
            base_time,
            time(0, 0, 0),      # Midnight
            time(23, 59, 59),   # End of day
            time(12, 0, 0),     # Noon
            time(9, 30, 45, 123456),  # With microseconds
            None,
            time(0, 0, 0, 1),   # 1 microsecond past midnight
            time(23, 59, 59, 999999),  # Last microsecond of day
        ],

        "timedeltas": [
            timedelta(0),                    # Zero duration
            timedelta(days=1),               # One day
            timedelta(hours=1),              # One hour
            timedelta(minutes=30),           # 30 minutes
            timedelta(seconds=45),           # 45 seconds
            timedelta(microseconds=123456),  # Microseconds
            timedelta(weeks=52),             # One year
            None,
            timedelta(days=-1)               # Negative duration
        ],

        # Boolean Types
        "booleans": [
            True, False, None, True, False,
            True, True, False, None, False
        ],

        # UUID Types
        "uuids": [
            uuid4(), uuid4(),
            UUID('550e8400-e29b-41d4-a716-446655440000'),  # Fixed UUID
            UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8'),  # Another fixed UUID
            None,
            uuid4(), uuid4(), uuid4(), None, uuid4()
        ],

        # JSON/Dictionary Types
        "json_data": [
            '{"key": "value"}',
            '{"number": 42, "boolean": true}',
            '[]',  # Empty array
            '{}',  # Empty object
            '{"nested": {"deep": {"very": "deep"}}}',
            '["array", "of", "strings"]',
            '{"mixed": [1, "two", true, null]}',
            None,
            '{"unicode": "🚀💻⚡"}',
            '{"large_number": 9007199254740991}'  # Max safe integer in JSON
        ],

        # Binary/Bytes Types (represented as strings for cross-platform compatibility)
        "binary_data": [
            b"Hello World".hex(),
            b"\\x00\\x01\\x02\\x03".hex(),
            b"Binary data with unicode \\xc3\\xa9".hex(),  # UTF-8 encoded é
            None,
            b"\\xff\\xfe\\xfd".hex(),  # High bytes
            b"".hex(),  # Empty bytes
            b"A" * 1000,  # Large binary data
            b"\\r\\n\\t\\0".hex(),  # Control characters
        ],

        # Enum Types (as strings)
        "status_enum": [
            StatusEnum.ACTIVE,
            StatusEnum.INACTIVE,
            StatusEnum.PENDING,
            StatusEnum.SUSPENDED,
            None,
            StatusEnum.ACTIVE,
            StatusEnum.PENDING,
            StatusEnum.INACTIVE,
            None,
            StatusEnum.SUSPENDED
        ],

        # Array/List Types (as JSON strings)
        "arrays": [
            json.dumps([1, 2, 3, 4, 5]),
            json.dumps(["a", "b", "c"]),
            json.dumps([]),  # Empty array
            json.dumps([1, "two", 3.0, True, None]),  # Mixed types
            json.dumps([[1, 2], [3, 4]]),  # Nested arrays
            None,
            json.dumps([i for i in range(100)]),  # Large array
            json.dumps(["🚀", "🌟", "✨"]),  # Unicode in array
            json.dumps([{"nested": "object"}]),  # Object in array
        ],

        # URL/URI Types
        "urls": [
            "https://www.example.com",
            "http://localhost:8080/api/v1/users",
            "ftp://files.example.com/data.csv",
            "mailto:user@example.com",
            "file:///path/to/local/file.txt",
            None,
            "https://unicode-domain.测试",
            "https://example.com/path?param=value&other=123",
            "ldap://ldap.example.com:389/cn=users,dc=example,dc=com",
        ],

        # File Path Types
        "file_paths": [
            "/home/user/documents/file.txt",
            "C:\\\\Users\\\\User\\\\Documents\\\\file.txt",  # Windows path
            "./relative/path/file.csv",
            "../parent/directory/file.json",
            "~/home/directory/file.log",
            None,
            "/very/long/path/with/many/segments/and/a/very/long/filename.extension",
            "path with spaces/file name.txt",
            "/path/with/unicode/café/résumé.pdf",
        ]
    }


@pytest.fixture(scope="session")
def null_patterns_comprehensive():
    """Comprehensive null value patterns and missing data scenarios."""
    size = 20

    return {
        "no_nulls": list(range(size)),

        "all_nulls": [None] * size,

        "sparse_nulls": [i if i % 10 != 0 else None for i in range(size)],  # Every 10th is null

        "clustered_nulls": [None] * 5 + list(range(10)) + [None] * 5,  # Nulls at start and end

        "alternating_nulls": [i if i % 2 == 0 else None for i in range(size)],

        "mostly_nulls": [None] * 18 + [1, 2],  # Only 2 non-null values

        "single_null": [1] * 9 + [None] + [1] * 10,  # One null in the middle

        "random_nulls": [i if i % 3 != 0 else None for i in range(size)],  # ~33% nulls

        # String null equivalents
        "string_null_equivalents": [
            "value", None, "", "NULL", "null", "None", "N/A",
            "n/a", "NA", "unknown", "undefined", "-", "?",
            " ", "  ", "\\t", "missing", "void", "<null>", "∅"
        ],

        # Numeric null equivalents
        "numeric_null_equivalents": [
            1, 2, None, -1, 0, 999999999, -999999999,
            float('nan'), float('inf'), float('-inf'),
            None, 9999, -9999, 0.0
        ],
    }


@pytest.fixture(scope="session")
def data_type_conversions():
    """Data for testing type conversion scenarios and coercion."""
    return {
        "string_to_numeric": {
            "valid_integers": ["1", "42", "-17", "0", " 123 ", "+456"],
            "valid_floats": ["1.5", "3.14159", "-2.718", "1e5", "1E-3", ".5", "5."],
            "invalid_numeric": ["abc", "12.34.56", "1,234", "1 2 3", "∞", "null"],
            "edge_cases": ["", " ", "NaN", "inf", "-inf", "+inf"]
        },

        "string_to_boolean": {
            "true_values": ["true", "True", "TRUE", "yes", "Yes", "YES", "1", "on", "On"],
            "false_values": ["false", "False", "FALSE", "no", "No", "NO", "0", "off", "Off"],
            "ambiguous": ["maybe", "unknown", "", " ", "2", "-1", "null"]
        },

        "string_to_date": {
            "iso_format": ["2024-01-15", "2024-12-31", "2000-02-29"],  # Leap year
            "us_format": ["01/15/2024", "12/31/2024", "02/29/2000"],
            "european_format": ["15/01/2024", "31/12/2024", "29/02/2000"],
            "named_months": ["15-Jan-2024", "31-Dec-2024", "29-Feb-2000"],
            "invalid_dates": ["2024-02-30", "2024-13-01", "invalid", ""]
        },

        "numeric_precision": {
            "integers": [1, 999999999999999999, -999999999999999999],
            "floats": [1.0, 1.23456789012345678901234567890],
            "decimals": [
                Decimal('1'),
                Decimal('1.23456789012345678901234567890'),
                Decimal('999999999999999999.99999999999999999999')
            ],
            "precision_loss": [
                0.1 + 0.2,  # Should be 0.3 but isn't exactly
                1.0 / 3.0,  # Repeating decimal
                float(Decimal('1.23456789012345678901234567890'))  # Precision loss in conversion
            ]
        },

        "unicode_normalization": {
            "nfc_form": ["café", "naïve", "résumé"],  # Precomposed form
            "nfd_form": [
                "cafe\\u0301",     # e + combining acute accent
                "nai\\u0308ve",    # i + combining diaeresis
                "re\\u0301sume\\u0301"  # e + combining acute accent (both e's)
            ],
            "mixed_form": ["caf\\u00E9", "na\\u00EFve", "r\\u00E9sum\\u00E9"]  # Mixed normalized/precomposed
        }
    }


@pytest.fixture(scope="session")
def temporal_data_comprehensive():
    """Comprehensive temporal data with various patterns and edge cases."""
    base_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    return {
        # Regular time series - hourly for one week
        "hourly_series": {
            "timestamp": [base_dt + timedelta(hours=i) for i in range(168)],  # 24*7 hours
            "value": [100 + (10 * math.sin(i * 0.1)) + random.gauss(0, 2) for i in range(168)]
        },

        # Irregular time series - missing some periods
        "irregular_series": {
            "timestamp": [
                base_dt + timedelta(hours=i)
                for i in range(168)
                if i % 7 != 3  # Skip every 7th hour starting from hour 3
            ],
            "value": [
                100 + (5 * math.sin(i * 0.2)) + random.gauss(0, 1.5)
                for i in range(168)
                if i % 7 != 3
            ]
        },

        # Daily aggregations
        "daily_aggregations": {
            "date": [base_dt.date() + timedelta(days=i) for i in range(30)],
            "daily_sum": [random.uniform(1000, 5000) for _ in range(30)],
            "daily_avg": [random.uniform(100, 200) for _ in range(30)],
            "daily_max": [random.uniform(300, 400) for _ in range(30)],
            "daily_min": [random.uniform(50, 99) for _ in range(30)]
        },

        # Multi-timezone data
        "multi_timezone": {
            "utc_time": [base_dt + timedelta(hours=i) for i in range(24)],
            "eastern_time": [
                (base_dt + timedelta(hours=i)).replace(tzinfo=timezone(timedelta(hours=-5)))
                for i in range(24)
            ],
            "pacific_time": [
                (base_dt + timedelta(hours=i)).replace(tzinfo=timezone(timedelta(hours=-8)))
                for i in range(24)
            ],
            "tokyo_time": [
                (base_dt + timedelta(hours=i)).replace(tzinfo=timezone(timedelta(hours=9)))
                for i in range(24)
            ]
        },

        # Seasonal patterns (monthly data for 3 years)
        "seasonal_monthly": {
            "year_month": [
                f"{2022 + (i // 12)}-{(i % 12) + 1:02d}"
                for i in range(36)
            ],
            "temperature": [
                20 + 15 * math.sin((i % 12) * math.pi / 6) + random.gauss(0, 3)
                for i in range(36)
            ],
            "sales": [
                10000 + 5000 * math.sin((i % 12) * math.pi / 6) +
                2000 * (1.05 ** (i // 12)) +  # Growth trend
                random.gauss(0, 1000)
                for i in range(36)
            ]
        },

        # High-frequency data (per-second for one hour)
        "high_frequency": {
            "timestamp": [base_dt + timedelta(seconds=i) for i in range(3600)],
            "price": [
                100 + sum(random.gauss(0, 0.1) for _ in range(i+1))  # Random walk
                for i in range(3600)
            ],
            "volume": [random.randint(1, 1000) for _ in range(3600)]
        },

        # Business calendar patterns (weekdays only)
        "business_days": {
            "date": [
                d for d in
                [base_dt.date() + timedelta(days=i) for i in range(100)]
                if d.weekday() < 5  # Monday=0, Friday=4
            ],
            "business_metric": [
                random.uniform(1000, 2000) * (1.1 if d.weekday() in [0, 4] else 1.0)  # Monday/Friday boost
                for d in [base_dt.date() + timedelta(days=i) for i in range(100)]
                if d.weekday() < 5
            ]
        }
    }


@pytest.fixture(scope="session")
def complex_nested_data():
    """Complex nested data structures for testing hierarchical data handling."""
    return {
        "json_documents": [
            {
                "id": 1,
                "user": {
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "preferences": {
                        "theme": "dark",
                        "notifications": {
                            "email": True,
                            "sms": False,
                            "push": True
                        }
                    }
                },
                "metadata": {
                    "created_at": "2024-01-15T10:30:00Z",
                    "tags": ["premium", "verified"],
                    "scores": [95, 87, 92]
                }
            },
            {
                "id": 2,
                "user": {
                    "name": "Bob Smith",
                    "email": "bob@example.com",
                    "preferences": {
                        "theme": "light",
                        "notifications": {
                            "email": False,
                            "sms": True,
                            "push": False
                        }
                    }
                },
                "metadata": {
                    "created_at": "2024-01-16T14:22:00Z",
                    "tags": ["basic"],
                    "scores": [78, 81, 85]
                }
            }
        ],

        "hierarchical_categories": [
            {
                "id": 1,
                "name": "Electronics",
                "parent_id": None,
                "children": [
                    {
                        "id": 2,
                        "name": "Computers",
                        "parent_id": 1,
                        "children": [
                            {"id": 3, "name": "Laptops", "parent_id": 2, "children": []},
                            {"id": 4, "name": "Desktops", "parent_id": 2, "children": []}
                        ]
                    },
                    {
                        "id": 5,
                        "name": "Mobile",
                        "parent_id": 1,
                        "children": [
                            {"id": 6, "name": "Smartphones", "parent_id": 5, "children": []},
                            {"id": 7, "name": "Tablets", "parent_id": 5, "children": []}
                        ]
                    }
                ]
            }
        ],

        "variable_schema": [
            # Records with different structures
            {"type": "user", "id": 1, "name": "Alice", "email": "alice@example.com"},
            {"type": "product", "id": 1, "title": "Laptop", "price": 999.99, "category": "Electronics"},
            {"type": "order", "id": 1, "user_id": 1, "product_id": 1, "quantity": 2, "total": 1999.98},
            {
                "type": "event",
                "id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": {"action": "login", "ip": "192.168.1.1"}
            }
        ],

        "arrays_of_objects": [
            {
                "order_id": 1,
                "items": [
                    {"product_id": 101, "name": "Laptop", "quantity": 1, "price": 999.99},
                    {"product_id": 102, "name": "Mouse", "quantity": 2, "price": 25.99}
                ],
                "shipping": {
                    "address": "123 Main St",
                    "method": "standard",
                    "tracking": "TRK123456"
                }
            },
            {
                "order_id": 2,
                "items": [
                    {"product_id": 103, "name": "Monitor", "quantity": 1, "price": 299.99}
                ],
                "shipping": {
                    "address": "456 Oak Ave",
                    "method": "express",
                    "tracking": "TRK789012"
                }
            }
        ]
    }


# Factory fixtures for dynamic data generation
@pytest.fixture
def data_type_factory():
    """Factory for generating data with specific type patterns."""

    def generate_typed_data(
        data_type: str,
        size: int = 10,
        null_rate: float = 0.1,
        **kwargs
    ) -> List[Any]:
        """Generate data of specified type with configurable null rate."""

        import random

        data = []
        for i in range(size):
            if random.random() < null_rate:
                data.append(None)
                continue

            if data_type == "integer":
                min_val = kwargs.get("min_val", -1000)
                max_val = kwargs.get("max_val", 1000)
                data.append(random.randint(min_val, max_val))

            elif data_type == "float":
                min_val = kwargs.get("min_val", -100.0)
                max_val = kwargs.get("max_val", 100.0)
                precision = kwargs.get("precision", 2)
                data.append(round(random.uniform(min_val, max_val), precision))

            elif data_type == "string":
                length = kwargs.get("length", random.randint(3, 20))
                chars = kwargs.get("chars", "abcdefghijklmnopqrstuvwxyz ")
                data.append(''.join(random.choices(chars, k=length)))

            elif data_type == "date":
                start_date = kwargs.get("start_date", date(2020, 1, 1))
                end_date = kwargs.get("end_date", date(2025, 12, 31))
                days_range = (end_date - start_date).days
                random_days = random.randint(0, days_range)
                data.append(start_date + timedelta(days=random_days))

            elif data_type == "datetime":
                start_dt = kwargs.get("start_dt", datetime(2020, 1, 1, tzinfo=timezone.utc))
                end_dt = kwargs.get("end_dt", datetime(2025, 12, 31, tzinfo=timezone.utc))
                seconds_range = int((end_dt - start_dt).total_seconds())
                random_seconds = random.randint(0, seconds_range)
                data.append(start_dt + timedelta(seconds=random_seconds))

            elif data_type == "boolean":
                data.append(random.choice([True, False]))

            elif data_type == "uuid":
                data.append(uuid4())

            elif data_type == "decimal":
                precision = kwargs.get("precision", 4)
                max_digits = kwargs.get("max_digits", 10)
                # Generate a decimal with specified precision
                integer_part = random.randint(1, 10**(max_digits-precision))
                decimal_part = random.randint(0, 10**precision - 1)
                data.append(Decimal(f"{integer_part}.{decimal_part:0{precision}d}"))

            else:
                raise ValueError(f"Unsupported data type: {data_type}")

        return data

    return generate_typed_data


@pytest.fixture
def mixed_type_scenarios():
    """Scenarios where columns have mixed or inconsistent types."""
    return {
        "numeric_mixed": [
            # Mix of int, float, string that could be numeric, and actual strings
            1, 2.5, "3", "4.7", "not_a_number", 5, None, "6.0", float('nan'), "inf"
        ],

        "date_mixed": [
            # Mix of date objects, datetime objects, strings, and invalid dates
            date(2024, 1, 15),
            datetime(2024, 1, 16, 10, 30),
            "2024-01-17",
            "01/18/2024",
            "invalid_date",
            None,
            "2024-01-19T10:30:00Z",
            date(2024, 1, 20)
        ],

        "boolean_mixed": [
            # Various representations of boolean values
            True, False, 1, 0, "true", "false", "yes", "no",
            "Y", "N", None, "maybe", 2, -1
        ],

        "container_mixed": [
            # Mix of different container types serialized as strings
            '{"key": "value"}',  # JSON object
            '[1, 2, 3]',         # JSON array
            'simple_string',      # Plain string
            '123',               # Numeric string
            None,
            '{"nested": {"deep": true}}',  # Nested JSON
            ''                   # Empty string
        ]
    }
