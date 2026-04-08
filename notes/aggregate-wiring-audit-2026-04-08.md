# Aggregate Wiring Audit — 2026-04-08

For each of the six wiring-matrix layers, status of `count(x)` and `count_records()` in the Substrait aggregate namespace.

| Layer | COUNT | COUNT_RECORDS | Notes |
|---|---|---|---|
| Enum (`FKEY_SUBSTRAIT_SCALAR_AGGREGATE`) | + | - | `COUNT = auto()` exists at line 120; `COUNT_RECORDS` absent entirely |
| Function mapping (`definitions.py`) | + | - | `SCALAR_AGGREGATE_FUNCTIONS` list has one entry for `COUNT`; no `COUNT_RECORDS` entry |
| Protocol (expression system) | + | - | `prtcl_expsys_aggregate_generic.py` has `def count(self, x, /, overflow=None)`; no `count_records` method |
| Backend impl — Polars | + | ~ | `expsys_pl_aggregate_generic.py` has `def count()`; `count_all` is commented out in the same file. A separate `_`-prefixed aspirational file `_expsys_pl_scalar_aggregate.py` has `def count_all()` but imports a non-existent protocol (`SubstraitScalarAggregateExpressionSystemProtocol`) — not authoritative |
| Backend impl — Narwhals | + | ~ | `expsys_nw_aggregate_generic.py` has `def count()`; `count_all` is commented out in same file. A `_`-prefixed aspirational file `_expsys_nw_scalar_aggregate.py` has `def count_all()` — not authoritative |
| Backend impl — Ibis | + | ~ | `expsys_ib_aggregate_generic.py` has `def count()`; `count_all` is commented out in same file. A `_`-prefixed aspirational file `_expsys_ib_scalar_aggregate.py` has `def count_all()` — not authoritative |
| api_builder protocol | ~ | - | File exists but is `_`-prefixed (`_prtcl_api_bldr_scalar_aggregate.py`); has `def count()` stub and `def any_value()` stub; no `count_records`. Underscore prefix means not yet authoritative |
| api_builder implementation | ~ | - | File exists but is `_`-prefixed (`_api_bldr_scalar_aggregate.py`); body is an empty stub (`pass`); no methods at all. Underscore prefix means not yet authoritative |
| Flat namespace wiring | - | - | `SubstraitScalarAggregateAPIBuilder` is commented out in both the import and `_FLAT_NAMESPACES` list in `boolean.py` (lines 20 and 125) |
| Free-function entrypoint (`entrypoints.py`) | - | - | `entrypoints.py` exists but has no `count` or `count_records` entry |

Legend: `+` ready, `~` aspirational/stub (not authoritative), `-` missing.

## Additional findings

### Broken import in aspirational backend files
`expsys_pl_ext_ma_scalar_aggregate.py` (and equivalent narwhals/ibis files) import
`SubstraitScalarAggregateExpressionSystemProtocol` from the substrait protocols `__init__`, but
this class does **not exist** in the substrait protocol namespace. The protocol exported from
`prtcl_expsys_aggregate_generic.py` is `SubstraitAggregateGenericExpressionSystemProtocol`.
These files would raise `ImportError` if imported. They are aspirational/dead code.

### extensions_mountainash has no aggregate protocol
There is no `prtcl_expsys_ext_ma_scalar_aggregate.py` in the `extensions_mountainash` protocols
directory. The `expsys_pl_ext_ma_scalar_aggregate.py` backend file (which has `count_all`) is
therefore an orphaned backend with no protocol backing it — confirming it is not authoritative.

### Narwhals and Ibis aggregate_generic backend files exist
Both `expsys_nw_aggregate_generic.py` and `expsys_ib_aggregate_generic.py` exist and already
implement `count(x)`. They do NOT need to be created from scratch in Task 3, only extended to
add `count_records()`.

### Substrait spec alignment
Substrait `functions_aggregate_generic.yaml` defines a single function named `count` with two
impls distinguished by arity:
1. `count(x: any)` — counts non-null values (already wired as `COUNT`)
2. `count()` (zero args) — counts all records ("Count the number of records") — not yet wired

The 0-arg overload is in the Substrait spec, so `COUNT_RECORDS` belongs in
`FKEY_SUBSTRAIT_SCALAR_AGGREGATE`, not in `FKEY_MOUNTAINASH_*`. The plan's architecture note
is confirmed correct.

## Gaps to close in this plan

1. **Enum:** Add `COUNT_RECORDS = auto()` to `FKEY_SUBSTRAIT_SCALAR_AGGREGATE` in `enums.py`.
2. **Protocol (expression system):** Add `def count_records(self, /, overflow=None) -> ExpressionT` to `prtcl_expsys_aggregate_generic.py`.
3. **Function mapping:** Append a `COUNT_RECORDS` `ExpressionFunctionDef` entry to `SCALAR_AGGREGATE_FUNCTIONS` in `definitions.py`, with `substrait_name="count"` and zero args (no `x` parameter).
4. **Backend — Polars:** Add `def count_records(self, overflow=None)` to `expsys_pl_aggregate_generic.py` (uncomment and rename the commented-out `count_all` body, returning `pl.len()` or `pl.count()`).
5. **Backend — Narwhals:** Add `def count_records(self, overflow=None)` to `expsys_nw_aggregate_generic.py` (same pattern as Polars).
6. **Backend — Ibis:** Add `def count_records(self, overflow=None)` to `expsys_ib_aggregate_generic.py` (same pattern as Polars).
7. **api_builder protocol:** Rename `_prtcl_api_bldr_scalar_aggregate.py` → `prtcl_api_bldr_scalar_aggregate.py` (drop underscore); add `count_records()` method signature.
8. **api_builder implementation:** Rename `_api_bldr_scalar_aggregate.py` → `api_bldr_scalar_aggregate.py` (drop underscore); replace empty stub `pass` body with real `count()` and `count_records()` implementations.
9. **Flat namespace wiring:** Uncomment `SubstraitScalarAggregateAPIBuilder` import and entry in `_FLAT_NAMESPACES` in `boolean.py`.
10. **Free-function entrypoint:** Add `def count_records() -> BaseExpressionAPI` to `entrypoints.py` and re-export from `src/mountainash/__init__.py`.
11. **Cleanup:** Remove or mark as dead code the three `_`-prefixed aspirational backend files (`_expsys_pl_scalar_aggregate.py`, `_expsys_nw_scalar_aggregate.py`, `_expsys_ib_scalar_aggregate.py`) and `expsys_pl_ext_ma_scalar_aggregate.py` — these have broken imports and no protocol backing.
