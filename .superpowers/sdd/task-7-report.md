# Task 7 report: arithmetic option honor-or-declare

## Status

DONE_WITH_CONCERNS. The API/protocol wiring is complete for the implemented
arithmetic option surface, but only the `abs/overflow` vertical slice is fully
empirically dispositioned and drained. I stopped rather than guessing across
the remaining semantic families. `factorial/overflow` remains deferred for its
missing FKEY, with the named central backlog item left uncommitted.

## RED / GREEN

### ABS overflow slice

The first test was the required real-Int8 `abs(overflow="ERROR")` case.

RED command:

```text
hatch run test:test-target-quick tests/expressions/argument_types/test_arg_types_arithmetic.py -k abs_overflow_error_declared_unsupported
```

RED result: all four fixtures failed while the builder dropped the option.
Polars and both Narwhals fixtures returned `[-128]`; Ibis/DuckDB raised
`_duckdb.OutOfRangeException: Overflow on abs(-128)`.

The builder and builder protocol were then wired, value-scoped facts and raw
probe registrations were added, and the ABS cells were appended. A later RED
from the full targeted gate showed that the legacy argument-probe guard treated
new option-value facts as missing `OpSpec`s. It now excludes option-value facts,
whose exact bidirectional coverage belongs to the role-aware option probe guard.

GREEN command/result:

```text
hatch run test:test-target-quick tests/expressions/argument_types/test_arg_types_arithmetic.py tests/expressions/argument_types/test_coverage_guard.py tests/core/test_option_fact_integrity.py tests/core/test_substrait_option_domains.py tests/expressions/argument_types/test_capability_probes.py tests/expressions/argument_types/test_registered_option_probes.py
178 passed, 98 xfailed; exit 0
```

All xfails are strict, documented capability/native probes. There were no
failures or skips in this targeted gate.

## Disposition inventory

Fully dispositioned parameter: `SubstraitScalarArithmeticExpressionSystemProtocol.abs/overflow`
with representative dtype `int8`, legal values `ERROR`, `SATURATE`, `SILENT`,
and four distinct fixtures.

- Polars: `ERROR` and `SATURATE` are declared unsupported; `SILENT` is a
  dialect-scoped probe exemption because explicit SILENT is indistinguishable
  from Polars' native Int8 wrapping behavior.
- Ibis/DuckDB: all three values are declared unsupported. The raw native path
  raises the exact `_duckdb.OutOfRangeException` for every value. `ERROR` is
  still declared rather than called honored because explicit ERROR cannot be
  discriminated from omission (the worked-example policy).
- Narwhals-Polars and Narwhals-Pandas remain separate cells. On each,
  `ERROR` and `SATURATE` are declared unsupported; `SILENT` is a dialect-scoped
  probe exemption because it matches native wrapping and cannot discriminate.

Declared accept-ignore probes use
`OptionProbeDidNotDiscriminateError`; Ibis probes use only the exact DuckDB
overflow exception. No registration uses broad `Exception` or `AssertionError`.
Invalid `WRAP`, lowercase `error`, and empty values raise
`InvalidOptionValueError` at build time.

No same-value divergence exists between honoring fixtures in this slice, so no
`DivergenceFact`, YAML entry, or `xfail_divergence` marker was added.

## Wiring

The builder and its separate API-builder protocol now expose the pinned option
kwargs for implemented arithmetic methods. The builder validates every explicit
non-None value through `validate_option` and emits only explicit values in
`ScalarFunctionNode.options`. Binary wiring covers add/subtract/multiply/power
overflow, divide overflow/domain/division-zero, and modulus
division-type/overflow/domain. Unary math wiring covers the existing rounding,
domain, and overflow parameters. `make_df(schema=...)` was verified already
present from Task 4 and was not duplicated.

The new `arithmetic_option_capabilities.py` module is dependency-free and is
bootstrapped from the central declaration loader.

## Drained and deferred keys

Drained:

```text
SubstraitScalarArithmeticExpressionSystemProtocol / abs / overflow
```

Deferred with the exact required reason:

