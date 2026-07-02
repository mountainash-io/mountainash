"""ConformContract — the unified per-dimension reconciliation contract.

One contract, four policy dimensions (`extra_columns`, `missing_columns`,
`data_type`, `keys`) plus two structural facets (`mapping`, guards).
`fields_match` is a Frictionless-faithful preset layer over the column
dimensions, not a separate mechanism: `FIELDS_MATCH_PRESETS` expands each
`fields_match` value into the column-dimension policies it has always meant
(locked to current behaviour — see conform-contract.md §"fields_match preset
expansion").

`from_preset` is the provenance flag: a contract built purely from a preset
(no explicit `TypeSpec.contract` / `conform(contract=...)` layer) still
raises the legacy `fields_match` errors (`MissingFieldsError`,
`ExtraFieldsError`, ...) on violation. Any explicit layer flips
`from_preset` to `False`, and a `freeze` on a column dimension then raises
`SchemaDriftError` instead — the two error families are distinguished by
provenance, not by dimension.

No evaluation/reconciliation logic lives here — this module only builds and
validates the contract. The evaluator (`resolve_conform_output`) is a
separate concern.

See: `conform-contract.md` (c.api-design/conform, item 48).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Optional, Union

from mountainash.conform.errors import ConformError

_DIMENSION_MODES: dict[str, set[str]] = {
    "extra_columns": {"evolve", "freeze", "discard"},
    "missing_columns": {"skip", "freeze", "null_fill"},
    "data_type": {"coerce", "evolve", "freeze", "discard_value", "discard_row"},
    "keys": {"ignore", "freeze"},
}
_EXTENSION_DIMENSIONS = ("data_type", "keys")   # scalar shorthand applies here only


@dataclass(frozen=True)
class ConformContract:
    """The unified conform contract: four policy dimensions + structural facets.

    `from_preset=True` (default) marks a contract as preset-only provenance:
    it was built solely from a `fields_match` preset, with no explicit
    `TypeSpec.contract` or `conform(contract=...)` layer applied. Preset-only
    contracts raise the legacy `fields_match` errors on violation. Any
    explicit layer (via `resolve_contract`) flips this to `False`, after
    which violations raise `SchemaDriftError` instead.
    """

    extra_columns: str = "evolve"
    missing_columns: str = "skip"
    data_type: str = "coerce"
    keys: str = "ignore"
    mapping: str = "by_name"          # by_name | positional
    count_must_match: bool = False    # exact guard
    minimum_overlap: int = 0          # partial guard
    from_preset: bool = True          # provenance: column dims set by a
                                      # fields_match preset raise the legacy
                                      # conform errors; explicit contract
                                      # freezes raise SchemaDriftError


FIELDS_MATCH_PRESETS: dict[str, ConformContract] = {
    "open":     ConformContract(extra_columns="evolve",  missing_columns="skip"),
    "exact":    ConformContract(extra_columns="freeze",  missing_columns="freeze",
                                mapping="positional", count_must_match=True),
    "equal":    ConformContract(extra_columns="freeze",  missing_columns="freeze"),
    "subset":   ConformContract(extra_columns="discard", missing_columns="freeze"),
    "superset": ConformContract(extra_columns="freeze",  missing_columns="skip"),
    "partial":  ConformContract(extra_columns="discard", missing_columns="skip",
                                minimum_overlap=1),
}


def validate_contract_dict(value: Mapping[str, str]) -> None:
    """Reject unknown dimensions and nonsensical mode x dimension pairs."""
    for dim, mode in value.items():
        if dim not in _DIMENSION_MODES:
            raise ConformError(f"unknown contract dimension {dim!r}")
        if mode not in _DIMENSION_MODES[dim]:
            raise ConformError(
                f"invalid mode {mode!r} for dimension {dim!r}; "
                f"allowed: {sorted(_DIMENSION_MODES[dim])}"
            )


def resolve_contract(
    fields_match: str,
    spec_contract: Optional[Mapping[str, str]] = None,
    override: Optional[Union[str, Mapping[str, str]]] = None,
) -> ConformContract:
    """Preset(fields_match) <- TypeSpec.contract <- conform(contract=) override.

    A scalar override ("freeze") applies to the extension dimensions only.
    Any explicit dict/scalar layer marks the contract non-preset (freeze on a
    column dimension then raises SchemaDriftError, not the legacy errors).
    """
    contract = FIELDS_MATCH_PRESETS[fields_match]
    for layer in (spec_contract, override):
        if layer is None:
            continue
        if isinstance(layer, str):
            layer = {dim: layer for dim in _EXTENSION_DIMENSIONS}
        validate_contract_dict(layer)
        contract = replace(contract, from_preset=False, **dict(layer))  # type: ignore[arg-type]
    return contract
