"""W8 safe-location display: rendering table and safe list (design sections 1, 2, 5)."""
from __future__ import annotations

import os
import pathlib

import pytest

from mountainash.core.safe_location import (
    REDACTED,
    display_value,
    raise_os_error,
    raise_safe,
    safe_cause,
    safe_location,
    safe_os_error,
)


class _Trusted(Exception):
    """Stands in for a package-own error built under the W8 rule."""


class _OtherNative(Exception):
    pass


RENDERING_TABLE = [
    # scheme://... and //...: scheme, host, port after the last "@", then the path
    ("https://u:p@h:8443/a/x.csv?sig=s#f", "https://h:8443/a/x.csv"),
    ("https://h.example/a/x.csv", "https://h.example/a/x.csv"),
    ("https://u:pa@ss@h/x", "https://h/x"),  # last "@" of the authority
    ("https://u:p@[::1]:8443/x", "https://[::1]:8443/x"),  # IPv6 with a port
    ("https://h/a@b/c", "https://h/a@b/c"),  # "@" in the path is not userinfo
    ("//u:p@h/x?q=1", "//h/x"),  # network path
    ("https://h?token=s", "https://h"),  # query straight after the authority
    ("https://h#token=s", "https://h"),
    ("https://h/x.csv#access_token=s", "https://h/x.csv"),  # fragment token
    ("s3://AKIA:secret@bucket/key", "s3://bucket/key"),
    ("file:///data/x.csv", "file:///data/x.csv"),
    # any other string that starts with a scheme
    ("s3:bucket/x", REDACTED),
    ("user:pass@host/x", REDACTED),
    ("https:/u:p@h/x", REDACTED),  # single slash, as pathlib leaves it
    ("a:b@c", REDACTED),  # one-letter scheme that is not a drive
    ("mailto:someone@example.com", REDACTED),
    # anything else: unchanged
    ("/data/x.csv", "/data/x.csv"),
    ("data/x.csv", "data/x.csv"),
    ("x.csv?token=s", "x.csv?token=s"),  # a relative path, not a location
    ("C:/d/x.csv", "C:/d/x.csv"),  # Windows drives
    ("C:\\d\\x.csv", "C:\\d\\x.csv"),
    ("", ""),
    # leading C0 controls and spaces are stripped; tab, CR and LF are removed
    (" https://u:p@h/x", "https://h/x"),
    ("\x01\x1f https://u:p@h/x", "https://h/x"),
    ("ht\ttps://u:p@h/\nx", "https://h/x"),
    ("\t\r\n  user:pass@h/x", REDACTED),
    # accepted limits O1-O3 (design "Accepted limits")
    ("https://u:pa?ss@h/x", "https://u:pa"),  # O1: the authority ends at "?"
    ("https:///u:p@h/x", "https:///u:p@h/x"),  # O3: empty authority, the rest is a path
]


@pytest.mark.parametrize(("location", "expected"), RENDERING_TABLE)
def test_rendering_table(location: str, expected: str) -> None:
    assert safe_location(location) == expected


def test_pathlike_is_converted_with_fspath() -> None:
    assert safe_location(pathlib.PurePosixPath("/data/x.csv")) == "/data/x.csv"

    class Like:
        def __fspath__(self) -> str:
            return "https://u:p@h/x?q=1"

    assert safe_location(Like()) == "https://h/x"


@pytest.mark.parametrize("sentinel_shape", [
    "https://SENTU:SENTP@h/x?t=SENTQ#SENTF",
    "//SENTU:SENTP@h/x?t=SENTQ#SENTF",
    "https:/SENTU:SENTP@h/x?t=SENTQ#SENTF",
    "SENTU:SENTP@h/x?t=SENTQ#SENTF",
    "  \thttps://SENTU:SENTP@h/x?t=SENTQ#SENTF",
    "https://SENTU:pa@SENTP@h/x?t=SENTQ#SENTF",
])
def test_output_never_carries_userinfo_query_or_fragment(sentinel_shape: str) -> None:
    shown = safe_location(sentinel_shape)
    assert not any(token in shown for token in ("SENTU", "SENTP", "SENTQ", "SENTF"))


def test_never_raises() -> None:
    for text in ("https://[", "https://h:notaport/x", "\x00", "://", "//", ":", "a:"):
        assert isinstance(safe_location(text), str)


def test_display_value_renders_containers_recursively() -> None:
    value = {
        "https://SENTU:SENTP@h/k?q=SENTQ": ["https://SENTU:SENTP@h/x?q=SENTQ", ("user:pass@h/x", 3)],
        "n": None,
        "b": b"https://SENTU:SENTP@h/x",
        "p": pathlib.PurePosixPath("/data/x.csv"),
    }
    assert display_value(value) == {
        "https://h/k": ["https://h/x", (REDACTED, 3)],
        "n": None,
        "b": "https://h/x",
        "p": "/data/x.csv",
    }


