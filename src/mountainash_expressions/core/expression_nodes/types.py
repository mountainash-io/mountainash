

from __future__ import annotations

from typing import TYPE_CHECKING, Union
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from . import (
   ArithmeticExpressionNode, ArithmeticIterableExpressionNode,
   BooleanComparisonExpressionNode, BooleanCollectionExpressionNode, BooleanConstantExpressionNode, BooleanIterableExpressionNode, BooleanUnaryExpressionNode,BooleanIsCloseExpressionNode,BooleanBetweenExpressionNode,

NativeExpressionNode,

    ColumnExpressionNode, LiteralExpressionNode,

    NullExpressionNode, NullConditionalExpressionNode, NullConstantExpressionNode, NullLogicalExpressionNode,

    TemporalExtractExpressionNode, TemporalDiffExpressionNode, TemporalAdditionExpressionNode, TemporalTruncateExpressionNode, TemporalOffsetExpressionNode, TemporalSnapshotExpressionNode,

    StringExpressionNode, StringIterableExpressionNode, StringSuffixExpressionNode, StringPrefixExpressionNode, StringSubstringExpressionNode, StringPatternExpressionNode, StringReplaceExpressionNode, StringPatternReplaceExpressionNode, StringSplitExpressionNode,

    IterableExpressionNode,

    NameAliasExpressionNode,NamePrefixExpressionNode,NameSuffixExpressionNode,NameExpressionNode,
    TypeExpressionNode

    )

    SupportedArithmeticExpressionNodeTypes: TypeAlias = Union[ArithmeticExpressionNode, ArithmeticIterableExpressionNode]

    SupportedBooleanExpressionNodeTypes: TypeAlias = Union[BooleanComparisonExpressionNode, BooleanCollectionExpressionNode, BooleanConstantExpressionNode, BooleanIterableExpressionNode, BooleanUnaryExpressionNode, BooleanIsCloseExpressionNode,BooleanBetweenExpressionNode]
    SupportedCoreExpressionNodeTypes: TypeAlias = Union[ColumnExpressionNode, LiteralExpressionNode]
    SupportedNullExpressionNodeTypes: TypeAlias = Union[NullExpressionNode, NullConditionalExpressionNode, NullConstantExpressionNode, NullLogicalExpressionNode]
    SupportedTemporalExpressionNodeTypes: TypeAlias = Union[    TemporalExtractExpressionNode,TemporalDiffExpressionNode,TemporalAdditionExpressionNode,TemporalTruncateExpressionNode,TemporalOffsetExpressionNode,TemporalSnapshotExpressionNode]
    SupportedStringExpressionNodeTypes: TypeAlias = Union[StringExpressionNode, StringIterableExpressionNode, StringSuffixExpressionNode, StringPrefixExpressionNode, StringSubstringExpressionNode, StringPatternExpressionNode, StringReplaceExpressionNode, StringPatternReplaceExpressionNode, StringSplitExpressionNode]
    SupportedIterableExpressionNodeTypes: TypeAlias = IterableExpressionNode
    SupportedNativeExpressionNodeTypes: TypeAlias = NativeExpressionNode
    SupportedNameExpressionNodeTypes: TypeAlias = Union[NameAliasExpressionNode,NamePrefixExpressionNode,NameSuffixExpressionNode,NameExpressionNode]
    SupportedTypeExpressionNodeTypes: TypeAlias = TypeExpressionNode
