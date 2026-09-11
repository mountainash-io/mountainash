# Mountainash Concept List

Total concepts: 200

## Foundation Concepts (1–12)

1. Python Type Hints
2. Protocol Classes
3. Pydantic Models
4. DataFrames
5. Polars Library
6. Pandas Library
7. Apache Arrow
8. SQL Databases
9. Lazy Evaluation
10. Method Chaining
11. Visitor Pattern
12. Directed Acyclic Graph

## Core Infrastructure (13–24)

13. Constants Module
14. Backend Enum
15. Backend System Enum
16. Backend Detection
17. DataFrame Type Guards
18. MountainashDtype
19. Lazy Import System
20. Factory Pattern
21. BaseFactoryMixin
22. Operation Enums
23. JoinType Enum
24. SetType Enum

## Expression API (25–54)

25. col Function
26. lit Function
27. Expression Building
28. BaseExpressionAPI
29. BooleanExpressionAPI
30. Fluent Expression Chain
31. Operator Overloading
32. String Namespace
33. Datetime Namespace
34. Struct Namespace
35. List Namespace
36. Name Namespace
37. NamespaceDescriptor
38. when Function
39. coalesce Function
40. greatest Function
41. least Function
42. native Function
43. Comparison Operations
44. Arithmetic Operations
45. Boolean Operations
46. String Operations
47. Datetime Operations
48. Aggregation Functions
49. Window Functions
50. cast Operation
51. Null Handling
52. duration Function
53. count_records Function
54. corr Function

## Expression AST & System (55–78)

55. ExpressionNode Base
56. ScalarFunctionNode
57. FieldReferenceNode
58. LiteralNode
59. CastNode
60. IfThenNode
61. SingularOrListNode
62. WindowFunctionNode
63. WindowSpec
64. WindowBound
65. OverNode
66. Function Key Enums
67. FKEY Substrait Prefix
68. FKEY Mountainash Prefix
69. ExpressionFunctionDef
70. ExpressionFunctionRegistry
71. Function Registry Lookup
72. Substrait Spec Alignment
73. Build Then Compile
74. Expression Compilation
75. Unified Expression Visitor
76. API Builder Protocols
77. Expression System Protocols
78. Mountainash Extensions

## Expression Backends (79–94)

79. PolarsExpressionSystem
80. NarwhalsExpressionSystem
81. IbisExpressionSystem
82. Polars Expr Compilation
83. Narwhals Expr Compilation
84. Ibis Expr Compilation
85. Backend Composition
86. Multiple Inheritance
87. Substrait Compile Files
88. Extension Compile Files
89. Known Expr Limitations
90. Expression Testing
91. Cross-Backend Parametrize
92. xfail Known Quirks
93. Arguments vs Options
94. Expression Type Generics

## Relation API (95–114)

95. relation Factory
96. Relation Class
97. RelationBase
98. Filter Operation
99. Sort Operation
100. Head Fetch Operation
101. Select Project Operation
102. Join Operation
103. Group By Operation
104. GroupedRelation
105. Aggregation on Groups
106. Set Operations
107. concat Function
108. Conform Operation
109. Unnest Operation
110. Build Then Collect
111. Terminal Operations
112. to_polars Method
113. to_pandas Method
114. collect Method

## Relation AST & System (115–134)

115. RelationNode Base
116. ReadRelNode
117. ProjectRelNode
118. FilterRelNode
119. AggregateRelNode
120. JoinRelNode
121. FetchRelNode
122. SortRelNode
123. SetRelNode
124. ExtensionRelNode
125. SourceRelNode
126. RefRelNode
127. ResourceReadRelNode
128. Relation Protocols
129. UnifiedRelationVisitor
130. Visitor Composition
131. RelationVisitRegistry
132. OptimisationRegistry
133. Relation System Base
134. ExtensionRelOperation

## Relation Backends (135–146)

135. PolarsRelationSystem
136. NarwhalsRelationSystem
137. IbisRelationSystem
138. LazyFrame Operations
139. Narwhals Portability
140. Ibis SQL Compilation
141. Cross-Type Joins
142. Join Key Coalescing
143. Backend Relation Testing
144. Backend Divergences
145. Execution Target
146. execute_on Parameter

## Type System & Schema (147–168)

147. TypeSpec
148. FieldSpec
149. FieldConstraints
150. UniversalType Enum
151. Type Bridge
152. Backend Type Mapping
153. Foreign Keys
154. ForeignKeyReference
155. Custom Type Registry
156. Type Converters
157. Frictionless Standard
158. Table Schema
159. Schema Extraction
160. DataFrame Extraction
161. Dataclass Extraction
162. Pydantic Extraction
163. Schema Validation
164. validate_match Function
165. Schema Comparison
166. Polars Schema Convert
167. Pandas Dtypes Convert
168. Arrow Schema Convert

## DAG & DataPackage (169–186)

169. RelationDAG
170. Named Relations
171. dag.ref Method
172. Dependency Edges
173. Constraint Edges
174. Two-Edge Graph Model
175. Topological Collection
176. dag.collect Method
177. ref_resolver Parameter
178. DataPackage
179. DataResource
180. TableDialect
181. from_descriptor Method
182. to_relation_dag Method
183. Resource Overrides
184. dag.add Method
185. to_package Method
186. FK Integrity Check

## Pipeline Framework (187–200)

187. PipelineBuilder
188. step Decorator
189. source Function
190. PipelineSpec
191. StepDefinition
192. StepContext
193. StepResult
194. SimplePipelineRunner
195. ParamSpec
196. Parameter Binding
197. relation.params Method
198. ParamsRelNode
199. PipelineStepRelNode
200. fold_params Function