def test_display_value_survives_self_referential_values() -> None:
    looped: list = ["https://SENTU:SENTP@h/x"]
    looped.append(looped)
    shown = display_value(looped)
    assert shown[0] == "https://h/x"
    assert "SENT" not in repr(shown)
    mapping: dict = {}
    mapping["self"] = mapping
    assert "SENT" not in repr(display_value(mapping))


def test_display_value_reduces_unknown_objects_to_the_type_name() -> None:
    class Opaque:
        def __repr__(self) -> str:
            return "https://SENTU:SENTP@h/x"

    assert display_value(Opaque()) == "<Opaque>"


def test_display_value_hides_a_third_party_path_object_that_moved_userinfo() -> None:
    class Moved:
        """Looks like universal_pathlib: userinfo already folded into the path."""

        def __fspath__(self) -> str:
            return "s3://akia:/SENTP@bucket/x.json"

    assert display_value(Moved()) == REDACTED


# --- safe list (design sections 2 and 5, test 3) ------------------------------------------


def test_oserror_keeps_errno_and_strerror_but_not_the_filename() -> None:
    native = FileNotFoundError(2, "No such file or directory", "https://SENTU:SENTP@h/x?t=SENTQ")
    cause = safe_cause(native)
    assert isinstance(cause, FileNotFoundError)
    assert (cause.errno, cause.strerror, cause.filename, cause.filename2) == (
        2, "No such file or directory", None, None,
    )
    assert "SENT" not in str(cause) + repr(cause) + repr(cause.args)


def test_oserror_without_errno_contributes_only_the_class_name() -> None:
    native = PermissionError("SENTQ in free text")
    assert safe_cause(native) is None


def test_oserror_subclass_with_a_strict_constructor_falls_back_to_oserror() -> None:
    class Strict(OSError):
        def __init__(self) -> None:
            super().__init__()

    cause = safe_cause(Strict())  # errno None: nothing safe to chain
    assert cause is None
    strict = Strict()
    strict.errno, strict.strerror = 5, "Input/output error"
    fresh = safe_cause(strict)
    assert type(fresh) is OSError and (fresh.errno, fresh.strerror) == (5, "Input/output error")


def test_non_listed_native_exception_contributes_only_its_class_name() -> None:
    native = _OtherNative("SENTQ in the text")
    assert safe_cause(native) is None


def test_trusted_type_is_matched_exactly() -> None:
    class Subclass(_Trusted):
        pass

    trusted = frozenset({_Trusted})
    own, derived = _Trusted("ours"), Subclass("built elsewhere")
    assert safe_cause(own, trusted) is own
    assert safe_cause(derived, trusted) is None


def test_raise_safe_clears_cause_and_context_of_a_non_listed_exception() -> None:
    def fail() -> None:
        try:
            raise _OtherNative("SENTQ")
        except _OtherNative as native:
            raise_safe(ValueError("fixed message"), native)

    with pytest.raises(ValueError) as caught:
        fail()
    assert caught.value.__cause__ is None and caught.value.__context__ is None


def test_raise_safe_clears_an_ambient_context() -> None:
    def fail() -> None:
        try:
            raise RuntimeError("SENTQ ambient")
        except RuntimeError:
            try:
                raise _OtherNative("SENTQ")
            except _OtherNative as native:
                raise_safe(ValueError("fixed message"), native)

    with pytest.raises(ValueError) as caught:
        fail()
    assert caught.value.__cause__ is None and caught.value.__context__ is None


def test_raise_safe_chains_a_fresh_oserror() -> None:
    def fail() -> None:
        try:
            raise OSError(5, "Input/output error", "SENTQ-name")
        except OSError as native:
            raise_safe(ValueError("fixed message"), native)

    with pytest.raises(ValueError) as caught:
        fail()
    cause = caught.value.__cause__
    assert isinstance(cause, OSError) and cause.filename is None and cause.errno == 5
    assert caught.value.__context__ is None


def test_safe_os_error_shows_the_display_form_of_the_original_input() -> None:
    native = FileNotFoundError(2, "No such file or directory", "https:/SENTU:SENTP@h/x?t=SENTQ")
    error = safe_os_error(native, "https://SENTU:SENTP@h/x?t=SENTQ#SENTF")
    assert isinstance(error, FileNotFoundError)
    assert error.filename == "https://h/x" and error.errno == 2
    assert "SENT" not in str(error) + repr(error) + repr(error.args)


def test_safe_os_error_without_errno() -> None:
    error = safe_os_error(OSError("SENTQ text"), "https://SENTU:SENTP@h/x")
    assert str(error) == "https://h/x: OSError"


def test_raise_os_error_leaves_no_chain() -> None:
    with pytest.raises(FileNotFoundError) as caught:
        try:
            raise FileNotFoundError(2, "No such file or directory", "https:/SENTU:SENTP@h/x")
        except OSError as native:
            raise_os_error(native, os.fspath("https://SENTU:SENTP@h/x"))
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    assert caught.value.filename == "https://h/x"
