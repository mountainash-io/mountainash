"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Protocol, Optional

from mountainash.core.types import ExpressionT


class SubstraitScalarStringExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar string operations.

    Auto-generated from Substrait string extension.
    Function type: scalar
    """


    def lower(self, input: ExpressionT, /, char_set: Optional[str] = None) -> ExpressionT:
        """Transform the string to lower case characters. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: lower
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def upper(self, input: ExpressionT, /, char_set: Optional[str] = None) -> ExpressionT:
        """Transform the string to upper case characters. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: upper
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def swapcase(self, input: ExpressionT, /, char_set: Optional[str] = None) -> ExpressionT:
        """Transform the string's lowercase characters to uppercase and uppercase characters to lowercase. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: swapcase
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def capitalize(self, input: ExpressionT, /, char_set: Optional[str] = None) -> ExpressionT:
        """Capitalize the first character of the input string. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: capitalize
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def title(self, input: ExpressionT, /, char_set: Optional[str] = None) -> ExpressionT:
        """Converts the input string into titlecase. Capitalize the first character of each word in the input string except for articles (a, an, the). Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: title
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def initcap(self, input: ExpressionT, /, char_set: Optional[str] = None) -> ExpressionT:
        """Capitalizes the first character of each word in the input string, including articles, and lowercases the rest. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: initcap
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def ltrim(self, input: ExpressionT, /, characters: ExpressionT) -> ExpressionT:
        """Remove any occurrence of the characters from the left side of the string. If no characters are specified, spaces are removed.

        Substrait: ltrim
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def rtrim(self, input: ExpressionT, /, characters: ExpressionT) -> ExpressionT:
        """Remove any occurrence of the characters from the right side of the string. If no characters are specified, spaces are removed.

        Substrait: rtrim
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def trim(self, input: ExpressionT, /, characters: ExpressionT) -> ExpressionT:
        """Remove any occurrence of the characters from the left and right sides of the string. If no characters are specified, spaces are removed.

        Substrait: trim
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def lpad(self, input: ExpressionT, /, length: ExpressionT, characters: ExpressionT) -> ExpressionT:
        """Left-pad the input string with the string of 'characters' until the specified length of the string has been reached. If the input string is longer than 'length', remove characters from the right-side to shorten it to 'length' characters. If the string of 'characters' is longer than the remaining 'length' needed to be filled, only pad until 'length' has been reached. If 'characters' is not specified, the default value is a single space.

        Substrait: lpad
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def rpad(self, input: ExpressionT, /, length: ExpressionT, characters: ExpressionT) -> ExpressionT:
        """Right-pad the input string with the string of 'characters' until the specified length of the string has been reached. If the input string is longer than 'length', remove characters from the left-side to shorten it to 'length' characters. If the string of 'characters' is longer than the remaining 'length' needed to be filled, only pad until 'length' has been reached. If 'characters' is not specified, the default value is a single space.

        Substrait: rpad
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def center(self, input: ExpressionT, /, length: ExpressionT, character: ExpressionT, padding: Optional[str] = None) -> ExpressionT:
        """Center the input string by padding the sides with a single `character` until the specified `length` of the string has been reached. By default, if the `length` will be reached with an uneven number of padding, the extra padding will be applied to the right side. The side with extra padding can be controlled with the `padding` option.
Behavior is undefined if the number of characters passed to the `character` argument is not 1.

        Substrait: center
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def substring(self, input: ExpressionT, /, start: ExpressionT, length: ExpressionT, negative_start: Optional[str] = None) -> ExpressionT:
        """Extract a substring of a specified `length` starting from position `start`. A `start` value of 1 refers to the first characters of the string.  When `length` is not specified the function will extract a substring starting from position `start` and ending at the end of the string.