```text
SubstraitScalarArithmeticExpressionSystemProtocol / factorial / overflow
operation not implemented (no FKEY) — see backlog: substrait-arithmetic-missing-ops
```

The following implemented parameters remain in the known-gap map pending their
own empirical slices: domain-error and rounding for acos/acosh/asin/atan2/atanh;
rounding for asinh/atan/cos/cosh/degrees/exp/radians/sin/sinh/tan/tanh;
overflow for add/subtract/multiply/divide/modulus/negate/power; divide
domain-error and division-zero; modulus division-type and domain-error; and
sqrt rounding and domain-error.

Central backlog path (created and intentionally uncommitted):
`mountainash-central/01.principles/mountainash/h.backlog/active/substrait-arithmetic-missing-ops.md`.

## Verification

```text
hatch run ruff:check <all changed production/test Python files>
All checks passed!

git diff --check
exit 0

hatch run test:test-target-quick tests/core/test_protocol_alignment.py -k scalar_arithmetic tests/core/test_protocol_completeness.py tests/core/test_namespace_infrastructure.py -k 'arithmetic or protocol'
424 passed, 40 xfailed, 36 skipped; exit 0
```

The protocol run includes repository-wide pre-existing skips; the Task 7
arithmetic/probe gate itself had no skips.

## Files

- Modified arithmetic API builder and its separate builder protocol.
- Added dependency-free arithmetic option capability declarations and bootstrap registration.
- Added ABS disposition/probe/behavior/invalid-value coverage.
- Updated option integrity synthetic isolation and legacy probe routing.
- Drained ABS and set the exact factorial deferred reason in the coverage guard.
- Added the uncommitted central factorial backlog item.

## Self-review and concerns

The exact ABS expected/disposition/fact/probe sets are bidirectionally guarded;
Narwhals dialects are not collapsed; node options are omitted for None by the
single `_validated_options` path; the new declaration module imports no optional
backend; and only exact task files are staged.

Concern: the full arithmetic disposition tranche is larger than could be
classified confidently from observable evidence in this execution. The
remaining keys are deliberately not drained, and no facts or cells were
invented for them. The API wiring is present, but their semantic values still
need raw probes and honor-or-declare classification in follow-up vertical
slices.

## Task 7A overflow continuation

### Status and TDD

DONE. This continuation dispositions and drains every remaining implemented
scalar arithmetic `overflow` parameter: `add`, `subtract`, `multiply`,
`divide`, `modulus`, `negate`, and `power`. `abs` remains as previously
completed and `factorial` remains deferred with its exact missing-FKEY reason.

The first new test used two real Int8 columns at `127 + 1` and asserted
SATURATE discrimination. RED:

```text
hatch run test:test-target-quick tests/expressions/argument_types/test_arg_types_arithmetic.py -k add_overflow_saturate_clamps_int8_boundary
4 failed
```

Polars and both Narwhals fixtures returned `[-128]`; Ibis/DuckDB raised
`_duckdb.OutOfRangeException` for Int8 addition. After the value-scoped facts
were registered, the focused four-fixture SATURATE behavior test was GREEN as
four strict xfails with `BackendCapabilityError` and no unexpected XPASS.

### Raw capability-disabled outcomes

Each row below is an independent raw `UnifiedExpressionVisitor(...,
enforce_capabilities=False)` probe. The columns give `ERROR / SATURATE /
SILENT`; omission produced the same outcome shown in every cell.

