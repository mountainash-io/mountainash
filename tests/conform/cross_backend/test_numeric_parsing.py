"""Tests for numeric parsing (decimalChar, groupChar, bareNumber) in conform pipeline."""
from __future__ import annotations

import pytest
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


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExactNumericConform:
    def test_decimal_declaration_bypasses_float_and_preserves_schema(self, backend_name, backend_factory):
        from decimal import Decimal
        from mountainash.core.types import BackendCapabilityError

        source = backend_factory.create({"v": ["9,007,199,254,740,993.125", "", None]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(
            name="v", type=UniversalType.NUMBER,
            dtype=ma.DecimalDtype(precision=20, scale=3), group_char=",",
        )])
        rel = ma.relation(source).conform(spec)
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                rel.to_dict()
            return
        result = rel.to_polars()
        assert result["v"].to_list() == [Decimal("9007199254740993.125"), None, None]
        assert result.schema["v"].precision == 20
        assert result.schema["v"].scale == 3
        # Re-conforming a native decimal must not compare it with string sentinels.
        assert ma.relation(result).conform(spec).to_dict() == result.to_dict(as_series=False)

    @pytest.mark.parametrize("action,expected", [
        ("discard_value", ["20", None, None]),
        ("discard_row", ["20", None]),
        ("evolve", ["+00020", "bad", None]),
    ])
    def test_lexical_numeric_actions(self, backend_name, backend_factory, action, expected):
        source = backend_factory.create({"v": ["+00020", "bad", None]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(
            name="v", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER,
        )])
        rel = ma.relation(source).conform(spec, contract={"data_type": action})
        assert rel.to_dict()["v"] == expected

    def test_lexical_numeric_freeze_and_structural_only(self, backend_name, backend_factory):
        from mountainash.conform.errors import SchemaDriftError

        source = backend_factory.create({"v": ["+00020", "bad"]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(
            name="v", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER,
        )])
        with pytest.raises(SchemaDriftError):
            ma.relation(source).conform(spec, contract={"data_type": "freeze"}).to_dict()
        assert ma.relation(source).conform(spec, apply_value_transforms=False).to_dict()["v"] == [
            "+00020", "bad",
        ]

    def test_decimal_fill_is_exact_without_filling_conversion_failures(self, backend_name, backend_factory):
        from decimal import Decimal
        from mountainash.core.types import BackendCapabilityError

        source = backend_factory.create({"v": ["12.345", "", "bad", None]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(
            name="v", type=UniversalType.NUMBER, dtype=ma.DecimalDtype(precision=20, scale=3),
            null_fill=Decimal("9007199254740993.125"),
        )])
        rel = ma.relation(source).conform(spec, contract={"data_type": "discard_value"})
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                rel.to_dict()
            return
        assert rel.to_dict()["v"] == [
            Decimal("12.345"), Decimal("9007199254740993.125"), None, Decimal("9007199254740993.125"),
        ]

    def test_lexical_null_fill_accepts_unbounded_integer(self, backend_name, backend_factory):
        source = backend_factory.create({"v": ["20", None]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(
            name="v", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER,
            null_fill=10**5000 - 1,
        )])
        assert ma.relation(source).conform(spec).to_dict()["v"] == ["20", "9" * 5000]

    def test_portable_dtype_takes_precedence_over_category_storage(self, backend_name, backend_factory):
        source = backend_factory.create({"v": ["+00020", "100"]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(
            name="v", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER,
            categories=["20", "100"],
        )])
        assert ma.relation(source).conform(spec).to_dict()["v"] == ["20", "100"]
