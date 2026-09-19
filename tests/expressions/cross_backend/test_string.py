"""
Cross-backend tests for string operations.

Tests all string operations: upper, lower, trim, length, contains,
starts_with, ends_with, replace, substring.

These tests validate that string operations work consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash.expressions as ma
import mountainash as ma_top
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure
from mountainash.core.types import BackendCapabilityError
from polars.exceptions import ComputeError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    ("operation", "unicode_expected", "ascii_expected"),
    [
        ("lower", ["äbc", "éa"], ["Äbc", "éa"]),
        ("upper", ["ÄBC", "ÉA"], ["ÄBC", "éA"]),
    ],
)
def test_explicit_character_mode_uses_intrinsic_refusal(
    backend_name, backend_factory, select_and_extract, operation, unicode_expected, ascii_expected,
):
    df = backend_factory.create({"s": ["ÄBC", "éA"]}, backend_name)
    ascii_native = backend_name == "ibis-sqlite"
    supported_mode = "ASCII_ONLY" if ascii_native else "UTF8"
    unsupported_mode = "UTF8" if ascii_native else "ASCII_ONLY"
    build = getattr(ma.col("s").str, operation)

    supported = build(char_set=supported_mode)
    expected = ascii_expected if ascii_native else unicode_expected
    assert select_and_extract(df, supported.compile(df), "result", backend_name) == expected

    with pytest.raises(BackendCapabilityError) as error:
        build(char_set=unsupported_mode).compile(df)
    assert error.value.function_key is getattr(FK_STR, operation.upper())
    assert error.value.limitation is None


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("options", [{"occurrence": 2}, {"multiline": "MULTILINE_ENABLED"}])
def test_regex_replacement_requires_implemented_options(
    backend_name, backend_factory, select_and_extract, options,
):
    df = backend_factory.create({"s": ["a1 a2 a3", "a4"]}, backend_name)
    supported = ma.col("s").str.regexp_replace("a[0-9]", "X")
    unsupported = ma.col("s").str.regexp_replace("a[0-9]", "X", **options)

    assert select_and_extract(df, supported.compile(df), "result", backend_name) == ["X X X", "X"]
    with pytest.raises(BackendCapabilityError) as error:
        unsupported.compile(df)
    assert error.value.function_key is FK_STR.REGEXP_REPLACE
    assert error.value.limitation is None


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("operation", ["contains", "starts_with", "ends_with"])
def test_unicode_literal_search_uses_backend_contract(
    backend_name, backend_factory, select_and_extract, operation,
):
    df = backend_factory.create({"s": ["Ä", "ä", None]}, backend_name)
    expression = getattr(ma.col("s").str, operation)("ä", case_sensitive="CASE_INSENSITIVE")

    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as error:
            expression.compile(df)
        assert error.value.function_key is getattr(FK_STR, operation.upper())
        assert error.value.limitation is None
        return

    result = select_and_extract(df, expression.compile(df), "result", backend_name)
    assert result[:2] == [True, True]
    with expect_call_failure(
        when=backend_name in ("pandas", "narwhals-pandas"),
        reason="A null input row yields False rather than propagating null.",
        errors=(AssertionError,),
    ):
        assert result[2] is None


# =============================================================================
# Cross-Backend Tests - Case Conversion
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCaseConversion:
    """Test upper and lower case conversion."""

    def test_str_upper(self, backend_name, backend_factory, collect_expr):
        """Test converting strings to uppercase."""
        data = {"name": ["Alice", "BOB", "Charlie", "DAVID", "eve"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.upper()
        actual = collect_expr(df, expr)

        expected = ["ALICE", "BOB", "CHARLIE", "DAVID", "EVE"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_str_lower(self, backend_name, backend_factory, collect_expr):
        """Test converting strings to lowercase."""
        data = {"name": ["Alice", "BOB", "Charlie", "DAVID", "eve"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.lower()
        actual = collect_expr(df, expr)

        expected = ["alice", "bob", "charlie", "david", "eve"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - Trim Operations
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTrimOperations:
    """Test trim, ltrim, and rtrim operations."""

    def test_str_trim(self, backend_name, backend_factory, collect_expr):
        """Test trimming whitespace from both sides."""
        data = {"text": ["  hello  ", "world  ", "  foo", "bar", "  baz  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.trim()
        actual = collect_expr(df, expr)

        expected = ["hello", "world", "foo", "bar", "baz"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - String Length
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringLength:
    """Test string length operation."""

    def test_str_length(self, backend_name, backend_factory, collect_expr):
        """Test getting string length."""
        data = {"word": ["cat", "hello", "a", "testing", ""]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("word").str.length()
        actual = collect_expr(df, expr)

        expected = [3, 5, 1, 7, 0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - String Contains
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringContains:
    """Test string contains check (returns boolean)."""

    def test_str_contains_hello(self, backend_name, backend_factory):
        """Test filtering rows containing 'hello'."""
        data = {"text": ["hello world", "foo bar", "test", "hello", "world"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.contains("hello")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello world", "hello"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_str_contains_world(self, backend_name, backend_factory):
        """Test filtering rows containing 'world'."""
        data = {"text": ["hello world", "foo bar", "test", "hello", "world"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.contains("world")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello world", "world"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - Starts With / Ends With
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringStartsEndsWith:
    """Test starts_with and ends_with checks."""

    def test_str_starts_with(self, backend_name, backend_factory):
        """Test filtering files starting with 'test'."""
        data = {"filename": ["test.txt", "data.csv", "test.csv", "report.txt", "test.json"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("filename").str.starts_with("test")
        actual = ma_top.relation(df).filter(expr).to_dict()["filename"]
        expected = ["test.txt", "test.csv", "test.json"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_str_ends_with(self, backend_name, backend_factory):
        """Test filtering files ending with '.csv'."""
        data = {"filename": ["test.txt", "data.csv", "test.csv", "report.txt", "test.json"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("filename").str.ends_with(".csv")
        actual = ma_top.relation(df).filter(expr).to_dict()["filename"]
        expected = ["data.csv", "test.csv"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - CASE_INSENSITIVE_ASCII
# =============================================================================
#
# Ibis Polars does not compile the ASCII-folding implementation. Its direct
# refusal is asserted below; the remaining backends verify the result.
_ASCII_FOLD_HONORING_BACKENDS = [b for b in ALL_BACKENDS if b != "ibis-polars"]

# SQLite's native LOWER()/UPPER() are ASCII-only without ICU, so the Unicode
# folding result is verified on the other supported backends. The Ibis SQLite
# refusal is asserted directly below.
_UNICODE_FOLD_KELVIN_HONORING_BACKENDS = [b for b in _ASCII_FOLD_HONORING_BACKENDS if b != "ibis-sqlite"]

# Dynamic search operands are exercised only where the backend implements
# them. Ibis Polars' ASCII-fold refusal remains explicit and separate.
_DYNAMIC_OPERAND_HONORING = {
    "contains": ["polars", "polars-lazy", "ibis-duckdb", "ibis-sqlite", "narwhals-polars"],
    "starts_with": ["polars", "polars-lazy", "ibis-duckdb", "ibis-sqlite"],
    "ends_with": ["polars", "polars-lazy", "ibis-duckdb", "ibis-sqlite"],
}

_KELVIN_DATA = {"text": ["\u212aelvin"]}  # Kelvin Sign (U+212A) + "elvin"

# Null INPUT-row propagation (contains(None-row, "x") -> null, not False)
# cannot be represented by the default boolean storage used by pandas and
# narwhals-pandas. The affected backends are therefore not included in this
# value assertion.
_NULL_INPUT_ROW_BACKENDS = _ASCII_FOLD_HONORING_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _ASCII_FOLD_HONORING_BACKENDS)
class TestCaseInsensitiveAsciiFold:
    """CASE_INSENSITIVE_ASCII on contains/starts_with/ends_with: real,
    ASCII-only case folding (backlog item 75)."""

    def test_contains_ascii_positive(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["HELLO world", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("hello", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [True, False], f"[{backend_name}]"

    def test_starts_with_ascii_positive(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["HELLO world", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with("hello", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [True, False], f"[{backend_name}]"

    def test_ends_with_ascii_positive(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello WORLD", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.ends_with("world", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [True, False], f"[{backend_name}]"

    def test_contains_ascii_empty_input(self, backend_name, backend_factory, collect_expr):
        data = {"text": [""]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("x", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [False], f"[{backend_name}]"

    def test_contains_ascii_empty_substring(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [True], f"[{backend_name}]"

    def test_contains_ascii_all_non_ascii_input(self, backend_name, backend_factory, collect_expr):
        """An input with no ASCII letters at all (only Turkish dotted capital
        I, which must NOT ASCII-fold) never matches an ASCII-lowercase needle."""
        data = {"text": ["\u0130\u0130\u0130"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("i", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [False], f"[{backend_name}]"

    def test_contains_ascii_mixed_input(self, backend_name, backend_factory, collect_expr):
        """Mixed ASCII + non-ASCII: the ASCII letters fold, the Turkish
        dotted capital I in the middle does not."""
        data = {"text": ["Test\u0130ng"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("test", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [True], f"[{backend_name}]"

    def test_contains_ascii_already_lowercase(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["already lowercase"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("lower", case_sensitive="CASE_INSENSITIVE_ASCII")
        assert collect_expr(df, expr) == [True], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _NULL_INPUT_ROW_BACKENDS)
def test_contains_ascii_null_input(backend_name, backend_factory, collect_expr):
    # A second non-null row keeps the input constructible on every backend.
    data = {"text": [None, "anchor"]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("text").str.contains("x", case_sensitive="CASE_INSENSITIVE_ASCII")
    with expect_call_failure(
        when=backend_name in ('pandas', 'narwhals-pandas'),
        reason='A null input row yields False rather than propagating null.',
        errors=(AssertionError,),
    ):
        assert collect_expr(df, expr) == [None, False], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _ASCII_FOLD_HONORING_BACKENDS)
def test_case_insensitive_ascii_kelvin_sign_does_not_fold(backend_name, backend_factory, collect_expr):
    """Discriminator (the actual point of this feature): the Kelvin Sign
    (U+212A) folds to 'k' under full Unicode case-fold but must NOT fold
    under CASE_INSENSITIVE_ASCII. Real cell on every backend except
    ibis-polars (excluded from the parametrize list above)."""
    df = backend_factory.create(_KELVIN_DATA, backend_name)
    expr = ma.col("text").str.contains("kelvin", case_sensitive="CASE_INSENSITIVE_ASCII")
    assert collect_expr(df, expr) == [False], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _UNICODE_FOLD_KELVIN_HONORING_BACKENDS)
def test_case_insensitive_unicode_kelvin_sign_folds(backend_name, backend_factory, collect_expr):
    """Companion discriminator sanity check: CASE_INSENSITIVE's full-Unicode
    fold DOES match the Kelvin Sign — proving CASE_INSENSITIVE_ASCII is
    behaviorally distinct, not just a differently-named alias for the same
    fold. ibis-sqlite excluded — see _UNICODE_FOLD_KELVIN_HONORING_BACKENDS."""
    df = backend_factory.create(_KELVIN_DATA, backend_name)
    expr = ma.col("text").str.contains("kelvin", case_sensitive="CASE_INSENSITIVE")
    assert collect_expr(df, expr) == [True], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize(
    ("method", "backend_name"),
    [(method, backend_name) for method, backends in _DYNAMIC_OPERAND_HONORING.items() for backend_name in backends],
)
def test_case_insensitive_ascii_dynamic_search_operand(method, backend_name, backend_factory, collect_expr):
    """CASE_INSENSITIVE_ASCII folds an expression-valued (column) search
    operand the same way as a literal one, on every cell that already
    supports expression operands for this op."""
    data = (
        {"text": ["HELLO world"], "needle": ["hello"]}
        if method != "ends_with"
        else {"text": ["world HELLO"], "needle": ["hello"]}
    )
    df = backend_factory.create(data, backend_name)
    expr = getattr(ma.col("text").str, method)(ma.col("needle"), case_sensitive="CASE_INSENSITIVE_ASCII")
    assert collect_expr(df, expr) == [True], f"[{backend_name}.{method}]"


class TestCaseInsensitiveIbisRefusals:
    """Only the unsupported case-folding modes refuse; supported neighbors
    remain covered by the ordinary result tests above."""

    @pytest.mark.parametrize("method", ["contains", "starts_with", "ends_with"])
    def test_ascii_fold_refusal_on_ibis_polars(self, method, backend_factory):
        df = backend_factory.create({"text": ["hello"]}, "ibis-polars")
        operation = getattr(FK_STR, method.upper())

        with pytest.raises(BackendCapabilityError) as error:
            getattr(ma.col("text").str, method)(
                "hello", case_sensitive="CASE_INSENSITIVE_ASCII"
            ).compile(df)

        assert error.value.function_key is operation
        assert error.value.limitation is None

    @pytest.mark.parametrize("method", ["contains", "starts_with", "ends_with"])
    def test_unicode_fold_refusal_on_ibis_sqlite(self, method, backend_factory):
        df = backend_factory.create(_KELVIN_DATA, "ibis-sqlite")
        operation = getattr(FK_STR, method.upper())

        with pytest.raises(BackendCapabilityError) as error:
            getattr(ma.col("text").str, method)(
                "kelvin", case_sensitive="CASE_INSENSITIVE"
            ).compile(df)

        assert error.value.function_key is operation
        assert error.value.limitation is None


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _ASCII_FOLD_HONORING_BACKENDS)
def test_case_insensitive_ascii_null_search_operand_propagates_null(
    backend_name,
    backend_factory,
    collect_expr,
):
    """A null search operand produces one null result per input row."""
    data = {"text": ["hello", "world", "test123"]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("text").str.contains(None, case_sensitive="CASE_INSENSITIVE_ASCII")
    assert collect_expr(df, expr) == [None, None, None], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("method", ["contains", "starts_with", "ends_with"])
def test_null_search_operand_preserves_row_count(
    method,
    backend_name,
    backend_factory,
    collect_expr,
):
    """contains/starts_with/ends_with's null-search-operand short-circuit
    (backlog item 80) returned a bare `nw.lit(None)` on the Narwhals
    backend, which has no reference to any column -- narwhals-pandas does
    not broadcast it to the input's row count under `.select()`, silently
    collapsing a 3-row input to a single-row result instead of raising or
    propagating null on every row (backlog item 82, HIGH severity: silent
    row-count corruption in already-shipped code, not a crash). Fixed by
    mirroring `count_substring`'s own null-substring guard in the same
    file: wrapping the null result in
    `nw.when(<receiver>.is_null()).then(...).otherwise(...)` gives it a
    row-shape to broadcast against, independent of the condition's truth
    value."""
    data = {"text": ["banana", "apple", "cherry"]}
    df = backend_factory.create(data, backend_name)
    expr = getattr(ma.col("text").str, method)(None)
    assert collect_expr(df, expr) == [None, None, None], f"[{backend_name}.{method}]"


# =============================================================================
# Cross-Backend Tests - count_substring (backlog item 78)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCountSubstring:
    """count_substring was a hardcoded stub returning 0 unconditionally on
    Ibis and Narwhals (backlog item 78) -- real length-arithmetic
    implementation now matches Polars' own str.count_matches(literal=True)
    semantics exactly (verified empirically) for a literal substring, on
    every backend."""

    def test_count_substring_multiple_occurrences(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["banana", "aaaa", "no vowels here"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("a")
        assert collect_expr(df, expr) == [3, 4, 0], f"[{backend_name}]"

    def test_count_substring_zero_occurrences(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("xyz")
        assert collect_expr(df, expr) == [0, 0], f"[{backend_name}]"

    def test_count_substring_non_overlapping(self, backend_name, backend_factory, collect_expr):
        """Non-overlapping counting: "aaa" contains "aa" once (positions
        0-1) -- the candidate "aa" at position 1-2 overlaps the first
        match's consumed characters and does not count as a second one."""
        data = {"text": ["aaa", "aaaa"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("aa")
        assert collect_expr(df, expr) == [1, 2], f"[{backend_name}]"

    def test_count_substring_empty_substring(self, backend_name, backend_factory, collect_expr):
        """Matches Polars' own count_matches("") convention exactly: one
        match at every one of the len(input) + 1 'gap' positions."""
        data = {"text": ["abc", "", "xx"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("")
        assert collect_expr(df, expr) == [4, 1, 3], f"[{backend_name}]"

    def test_count_substring_null_input(self, backend_name, backend_factory, collect_expr):
        """Anchored with a second real-valued row: DuckDB rejects an
        all-null-typed column at table creation (item 61 precedent) --
        a test-fixture limitation, not a fold-logic concern."""
        data = {"text": [None, "banana"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("a")
        assert collect_expr(df, expr) == [None, 3], f"[{backend_name}]"

    def test_count_substring_null_substring(self, backend_name, backend_factory, collect_expr):
        """A null literal substring propagates to a null result on every
        row -- not a crash (Ibis: len(None)/replace on an untyped null
        scalar; Narwhals: len(None); Polars: count_matches() SchemaError
        on an untyped-null literal) and not a collapse to a single row
        (narwhals-pandas does not broadcast a bare nw.lit(None) with no
        column reference under .select() -- verified empirically)."""
        data = {"text": ["banana", "apple", "cherry"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring(ma.lit(None))
        assert collect_expr(df, expr) == [None, None, None], f"[{backend_name}]"


# A dynamic (column-valued) substring: narwhals (all variants, including
# mountainash's own "pandas" -- routes through the identical narwhals
# expression-system code, item 80 precedent) gates it LITERAL_ONLY --
# narwhals' str.replace_all() pattern argument does not accept an
# expression on ANY dialect (verified empirically), the same root cause as
# sibling replace.substring (NW-STR-03), reused here. ibis-polars is
# excluded too: a dynamic substring crashes with a raw, unenriched
# polars.exceptions.ComputeError -- a pre-existing gap shared with
# replace() (disclosed, not fixed here -- see backlog item
# ibis-polars-dynamic-pattern-raw-error.md).
_COUNT_SUBSTRING_DYNAMIC_HONORING = [
    b for b in ALL_BACKENDS if b not in ("narwhals-polars", "narwhals-pandas", "narwhals-lazy", "pandas", "ibis-polars")
]


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _COUNT_SUBSTRING_DYNAMIC_HONORING)
def test_count_substring_dynamic_operand(backend_name, backend_factory, collect_expr):
    """Needle varies per row (proving per-row evaluation, not a fixed value
    baked in at build time) and includes an empty-substring row (proving the
    dynamic empty-substring guard, not just the literal one)."""
    data = {"text": ["banana", "aaaa", "hello"], "needle": ["a", "aa", ""]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("text").str.count_substring(ma.col("needle"))
    assert collect_expr(df, expr) == [3, 2, 6], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _COUNT_SUBSTRING_DYNAMIC_HONORING)
def test_count_substring_dynamic_operand_regex_metacharacter(backend_name, backend_factory, collect_expr):
    """A dynamic (column-valued) needle containing a regex metacharacter
    ('.') must count LITERAL occurrences, not be interpreted as a regex
    ("any character"). Distinguishes correct literal semantics from a
    naive regex-based fold: "aaaa" has zero literal '.', "a.b.c" has two."""
    data = {"text": ["aaaa", "banana", "a.b.c"], "needle": [".", "a", "."]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("text").str.count_substring(ma.col("needle"))
    assert collect_expr(df, expr) == [0, 3, 2], f"[{backend_name}]"


# =============================================================================
# Cross-Backend Tests - String Replace
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringReplace:
    """Test string replace operation."""

    def test_str_replace_hello(self, backend_name, backend_factory, collect_expr):
        """Test replacing 'hello' with 'hi'."""
        data = {"text": ["hello world", "foo bar", "hello foo", "world bar"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.replace("hello", "hi")
        actual = collect_expr(df, expr)

        expected = ["hi world", "foo bar", "hi foo", "world bar"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_str_replace_bar(self, backend_name, backend_factory, collect_expr):
        """Test replacing 'bar' with 'baz'."""
        data = {"text": ["hello world", "foo bar", "hello foo", "world bar"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.replace("bar", "baz")
        actual = collect_expr(df, expr)

        expected = ["hello world", "foo baz", "hello foo", "world baz"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# Dynamic column-valued replacement is exercised on the Ibis dialects that
# implement it. Ibis Polars' direct refusal is covered separately.
_REPLACE_DYNAMIC_HONORING = ["ibis-duckdb", "ibis-sqlite"]


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", _REPLACE_DYNAMIC_HONORING)
def test_str_replace_dynamic_operand(backend_name, backend_factory, collect_expr):
    """Pattern varies per row (proving per-row evaluation, not a fixed
    value baked in at build time)."""
    data = {"text": ["hello world", "foo bar", "hello foo"], "pattern": ["hello", "foo", "hello"]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("text").str.replace(ma.col("pattern"), "X")
    assert collect_expr(df, expr) == ["X world", "X bar", "X foo"], f"[{backend_name}]"


class TestDynamicPatternIbisPolarsRefusals:
    """Ibis Polars accepts literal patterns but intrinsically refuses a
    column-valued pattern for these operations."""

    @pytest.mark.parametrize(
        ("operation", "build"),
        [
            (FK_STR.REPLACE, lambda: ma.col("text").str.replace(ma.col("pattern"), "X")),
            (FK_STR.COUNT_SUBSTRING, lambda: ma.col("text").str.count_substring(ma.col("pattern"))),
            (FK_STR.REGEXP_REPLACE, lambda: ma.col("text").str.regexp_replace(ma.col("pattern"), "X")),
        ],
        ids=["replace", "count_substring", "regexp_replace"],
    )
    def test_dynamic_pattern_refusal_identifies_the_operation(self, operation, build, backend_factory):
        df = backend_factory.create({"text": ["hello world"], "pattern": ["hello"]}, "ibis-polars")

        with pytest.raises(BackendCapabilityError) as error:
            build().compile(df)

        assert error.value.function_key is operation
        assert error.value.limitation is None




# ibis-polars raw native-error leaks on regexp_match_substring/string_split
# (backlog item 83). Literal path is genuinely unaffected on ibis-polars
# (no existing coverage found there prior to this item — confirmed via
# grep, not assumed) — new regression tests below prove it, not merely
# assume it stays untouched.
def test_regexp_match_substring_literal_pattern_on_ibis_polars(backend_factory, collect_expr):
    df = backend_factory.create({"text": ["abc 123", "no digits", "7 ate 9"]}, "ibis-polars")
    expr = ma.col("text").str.regexp_match_substring(r"\d+")
    assert collect_expr(df, expr) == ["123", None, "7"]


def test_string_split_literal_separator_on_ibis_polars(backend_factory, collect_expr):
    df = backend_factory.create({"text": ["a,b,c", "d,e", "f"]}, "ibis-polars")
    expr = ma.col("text").str.string_split(",")
    assert collect_expr(df, expr) == [["a", "b", "c"], ["d", "e"], ["f"]]


class TestRegexpMatchSplitIbisPolarsRefusals:
    """The supported literal cases above are distinct from these intrinsic
    dynamic-operand refusals."""

    @pytest.mark.parametrize(
        ("operation", "build"),
        [
            (FK_STR.REGEXP_MATCH, lambda: ma.col("text").str.regexp_match_substring(ma.col("pattern"))),
            (FK_STR.SPLIT, lambda: ma.col("text").str.string_split(ma.col("sep"))),
        ],
        ids=["regexp_match_substring", "string_split"],
    )
    def test_dynamic_operand_refusal_identifies_the_operation(self, operation, build, backend_factory):
        df = backend_factory.create(
            {"text": ["hello world"], "pattern": ["hello"], "sep": [" "]},
            "ibis-polars",
        )

        with pytest.raises(BackendCapabilityError) as error:
            build().compile(df)

        assert error.value.function_key is operation
        assert error.value.limitation is None

    def test_string_split_null_separator_still_raises_on_ibis_polars(self, backend_factory, collect_expr):
        """A null literal separator reaches the native Polars schema error."""
        import polars as pl

        df = backend_factory.create({"text": ["a,b,c"]}, "ibis-polars")
        with pytest.raises(pl.exceptions.SchemaError):
            collect_expr(df, ma.col("text").str.string_split(ma.lit(None)))


class TestNullPatternNativeGap:
    """Ibis Polars exposes Polars' concrete failure for null replacement
    patterns."""

    @pytest.mark.parametrize(
        "build",
        [
            lambda: ma.col("text").str.replace(ma.lit(None), "X"),
            lambda: ma.col("text").str.regexp_replace(ma.lit(None), "X"),
        ],
        ids=["replace", "regexp_replace"],
    )
    def test_null_literal_pattern_raises_native_compute_error(self, build, backend_factory, collect_expr):
        df = backend_factory.create({"text": ["hello world"]}, "ibis-polars")
        with expect_call_failure(
            reason="Polars rejects a null replacement pattern.",
            errors=(ComputeError,),
        ):
            collect_expr(df, build())


def test_regexp_strpos_and_count_substring_identify_intrinsic_refusals(backend_factory):
    df = backend_factory.create({"text": ["hello"], "pattern": ["ell"]}, "ibis-polars")
    cases = (
        (FK_STR.REGEXP_STRPOS, lambda: ma.col("text").str.regexp_strpos("ell")),
        (FK_STR.REGEXP_STRPOS, lambda: ma.col("text").str.regexp_strpos(ma.col("pattern"))),
        (FK_STR.REGEXP_COUNT, lambda: ma.col("text").str.regexp_count_substring("ell")),
        (FK_STR.REGEXP_COUNT, lambda: ma.col("text").str.regexp_count_substring(ma.col("pattern"))),
    )
    for operation, build in cases:
        with pytest.raises(BackendCapabilityError) as error:
            build().compile(df)
        assert error.value.function_key is operation
        assert error.value.limitation is None


# =============================================================================
# Cross-Backend Tests - regexp_string_split / string_split (backlog items 85/86)
# =============================================================================
# regexp_string_split was broken on every backend: Polars called
# str.split(pattern) (Polars' str.split is literal-substring-only, not a
# regex primitive) instead of real regex splitting; Ibis was a bare
# `return input` pass-through on all 3 dialects; Narwhals was also a bare
# pass-through, and narwhals has no native regex-split capability at all.
# narwhals.string_split (item 86, non-regex) was also a bare pass-through
# despite narwhals genuinely supporting a literal-separator native split.


def test_regexp_string_split_real_output_on_polars(backend_factory, collect_expr):
    """Polars has no native regex-split primitive — the map_elements
    fallback must actually split on the regex, not the previous silent
    literal-split-that-never-matches no-op."""
    df = backend_factory.create({"text": ["a1b22c", "d333e", "f"]}, "polars")
    expr = ma.col("text").str.regexp_string_split(r"\d+")
    assert collect_expr(df, expr) == [["a", "b", "c"], ["d", "e"], ["f"]]


def test_regexp_string_split_excludes_capture_group_text_on_polars(backend_factory, collect_expr):
    """A pattern with a capturing group must not leak the captured text into
    the result — the Substrait contract is explicit that matched separators
    are excluded from the output, unlike bare re.split's default behavior."""
    df = backend_factory.create({"text": ["a1b22c"]}, "polars")
    expr = ma.col("text").str.regexp_string_split(r"(\d+)")
    assert collect_expr(df, expr) == [["a", "b", "c"]]


def test_regexp_string_split_zero_width_pattern_is_documented_divergence_on_polars(backend_factory, collect_expr):
    """Empty/zero-width-capable patterns diverge from the ibis-duckdb oracle
    — a genuine engine-consolidation difference between DuckDB's regex
    engine and Python's re module (not introduced by this fix), documented
    rather than silently chased for bit-for-bit parity."""
    df = backend_factory.create({"text": ["ab"]}, "polars")
    expr = ma.col("text").str.regexp_string_split(r"a*")
    with expect_call_failure(
        when=True,
        reason='Zero-width-capable regexp split differs from ibis-duckdb on polars.',
        errors=(AssertionError,),
    ):
        assert collect_expr(df, expr) == [["", "b"]]


def test_regexp_string_split_real_output_on_ibis_duckdb(backend_factory, collect_expr):
    """ibis-duckdb's native re_split works correctly, literal or dynamic
    pattern — was previously a silent no-op."""
    df = backend_factory.create({"text": ["a1b22c", "d333e", "f"]}, "ibis-duckdb")
    expr = ma.col("text").str.regexp_string_split(r"\d+")
    assert collect_expr(df, expr) == [["a", "b", "c"], ["d", "e"], ["f"]]


def test_regexp_string_split_literal_pattern_on_ibis_polars(backend_factory, collect_expr):
    """Ibis-Polars supports this literal pattern; dynamic input is tested
    as an explicit refusal below."""
    df = backend_factory.create({"text": ["a1b22c", "d333e", "f"]}, "ibis-polars")
    expr = ma.col("text").str.regexp_string_split(r"\d+")
    assert collect_expr(df, expr) == [["a", "b", "c"], ["d", "e"], ["f"]]


def test_string_split_real_output_on_narwhals_polars(backend_factory, collect_expr):
    """narwhals's plain (non-regex) string_split has a working native
    primitive for a literal separator. Narwhals-pandas requires
    pyarrow-backed storage for its successful result."""
    df = backend_factory.create({"text": ["a,b,c", "d,e", "f"]}, "narwhals-polars")
    expr = ma.col("text").str.string_split(",")
    assert collect_expr(df, expr) == [["a", "b", "c"], ["d", "e"], ["f"]]


class TestRegexpStringSplitRefusals:
    """Unsupported pattern shapes are asserted from the concrete call, not
    a registry or a capability description."""

    @pytest.mark.parametrize("pattern", [r"\d+", ma.col("pattern")], ids=["literal", "dynamic"])
    def test_ibis_sqlite_refusal_identifies_regex_split(self, pattern, backend_factory):
        df = backend_factory.create({"text": ["a1b"], "pattern": [r"\d+"]}, "ibis-sqlite")

        with pytest.raises(BackendCapabilityError) as error:
            ma.col("text").str.regexp_string_split(pattern).compile(df)

        assert error.value.function_key is FK_STR.REGEXP_SPLIT
        assert error.value.limitation is None

    def test_ibis_polars_dynamic_pattern_refusal_identifies_regex_split(self, backend_factory):
        df = backend_factory.create({"text": ["a1b"], "pattern": [r"\d+"]}, "ibis-polars")

        with pytest.raises(BackendCapabilityError) as error:
            ma.col("text").str.regexp_string_split(ma.col("pattern")).compile(df)

        assert error.value.function_key is FK_STR.REGEXP_SPLIT
        assert error.value.limitation is None

    @pytest.mark.parametrize("backend_name", ["narwhals-polars", "narwhals-pandas"])
    def test_narwhals_regex_split_refusal_identifies_the_operation(self, backend_name, backend_factory):
        df = backend_factory.create({"text": ["a1b"]}, backend_name)

        with pytest.raises(BackendCapabilityError) as error:
            ma.col("text").str.regexp_string_split(r"\d+").compile(df)

        assert error.value.function_key is FK_STR.REGEXP_SPLIT
        assert error.value.limitation is None

    @pytest.mark.parametrize("backend_name", ["narwhals-polars", "narwhals-pandas"])
    def test_narwhals_dynamic_separator_refusal_identifies_string_split(self, backend_name, backend_factory):
        df = backend_factory.create({"text": ["a,b,c"], "sep": [","]}, backend_name)

        with pytest.raises(BackendCapabilityError) as error:
            ma.col("text").str.string_split(ma.col("sep")).compile(df)

        assert error.value.function_key is FK_STR.SPLIT
        assert error.value.limitation is None

    def test_narwhals_pandas_string_split_storage_residue(self, backend_factory, collect_expr):
        """The ordinary pandas fixture raises the result-protection error,
        while Arrow-backed pandas storage preserves the supported value."""
        import pandas as pd

        df = backend_factory.create({"text": ["a,b,c"]}, "narwhals-pandas")
        expr = ma.col("text").str.string_split(",")
        with pytest.raises(BackendCapabilityError) as error:
            ma_top.relation(df).select(expr.name.alias("r")).collect()
        assert error.value.function_key is FK_STR.SPLIT

        pyarrow_df = pd.DataFrame({"text": ["a,b,c", "d,e"]}).convert_dtypes(dtype_backend="pyarrow")
        assert collect_expr(pyarrow_df, expr) == [["a", "b", "c"], ["d", "e"]]


# =============================================================================
# Cross-Backend Tests - String Substring
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringSubstring:
    """Test substring extraction."""

    def test_str_substring_first_3(self, backend_name, backend_factory, collect_expr):
        """Test extracting first 3 characters."""
        data = {"text": ["hello", "world", "testing", "foo", "bar"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.substring(0, 3)
        actual = collect_expr(df, expr)

        expected = ["hel", "wor", "tes", "foo", "bar"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_str_substring_from_pos_2(self, backend_name, backend_factory, collect_expr):
        """Test extracting from position 2 to end."""
        data = {"text": ["hello", "world", "testing", "foo", "bar"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.substring(2)
        actual = collect_expr(df, expr)

        expected = ["llo", "rld", "sting", "o", "r"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Integration Tests - Chaining String Operations
# =============================================================================


@pytest.mark.integration
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestChainingStringOperations:
    """Test chaining multiple string operations."""

    def test_chain_trim_and_lowercase(self, backend_name, backend_factory, collect_expr):
        """Test chaining trim -> lowercase."""
        data = {"name": ["  Alice  ", "  BOB  ", "  Charlie  "]}
        df = backend_factory.create(data, backend_name)

        # Chain: trim -> lowercase
        expr = ma.col("name").str.trim().str.lower()
        actual = collect_expr(df, expr)

        expected = ["alice", "bob", "charlie"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_chain_trim_upper_starts_with(self, backend_name, backend_factory):
        """Test chaining trim -> upper -> starts_with filter."""
        data = {"text": ["  hello world  ", "  foo bar  ", "  hello  ", "  goodbye  "]}
        df = backend_factory.create(data, backend_name)

        # Chain: trim -> upper -> check starts with "HELLO"
        expr = ma.col("text").str.trim().str.upper().str.starts_with("HELLO")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["  hello world  ", "  hello  "]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Integration Tests - String with Boolean Filters
# =============================================================================


@pytest.mark.integration
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringWithBooleanFilter:
    """Test combining string operations with boolean filtering."""

    def test_age_and_city_contains(self, backend_name, backend_factory):
        """Test filtering: age > 30 AND city contains 'New'."""
        data = {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "city": ["New York", "Boston", "New York", "Chicago", "Boston"],
        }
        df = backend_factory.create(data, backend_name)

        # Filter: age > 30 AND city contains "New"
        # Charlie: age 35 > 30, city "New York" contains "New" ✓
        # David: age 40 > 30, city "Chicago" does NOT contain "New" ✗
        expr = (ma.col("age") > 30) & ma.col("city").str.contains("New")
        actual = ma_top.relation(df).filter(expr).to_dict()["name"]
        expected = ["Charlie"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_age_and_name_starts_with(self, backend_name, backend_factory):
        """Test filtering: age < 40 AND name starts with 'A' or 'B'."""
        data = {"name": ["Alice", "Bob", "Charlie", "David", "Eve"], "age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Filter: age < 40 AND (name starts with "A" or "B")
        expr_a = ma.col("name").str.starts_with("A")
        expr_b = ma.col("name").str.starts_with("B")
        expr = (ma.col("age") < 40) & (expr_a | expr_b)
        actual = ma_top.relation(df).filter(expr).to_dict()["name"]
        expected = ["Alice", "Bob"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Integration Tests - String with Arithmetic
# =============================================================================


@pytest.mark.integration
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringWithArithmetic:
    """Test combining string operations with arithmetic."""

    def test_string_length_plus_score(self, backend_name, backend_factory, collect_expr):
        """Test getting length of name and adding to score."""
        data = {"name": ["Alice", "Bob", "Charlie", "David"], "score": [85, 92, 78, 95]}
        df = backend_factory.create(data, backend_name)

        # Get length of name and add to score
        expr_len = ma.col("name").str.length()
        expr_result = expr_len + ma.col("score")
        actual = collect_expr(df, expr_result)

        expected = [85 + 5, 92 + 3, 78 + 7, 95 + 5]  # [90, 95, 85, 100]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStringEdgeCases:
    """Test edge cases for string operations."""

    def test_empty_string_operations(self, backend_name, backend_factory, collect_expr):
        """Test operations on empty strings."""
        data = {"text": ["", "a", "", "test", ""]}
        df = backend_factory.create(data, backend_name)

        # Length of empty strings
        expr = ma.col("text").str.length()
        actual = collect_expr(df, expr)

        expected = [0, 1, 0, 4, 0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_case_conversion_on_mixed(self, backend_name, backend_factory, collect_expr):
        """Test case conversion on mixed case strings."""
        data = {"text": ["HeLLo", "WoRLD", "TeSt123", "MiXeD"]}
        df = backend_factory.create(data, backend_name)

        # Uppercase
        expr = ma.col("text").str.upper()
        actual = collect_expr(df, expr)

        expected = ["HELLO", "WORLD", "TEST123", "MIXED"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_trim_no_whitespace(self, backend_name, backend_factory, collect_expr):
        """Test trimming strings with no whitespace."""
        data = {"text": ["hello", "world", "test"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.trim()
        actual = collect_expr(df, expr)

        # Should return unchanged
        expected = ["hello", "world", "test"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_substring_full_length(self, backend_name, backend_factory, collect_expr):
        """Test substring that extracts entire string."""
        data = {"text": ["hello", "world", "test"]}
        df = backend_factory.create(data, backend_name)

        # Extract from position 0 with no length limit (entire string)
        expr = ma.col("text").str.substring(0)
        actual = collect_expr(df, expr)

        expected = ["hello", "world", "test"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_replace_no_match(self, backend_name, backend_factory, collect_expr):
        """Test replace when pattern doesn't exist."""
        data = {"text": ["hello", "world", "test"]}
        df = backend_factory.create(data, backend_name)

        # Try to replace "xyz" which doesn't exist
        expr = ma.col("text").str.replace("xyz", "abc")
        actual = collect_expr(df, expr)

        # Should return unchanged
        expected = ["hello", "world", "test"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_contains_empty_string(self, backend_name, backend_factory):
        """Test contains with empty substring."""
        data = {"text": ["hello", "world", "test"]}
        df = backend_factory.create(data, backend_name)

        # Empty string is contained in all strings
        expr = ma.col("text").str.contains("")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        # All strings contain empty string
        expected = ["hello", "world", "test"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_starts_with_empty_string(self, backend_name, backend_factory):
        """Test starts_with empty string."""
        data = {"text": ["hello", "world", "test"]}
        df = backend_factory.create(data, backend_name)

        # All strings start with empty string
        expr = ma.col("text").str.starts_with("")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello", "world", "test"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_ends_with_empty_string(self, backend_name, backend_factory):
        """Test ends_with empty string."""
        data = {"text": ["hello", "world", "test"]}
        df = backend_factory.create(data, backend_name)

        # All strings end with empty string
        expr = ma.col("text").str.ends_with("")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello", "world", "test"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_replace_multiple_occurrences(self, backend_name, backend_factory, collect_expr):
        """Test replacing multiple occurrences in same string."""
        data = {"text": ["hello hello", "test test test", "world"]}
        df = backend_factory.create(data, backend_name)

        # Replace all occurrences of a word
        expr = ma.col("text").str.replace("test", "exam")
        actual = collect_expr(df, expr)

        # str.replace should replace ALL occurrences (consistent with Python str.replace)
        expected = ["hello hello", "exam exam exam", "world"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_case_sensitivity_contains(self, backend_name, backend_factory):
        """Test case sensitivity in contains operation."""
        data = {"text": ["Hello World", "HELLO WORLD", "hello world", "goodbye"]}
        df = backend_factory.create(data, backend_name)

        # Search for lowercase "hello"
        expr = ma.col("text").str.contains("hello")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        # Should only match lowercase "hello"
        expected = ["hello world"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_substring_beyond_length(self, backend_name, backend_factory, collect_expr):
        """Test substring starting beyond string length."""
        data = {"text": ["hi", "hello", "x"]}
        df = backend_factory.create(data, backend_name)

        # Start at position 10 (beyond all strings)
        expr = ma.col("text").str.substring(10, 5)
        actual = collect_expr(df, expr)

        # Should return empty strings
        expected = ["", "", ""]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_length_with_special_characters(self, backend_name, backend_factory, collect_expr):
        """Test length with special characters and numbers."""
        data = {"text": ["hello!", "123", "test@example.com", "a-b-c"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.length()
        actual = collect_expr(df, expr)

        expected = [6, 3, 16, 5]  # "hello!" = 6, "123" = 3, "test@example.com" = 16, "a-b-c" = 5
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConcatMultiOperand:
    """concat/concat_ws with 2-3 operands and null-containing data — the
    core multi-operand + null_handling fold, before the separator-null
    guard (added in a later commit) and dynamic-separator/operand-type
    coverage (also added later)."""

    def test_concat_two_operands(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", "y", "z"], "b": ["1", "2", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == ["x1", "y2", "z3"], f"[{backend_name}] got {actual}"

    def test_concat_three_operands(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", "y"], "b": ["1", "2"], "c": ["!", "?"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat(ma.col("b"), ma.col("c"))
        actual = collect_expr(df, expr)
        assert actual == ["x1!", "y2?"], f"[{backend_name}] got {actual}"

    def test_concat_single_operand_ignore_nulls_yields_empty_string(self, backend_name, backend_factory, collect_expr):
        """The single-input case is not a `return input`/`return others[0]`
        fast path — the old broken shortcut silently returned the nullable
        operand unchanged instead of routing it through the fold, so a null
        input never became "". Regression coverage for that exact bug."""
        data = {"a": ["x", None]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat()
        actual = collect_expr(df, expr)
        assert actual == ["x", ""], f"[{backend_name}] got {actual}"

    def test_concat_single_operand_accept_nulls_propagates_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", None]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat(null_handling="ACCEPT_NULLS")
        actual = collect_expr(df, expr)
        assert actual == ["x", None], f"[{backend_name}] got {actual}"

    def test_concat_ignore_nulls_default_skips_null_operand(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", None, "z"], "b": ["1", "2", None]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == ["x1", "2", "z"], f"[{backend_name}] got {actual}"

    def test_concat_accept_nulls_propagates_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", None, "z"], "b": ["1", "2", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat(ma.col("b"), null_handling="ACCEPT_NULLS")
        actual = collect_expr(df, expr)
        assert actual == ["x1", None, "z3"], f"[{backend_name}] got {actual}"

    def test_concat_ws_three_operands(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", "y"], "b": ["1", "2"], "c": ["!", "?"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat_ws("-", ma.col("b"), ma.col("c"))
        actual = collect_expr(df, expr)
        assert actual == ["x-1-!", "y-2-?"], f"[{backend_name}] got {actual}"

    def test_concat_ws_skips_null_operand_no_double_separator(self, backend_name, backend_factory, collect_expr):
        """The exact NW-STR-19 trigger scenario the fold eliminates: a
        trailing null operand must not leave a trailing separator.

        A second, fully-populated row anchors ``c``'s dtype as string —
        an all-null column cannot be represented as a table at all on
        ibis-duckdb (rejects NULL-typed columns at creation) and infers
        an untyped ``null`` column on ibis-polars/sqlite that concat_ws
        cannot accept as a string operand; this is a test-fixture
        table-construction limitation, unrelated to the fold under test."""
        data = {"a": ["p", "x"], "b": ["q", "y"], "c": [None, "z"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat_ws("-", ma.col("b"), ma.col("c"))
        actual = collect_expr(df, expr)
        assert actual == ["p-q", "x-y-z"], f"[{backend_name}] got {actual}"

    def test_concat_ws_all_null_row_yields_empty_string(self, backend_name, backend_factory, collect_expr):
        """The all-null-row trigger scenario the fold eliminates: an
        all-null row must yield '', not NULL, on every dialect.

        A second, fully-populated row anchors both columns' dtype as
        string — see the note on the sibling test above for why an
        all-null column cannot be used as-is on ibis."""
        data = {"a": [None, "x"], "b": [None, "y"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat_ws("-", ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == ["", "x-y"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConcatWsNullSeparator:
    """A NULL separator must propagate to the whole result unconditionally
    (matching DuckDB's own native CONCAT_WS convention), even in the 0/1
    present-operand rows where the bare fold never actually touches `sep`."""

    def test_null_separator_column_propagates_regardless_of_operand_count(
        self, backend_name, backend_factory, collect_expr
    ):
        # Row 1: sep null, 2 present operands (fold would touch sep if unguarded).
        # Row 2: sep present, 2 present operands (control — must NOT be affected).
        # Row 3: sep null, 1 present + 1 null operand (fold would never touch
        #        sep without the guard -- this is the exact case round 3 found).
        data = {
            "sep": [None, "-", None],
            "a": ["x", "x", "x"],
            "b": ["y", "y", None],
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat_ws(ma.col("sep"), ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [None, "x-y", None], f"[{backend_name}] got {actual}"

    def test_literal_none_separator_propagates_and_does_not_crash(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["x", "y"], "b": ["1", "2"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat_ws(None, ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [None, None], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConcatWsDynamicSeparator:
    """The fold supports a genuinely dynamic (column-expression) separator
    on every backend — no LITERAL_ONLY gate is needed anywhere."""

    def test_column_expression_separator_varies_per_row(self, backend_name, backend_factory, collect_expr):
        data = {"sep": ["-", "_", "."], "a": ["x", "y", "z"], "b": ["1", "2", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat_ws(ma.col("sep"), ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == ["x-1", "y_2", "z.3"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConcatOperandType:
    """A non-string operand is a native caller error, not a mountainash
    coercion/validation feature — Substrait types every concat/concat_ws
    operand as string/varchar, with no implicit-cast contract."""

    def test_concat_numeric_operand_raises_native_error(self, backend_name, backend_factory):
        data = {"a": ["x", "y"], "n": [1, 2]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").str.concat(ma.col("n"))
        with pytest.raises(
            Exception
        ):  # native TypeError/InvalidOperationError/SignatureValidationError — backend-specific, not mountainash's
            ma.relation(df).select(expr.name.alias("r")).to_dict()
