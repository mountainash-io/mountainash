"""Tests for numeric parsing (decimalChar, groupChar, bareNumber) in conform pipeline."""
from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

# POLARS_ONLY = ["polars"]
from fixtures.backend_registry import ALL_BACKENDS


# ---------------------------------------------------------------------------
# Unit tests: _build_conform_exprs emits numeric parsing expressions
# ---------------------------------------------------------------------------


class TestBuildConformExprsNumericParsing:
    """Unit tests that the expression builder emits numeric parsing logic."""

    def test_no_parsing_for_default_number(self):
        """No extra expressions when decimalChar/groupChar/bareNumber are defaults."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.NUMBER)],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_decimal_char(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.NUMBER, decimal_char=",")],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_group_char(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER, group_char=".")],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_bare_number_false(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.NUMBER, bare_number=False)],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1


# ---------------------------------------------------------------------------
# Integration tests: decimalChar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDecimalChar:
    def test_comma_decimal(self, backend_name, backend_factory):
        df = backend_factory.create({"price": ["1,50", "2,99", "3,00"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="price", type=UniversalType.NUMBER, decimal_char=",")],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["price"].to_list() == [1.5, 2.99, 3.0]

    def test_default_decimal_char_is_noop(self, backend_name, backend_factory):
        """decimalChar='.' should not emit any replace (it's the default)."""
        df = backend_factory.create({"price": ["1.50", "2.99"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="price", type=UniversalType.NUMBER, decimal_char=".")],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["price"].to_list() == [1.5, 2.99]

    def test_no_decimal_char_is_noop(self, backend_name, backend_factory):
        """decimalChar=None means use default '.' — no replace needed."""
        df = backend_factory.create({"price": ["1.50", "2.99"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="price", type=UniversalType.NUMBER)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["price"].to_list() == [1.5, 2.99]


# ---------------------------------------------------------------------------
# Integration tests: groupChar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestGroupChar:
    def test_dot_thousands_separator(self, backend_name, backend_factory):
        df = backend_factory.create({"amount": ["1.000", "2.500", "10.000"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="amount", type=UniversalType.INTEGER, group_char="."),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["amount"].to_list() == [1000, 2500, 10000]

    def test_comma_thousands_separator(self, backend_name, backend_factory):
        df = backend_factory.create({"amount": ["1,000", "2,500"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="amount", type=UniversalType.INTEGER, group_char=","),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["amount"].to_list() == [1000, 2500]

    def test_space_thousands_separator(self, backend_name, backend_factory):
        df = backend_factory.create({"amount": ["1 000", "2 500"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="amount", type=UniversalType.INTEGER, group_char=" "),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["amount"].to_list() == [1000, 2500]

    def test_group_char_with_number_type(self, backend_name, backend_factory):
        """groupChar also works for NUMBER fields, not just INTEGER."""
        df = backend_factory.create({"val": ["1,234.56", "7,890.12"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="val", type=UniversalType.NUMBER, group_char=","),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1234.56, 7890.12]


# ---------------------------------------------------------------------------
# Integration tests: bareNumber
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestBareNumber:
    def test_strip_currency_prefix(self, backend_name, backend_factory):
        df = backend_factory.create({"price": ["$100", "$200", "$300"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="price", type=UniversalType.NUMBER, bare_number=False)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["price"].to_list() == [100.0, 200.0, 300.0]

    def test_strip_percentage_suffix(self, backend_name, backend_factory):
        df = backend_factory.create({"rate": ["95%", "100%", "50%"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="rate", type=UniversalType.NUMBER, bare_number=False)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["rate"].to_list() == [95.0, 100.0, 50.0]

    def test_strip_currency_prefix_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"qty": ["#10", "#20"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="qty", type=UniversalType.INTEGER, bare_number=False)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["qty"].to_list() == [10, 20]

    def test_bare_number_true_is_default(self, backend_name, backend_factory):
        """bareNumber=True (default) means no stripping."""
        df = backend_factory.create({"val": ["100", "200"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.NUMBER, bare_number=True)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [100.0, 200.0]

    def test_bare_number_none_is_default(self, backend_name, backend_factory):
        """bareNumber=None means default (True) — no stripping."""
        df = backend_factory.create({"val": ["100", "200"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.NUMBER)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [100.0, 200.0]


# ---------------------------------------------------------------------------
# Integration tests: combined numeric parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCombinedNumericParsing:
    def test_european_format(self, backend_name, backend_factory):
        """European: 1.234,56 with groupChar=".", decimalChar=","."""
        df = backend_factory.create({"val": ["1.234,56", "7.890,12"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="val",
                    type=UniversalType.NUMBER,
                    group_char=".",
                    decimal_char=",",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1234.56, 7890.12]

    def test_european_with_currency(self, backend_name, backend_factory):
        """Full European: euro sign + groupChar + decimalChar + bareNumber."""
        df = backend_factory.create({"val": ["€1.234,56"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="val",
                    type=UniversalType.NUMBER,
                    bare_number=False,
                    group_char=".",
                    decimal_char=",",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1234.56]

    def test_group_and_decimal_same_value_uses_correct_order(self, backend_name, backend_factory):
        """groupChar removed first, then decimalChar normalized."""
        df = backend_factory.create({"val": ["1'234.56"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="val",
                    type=UniversalType.NUMBER,
                    group_char="'",
                    decimal_char=".",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        # decimalChar="." is the default, so no replace for it
        assert result["val"].to_list() == [1234.56]