The `negative_start` option applies to the `start` parameter. `WRAP_FROM_END` means the index will start from the end of the `input` and move backwards. The last character has an index of -1, the second to last character has an index of -2, and so on. `LEFT_OF_BEGINNING` means the returned substring will start from the left of the first character.  A `start` of -1 will begin 2 characters left of the the `input`, while a `start` of 0 begins 1 character left of the `input`.

        Substrait: substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def left(self, input: ExpressionT, /, count: ExpressionT) -> ExpressionT:
        """Extract `count` characters starting from the left of the string.

        Substrait: left
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def right(self, input: ExpressionT, /, count: ExpressionT) -> ExpressionT:
        """Extract `count` characters starting from the right of the string.

        Substrait: right
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def replace_slice(self, input: ExpressionT, /, start: ExpressionT, length: ExpressionT, replacement: ExpressionT) -> ExpressionT:
        """Replace a slice of the input string.  A specified 'length' of characters will be deleted from the input string beginning at the 'start' position and will be replaced by a new string.  A start value of 1 indicates the first character of the input string. If start is negative or zero, or greater than the length of the input string, a null string is returned. If 'length' is negative, a null string is returned.  If 'length' is zero, inserting of the new string occurs at the specified 'start' position and no characters are deleted. If 'length' is greater than the input string, deletion will occur up to the last character of the input string.

        Substrait: replace_slice
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def contains(self, input: ExpressionT, /, substring: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Whether the `input` string contains the `substring`.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: contains
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def starts_with(self, input: ExpressionT, /, substring: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Whether the `input` string starts with the `substring`.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: starts_with
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def ends_with(self, input: ExpressionT, /, substring: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Whether `input` string ends with the substring.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: ends_with
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def strpos(self, input: ExpressionT, /, substring: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Return the position of the first occurrence of a string in another string. The first character of the string is at position 1. If no occurrence is found, 0 is returned.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: strpos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def count_substring(self, input: ExpressionT, /, substring: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Return the number of non-overlapping occurrences of a substring in an input string.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: count_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def char_length(self, input: ExpressionT, /) -> ExpressionT:
        """Return the number of characters in the input string.  The length includes trailing spaces.

        Substrait: char_length
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def bit_length(self, input: ExpressionT, /) -> ExpressionT:
        """Return the number of bits in the input string.

        Substrait: bit_length
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def octet_length(self, input: ExpressionT, /) -> ExpressionT:
        """Return the number of bytes in the input string.

        Substrait: octet_length
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def concat(self, input: ExpressionT, /, null_handling: Optional[str] = None) -> ExpressionT:
        """Concatenate strings.
The `null_handling` option determines whether or not null values will be recognized by the function. If `null_handling` is set to `IGNORE_NULLS`, null value arguments will be ignored when strings are concatenated. If set to `ACCEPT_NULLS`, the result will be null if any argument passed to the concat function is null.

        Substrait: concat
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def concat_ws(self, separator: ExpressionT, string_arguments: ExpressionT) -> ExpressionT:
        """Concatenate strings together separated by a separator.

        Substrait: concat_ws
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def replace(self, input: ExpressionT, /, substring: ExpressionT, replacement: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Replace all occurrences of the substring with the replacement string.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: replace
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def repeat(self, input: ExpressionT, /, count: ExpressionT) -> ExpressionT:
        """Repeat a string `count` number of times.

        Substrait: repeat
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def reverse(self, input: ExpressionT, /) -> ExpressionT:
        """Returns the string in reverse order.

        Substrait: reverse
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def like(self, input: ExpressionT, /, match: ExpressionT, case_sensitivity: Optional[str] = None) -> ExpressionT:
        """Are two strings like each other.
The `case_sensitivity` option applies to the `match` argument.

        Substrait: like
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def regexp_match_substring(self, input: ExpressionT, /, pattern: ExpressionT, position: Optional[int] = None, occurrence: Optional[int] = None, group: Optional[int] = None, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> ExpressionT:
        """Extract a substring that matches the given regular expression pattern. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The occurrence of the pattern to be extracted is specified using the `occurrence` argument. Specifying `1` means the first occurrence will be extracted, `2` means the second occurrence, and so on. The `occurrence` argument should be a positive non-zero integer. The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. The regular expression capture group can be specified using the `group` argument. Specifying `0` will return the substring matching the full regular expression. Specifying `1` will return the substring matching only the first capture group, and so on. The `group` argument should be a non-negative integer.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the occurrence value is out of range, the position value is out of range, or the group value is out of range.

        Substrait: regexp_match_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

#     def regexp_match_substring(self, input: SupportedExpressions, pattern: SupportedExpressions, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> SupportedExpressions:
#         """Extract a substring that matches the given regular expression pattern. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The first occurrence of the pattern from the beginning of the string is extracted. It returns the substring matching the full regular expression.
# The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
# Behavior is undefined if the regex fails to compile.

#         Substrait: regexp_match_substring
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
#         """
#         ...

    def regexp_match_substring_all(self, input: ExpressionT, /, pattern: ExpressionT, position: Optional[int] = None, group: Optional[int] = None, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> ExpressionT:
        """Extract all substrings that match the given regular expression pattern. This will return a list of extracted strings with one value for each occurrence of a match. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. The regular expression capture group can be specified using the `group` argument. Specifying `0` will return substrings matching the full regular expression. Specifying `1` will return substrings matching only the first capture group, and so on. The `group` argument should be a non-negative integer.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the position value is out of range, or the group value is out of range.

        Substrait: regexp_match_substring_all
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def regexp_strpos(self, input: ExpressionT, /, pattern: ExpressionT, position: Optional[int] = None, occurrence: Optional[int] = None, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> ExpressionT:
        """Return the position of an occurrence of the given regular expression pattern in a string. The first character of the string is at position 1. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. Which occurrence to return the position of is specified using the `occurrence` argument. Specifying `1` means the position first occurrence will be returned, `2` means the position of the second occurrence, and so on. The `occurrence` argument should be a positive non-zero integer. If no occurrence is found, 0 is returned.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the occurrence value is out of range, or the position value is out of range.

        Substrait: regexp_strpos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...


    def regexp_count_substring(self, input: ExpressionT, /, pattern: ExpressionT, position: Optional[int] = None, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> ExpressionT:
        """Return the number of non-overlapping occurrences of a regular expression pattern in an input string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile or the position value is out of range.

        Substrait: regexp_count_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

#     def regexp_count_substring(self, input: SupportedExpressions, pattern: SupportedExpressions, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> SupportedExpressions:
#         """Return the number of non-overlapping occurrences of a regular expression pattern in an input string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The match starts at the first character of the input string.
# The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
# Behavior is undefined if the regex fails to compile.

#         Substrait: regexp_count_substring
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
#         """
#         ...


    def regexp_replace(self, input: ExpressionT, /, pattern: ExpressionT, replacement: ExpressionT, position: Optional[int] = None, occurrence: Optional[int] = None, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> ExpressionT:
        """Search a string for a substring that matches a given regular expression pattern and replace it with a replacement string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github .io/icu/userguide/strings/regexp.html). The occurrence of the pattern to be replaced is specified using the `occurrence` argument. Specifying `1` means only the first occurrence will be replaced, `2` means the second occurrence, and so on. Specifying `0` means all occurrences will be replaced. The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. The replacement string can capture groups using numbered backreferences.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines.  This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the replacement contains an illegal back-reference, the occurrence value is out of range, or the position value is out of range.

        Substrait: regexp_replace
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

#     def regexp_replace(self, input: SupportedExpressions, pattern: SupportedExpressions, replacement: SupportedExpressions, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> SupportedExpressions:
#         """Search a string for a substring that matches a given regular expression pattern and replace it with a replacement string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github .io/icu/userguide/strings/regexp.html). The replacement string can capture groups using numbered backreferences. All occurrences of the pattern will be replaced. The search for matches start at the first character of the input.
# The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines.  This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
# Behavior is undefined if the regex fails to compile or the replacement contains an illegal back-reference.

#         Substrait: regexp_replace
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
#         """
#         ...


    def string_split(self, input: ExpressionT, /, separator: ExpressionT) -> ExpressionT:
        """Split a string into a list of strings, based on a specified `separator` character.

        Substrait: string_split
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_string_split(self, input: ExpressionT, /, pattern: ExpressionT, case_sensitivity: Optional[str] = None, multiline: Optional[bool] = None, dotall: Optional[bool] = None) -> ExpressionT:
        """Split a string into a list of strings, based on a regular expression pattern.  The substrings matched by the pattern will be used as the separators to split the input string and will not be included in the resulting list. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html).
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.

        Substrait: regexp_string_split
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...
