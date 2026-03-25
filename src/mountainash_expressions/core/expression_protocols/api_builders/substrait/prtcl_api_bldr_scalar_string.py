"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode



class SubstraitScalarStringAPIBuilderProtocol(Protocol):
    """Builder protocol for string operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """



    def lower(self) -> BaseExpressionAPI:
        """Convert to lowercase.

        Substrait: lower
        """
        ...

    def upper(self) -> BaseExpressionAPI:
        """Convert to uppercase.

        Substrait: upper
        """
        ...

    def swapcase(self) -> BaseExpressionAPI:
        """Swap case of characters.

        Substrait: swapcase
        """
        ...

    def capitalize(self) -> BaseExpressionAPI:
        """Capitalize first character.

        Substrait: capitalize
        """
        ...

    def title(self) -> BaseExpressionAPI:
        """Convert to title case (except articles).

        Substrait: title
        """
        ...

    def initcap(self) -> BaseExpressionAPI:
        """Capitalize first character of each word.

        Substrait: initcap
        """
        ...


    def ltrim(
        self,
        characters: Optional[Union[BaseExpressionAPI, ExpressionNode, Any]] = None,
    ) -> BaseExpressionAPI:
        """Remove characters from left side.

        Substrait: ltrim
        """
        ...

    def rtrim(
        self,
        characters: Optional[Union[BaseExpressionAPI, ExpressionNode, Any]] = None,
    ) -> BaseExpressionAPI:
        """Remove characters from right side.

        Substrait: rtrim
        """
        ...

    def trim(
        self,
        characters: Optional[Union[BaseExpressionAPI, ExpressionNode, Any]] = None,
    ) -> BaseExpressionAPI:
        """Remove characters from both sides.

        Substrait: trim
        """
        ...

    def lpad(
        self,
        length: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        characters: Optional[Union[BaseExpressionAPI, ExpressionNode, Any]] = None,
    ) -> BaseExpressionAPI:
        """Left-pad to specified length.

        Substrait: lpad
        """
        ...

    def rpad(
        self,
        length: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        characters: Optional[Union[BaseExpressionAPI, ExpressionNode, Any]] = None,
    ) -> BaseExpressionAPI:
        """Right-pad to specified length.

        Substrait: rpad
        """
        ...

    def center(
        self,
        length: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        character: Optional[Union[BaseExpressionAPI, ExpressionNode, Any]] = None,
    ) -> BaseExpressionAPI:
        """Center string by padding sides.

        Substrait: center
        """
        ...

    def substring(
        self,
        start: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        length: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
    ) -> BaseExpressionAPI:
        """Extract a substring.

        Substrait: substring
        """
        ...



    def left(
        self,
        count: Union[BaseExpressionAPI, ExpressionNode, Any, int],
    ) -> BaseExpressionAPI:
        """Extract count characters from left.

        Substrait: left
        """
        ...

    def right(
        self,
        count: Union[BaseExpressionAPI, ExpressionNode, Any, int],
    ) -> BaseExpressionAPI:
        """Extract count characters from right.

        Substrait: right
        """
        ...

    def replace_slice(
        self,
        start: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        length: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        replacement: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Replace a slice of the string.

        Substrait: replace_slice
        """
        ...

    def contains(
        self,
        substring: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Whether string contains substring.

        Substrait: contains
        """
        ...



    def starts_with(
        self,
        prefix: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Whether string starts with prefix.

        Substrait: starts_with
        """
        ...

    def ends_with(
        self,
        suffix: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Whether string ends with suffix.

        Substrait: ends_with
        """
        ...


    def strpos(
        self,
        substring: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Position of first occurrence of substring (1-indexed).

        Substrait: strpos
        """
        ...

    def count_substring(
        self,
        substring: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Count non-overlapping occurrences of substring.

        Substrait: count_substring
        """
        ...


    def char_length(self) -> BaseExpressionAPI:
        """Return number of characters.

        Substrait: char_length
        """
        ...

    def bit_length(self) -> BaseExpressionAPI:
        """Return number of bits.

        Substrait: bit_length
        """
        ...

    def octet_length(self) -> BaseExpressionAPI:
        """Return number of bytes.

        Substrait: octet_length
        """
        ...

    def concat(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Concatenate strings.

        Substrait: concat
        """
        ...

    def concat_ws(
        self,
        separator: Union[BaseExpressionAPI, ExpressionNode, Any],
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Concatenate strings with separator.

        Substrait: concat_ws
        """
        ...

    def replace(
        self,
        old: Union[BaseExpressionAPI, ExpressionNode, Any],
        new: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Replace all occurrences of substring.

        Substrait: replace
        """
        ...



    def repeat(
        self,
        count: Union[BaseExpressionAPI, ExpressionNode, Any, int],
    ) -> BaseExpressionAPI:
        """Repeat string count times.

        Substrait: repeat
        """
        ...



    def reverse(self) -> BaseExpressionAPI:
        """Reverse the string.

        Substrait: reverse
        """
        ...



    def like(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Match against a LIKE pattern.

        Substrait: like
        """
        ...



    def regexp_match_substring(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        occurrence: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        group: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,

    ) -> BaseExpressionAPI:
        """Extract substring matching regex pattern.

        Substrait: regexp_match_substring
        """
        ...


    def regexp_match_substring_all(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        group: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,
    ) -> BaseExpressionAPI:
        """Extract all substrings that match the given regular expression pattern

        Substrait: regexp_match_substring_all
        """
        ...

    def regexp_strpos(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        occurrence: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,
    ) -> BaseExpressionAPI:
        """"Return the position of an occurrence of the given regular expression pattern in a string.

        Substrait: regexp_strpos
        """
        ...

    def regexp_count_substring(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,
    ) -> BaseExpressionAPI:
        """"Return the number of non-overlapping occurrences of a regular expression pattern in an input string
        Substrait: regexp_count_substring
        """
        ...


    def regexp_replace(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        replacement: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        occurrence: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Replace occurrences matching regex pattern.

        Substrait: regexp_replace
        """
        ...




    def string_split(
        self,
        separator: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Split string by separator.

        Substrait: string_split
        """
        ...

    def regexp_string_split(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Split string by regex pattern.

        Substrait: regexp_string_split
        """
        ...

    # Convenience aliases

    def len(self) -> BaseExpressionAPI:
        """Alias for char_length. String length in characters."""
        ...

    def length(self) -> BaseExpressionAPI:
        """Alias for char_length. String length in characters."""
        ...

    def regex_contains(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], *, case_sensitive: bool = True) -> BaseExpressionAPI:
        """Test if pattern matches. Alias for regexp_match_substring (returns bool)."""
        ...

    def regex_match(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], *, case_sensitive: bool = True) -> BaseExpressionAPI:
        """Alias for regexp_match_substring."""
        ...

    def regex_replace(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], replacement: Union[BaseExpressionAPI, ExpressionNode, Any], case_sensitive: bool = True) -> BaseExpressionAPI:
        """Alias for regexp_replace."""
        ...

    def slice(self, offset: Union[BaseExpressionAPI, ExpressionNode, Any, int], length: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None) -> BaseExpressionAPI:
        """Alias for substring."""
        ...
