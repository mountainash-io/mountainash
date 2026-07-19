# tests/core/test_expression_provenance_lint.py
from enum import Enum, auto

from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionDef,
    classify_expression_def,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    SubstraitExtension,
    MountainashExtension,
)


class _FK(Enum):
    A = auto()


def test_valid_substrait_catalog():
    d = ExpressionFunctionDef(
        function_key=_FK.A,
        substrait_uri=SubstraitExtension.SCALAR_DATETIME,
        substrait_name="assume_timezone",
        is_extension=False,
    )
    assert classify_expression_def(d) == "substrait"


def test_valid_mountainash_extension():
    d = ExpressionFunctionDef(
        function_key=_FK.A,
        substrait_uri=MountainashExtension.STRING,
        substrait_name="regex_contains",
        is_extension=True,
    )
    assert classify_expression_def(d) == "extension"


def test_invalid_null_uri_null_name():
    d = ExpressionFunctionDef(function_key=_FK.A, substrait_uri=None, substrait_name=None)
    assert classify_expression_def(d) is None


def test_invalid_extension_uri_without_flag():
    # MountainashExtension URI but is_extension left False
    d = ExpressionFunctionDef(
        function_key=_FK.A,
        substrait_uri=MountainashExtension.STRING,
        substrait_name="regex_contains",
        is_extension=False,
    )
    assert classify_expression_def(d) is None


def test_invalid_substrait_uri_with_extension_flag():
    d = ExpressionFunctionDef(
        function_key=_FK.A,
        substrait_uri=SubstraitExtension.SCALAR_DATETIME,
        substrait_name="assume_timezone",
        is_extension=True,
    )
    assert classify_expression_def(d) is None


def test_invalid_missing_name():
    d = ExpressionFunctionDef(
        function_key=_FK.A,
        substrait_uri=SubstraitExtension.SCALAR_DATETIME,
        substrait_name=None,
        is_extension=False,
    )
    assert classify_expression_def(d) is None