| op | fixture | ERROR / SATURATE / SILENT raw outcome |
|---|---|---|
| add | polars | `[-128] / [-128] / [-128]` |
| add | ibis | `_duckdb.OutOfRangeException` (Int8 addition) for all three |
| add | narwhals-polars | `[-128] / [-128] / [-128]` |
| add | narwhals-pandas | `[-128] / [-128] / [-128]` |
| subtract | polars | `[127] / [127] / [127]` |
| subtract | ibis | `_duckdb.OutOfRangeException` (Int8 subtraction) for all three |
| subtract | narwhals-polars | `[127] / [127] / [127]` |
| subtract | narwhals-pandas | `[127] / [127] / [127]` |
| multiply | polars | `[-128] / [-128] / [-128]` |
| multiply | ibis | `_duckdb.OutOfRangeException` (Int8 multiplication) for all three |
| multiply | narwhals-polars | `[-128] / [-128] / [-128]` |
| multiply | narwhals-pandas | `[-128] / [-128] / [-128]` |
| divide | polars | `[128.0] / [128.0] / [128.0]` |
| divide | ibis | `[128.0] / [128.0] / [128.0]` |
| divide | narwhals-polars | `[128.0] / [128.0] / [128.0]` |
| divide | narwhals-pandas | `[128.0] / [128.0] / [128.0]` |
| modulus | polars | `[0] / [0] / [0]` |
| modulus | ibis | `_duckdb.OutOfRangeException` (`-128 / -1`) for all three |
| modulus | narwhals-polars | `[0] / [0] / [0]` |
| modulus | narwhals-pandas | `[0] / [0] / [0]` |
| negate | polars | `[-128] / [-128] / [-128]` |
| negate | ibis | `_duckdb.OutOfRangeException` (numeric negation) for all three |
| negate | narwhals-polars | `[-128] / [-128] / [-128]` |
| negate | narwhals-pandas | `[-128] / [-128] / [-128]` |
| power | polars | `[-128] / [-128] / [-128]` |
| power | ibis | `[128.0] / [128.0] / [128.0]` |
| power | narwhals-polars | `[-128] / [-128] / [-128]` |
| power | narwhals-pandas | `[-128] / [-128] / [-128]` |

Boundary inputs were respectively `127+1`, `-128-1`, `64*2`, `-128/-1`,
`-128%-1`, `-(-128)`, and `2**7`, always with explicit Polars Int8 schemas
before conversion to each fixture.

### Facts, probes, taxonomy, and divergences

No value was honored by a discriminator. SILENT is a dialect-scoped
`EXPR_CAPABLE` probe exemption on Polars, Narwhals-Polars, and
Narwhals-Pandas for the six native-wrapping operations (`add`, `subtract`,
`multiply`, `modulus`, `negate`, `power`). `divide` widens to Float64 on every
fixture, so none of its three Int8 overflow modes matches the pinned Int8
contract; all are declared unsupported.

All remaining cells are value-scoped `UNSUPPORTED` facts with
`role=declared_unsupported` raw-probe registrations. Accept-ignore and widened
results use only `OptionProbeDidNotDiscriminateError`. DuckDB native errors for
`add`, `subtract`, `multiply`, `modulus`, and `negate` use only the exact
`_duckdb.OutOfRangeException`. No broad `AssertionError`, `Exception`, or
`BaseException` registration was added. The seven parameter taxonomies are
`capability-declared` because each mixes declarations with probe exemptions or
is wholly declared.

There are 84 exact new cells, 66 declared registrations/facts, and 18 exact
dialect probe-exempt facts. No fixture honored a value, so there is no
same-value honoring divergence and no `DivergenceFact`, YAML row, or
`xfail_divergence` marker.

### Tests and files

Behavior coverage includes every declared op/value/fixture gate, every SILENT
probe exemption, all registered raw probes, and build-time rejection of
`WRAP`, lowercase `error`, and the empty string for each operation. The
bidirectional guard proves expected == dispositioned == facts/probes after all
seven known-gap entries are removed.

Modified files:

- `src/mountainash/expressions/backends/expression_systems/arithmetic_option_capabilities.py`
- `tests/expressions/argument_types/test_arg_types_arithmetic.py`
- `tests/expressions/argument_types/test_coverage_guard.py`

Concern: `divide` and Ibis `power` widen Int8 inputs to Float64, which avoids a
native Int8 overflow rather than implementing any pinned overflow mode. They
are therefore narrowly declared unsupported using the observed
non-discrimination failure, not treated as omission-equivalent support.

## Task 7A power signature correction

The pinned `functions_arithmetic.yaml` has exactly one integer `power`
overload: `(i64, i64) -> i64`. The previous `Int8(2) ** Int8(7)` cells therefore
classified an overload that the pinned contract does not define. The
regression test changed the representative policy expectation to `int64` before
the implementation changed. RED was the exact mismatch
`('power', 'overflow'): ('int8',) != ('int64',)`; the probe contract test also
failed with `spec.dtype == 'int8'` instead of `int64`.

