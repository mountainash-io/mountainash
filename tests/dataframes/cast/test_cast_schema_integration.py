"""
Tests for schema integration in cast module.

Tests the new schema_config parameter for dataclass/Pydantic conversion.
"""
import pytest
import polars as pl
from dataclasses import dataclass
from mountainash.dataframes.cast import CastFromPolars
from mountainash.dataframes.schema_config import SchemaConfig, TableSchema, SchemaField


class TestSchemaIntegrationDataclass:
    """Test schema integration with dataclass conversion."""

    def test_auto_derive_exact_match(self):
        """Test auto-derivation with exact column name match."""
        @dataclass
        class User:
            id: int
            name: str

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        # Exact match - should work without any schema_config
        users = CastFromPolars._to_list_of_dataclasses(df, User, auto_derive_schema=False)

        assert len(users) == 3
        assert users[0].id == 1
        assert users[0].name == "Alice"

    def test_auto_derive_fuzzy_match(self):
        """Test auto-derivation with fuzzy column name matching."""
        @dataclass
        class User:
            person_id: int
            person_name: str

        df = pl.DataFrame({
            "personid": [1, 2, 3],
            "personname": ["Alice", "Bob", "Charlie"]
        })

        # Fuzzy matching should match "personid" → "person_id" and "personname" → "person_name"
        users = CastFromPolars._to_list_of_dataclasses(df, User, fuzzy_match_threshold=0.7)

        assert len(users) == 3
        assert users[0].person_id == 1
        assert users[0].person_name == "Alice"

    def test_explicit_schema_config(self):
        """Test explicit schema_config with column rename."""
        @dataclass
        class User:
            id: int
            name: str

        df = pl.DataFrame({
            "user_id": [1, 2, 3],
            "full_name": ["Alice", "Bob", "Charlie"]
        })

        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "full_name": {"rename": "name"}
        })

        users = CastFromPolars._to_list_of_dataclasses(
            df,
            User,
            schema_config=config
        )

        assert len(users) == 3
        assert users[0].id == 1
        assert users[0].name == "Alice"

    def test_schema_with_type_cast(self):
        """Test schema with type casting."""
        @dataclass
        class User:
            id: int
            age: int

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "age": ["25", "30", "35"]  # String ages
        })

        config = SchemaConfig(columns={
            "age": {"cast": "integer"}
        })

        users = CastFromPolars._to_list_of_dataclasses(
            df,
            User,
            schema_config=config
        )

        assert len(users) == 3
        assert users[0].age == 25
        assert isinstance(users[0].age, int)

    def test_disable_auto_derive(self):
        """Test disabling auto-derivation."""
        @dataclass
        class User:
            id: int
            name: str

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        # With auto_derive_schema=False and no config, should still work (no transformations)
        users = CastFromPolars._to_list_of_dataclasses(
            df,
            User,
            auto_derive_schema=False
        )

        assert len(users) == 3
        assert users[0].id == 1

    def test_fuzzy_match_threshold(self):
        """Test custom fuzzy match threshold."""
        @dataclass
        class ProductInfo:
            product_code: int
            product_description: str

        df = pl.DataFrame({
            "productcode": [1, 2, 3],
            "productdescription": ["Widget", "Gadget", "Doohickey"]
        })

        # High similarity should match with reasonable threshold
        users = CastFromPolars._to_list_of_dataclasses(
            df,
            ProductInfo,
            fuzzy_match_threshold=0.7
        )

        assert len(users) == 3
        assert users[0].product_code == 1


class TestSchemaIntegrationBackwards:
    """Test that default behavior doesn't break existing code."""

    def test_simple_case_no_parameters(self):
        """Test that simple case works without any schema parameters."""
        @dataclass
        class User:
            id: int
            name: str

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        # Exact match - disable auto_derive to avoid schema transformations
        users = CastFromPolars._to_list_of_dataclasses(df, User, auto_derive_schema=False)

        assert len(users) == 3
        assert users[0].id == 1
        assert users[0].name == "Alice"
