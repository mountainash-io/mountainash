"""Comprehensive realistic data fixtures for enhanced test coverage.

This module provides fixtures that simulate real-world business scenarios,
edge cases, and complex data patterns commonly found in production systems.
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import uuid
from typing import Dict, List, Any
import random
import string


@pytest.fixture(scope="session")
def financial_transactions_data():
    """Realistic financial transaction dataset with multiple currencies and complex scenarios."""
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    return {
        "transaction_id": [str(uuid.uuid4()) for _ in range(100)],
        "account_id": [f"ACC_{i:06d}" for i in random.choices(range(1000, 9999), k=100)],
        "transaction_date": [
            base_date + timedelta(days=random.randint(0, 365), 
                                hours=random.randint(0, 23),
                                minutes=random.randint(0, 59))
            for _ in range(100)
        ],
        "amount": [
            Decimal(str(random.uniform(-5000.00, 10000.00))).quantize(Decimal('0.01'))
            for _ in range(100)
        ],
        "currency": random.choices(["USD", "EUR", "GBP", "JPY", "CAD"], k=100, weights=[40, 25, 15, 10, 10]),
        "transaction_type": random.choices(
            ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "REFUND"], 
            k=100, weights=[30, 25, 20, 20, 5]
        ),
        "description": [
            random.choice([
                "ATM Withdrawal",
                "Online Purchase - Amazon",
                "Salary Deposit",
                "Utility Payment - Electric",
                "Restaurant - Downtown Cafe",
                "Gas Station - Shell",
                "Bank Transfer",
                "Insurance Payment",
                "Grocery Store - Whole Foods",
                "Subscription - Netflix"
            ]) for _ in range(100)
        ],
        "merchant_id": [
            random.choice([None, f"MER_{i:04d}"]) 
            for i in random.choices(range(1, 500), k=100)
        ],
        "is_reconciled": [random.choice([True, False, None]) for _ in range(100)],
        "created_at": [datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 1440)) for _ in range(100)],
        "updated_at": [datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60)) for _ in range(100)]
    }


@pytest.fixture(scope="session") 
def ecommerce_orders_data():
    """E-commerce order data with complex customer and product relationships."""
    customers = [f"CUST_{i:06d}" for i in range(1, 501)]
    products = [f"PROD_{i:04d}" for i in range(1, 201)]
    
    return {
        "order_id": [f"ORD_{i:08d}" for i in range(1, 201)],
        "customer_id": random.choices(customers, k=200),
        "order_date": [
            datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
            for _ in range(200)
        ],
        "product_id": random.choices(products, k=200),
        "quantity": [random.randint(1, 10) for _ in range(200)],
        "unit_price": [
            round(random.uniform(5.99, 999.99), 2) for _ in range(200)
        ],
        "discount_pct": [
            round(random.uniform(0, 0.5), 3) if random.random() < 0.3 else 0.0
            for _ in range(200)
        ],
        "shipping_cost": [
            round(random.uniform(0, 29.99), 2) if random.random() < 0.8 else 0.0
            for _ in range(200)
        ],
        "tax_amount": [
            round(random.uniform(0, 50), 2) for _ in range(200)
        ],
        "order_status": random.choices(
            ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"],
            k=200, weights=[5, 10, 25, 50, 8, 2]
        ),
        "payment_method": random.choices(
            ["CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "BANK_TRANSFER", "CASH_ON_DELIVERY"],
            k=200, weights=[45, 20, 20, 10, 5]
        ),
        "shipping_address": [
            random.choice([
                "123 Main St, New York, NY 10001",
                "456 Oak Ave, Los Angeles, CA 90210", 
                "789 Pine Rd, Chicago, IL 60601",
                "321 Elm St, Houston, TX 77001",
                "654 Maple Dr, Phoenix, AZ 85001"
            ]) for _ in range(200)
        ],
        "customer_notes": [
            random.choice([None, "Leave at door", "Ring doorbell", "Fragile item", ""])
            for _ in range(200)
        ]
    }


@pytest.fixture(scope="session")
def time_series_data():
    """Time series data with irregular intervals and missing values."""
    base_timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = []
    values = []
    
    current_time = base_timestamp
    for i in range(1000):
        # Irregular intervals - sometimes missing periods
        if random.random() > 0.05:  # 5% chance of missing data point
            timestamps.append(current_time)
            # Simulate sensor readings with noise and trends
            base_value = 100 + (i * 0.1) + (10 * random.random()) - 5
            if random.random() < 0.02:  # 2% chance of outlier
                base_value *= random.choice([0.1, 0.2, 5.0, 10.0])
            values.append(round(base_value, 3))
        
        # Irregular time intervals
        minutes_increment = random.choice([15, 30, 60, 120, 180])  # 15min to 3hrs
        current_time += timedelta(minutes=minutes_increment)
    
    return {
        "timestamp": timestamps,
        "sensor_value": values,
        "sensor_id": [f"SENSOR_{random.randint(1, 10):02d}" for _ in range(len(timestamps))],
        "location": [
            random.choice(["Factory_A", "Factory_B", "Warehouse_C", "Office_D"])
            for _ in range(len(timestamps))
        ],
        "quality_flag": [
            random.choice(["GOOD", "WARNING", "ERROR", "MAINTENANCE"])
            for _ in range(len(timestamps))
        ]
    }


@pytest.fixture(scope="session")
def hierarchical_org_data():
    """Hierarchical organizational data with parent-child relationships."""
    departments = [
        ("Engineering", None, "ENG"),
        ("Frontend", "Engineering", "FE"),
        ("Backend", "Engineering", "BE"),
        ("DevOps", "Engineering", "DO"),
        ("Sales", None, "SAL"),
        ("Enterprise Sales", "Sales", "ES"),
        ("SMB Sales", "Sales", "SMS"),
        ("Marketing", None, "MKT"),
        ("Digital Marketing", "Marketing", "DM"),
        ("Content Marketing", "Marketing", "CM"),
        ("HR", None, "HR"),
        ("Recruiting", "HR", "REC"),
        ("People Ops", "HR", "PO")
    ]
    
    employees = []
    for i in range(150):
        dept_info = random.choice(departments)
        employee = {
            "employee_id": f"EMP_{i:05d}",
            "full_name": random.choice([
                "Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince",
                "Eve Wilson", "Frank Miller", "Grace Lee", "Henry Davis",
                "Iris Chen", "Jack Thompson", "Karen White", "Leo Martinez"
            ]),
            "email": f"employee{i}@company.com",
            "department": dept_info[0],
            "parent_department": dept_info[1], 
            "dept_code": dept_info[2],
            "job_title": random.choice([
                "Software Engineer", "Senior Engineer", "Staff Engineer",
                "Engineering Manager", "Sales Representative", "Account Executive",
                "Marketing Specialist", "HR Business Partner", "Data Analyst"
            ]),
            "hire_date": date(2020, 1, 1) + timedelta(days=random.randint(0, 1460)),
            "salary": random.randint(50000, 200000),
            "manager_id": f"EMP_{random.randint(0, min(i, 20)):05d}" if i > 0 else None,
            "office_location": random.choice([
                "San Francisco, CA", "New York, NY", "Austin, TX", "Remote", "London, UK"
            ]),
            "employment_status": random.choice(["ACTIVE", "INACTIVE", "ON_LEAVE"]),
            "performance_rating": random.choice([1, 2, 3, 4, 5, None])
        }
        employees.append(employee)
    
    return {key: [emp[key] for emp in employees] for key in employees[0].keys()}


@pytest.fixture(scope="session")
def geographic_data():
    """Geographic data with addresses, coordinates, and location hierarchies."""
    locations = [
        # US Cities
        ("New York", "NY", "US", 40.7128, -74.0060, "10001"),
        ("Los Angeles", "CA", "US", 34.0522, -118.2437, "90210"),
        ("Chicago", "IL", "US", 41.8781, -87.6298, "60601"),
        ("Houston", "TX", "US", 29.7604, -95.3698, "77001"),
        ("Phoenix", "AZ", "US", 33.4484, -112.0740, "85001"),
        # International Cities
        ("London", "ENG", "GB", 51.5074, -0.1278, "SW1A 1AA"),
        ("Paris", "IDF", "FR", 48.8566, 2.3522, "75001"),
        ("Tokyo", "TKY", "JP", 35.6762, 139.6503, "100-0001"),
        ("Sydney", "NSW", "AU", -33.8688, 151.2093, "2000"),
        ("Toronto", "ON", "CA", 43.6532, -79.3832, "M5H 2N2")
    ]
    
    addresses = []
    for _ in range(500):
        city_info = random.choice(locations)
        # Add some coordinate noise for realistic variation
        lat_noise = random.uniform(-0.1, 0.1)
        lon_noise = random.uniform(-0.1, 0.1)
        
        address = {
            "address_id": f"ADDR_{len(addresses):06d}",
            "street_number": random.randint(1, 9999),
            "street_name": random.choice([
                "Main St", "Oak Ave", "Pine Rd", "Elm St", "Maple Dr",
                "First Ave", "Second St", "Park Pl", "Broadway", "Market St"
            ]),
            "city": city_info[0],
            "state_province": city_info[1],
            "country_code": city_info[2],
            "postal_code": city_info[5],
            "latitude": round(city_info[3] + lat_noise, 6),
            "longitude": round(city_info[4] + lon_noise, 6),
            "timezone": random.choice([
                "America/New_York", "America/Los_Angeles", "America/Chicago",
                "Europe/London", "Europe/Paris", "Asia/Tokyo",
                "Australia/Sydney", "America/Toronto"
            ]),
            "is_business_address": random.choice([True, False]),
            "building_type": random.choice([
                "Residential", "Commercial", "Industrial", "Mixed-Use", None
            ])
        }
        addresses.append(address)
    
    return {key: [addr[key] for addr in addresses] for key in addresses[0].keys()}


@pytest.fixture(scope="session")
def user_behavior_data():
    """User behavior and event data for analytics scenarios."""
    user_ids = [f"USER_{i:08d}" for i in range(1, 10001)]
    session_types = ["web", "mobile_app", "api", "bot"]
    event_types = [
        "page_view", "click", "form_submit", "purchase", "login",
        "logout", "search", "download", "share", "error"
    ]
    
    events = []
    for _ in range(5000):
        session_start = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        event = {
            "event_id": str(uuid.uuid4()),
            "user_id": random.choice(user_ids),
            "session_id": str(uuid.uuid4()) if random.random() < 0.1 else f"SESS_{random.randint(1, 50000):08d}",
            "timestamp": session_start,
            "event_type": random.choice(event_types),
            "page_url": random.choice([
                "/", "/products", "/about", "/contact", "/login", 
                "/dashboard", "/settings", "/profile", "/cart", "/checkout"
            ]),
            "referrer_url": random.choice([
                None, "https://google.com", "https://facebook.com",
                "https://twitter.com", "direct", "email"
            ]),
            "user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
                "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0"
            ]),
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "country": random.choice(["US", "GB", "CA", "AU", "DE", "FR", "JP"]),
            "device_type": random.choice(["desktop", "mobile", "tablet"]),
            "session_duration_seconds": random.randint(30, 3600) if random.random() < 0.7 else None,
            "conversion_value": round(random.uniform(0, 500), 2) if random.random() < 0.05 else None
        }
        events.append(event)
    
    return {key: [event[key] for event in events] for key in events[0].keys()}


@pytest.fixture(scope="session")
def data_quality_issues_data():
    """Dataset with intentional data quality issues for testing validation and cleaning."""
    return {
        # Duplicate detection scenarios
        "customer_id": [1, 2, 3, 3, 4, 5, 5, 6, 7, 8],  # Duplicates: 3, 5
        "email": [
            "alice@example.com",
            "bob@example.com", 
            "charlie@example.com",
            "charlie@example.com",  # Exact duplicate
            "diana@example.com",
            "eve@example.com",
            "EVE@EXAMPLE.COM",  # Case difference
            "frank@example.com",
            "grace@example.com",
            "henry@example.com"
        ],
        
        # Inconsistent formatting
        "phone_number": [
            "(555) 123-4567",
            "555-234-5678",
            "5552345678",
            "+1-555-345-6789",
            "555.456.7890",
            None,
            "(555) 567-8901",
            "invalid_phone",
            "555-678-9012",
            ""
        ],
        
        # Missing and inconsistent data
        "first_name": [
            "Alice", "Bob", "Charlie", "Charlie", None,
            "Eve", "Eve", "Frank", "", "Henry"
        ],
        "last_name": [
            "Johnson", "Smith", "Brown", "BROWN", "Wilson",
            None, "Miller", "Davis", "Lee", "Martinez"
        ],
        
        # Inconsistent date formats and invalid dates
        "registration_date": [
            "2024-01-15",
            "01/15/2024", 
            "15-Jan-2024",
            "2024-01-15T10:30:00Z",
            None,
            "invalid_date",
            "2024-02-30",  # Invalid date
            "2024-01-15",
            "",
            "2024-01-15"
        ],
        
        # Outliers and invalid values
        "age": [25, 30, 35, 35, -5, 150, 28, 999, 42, None],  # Negative, too high values
        
        # Inconsistent categories
        "status": [
            "Active", "active", "ACTIVE", "Active", "Inactive",
            "inactive", "PENDING", "pending", "Suspended", None
        ]
    }


@pytest.fixture(scope="session")
def audit_trail_data():
    """Audit trail data for testing change tracking and compliance scenarios."""
    entities = ["USER", "ORDER", "PRODUCT", "CUSTOMER", "PAYMENT"]
    operations = ["CREATE", "UPDATE", "DELETE", "VIEW"]
    
    audit_records = []
    for i in range(1000):
        entity_type = random.choice(entities)
        entity_id = f"{entity_type}_{random.randint(1, 10000):06d}"
        
        audit_record = {
            "audit_id": f"AUDIT_{i:08d}",
            "entity_type": entity_type,
            "entity_id": entity_id, 
            "operation": random.choice(operations),
            "user_id": f"USER_{random.randint(1, 100):06d}",
            "timestamp": datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            ),
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "API Client v1.2.3", "Internal System"
            ]),
            "changes": random.choice([
                '{"status": {"old": "pending", "new": "active"}}',
                '{"email": {"old": "old@example.com", "new": "new@example.com"}}',
                '{"price": {"old": 99.99, "new": 89.99}}',
                None  # For VIEW operations
            ]),
            "success": random.choice([True, True, True, False]),  # Mostly successful
            "error_message": random.choice([
                None, "Permission denied", "Validation error", "Network timeout"
            ]) if random.random() < 0.1 else None,
            "session_id": f"SESS_{random.randint(1, 1000):06d}",
            "compliance_flag": random.choice([True, False, None])
        }
        audit_records.append(audit_record)
    
    return {key: [record[key] for record in audit_records] for key in audit_records[0].keys()}


# Fixture factory for generating custom datasets
@pytest.fixture
def data_generator():
    """Factory fixture for generating custom test datasets on demand."""
    
    def _generate_dataset(
        records: int = 100,
        include_nulls: float = 0.1,
        include_duplicates: float = 0.05,
        data_types: List[str] = None
    ) -> Dict[str, List[Any]]:
        """
        Generate a custom dataset with specified characteristics.
        
        Args:
            records: Number of records to generate
            include_nulls: Proportion of null values (0-1)
            include_duplicates: Proportion of duplicate records (0-1)
            data_types: List of data types to include ['string', 'int', 'float', 'date', 'bool']
        """
        if data_types is None:
            data_types = ['string', 'int', 'float', 'date', 'bool']
        
        dataset = {}
        
        # Generate columns based on requested data types
        for dtype in data_types:
            if dtype == 'string':
                dataset['text_column'] = [
                    ''.join(random.choices(string.ascii_letters, k=random.randint(3, 15)))
                    if random.random() > include_nulls else None
                    for _ in range(records)
                ]
                
            elif dtype == 'int':
                dataset['integer_column'] = [
                    random.randint(-1000, 1000) 
                    if random.random() > include_nulls else None
                    for _ in range(records)
                ]
                
            elif dtype == 'float':
                dataset['float_column'] = [
                    round(random.uniform(-100.0, 100.0), 3)
                    if random.random() > include_nulls else None
                    for _ in range(records)
                ]
                
            elif dtype == 'date':
                base_date = date(2020, 1, 1)
                dataset['date_column'] = [
                    base_date + timedelta(days=random.randint(0, 1460))
                    if random.random() > include_nulls else None
                    for _ in range(records)
                ]
                
            elif dtype == 'bool':
                dataset['boolean_column'] = [
                    random.choice([True, False])
                    if random.random() > include_nulls else None
                    for _ in range(records)
                ]
        
        # Add some duplicate records if requested
        if include_duplicates > 0:
            num_duplicates = int(records * include_duplicates)
            duplicate_indices = random.sample(range(max(1, records-1)), num_duplicates)
            
            for idx in duplicate_indices:
                for column in dataset:
                    if dataset[column][idx-1] is not None:
                        dataset[column][idx] = dataset[column][idx-1]
        
        return dataset
    
    return _generate_dataset