The replacement boundary is `Int64(2) ** Int64(63)`: the exact mathematical
result is `2**63`, one above signed Int64 maximum `2**63 - 1`. Every result below
comes from an independent raw `UnifiedExpressionVisitor(...,
enforce_capabilities=False)` execution. Outcomes are ordered
`ERROR / SATURATE / SILENT / omission`:

| fixture | raw i64 outcome |
|---|---|
| polars | `[-9223372036854775808]` for all four |
| ibis | `[9.223372036854776e+18]` (`float`) for all four |
| narwhals-polars | `[-9223372036854775808]` for all four |
| narwhals-pandas | `[-9223372036854775808]` for all four |

All twelve cells were regenerated at representative dtype `int64` solely from
those results. Polars and both Narwhals dialects retain a dialect-scoped
`probe_exempt` fact only for SILENT because native i64 wrapping is exactly
omission-equivalent. Their ERROR and SATURATE cells are declared unsupported.
All three Ibis cells are declared unsupported: widening to Float64 violates the
pinned i64 return signature and does not discriminate any option. No power
value is honored. All nine declared probes still expect only
`OptionProbeDidNotDiscriminateError`; no broad exception was introduced.

Power facts now use i64-specific messages and direct users to pre-check the i64
base/exponent and handle an out-of-range result before `power()`. Wider-cast
advice is intentionally absent because i64 is already the pinned width.

## Task 7B domain, division-zero, and modulus semantics

### Status and TDD

DONE_WITH_CONCERNS. This continuation dispositions and drains every implemented
non-rounding, non-overflow arithmetic option parameter: `on_domain_error` for
`acos`, `acosh`, `asin`, `atan2`, `atanh`, `sqrt`, `divide`, and `modulus`;
`divide/on_division_by_zero`; and `modulus/division_type`.

The first RED used signed Int64 operands `-5` and `3`, for which FLOOR modulus
is `1` and TRUNCATE modulus is `-2`. All four fixtures failed the two-result
assertion: Polars and both Narwhals dialects returned FLOOR's `1` for both
values, while Ibis/DuckDB returned TRUNCATE's `-2` for both. A second RED proved
that the raw probe falsely treated corresponding NaNs as unequal. The helper
now compares corresponding NaNs as equal while preserving the observable
NaN-versus-null distinction. A third RED corrected the representative modulus
domain dtype from the nonexistent Float64 overload to the pinned Int64
overload.

### Raw capability-disabled outcomes

Every entry below is an independent option expression and omission reference
executed through `UnifiedExpressionVisitor(..., enforce_capabilities=False)`.
Outcomes include the reference after the slash.

| operation | fixture | raw explicit values / omission |
|---|---|---|
| `acos` (`2.0`) | polars | `NAN=[nan], ERROR=[nan] / [nan]` |
| `acos` | ibis | `_duckdb.InvalidInputException` for both / same |
| `acos` | both Narwhals dialects | `NotImplementedError` for both / same |
| `acosh` (`0.0`) | polars | `NAN=[nan], ERROR=[nan] / [nan]` |
| `acosh` | ibis and both Narwhals dialects | `NotImplementedError` for both / same |
| `asin` (`2.0`) | polars | `NAN=[nan], ERROR=[nan] / [nan]` |
| `asin` | ibis | `_duckdb.InvalidInputException` for both / same |
| `asin` | both Narwhals dialects | `NotImplementedError` for both / same |
| `atan2` (`NaN, 1.0`) | polars | `NAN=[nan], ERROR=[nan] / [nan]` |
| `atan2` | ibis | `NAN=[None], ERROR=[None] / [None]` |
| `atan2` | both Narwhals dialects | `NotImplementedError` for both / same |
| `atanh` (`2.0`) | polars | `NAN=[nan], ERROR=[nan] / [nan]` |
| `atanh` | ibis and both Narwhals dialects | `NotImplementedError` for both / same |
| `sqrt` (`-1.0`) | polars, narwhals-polars | `NAN=[nan], ERROR=[nan] / [nan]` |
| `sqrt` | ibis | `_duckdb.OutOfRangeException` for both / same |
| `sqrt` | narwhals-pandas | `NAN=[None], ERROR=[None] / [None]` |
| `divide/on_domain_error` (`NaN, 1.0`) | polars, narwhals-polars | `NAN/NULL/ERROR=[nan] / [nan]` |
| `divide/on_domain_error` | ibis, narwhals-pandas | `NAN/NULL/ERROR=[None] / [None]` |
| `divide/on_division_by_zero` (`0.0, 0.0`) | polars, ibis, narwhals-polars | `IEEE/LIMIT/NULL/ERROR=[nan] / [nan]` |
| `divide/on_division_by_zero` | narwhals-pandas | `IEEE/LIMIT/NULL/ERROR=[None] / [None]` |
| `modulus/division_type` (`-5, 3`, Int64) | polars, both Narwhals dialects | `FLOOR=[1], TRUNCATE=[1] / [1]` |
| `modulus/division_type` | ibis | `FLOOR=[-2], TRUNCATE=[-2] / [-2]` |
| `modulus/on_domain_error` (`5, 0`, Int64) | all fixtures | `NULL=[None], ERROR=[None] / [None]` |

