"""Type aliases for expression node types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from . import (
        # Arithmetic
        ArithmeticExpressionNode,
        ArithmeticIterableExpressionNode,
        # Boolean
        BooleanComparisonExpressionNode,
        BooleanCollectionExpressionNode,
        BooleanConstantExpressionNode,
        BooleanIterableExpressionNode,
        BooleanUnaryExpressionNode,
        BooleanIsCloseExpressionNode,
        BooleanBetweenExpressionNode,
        # Core
        ColumnExpressionNode,
        LiteralExpressionNode,
        # Horizontal
        HorizontalExpressionNode,
        # Name
        NameAliasExpressionNode,
        NamePrefixExpressionNode,
        NameSuffixExpressionNode,
        NameExpressionNode,
        # Native
        NativeExpressionNode,
        # Null
        NullExpressionNode,
        NullConditionalExpressionNode,
        NullConstantExpressionNode,
        NullLogicalExpressionNode,
        # String (consolidated)
        StringExpressionNode,
        StringPatternNode,
        StringReplaceNode,
        StringSliceNode,
        StringConcatNode,
        # Temporal
        TemporalExtractExpressionNode,
        TemporalDiffExpressionNode,
        TemporalAdditionExpressionNode,
        TemporalTruncateExpressionNode,
        TemporalOffsetExpressionNode,
        TemporalSnapshotExpressionNode,
        # Type
        TypeExpressionNode,
    )

    # Type aliases for node categories
    SupportedArithmeticExpressionNodeTypes: TypeAlias = Union[
        ArithmeticExpressionNode,
        ArithmeticIterableExpressionNode
    ]

    SupportedBooleanExpressionNodeTypes: TypeAlias = Union[
        BooleanComparisonExpressionNode,
        BooleanCollectionExpressionNode,
        BooleanConstantExpressionNode,
        BooleanIterableExpressionNode,
        BooleanUnaryExpressionNode,
        BooleanIsCloseExpressionNode,
        BooleanBetweenExpressionNode
    ]

    SupportedCoreExpressionNodeTypes: TypeAlias = Union[
        ColumnExpressionNode,
        LiteralExpressionNode
    ]

    SupportedHorizontalExpressionNodeTypes: TypeAlias = HorizontalExpressionNode

    SupportedNameExpressionNodeTypes: TypeAlias = Union[
        NameAliasExpressionNode,
        NamePrefixExpressionNode,
        NameSuffixExpressionNode,
        NameExpressionNode
    ]

    SupportedNativeExpressionNodeTypes: TypeAlias = NativeExpressionNode

    SupportedNullExpressionNodeTypes: TypeAlias = Union[
        NullExpressionNode,
        NullConditionalExpressionNode,
        NullConstantExpressionNode,
        NullLogicalExpressionNode
    ]

    SupportedStringExpressionNodeTypes: TypeAlias = Union[
        StringExpressionNode,
        StringPatternNode,
        StringReplaceNode,
        StringSliceNode,
        StringConcatNode
    ]

    SupportedTemporalExpressionNodeTypes: TypeAlias = Union[
        TemporalExtractExpressionNode,
        TemporalDiffExpressionNode,
        TemporalAdditionExpressionNode,
        TemporalTruncateExpressionNode,
        TemporalOffsetExpressionNode,
        TemporalSnapshotExpressionNode
    ]

    SupportedTypeExpressionNodeTypes: TypeAlias = TypeExpressionNode
