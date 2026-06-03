---
title: Expression Backends
description: Backend expression systems for Polars, Narwhals, and Ibis, including compilation implementations, composition patterns, testing strategies, and known limitations.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 8: Expression Backends

## Summary

Backend expression systems (Polars, Narwhals, Ibis), their compilation implementations, backend composition via multiple inheritance, Substrait and extension compile files, known limitations, cross-backend testing with parametrize and xfail, arguments vs options, and expression type generics.

## Concepts Covered

- PolarsExpressionSystem
- NarwhalsExpressionSystem
- IbisExpressionSystem
- Polars Expr Compilation
- Narwhals Expr Compilation
- Ibis Expr Compilation
- Backend Composition
- Multiple Inheritance
- Substrait Compile Files
- Extension Compile Files
- Known Expr Limitations
- Expression Testing
- Cross-Backend Parametrize
- xfail Known Quirks
- Arguments vs Options
- Expression Type Generics

## Prerequisites

- [Chapter 2. Core Infrastructure](../02-core-infrastructure/)
- [Chapter 7. Expression Function Registry and Compilation](../07-expression-function-registry/)

---

## Introduction

The expression system protocols defined in Chapter 7 describe what backends must implement. This chapter examines how the three concrete backends (Polars, Narwhals, Ibis) satisfy those protocols, how their implementations are organized via multiple inheritance, and how mountainash tests expression behavior across all backends simultaneously.

## PolarsExpressionSystem

The `PolarsExpressionSystem` is the primary expression backend. It compiles mountainash expression ASTs into native Polars expression objects (`pl.Expr`). Because mountainash's expression API was originally modeled on Polars, this backend provides the most natural and complete mapping.

The Polars system handles field references by producing `pl.col(name)`, literals by producing `pl.lit(value)`, and scalar functions by dispatching to the appropriate Polars expression method. Cast operations use Polars dtype objects resolved from the canonical MountainashDtype string.

```python
# Conceptual Polars compilation
def compile_field_reference(self, node):
    return pl.col(node.column_name)

def compile_literal(self, node):
    return pl.lit(node.value)

def compile_add(self, args, options):
    return args[0] + args[1]  # Polars expression arithmetic
```

The Polars backend supports the full operation catalog including window functions, advanced string operations, and all temporal operations. It serves as the reference implementation against which other backends are compared.

## NarwhalsExpressionSystem

The `NarwhalsExpressionSystem` handles compilation for pandas DataFrames and PyArrow tables by routing through the Narwhals compatibility layer. Narwhals provides a Polars-like API on top of other DataFrame libraries, so the compilation output closely mirrors the Polars backend.

```python
# Narwhals compilation produces nw.col expressions
def compile_field_reference(self, node):
    return nw.col(node.column_name)

def compile_literal(self, node):
    return nw.lit(node.value)
```

The Narwhals backend has some limitations compared to Polars. Certain advanced operations (complex window frames, some string regex operations) may not have Narwhals equivalents. When this occurs, the backend either raises a clear error or falls back to a less efficient implementation.

## IbisExpressionSystem

The `IbisExpressionSystem` compiles expression ASTs into Ibis expression objects that ultimately translate to SQL. This backend enables mountainash expressions to execute against SQL databases (DuckDB, PostgreSQL, SQLite, and others).

The Ibis backend's compilation differs significantly from Polars and Narwhals because SQL has different semantics for certain operations. For example, string pattern matching uses SQL's LIKE syntax, division behavior depends on operand types, and window functions require explicit frame specifications.

```python
# Ibis compilation targets SQL-compatible expressions
def compile_field_reference(self, node):
    return self._table[node.column_name]  # Ibis column access

def compile_add(self, args, options):
    return args[0] + args[1]  # Ibis expression arithmetic
```

| Aspect | Polars | Narwhals | Ibis |
|--------|--------|----------|------|
| Target format | `pl.Expr` | `nw.Expr` | `ibis.Expr` |
| Execution model | Lazy/Eager | Depends on wrapped lib | SQL compilation |
| String regex | Full support | Partial | Backend-dependent |
| Window frames | Full support | Limited | Full SQL support |
| Null semantics | Polars rules | Follows wrapped lib | SQL NULL rules |

## Polars Expr Compilation

Polars expression compilation translates each mountainash AST node into the corresponding Polars expression API call. The compilation is mostly a one-to-one mapping because mountainash's API was designed to align with Polars.

For arithmetic operations, compilation produces Polars operator expressions. For string operations, it accesses the `.str` namespace. For temporal operations, it accesses the `.dt` namespace. Window functions compile to `.over()` calls with the appropriate partition and ordering.