### Classifications, facts, and divergences

No explicit value discriminated from omission, so no cell is `honored` and no
parameter is error-sensitive. Probe exemptions are limited to exact requested
semantics on concrete dialects:

- Polars: `NAN` for all six unary domain operations and divide domain errors;
  `IEEE` for divide-by-zero; `FLOOR` for signed modulus; and `NULL` for modulus
  domain errors.
- Narwhals-Polars: `NAN` for sqrt and divide domain errors; `IEEE` for
  divide-by-zero; `FLOOR` for signed modulus; and `NULL` for modulus domain
  errors.
- Narwhals-Pandas: `NULL` for divide domain and divide-by-zero behavior;
  `FLOOR` for signed modulus; and `NULL` for modulus domain errors.

All remaining cells are value-scoped `UNSUPPORTED` facts with
`role=declared_unsupported` raw registrations. Accept-ignore paths use only
`OptionProbeDidNotDiscriminateError`; inverse-function absence uses exact
`NotImplementedError`; DuckDB uses only `_duckdb.InvalidInputException` for
acos/asin and `_duckdb.OutOfRangeException` for sqrt. No broad failure class is
registered. Because no fixture honored an explicit value, there is no honoring
divergence and no `DivergenceFact`, YAML row, or `xfail_divergence` marker.

Ibis has no concrete fixture dialect (`dialect=None`). The capability schema
forbids explicit family-level `EXPR_CAPABLE` facts when the family default is
already capable, while integrity requires every exemption to be an exact
dialect refinement. Following the existing ABS precedent, all Ibis cells are
therefore declared unsupported even when its omission result happens to match
one requested value; treating those ignored options as honored would violate
the discriminator rule.

### Tests, verification, and files

Behavior tests cover every declared value through the enforcing gate and every
probe exemption against the requested result. Every parameter rejects
`INVALID`, lowercase `nan`, and the empty string at build time. The
bidirectional integrity gate proves exact expected/disposition/fact/probe
equality after the ten known-gap entries are removed. The complete Task 7
target gate passed with only documented strict xfails; Ruff and `git diff
--check` passed.

Modified files:

- `src/mountainash/expressions/backends/expression_systems/arithmetic_option_capabilities.py`
- `tests/expressions/argument_types/_option_helpers.py`
- `tests/expressions/argument_types/option_disposition.py`
- `tests/expressions/argument_types/test_arg_types_arithmetic.py`
- `tests/expressions/argument_types/test_coverage_guard.py`
- `tests/expressions/argument_types/test_option_helpers_selfcheck.py`
- `tests/core/test_option_fact_integrity.py`
- `.superpowers/sdd/task-7-report.md`

Concern: Ibis cannot represent dialect-scoped probe exemptions until its
fixture identity gains a concrete dialect. This slice does not broaden that
machinery or mislabel ignored options to conceal the limitation.
