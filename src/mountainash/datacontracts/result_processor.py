"""ValidationResultProcessor — failure-case analysis over the unified schema.

Consumes the spec §8 failure-case frame (check_id/check_kind/column/outcome/
value/message/key-fields/row_number/row). Keyed-only capabilities gate with
IdentityRequiredError (spec §7); nothing silently falls back to positional
identity. See tests/datacontracts/test_processor_compat.py for the pinned
per-method compatibility matrix.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import polars as pl_mod

import mountainash as ma
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.validation.errors import IdentityRequiredError
from mountainash.validation.identity import RowIdentity, require_keyed

if TYPE_CHECKING:
    import polars as pl


def _collect_polars(relation: Any) -> "pl.DataFrame":
    """Materialize a Relation built purely over ValidationResultProcessor's
    own Polars-only sources (spec section 13 step 6).

    Uses ``Relation.compile()`` -- the raw, unmaterialized native plan --
    instead of ``Relation.collect()``, so the ONLY conversion boundary this
    processor's own materialization records is
    ``RESULT_PROCESSOR_POLARS_MATERIALIZE`` (route=RESULT_PROCESSING), never
    ``Relation.collect()``'s own generic NATIVE_MATERIALIZATION-routed
    ``POLARS_LAZY_COLLECT``. Fails closed if the compiled plan is ever not
    Polars -- every processor source is contractually Polars-only.
    """
    compiled = relation.compile()
    if isinstance(compiled, pl_mod.LazyFrame):
        return cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.RESULT_PROCESSOR_POLARS_MATERIALIZE, compiled.collect),
        )
    if isinstance(compiled, pl_mod.DataFrame):
        return compiled
    raise TypeError(
        "ValidationResultProcessor requires Polars-only relations; "
        f"got a compiled plan of type {type(compiled).__name__}"
    )


class ValidationResultProcessor:
    """Processes unified failure cases using mountainash relations."""

    def __init__(
        self,
        failure_cases: "pl.DataFrame",
        *,
        source_data: "pl.DataFrame | None" = None,
        natural_key: "list[str] | None" = None,
        identity: "RowIdentity | None" = None,
        check_summaries: "pl.DataFrame | None" = None,
        validator_name: str | None = None,
    ) -> None:
        if identity is None:
            identity = (
                RowIdentity("keyed", tuple(natural_key))
                if natural_key
                else RowIdentity("none")
            )
        self._identity = identity
        self._failure_cases = failure_cases
        self._source_data = source_data
        self._natural_key = (
            natural_key if natural_key is not None else (list(identity.key_fields) or None)
        )
        self._check_summaries = check_summaries
        self._validator_name = validator_name
        self._rel = ma.relation(failure_cases)
        self._enriched: "pl.DataFrame | None" = None

    # -- raw access / filters -------------------------------------------------

    def failure_cases(self) -> "pl.DataFrame":
        return self._failure_cases

    def failure_cases_for_column(self, column: str) -> "pl.DataFrame":
        return _collect_polars(self._rel.filter(ma.col("column").eq(ma.lit(column))))

    def failure_cases_for_rule(self, rule_id: str) -> "pl.DataFrame":
        return _collect_polars(self._rel.filter(ma.col("check_id").eq(ma.lit(rule_id))))

    def failure_count(self) -> int:
        return len(self._failure_cases)

    def failure_count_by_column(self) -> "pl.DataFrame":
        return _collect_polars(
            self._rel.filter(ma.col("column").is_not_null())
            .group_by("column")
            .agg(ma.count_records().alias("count"))
        )

    def failure_count_by_rule(self) -> "pl.DataFrame":
        return _collect_polars(
            self._rel.group_by("check_id").agg(ma.count_records().alias("count"))
        )

    # -- enrichment -------------------------------------------------------------

    def enriched_failure_cases(self) -> "pl.DataFrame":
        """Standardised failure cases: rule_id/column_name/row_index/value_str.

        `check_kind` replaces the removed Pandera `schema_context`;
        `row_index` is always present and gated on NULLNESS, not absence.
        """
        if self._enriched is not None:
            return self._enriched

        rel = ma.relation(self._failure_cases)
        enriched = rel.with_columns(
            ma.lit(self._validator_name).alias("validator_name"),
            ma.col("check_id").alias("rule_id"),
            ma.col("column").alias("column_name"),
            ma.col("row_number").alias("row_index"),
            ma.col("value").alias("value_str"),
        ).select(
            "validator_name", "rule_id", "check_kind",
            "column_name", "row_index", "value_str",
            *self._identity.key_fields,
        )

        if self._natural_key is not None:
            enriched = enriched.with_columns(
                ma.col("column_name").is_in(self._natural_key).alias("column_is_natural_key"),
            )

        result = _collect_polars(enriched)
        self._enriched = result
        return result

    # -- profiled counts (identity-gated) ----------------------------------------

    def _identity_columns(self, feature: str) -> "list[str]":
        if self._identity.kind == "keyed":
            return list(self._identity.key_fields)
        if self._identity.kind == "row_number":
            return ["row_index"]
        raise IdentityRequiredError(
            f"{feature} requires keyed or row_number identity; current tier is 'none'"
        )

    def _unique_failing(self, *dims: str) -> Any:
        identity_cols = self._identity_columns("profiled failure counts")
        rel = ma.relation(self.enriched_failure_cases())
        if self._identity.kind == "row_number":
            rel = rel.filter(ma.col("row_index").is_not_null())
        return rel.select(*dims, *identity_cols).unique()

    def profiled_failure_count(self) -> "pl.DataFrame":
        return _collect_polars(
            self._unique_failing("validator_name")
            .group_by("validator_name")
            .agg(ma.count_records().alias("unique_row_count"))
        )

    def profiled_failure_count_by_column(self) -> "pl.DataFrame":
        return _collect_polars(
            self._unique_failing("validator_name", "column_name")
            .group_by("validator_name", "column_name")
            .agg(ma.count_records().alias("unique_row_count"))
        )

    def profiled_failure_count_by_value(self) -> "pl.DataFrame":
        return _collect_polars(
            self._unique_failing("validator_name", "column_name", "value_str")
            .group_by("validator_name", "column_name", "value_str")
            .agg(ma.count_records().alias("unique_row_count"))
        )

    def profiled_failure_count_by_rule(self) -> "pl.DataFrame":
        return _collect_polars(
            self._unique_failing("validator_name", "rule_id")
            .group_by("validator_name", "rule_id")
            .agg(ma.count_records().alias("unique_row_count"))
        )

    # -- rule health -----------------------------------------------------------

    def malformed_rules(self) -> "pl.DataFrame":
        """Rules whose execution errored — from CheckSummary(status='error').

        (Pandera-era heuristic 'null index means the rule errored' is gone:
        errored rules produce no failure-case rows at all.)
        """
        import polars as pl_mod

        if self._check_summaries is None:
            return pl_mod.DataFrame(
                schema={"rule_id": pl_mod.String, "error": pl_mod.String}
            )
        return (
            self._check_summaries
            .filter(pl_mod.col("status") == "error")
            .select(pl_mod.col("check_id").alias("rule_id"), pl_mod.col("error"))
        )

    def rules_well_formed(self) -> bool:
        return len(self.malformed_rules()) == 0

    # -- keyed-only capabilities -------------------------------------------------

    def _resolve_source_data(self, source_data: Any | None) -> Any:
        resolved = source_data if source_data is not None else self._source_data
        if resolved is None:
            raise ValueError(
                "source_data is required for pivot operations. "
                "Pass it to the constructor or to this method."
            )
        return resolved

    def pivot_all_fields(self, source_data: Any | None = None) -> "pl.DataFrame":
        """Wide pivot: all source field values for failing rows (keyed only —
        row_number is a diagnostic ordinal and never joins back)."""
        require_keyed(self._identity, feature="pivot_all_fields")
        resolved = self._resolve_source_data(source_data)
        keys = list(self._identity.key_fields)

        failures = (
            ma.relation(self.enriched_failure_cases())
            .select("rule_id", *keys)
            .unique()
        )
        joined = failures.join(ma.relation(resolved), on=keys, how="inner")
        return _collect_polars(joined)

    def pivot_key_fields(self, source_data: Any | None = None) -> "pl.DataFrame":
        """Key field values per failing rule — straight from the failure cases
        (source_data accepted for back-compat; no longer needed)."""
        require_keyed(self._identity, feature="pivot_key_fields")
        chain = (
            ma.relation(self.enriched_failure_cases())
            .select("rule_id", *self._identity.key_fields)
            .unique()
        )
        return _collect_polars(chain)

    def _normalise_rule_metadata(self, rule_metadata: Any) -> "pl.DataFrame":
        import polars as pl_mod

        if isinstance(rule_metadata, dict):
            rows = [
                {
                    "rule_id": rule_id,
                    "error_message": meta["error_message"],
                    "fields": meta["fields"],
                }
                for rule_id, meta in rule_metadata.items()
            ]
            return pl_mod.DataFrame(rows)
        if isinstance(rule_metadata, pl_mod.DataFrame):
            return rule_metadata
        return _collect_polars(ma.relation(rule_metadata))

    def interpolate_messages(
        self, rule_metadata: Any, source_data: Any | None = None
    ) -> "pl.DataFrame":
        """Join failure cases with rule metadata via key fields, replace
        {field} placeholders with actual source values (keyed only)."""
        import polars as pl_mod

        require_keyed(self._identity, feature="interpolate_messages")
        resolved_source = self._resolve_source_data(source_data)
        meta_df = self._normalise_rule_metadata(rule_metadata)

        dup_ids = meta_df.group_by("rule_id").len().filter(pl_mod.col("len") > 1)
        if len(dup_ids) > 0:
            raise ValueError(
                f"rule_metadata contains duplicate rule_ids: {dup_ids['rule_id'].to_list()}"
            )

        keys = list(self._identity.key_fields)
        failures = ma.relation(self.enriched_failure_cases()).select(
            "validator_name", "rule_id", *keys
        ).unique()
        joined_source = failures.join(ma.relation(resolved_source), on=keys, how="inner")
        with_meta = joined_source.join(ma.relation(meta_df), on=["rule_id"], how="inner")
        result_df = _collect_polars(with_meta)

        result_df = result_df.with_columns(
            pl_mod.col("error_message").alias("error_message_template"),
        )
        for rule_row in meta_df.to_dicts():
            rule_id, fields = rule_row["rule_id"], rule_row["fields"]
            if not fields:
                continue
            mask = result_df["rule_id"] == rule_id
            for field_name in fields:
                if field_name not in result_df.columns:
                    continue
                result_df = result_df.with_columns(
                    pl_mod.when(mask)
                    .then(
                        pl_mod.col("error_message").str.replace(
                            "{" + field_name + "}",
                            pl_mod.col(field_name).cast(pl_mod.Utf8),
                            literal=True,
                        )
                    )
                    .otherwise(pl_mod.col("error_message"))
                    .alias("error_message")
                )
        return result_df

    # -- verdict helpers ---------------------------------------------------------

    @staticmethod
    def _blocking_frame_filter() -> "pl_mod.Expr":
        # spec §8 third amendment: frame re-expression of is_blocking() —
        # error always blocks; failed blocks only at blocking severity
        return (pl_mod.col("status") == "error") | (
            (pl_mod.col("status") == "failed")
            & (pl_mod.col("severity") == "blocking")
        )

    def passed(self) -> bool:
        # spec §8: NOT a second owner of pass semantics — statuses (composed
        # with severity via is_blocking) not failure-row emptiness decide
        # (scalar/errored checks emit no rows).
        # Frame fallback only for bare failure-frame construction.
        if self._check_summaries is not None:
            return (
                self._check_summaries.filter(self._blocking_frame_filter()).height == 0
            )
        return len(self._failure_cases) == 0

    def passed_for_column(self, column: str) -> bool:
        # failure-row-based by nature: column verdicts only exist through
        # failure rows (summaries have no column dimension)
        return len(self.failure_cases_for_column(column)) == 0

    def passed_for_rule(self, rule_id: str) -> bool:
        if self._check_summaries is not None:
            return (
                self._check_summaries.filter(
                    (pl_mod.col("check_id") == rule_id) & self._blocking_frame_filter()
                ).height
                == 0
            )
        return len(self.failure_cases_for_rule(rule_id)) == 0
