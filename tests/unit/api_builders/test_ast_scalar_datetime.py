"""AST construction tests for datetime API builders."""
import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME


class TestDatetimeExtraction:
    @pytest.mark.parametrize("method,fkey", [
        ("year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_YEAR),
        ("month", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MONTH),
        ("day", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY),
        ("hour", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_HOUR),
        ("minute", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MINUTE),
        ("second", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_SECOND),
        ("millisecond", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MILLISECOND),
        ("microsecond", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MICROSECOND),
        ("nanosecond", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_NANOSECOND),
        ("quarter", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_QUARTER),
        ("day_of_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY_OF_YEAR),
        ("day_of_week", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEKDAY),
        ("week_of_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK),
        ("iso_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_ISO_YEAR),
        ("unix_timestamp", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_UNIX_TIME),
        ("timezone_offset", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_TIMEZONE_OFFSET),
    ])
    def test_extraction(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestDatetimeBooleanExtraction:
    def test_is_leap_year(self):
        expr = ma.col("ts").dt.is_leap_year()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_LEAP_YEAR
        assert len(node.arguments) == 1

    @pytest.mark.xfail(reason="is_dst passes options=None to ScalarFunctionNode, pydantic rejects it")
    def test_is_dst(self):
        expr = ma.col("ts").dt.is_dst()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST
        assert len(node.arguments) == 1


class TestDatetimeAdd:
    @pytest.mark.parametrize("method,fkey", [
        ("add_years", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS),
        ("add_months", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS),
        ("add_days", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS),
        ("add_hours", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS),
        ("add_minutes", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES),
        ("add_seconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS),
        ("add_milliseconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS),
        ("add_microseconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS),
    ])
    def test_add_method(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 5


class TestDatetimeDiff:
    @pytest.mark.parametrize("method,fkey", [
        ("diff_years", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_YEARS),
        ("diff_months", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MONTHS),
        ("diff_days", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_DAYS),
        ("diff_hours", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_HOURS),
        ("diff_minutes", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MINUTES),
        ("diff_seconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_SECONDS),
    ])
    def test_diff_method(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)(ma.col("other_ts"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2


class TestDatetimeTruncation:
    @pytest.mark.parametrize("method,fkey", [
        ("truncate", FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE),
        ("round", FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND),
        ("ceil", FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL),
        ("floor", FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR),
    ])
    def test_truncation(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)("1d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey


class TestDatetimeTimezone:
    def test_to_timezone(self):
        expr = ma.col("ts").dt.to_timezone("UTC")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE

    def test_assume_timezone(self):
        expr = ma.col("ts").dt.assume_timezone("UTC")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.ASSUME_TIMEZONE


class TestDatetimeFormatting:
    def test_strftime(self):
        expr = ma.col("ts").dt.strftime("%Y-%m-%d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.STRFTIME


class TestDatetimeComponents:
    def test_date(self):
        expr = ma.col("ts").dt.date()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.DATE

    def test_time(self):
        expr = ma.col("ts").dt.time()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME


class TestDatetimeCalendar:
    def test_month_start(self):
        expr = ma.col("ts").dt.month_start()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START

    def test_month_end(self):
        expr = ma.col("ts").dt.month_end()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END

    def test_days_in_month(self):
        expr = ma.col("ts").dt.days_in_month()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH


class TestDatetimeNaturalLanguage:
    """Natural language filter methods delegate to comparison builders, not datetime nodes."""

    def test_offset_by(self):
        expr = ma.col("ts").dt.offset_by("1d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY

    def test_within_last(self):
        # within_last returns a gt() comparison, not a datetime-keyed node
        expr = ma.col("ts").dt.within_last("7d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_older_than(self):
        # older_than returns a lt() comparison, not a datetime-keyed node
        expr = ma.col("ts").dt.older_than("30d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_newer_than(self):
        # newer_than is an alias for within_last — returns a gt() comparison
        expr = ma.col("ts").dt.newer_than("1h")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_within_next(self):
        # within_next returns a compound comparison (and_ node at top)
        expr = ma.col("ts").dt.within_next("24h")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_between_last(self):
        # between_last returns a compound comparison (and_ node at top)
        expr = ma.col("ts").dt.between_last("1d", "7d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)


class TestDatetimeAliases:
    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("week", "week_of_year"),
        ("weekday", "day_of_week"),
        ("ordinal_day", "day_of_year"),
    ])
    def test_extraction_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("ts").dt, canonical_method)()._node
        alias = getattr(ma.col("ts").dt, alias_method)()._node
        assert canonical.function_key == alias.function_key

    def test_convert_time_zone_alias(self):
        canonical = ma.col("ts").dt.to_timezone("UTC")._node
        alias = ma.col("ts").dt.convert_time_zone("UTC")._node
        assert canonical.function_key == alias.function_key

    def test_replace_time_zone_alias(self):
        canonical = ma.col("ts").dt.assume_timezone("UTC")._node
        alias = ma.col("ts").dt.replace_time_zone("UTC")._node
        assert canonical.function_key == alias.function_key

    def test_epoch_alias(self):
        canonical = ma.col("ts").dt.unix_timestamp()._node
        alias = ma.col("ts").dt.epoch()._node
        assert canonical.function_key == alias.function_key
