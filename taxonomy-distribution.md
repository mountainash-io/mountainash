# Taxonomy Distribution Report

## Overview

- **Total Concepts**: 200
- **Number of Taxonomies**: 11
- **Average Concepts per Taxonomy**: 18.2

## Distribution Summary

| Category | TaxonomyID | Count | Percentage | Status |
|----------|-----------|-------|------------|--------|
| Expression API | EXAPI | 30 | 15.0% | ✅ |
| Expression AST & System | EXAST | 24 | 12.0% | ✅ |
| Type System & Schema | TSPEC | 22 | 11.0% | ✅ |
| Relation API | RELAP | 20 | 10.0% | ✅ |
| Relation AST & System | REAST | 20 | 10.0% | ✅ |
| DAG & DataPackage | DAGPK | 18 | 9.0% | ✅ |
| Expression Backends | EXBKD | 16 | 8.0% | ✅ |
| Pipeline Framework | PIPE | 14 | 7.0% | ✅ |
| Foundation Concepts | FOUND | 12 | 6.0% | ✅ |
| Core Infrastructure | CORE | 12 | 6.0% | ✅ |
| Relation Backends | RELBK | 12 | 6.0% | ✅ |

## Visual Distribution

```
Expression API          ███████  30 ( 15.0%)
Expression AST & System ██████  24 ( 12.0%)
Type System & Schema    █████  22 ( 11.0%)
Relation API            █████  20 ( 10.0%)
Relation AST & System   █████  20 ( 10.0%)
DAG & DataPackage       ████  18 (  9.0%)
Expression Backends     ████  16 (  8.0%)
Pipeline Framework      ███  14 (  7.0%)
Foundation Concepts     ███  12 (  6.0%)
Core Infrastructure     ███  12 (  6.0%)
Relation Backends       ███  12 (  6.0%)
```

## Balance Analysis

### ✅ No Over-Represented Categories

All categories are under the 30% threshold. Good balance!

## Category Details

### Expression API (EXAPI)

**Count**: 30 concepts (15.0%)

**Concepts**:

- 25. col Function
- 26. lit Function
- 27. Expression Building
- 28. BaseExpressionAPI
- 29. BooleanExpressionAPI
- 30. Fluent Expression Chain
- 31. Operator Overloading
- 32. String Namespace
- 33. Datetime Namespace
- 34. Struct Namespace
- 35. List Namespace
- 36. Name Namespace
- 37. NamespaceDescriptor
- 38. when Function
- 39. coalesce Function
- *...and 15 more*

### Expression AST & System (EXAST)

**Count**: 24 concepts (12.0%)

**Concepts**:

- 55. ExpressionNode Base
- 56. ScalarFunctionNode
- 57. FieldReferenceNode
- 58. LiteralNode
- 59. CastNode
- 60. IfThenNode
- 61. SingularOrListNode
- 62. WindowFunctionNode
- 63. WindowSpec
- 64. WindowBound
- 65. OverNode
- 66. Function Key Enums
- 67. FKEY Substrait Prefix
- 68. FKEY Mountainash Prefix
- 69. ExpressionFunctionDef
- *...and 9 more*

### Type System & Schema (TSPEC)

**Count**: 22 concepts (11.0%)

**Concepts**:

- 147. TypeSpec
- 148. FieldSpec
- 149. FieldConstraints
- 150. UniversalType Enum
- 151. Type Bridge
- 152. Backend Type Mapping
- 153. Foreign Keys
- 154. ForeignKeyReference
- 155. Custom Type Registry
- 156. Type Converters
- 157. Frictionless Standard
- 158. Table Schema
- 159. Schema Extraction
- 160. DataFrame Extraction
- 161. Dataclass Extraction
- *...and 7 more*

### Relation API (RELAP)

**Count**: 20 concepts (10.0%)

**Concepts**:

- 95. relation Factory
- 96. Relation Class
- 97. RelationBase
- 98. Filter Operation
- 99. Sort Operation
- 100. Head Fetch Operation
- 101. Select Project Operation
- 102. Join Operation
- 103. Group By Operation
- 104. GroupedRelation
- 105. Aggregation on Groups
- 106. Set Operations
- 107. concat Function
- 108. Conform Operation
- 109. Unnest Operation
- *...and 5 more*

### Relation AST & System (REAST)

