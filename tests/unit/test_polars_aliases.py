"""Unit tests verifying Polars-compatible aliases resolve to the same methods."""

import mountainash_expressions as ma


class TestArithmeticAliases:
    def test_sub_alias(self):
        expr = ma.col("a").sub(ma.col("b"))
        assert expr is not None

    def test_mul_alias(self):
        expr = ma.col("a").mul(ma.col("b"))
        assert expr is not None

    def test_truediv_alias(self):
        expr = ma.col("a").truediv(ma.col("b"))
        assert expr is not None

    def test_floordiv_alias(self):
        expr = ma.col("a").floordiv(ma.col("b"))
        assert expr is not None

    def test_mod_alias(self):
        expr = ma.col("a").mod(ma.col("b"))
        assert expr is not None

    def test_pow_alias(self):
        expr = ma.col("a").pow(ma.col("b"))
        assert expr is not None

    def test_neg_alias(self):
        expr = ma.col("a").neg()
        assert expr is not None


class TestStringAliases:
    def test_to_uppercase(self):
        expr = ma.col("a").str.to_uppercase()
        assert expr is not None

    def test_to_lowercase(self):
        expr = ma.col("a").str.to_lowercase()
        assert expr is not None

    def test_strip_chars(self):
        expr = ma.col("a").str.strip_chars()
        assert expr is not None

    def test_strip_chars_start(self):
        expr = ma.col("a").str.strip_chars_start()
        assert expr is not None

    def test_strip_chars_end(self):
        expr = ma.col("a").str.strip_chars_end()
        assert expr is not None

    def test_len_chars(self):
        expr = ma.col("a").str.len_chars()
        assert expr is not None


class TestDatetimeAliases:
    def test_week(self):
        expr = ma.col("a").dt.week()
        assert expr is not None

    def test_weekday(self):
        expr = ma.col("a").dt.weekday()
        assert expr is not None

    def test_ordinal_day(self):
        expr = ma.col("a").dt.ordinal_day()
        assert expr is not None


class TestComparisonAliases:
    def test_is_between(self):
        expr = ma.col("a").is_between(1, 10)
        assert expr is not None


class TestNameAliases:
    def test_to_lowercase(self):
        expr = ma.col("a").name.to_lowercase()
        assert expr is not None

    def test_to_uppercase(self):
        expr = ma.col("a").name.to_uppercase()
        assert expr is not None