```python
# Examples of Polars compilation output:
# ma.col("x") + ma.col("y")  ->  pl.col("x") + pl.col("y")
# ma.col("name").str.upper()  ->  pl.col("name").str.to_uppercase()
# ma.col("val").sum().over(partition_by="grp")  ->  pl.col("val").sum().over("grp")
```

Note that method names may differ between the mountainash API and Polars. For example, mountainash uses `upper()` while Polars uses `to_uppercase()`. The compilation layer handles these name translations transparently.

## Narwhals Expr Compilation

Narwhals expression compilation translates to the Narwhals expression API, which itself is a Polars-compatible interface over pandas, PyArrow, and other backends. The output is `nw.Expr` objects that Narwhals can then lower to the underlying library.

The double-layer translation (mountainash -> Narwhals -> backend) adds some overhead but provides broad compatibility. Any DataFrame library that Narwhals supports becomes automatically available to mountainash without a dedicated expression system implementation.

## Ibis Expr Compilation

Ibis expression compilation takes a fundamentally different approach. Instead of producing expression objects that operate on in-memory data, it produces Ibis expression objects that compile to SQL strings for execution on database engines.

Key differences in Ibis compilation include:

- Column references are table-scoped (require an Ibis table context)
- Type casts use Ibis type objects rather than Polars/Arrow types
- String operations map to SQL function calls
- Window functions compile to SQL OVER clauses
- Some operations have no SQL equivalent and raise NotImplementedError

## Backend Composition

Backend composition is the pattern by which each expression system class is assembled from multiple mixin classes, each implementing a specific protocol. Rather than a single monolithic class, each backend is composed from focused, testable components.

```python
class PolarsExpressionSystem(
    PolarsArithmeticCompiler,
    PolarsComparisonCompiler,
    PolarsBooleanCompiler,
    PolarsStringCompiler,
    PolarsDatetimeCompiler,
    PolarsWindowCompiler,
    PolarsNameCompiler,
    PolarsNullCompiler,
    # ... more mixins
):
    """Composed from category-specific compilation mixins."""
    pass
```

This composition enables independent development and testing of each operation category. A change to string compilation affects only the string mixin, reducing merge conflicts and cognitive load.

## Multiple Inheritance

Multiple inheritance is the Python mechanism that enables backend composition. Each expression system class inherits from many mixin classes simultaneously, combining their methods into a single interface.

#### Diagram: Expression System Composition
<iframe src="../../sims/expression-system-composition/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Expression System Composition</summary>
Type: diagram
**sim-id:** expression-system-composition<br/>
**Library:** vis-network<br/>
**Status:** Specified

A class hierarchy diagram showing three expression system classes (Polars, Narwhals, Ibis) at the bottom, with their mixin parent classes arranged above. Each mixin is labeled with its operation category (Arithmetic, Comparison, String, DateTime, Window, Name, Null, Native). Edges show inheritance relationships. Color coding distinguishes Substrait-aligned mixins (LimeGreen) from Extension mixins (Gold). Clicking a system class highlights all its parent mixins. Learning objective: Explain how multiple inheritance composes focused compilation mixins into complete backend systems (Bloom: Analyze).
</details>

Python's Method Resolution Order (MRO) determines which implementation wins when multiple parent classes define the same method. In practice, mountainash's mixins have non-overlapping method names (each mixin handles a distinct function category), so MRO conflicts do not arise.

## Substrait Compile Files

Substrait compile files are the source modules that implement compilation for Substrait-standard operations. They are organized by function category, with one file per category per backend.

The naming convention follows a predictable pattern:

- `compile_substrait_arithmetic.py` -- Addition, subtraction, multiplication, etc.
- `compile_substrait_comparison.py` -- Equality, ordering comparisons
- `compile_substrait_boolean.py` -- AND, OR, NOT
- `compile_substrait_string.py` -- String manipulation functions
- `compile_substrait_datetime.py` -- Temporal operations

Each file defines a mixin class containing compile methods for all functions in that category. The mixin satisfies the corresponding expression system protocol.

## Extension Compile Files

Extension compile files implement compilation for mountainash-specific extensions that go beyond the Substrait specification. They follow the same pattern as Substrait compile files but use the `extensions_mountainash` namespace.

- `compile_ext_ma_name.py` -- Alias, prefix, suffix operations
- `compile_ext_ma_null.py` -- Extended null handling
- `compile_ext_ma_native.py` -- Backend passthrough
- `compile_ext_ma_scalar_aggregate.py` -- Custom aggregation functions
- `compile_ext_ma_scalar_ternary.py` -- Three-valued logic operations