**Count**: 20 concepts (10.0%)

**Concepts**:

- 115. RelationNode Base
- 116. ReadRelNode
- 117. ProjectRelNode
- 118. FilterRelNode
- 119. AggregateRelNode
- 120. JoinRelNode
- 121. FetchRelNode
- 122. SortRelNode
- 123. SetRelNode
- 124. ExtensionRelNode
- 125. SourceRelNode
- 126. RefRelNode
- 127. ResourceReadRelNode
- 128. Relation Protocols
- 129. UnifiedRelationVisitor
- *...and 5 more*

### DAG & DataPackage (DAGPK)

**Count**: 18 concepts (9.0%)

**Concepts**:

- 169. RelationDAG
- 170. Named Relations
- 171. dag.ref Method
- 172. Dependency Edges
- 173. Constraint Edges
- 174. Two-Edge Graph Model
- 175. Topological Collection
- 176. dag.collect Method
- 177. ref_resolver Parameter
- 178. DataPackage
- 179. DataResource
- 180. TableDialect
- 181. from_descriptor Method
- 182. to_relation_dag Method
- 183. Resource Overrides
- *...and 3 more*

### Expression Backends (EXBKD)

**Count**: 16 concepts (8.0%)

**Concepts**:

- 79. PolarsExpressionSystem
- 80. NarwhalsExpressionSystem
- 81. IbisExpressionSystem
- 82. Polars Expr Compilation
- 83. Narwhals Expr Compilation
- 84. Ibis Expr Compilation
- 85. Backend Composition
- 86. Multiple Inheritance
- 87. Substrait Compile Files
- 88. Extension Compile Files
- 89. Known Expr Limitations
- 90. Expression Testing
- 91. Cross-Backend Parametrize
- 92. xfail Known Quirks
- 93. Arguments vs Options
- *...and 1 more*

### Pipeline Framework (PIPE)

**Count**: 14 concepts (7.0%)

**Concepts**:

- 187. PipelineBuilder
- 188. step Decorator
- 189. source Function
- 190. PipelineSpec
- 191. StepDefinition
- 192. StepContext
- 193. StepResult
- 194. SimplePipelineRunner
- 195. ParamSpec
- 196. Parameter Binding
- 197. relation.params Method
- 198. ParamsRelNode
- 199. PipelineStepRelNode
- 200. fold_params Function

### Foundation Concepts (FOUND)

**Count**: 12 concepts (6.0%)

**Concepts**:

- 1. Python Type Hints
- 2. Protocol Classes
- 3. Pydantic Models
- 4. DataFrames
- 5. Polars Library
- 6. Pandas Library
- 7. Apache Arrow
- 8. SQL Databases
- 9. Lazy Evaluation
- 10. Method Chaining
- 11. Visitor Pattern
- 12. Directed Acyclic Graph

### Core Infrastructure (CORE)

**Count**: 12 concepts (6.0%)

**Concepts**:

- 13. Constants Module
- 14. Backend Enum
- 15. Backend System Enum
- 16. Backend Detection
- 17. DataFrame Type Guards
- 18. MountainashDtype
- 19. Lazy Import System
- 20. Factory Pattern
- 21. BaseFactoryMixin
- 22. Operation Enums
- 23. JoinType Enum
- 24. SetType Enum

### Relation Backends (RELBK)

**Count**: 12 concepts (6.0%)

**Concepts**:

- 135. PolarsRelationSystem
- 136. NarwhalsRelationSystem
- 137. IbisRelationSystem
- 138. LazyFrame Operations
- 139. Narwhals Portability
- 140. Ibis SQL Compilation
- 141. Cross-Type Joins
- 142. Join Key Coalescing
- 143. Backend Relation Testing
- 144. Backend Divergences
- 145. Execution Target
- 146. execute_on Parameter

## Recommendations

- ✅ **Excellent balance**: Categories are evenly distributed (spread: 9.0%)
- ✅ **MISC category minimal**: Good categorization specificity

### Educational Use Recommendations

- Use taxonomy categories for color-coding in graph visualizations
- Design curriculum modules based on taxonomy groupings
- Create filtered views for focused learning paths
- Use categories for assessment organization
- Enable navigation by topic area in interactive tools

---

*Report generated by learning-graph-reports/taxonomy_distribution.py*
