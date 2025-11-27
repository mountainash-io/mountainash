"""Expression node classes for building expression trees."""

from typing import TYPE_CHECKING

from .base_expression_node import ExpressionNode

from .arithmetic_expression_nodes import (
    ArithmeticExpressionNode,
    ArithmeticIterableExpressionNode,

)

from .boolean_expression_nodes import (
    BooleanExpressionNode,
    BooleanUnaryExpressionNode,
    BooleanComparisonExpressionNode,
    BooleanCollectionExpressionNode,
    BooleanIterableExpressionNode,
    BooleanConstantExpressionNode,
    BooleanIsCloseExpressionNode,
    BooleanBetweenExpressionNode
    # SupportedBooleanExpressionNodeTypes
)

from .core_expression_nodes import (
    ColumnExpressionNode,
    LiteralExpressionNode
)

from .name_expression_nodes import (
    NameAliasExpressionNode,
    NamePrefixExpressionNode,
    NameSuffixExpressionNode,
    NameExpressionNode,
)

from .native_expression_nodes import NativeExpressionNode

from .horizontal_expression_nodes import HorizontalExpressionNode

from .null_expression_nodes import (
    NullExpressionNode,
    NullConstantExpressionNode,
    NullConditionalExpressionNode,
    NullLogicalExpressionNode
)

from .type_expression_nodes import TypeExpressionNode

from .string_expression_nodes import (
    # New consolidated classes
    StringExpressionNode,
    StringPatternNode,
    StringReplaceNode,
    StringSliceNode,
    StringConcatNode,
    # Backwards compatibility aliases (deprecated)
    StringIterableExpressionNode,
    StringSuffixExpressionNode,
    StringPrefixExpressionNode,
    StringSubstringExpressionNode,
    StringSearchExpressionNode,
    StringPatternExpressionNode,
    StringReplaceExpressionNode,
    StringPatternReplaceExpressionNode,
    StringSplitExpressionNode,
)

from .temporal_expression_nodes import (
    TemporalExtractExpressionNode,
    TemporalDiffExpressionNode,
    TemporalAdditionExpressionNode,
    TemporalTruncateExpressionNode,
    TemporalOffsetExpressionNode,
    TemporalSnapshotExpressionNode

)

if TYPE_CHECKING:
    from .types import (
        SupportedArithmeticExpressionNodeTypes,
        SupportedCoreExpressionNodeTypes,
        SupportedBooleanExpressionNodeTypes,
        SupportedNullExpressionNodeTypes,
        SupportedTemporalExpressionNodeTypes,
        SupportedStringExpressionNodeTypes,
        SupportedHorizontalExpressionNodeTypes,
        SupportedNameExpressionNodeTypes,
        SupportedNativeExpressionNodeTypes,
        SupportedTypeExpressionNodeTypes

    )



__all__ = [
    # Base nodes
    "ExpressionNode",
    "ColumnExpressionNode",
    "LiteralExpressionNode",

    "ArithmeticExpressionNode",
    "ArithmeticIterableExpressionNode",

    "ColumnExpressionNode",
    "LiteralExpressionNode",

    "NativeExpressionNode",

    "HorizontalExpressionNode",

    "NameAliasExpressionNode",
    "NamePrefixExpressionNode",
    "NameSuffixExpressionNode",
    "NameExpressionNode",

    "NullExpressionNode",
    "NullConstantExpressionNode",
    "NullConditionalExpressionNode",
    "NullLogicalExpressionNode",


    "BooleanExpressionNode",
    "BooleanUnaryExpressionNode",
    "BooleanComparisonExpressionNode",
    "BooleanCollectionExpressionNode",
    "BooleanIterableExpressionNode",
    "BooleanConstantExpressionNode",
    "BooleanIsCloseExpressionNode",
    "BooleanBetweenExpressionNode",


    # New consolidated string nodes
    "StringExpressionNode",
    "StringPatternNode",
    "StringReplaceNode",
    "StringSliceNode",
    "StringConcatNode",
    # Backwards compatibility aliases (deprecated)
    "StringIterableExpressionNode",
    "StringSuffixExpressionNode",
    "StringPrefixExpressionNode",
    "StringSubstringExpressionNode",
    "StringSearchExpressionNode",
    "StringPatternExpressionNode",
    "StringReplaceExpressionNode",
    "StringPatternReplaceExpressionNode",
    "StringSplitExpressionNode",


    "TemporalExtractExpressionNode",
    "TemporalDiffExpressionNode",
    "TemporalAdditionExpressionNode",
    "TemporalTruncateExpressionNode",
    "TemporalOffsetExpressionNode",
    "TemporalSnapshotExpressionNode",

    "TypeExpressionNode",

]