The separation between Substrait and extension compile files makes it immediately clear which operations are standardized and which are mountainash-specific. This clarity helps when evaluating portability across different Substrait-compatible systems.

## Known Expr Limitations

Known expression limitations are operations where backends diverge in behavior or where certain operations are unsupported on specific backends. Mountainash tracks these systematically rather than hiding them.

Common limitation categories include:

- **Regex support**: Ibis backends vary in regex dialect support
- **Division semantics**: Integer division behavior differs between Polars and SQL
- **Null propagation**: Edge cases in null handling across backends
- **Window frame bounds**: Narwhals has limited frame bound support
- **Type coercion**: Implicit casting rules differ by backend

These limitations are documented in the test suite and enforced through the `xfail` mechanism (described below).

## Expression Testing

Expression testing verifies that the compilation output is correct across all backends. The test suite constructs expression ASTs, compiles them against each backend, executes the compiled expressions on sample data, and asserts that results match expected values.

```python
def test_addition(backend_fixture):
    """Addition should work identically across all backends."""
    expr = ma.col("a") + ma.col("b")
    result = compile_and_execute(expr, backend_fixture, sample_data)
    assert result == expected_values
```

The testing strategy emphasizes behavioral equivalence: the same expression should produce the same results regardless of backend, within the bounds of known limitations.

## Cross-Backend Parametrize

Cross-backend parametrize is a pytest pattern that runs the same test against all three backends automatically. Using `@pytest.mark.parametrize`, each test case executes once per backend, catching divergences early.

```python
@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_string_upper(backend):
    """String upper should work across all backends."""
    expr = ma.col("name").str.upper()
    result = compile_and_execute(expr, backend, test_data)
    assert_equal(result, expected)
```

This pattern multiplies the effective test coverage by the number of backends. A single logical test case produces three test executions, one per backend. Failures indicate backend-specific bugs or unimplemented features.

## xfail Known Quirks

The `xfail` (expected failure) mechanism marks tests that are known to fail on specific backends due to fundamental behavioral differences. Rather than skipping these tests entirely, `xfail` documents the divergence and alerts developers if a previously-failing test starts passing (indicating the underlying issue was fixed).

```python
@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_regex_lookahead(backend):
    if backend == "ibis":
        pytest.xfail("Ibis/SQLite does not support regex lookahead")
    # ... test body
```

The xfail annotations serve as living documentation of backend divergences. They prevent test suite noise from known issues while still running the tests (so improvements are detected automatically).

## Arguments vs Options

In the expression AST, the distinction between arguments and options determines how data flows through function compilation. Arguments are expression nodes (compiled recursively by the visitor). Options are plain Python values (passed directly to the compile method).

```python
class ScalarFunctionNode(ExpressionNode):
    function_key: Enum
    arguments: list[ExpressionNode]  # Compiled by visitor
    options: dict[str, Any]          # Passed directly
```

Arguments represent data dependencies (column references, literal values, sub-expressions). Options represent configuration (format strings, flags, precision levels). This distinction matters because the compiler needs to recursively visit arguments but can simply pass options through.

For example, `substring(offset, length)` stores the source expression as an argument but may store offset and length as options if they are always integer literals rather than expressions.

## Expression Type Generics

Expression type generics use Python's `TypeVar` and `Generic` to preserve type information through expression chains. This enables static type checkers to know that a comparison operation returns a `BooleanExpressionAPI` rather than a generic `BaseExpressionAPI`.

```python
T = TypeVar("T", bound=BaseExpressionAPI)

class ExpressionChain(Generic[T]):
    def filter(self, predicate: BooleanExpressionAPI) -> T: ...
```

Type generics improve the developer experience by enabling IDE autocompletion to show only relevant methods. After a comparison operation, the IDE knows the result is boolean and offers `and_`, `or_`, and `not_` methods. After an arithmetic operation, it offers numeric methods instead.

## Key Takeaways

- Three expression systems (Polars, Narwhals, Ibis) provide complete compilation targets, with Polars as the reference implementation.
- Each system is composed from focused mixin classes via multiple inheritance, enabling independent development and testing per operation category.
- Substrait compile files handle standardized operations while extension compile files handle mountainash-specific features, maintaining clear separation.
- Known limitations are tracked systematically through xfail markers rather than hidden, providing living documentation of backend divergences.
- Cross-backend parametrize multiplies test coverage across all backends, catching behavioral differences early in development.
- Arguments (expression nodes, compiled recursively) are distinguished from options (plain values, passed directly) in the function node structure.
- Expression type generics preserve type information through chains, enabling static analysis tools to provide accurate autocompletion and type checking.
- The Polars backend provides the most complete mapping due to mountainash's API design alignment with Polars conventions.
