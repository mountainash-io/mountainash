"""Enhanced fixtures configuration - separate file to avoid import issues."""

import pytest
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import uuid
from typing import Dict, List, Any
import random
import string
import math

# Import fixtures with absolute imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fixtures'))

# Now import the fixture modules
from fixtures.realistic_data_fixtures import (
    financial_transactions_data,
    ecommerce_orders_data,
    geographic_data,
    audit_trail_data
)
from fixtures.edge_case_fixtures import (
    numeric_boundary_data,
    string_boundary_data,
    datetime_boundary_data,
    null_and_missing_data
)
from fixtures.data_type_fixtures import (
    comprehensive_data_types,
    temporal_data_comprehensive,
    data_type_factory,
    mixed_type_scenarios
)
