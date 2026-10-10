"""Item 48 PR-D: `keys` dimension — DAG constraint context + KeyDrift.

Exercises the full wiring: ``RelationDAG.collect()``/``execute()`` build a
``KeyDriftContext`` (+1 optional visitor param, analogous to
``ref_resolver``) and pass it to ``UnifiedRelationVisitor``;
``apply_conform`` uses it to child-scope-evaluate declared foreign keys
(``RelationDAG.constraints_for``) against the conformed output. Assessment
is child-scoped only (finding 9): FKs where this resource is the
*reference* (parent) side are not evaluated.

``ConformDrift.key_changes`` distinguishes ``None`` (not assessed — no
DAG/FK context) from ``[]`` (assessed, clean) from a populated list
(assessed, drift found) — see conform/drift.py.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.drift import KeyDrift
from mountainash.conform.errors import SchemaDriftError
from mountainash.core.dtypes import MountainashDtype
from mountainash.relations.dag.dag import RelationDAG
from mountainash.typespec.spec import FieldSpec, ForeignKey, ForeignKeyReference, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _fk(fields, resource, ref_fields):
    return ForeignKey(
        fields=list(fields),
        reference=ForeignKeyReference(resource=resource, fields=list(ref_fields)),
    )


def _open_spec(*fields):
    return TypeSpec(fields=list(fields), fields_match="open")


class TestFrameLevelNotAssessed:
    """A bare Relation.conform() with no owning RelationDAG never assesses
    keys -- key_changes stays None (not [])."""

    def test_key_changes_stays_none(self):
        spec = _open_spec(FieldSpec(name="id", type=UniversalType.INTEGER))
        result = ma.relation(pl.DataFrame({"id": [1, 2]})).conform(spec).collect_with_drift()

        assert result.drift.key_changes is None


class TestDagCleanAssessment:
    """A DAG-collected conform with zero declared FKs is still ASSESSED
    (a KeyDriftContext was available) -- key_changes is [], not None."""

    def test_no_declared_fks_is_assessed_clean(self):
        dag = RelationDAG()
        spec = _open_spec(FieldSpec(name="id", type=UniversalType.INTEGER))
        dag.add("orders", ma.relation(pl.DataFrame({"id": [1, 2]})).conform(spec))

        coll = dag.collect_with_drift("orders")

        assert len(coll.drifts) == 1
        assert coll.drifts[0].key_changes == []


class TestFkFieldDropped:
    """finding: a declared FK field that conform silently skipped (source
    column absent, missing_columns='skip' default) is no longer in the
    output -- the FK is now dangling on the child side."""

    def test_missing_source_column_reported_as_dropped(self):
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))
        # "customer_id" is declared but the source frame doesn't have it --
        # open/skip silently omits it from the conformed output.
        spec = _open_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="customer_id", type=UniversalType.INTEGER),
        )
        dag.add("orders", ma.relation(pl.DataFrame({"id": [1, 2]})).conform(spec))
        dag.add_constraint(
            "orders", _fk(["customer_id"], "customers", ["id"]),
        )

        coll = dag.collect_with_drift("orders")

        assert coll.drifts[0].key_changes == [
            KeyDrift(
                kind="fk_field_dropped", fields=["customer_id"],
                reference="customers", action="ignore",
            )
        ]
        assert coll.drifts[0].compatible is False

    def test_undeclared_fk_field_is_also_dropped(self):
        """A FK field that was never a spec field at all is equally dropped."""
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))
        spec = _open_spec(FieldSpec(name="id", type=UniversalType.INTEGER))
        dag.add(
            "orders",
            ma.relation(pl.DataFrame({"id": [1, 2]})).conform(
                spec, contract={"extra_columns": "discard"},
            ),
        )
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))

        coll = dag.collect_with_drift("orders")

        drift = coll.drifts[0].key_changes[0]
        assert drift.kind == "fk_field_dropped"
        assert drift.fields == ["customer_id"]


class TestDanglingReference:
    """finding: the referenced resource's fields aren't resolvable."""

    def test_reference_field_absent_on_parent(self):
        dag = RelationDAG()
        # "customers" exists but has no "id" column at all.
        dag.add("customers", ma.relation(pl.DataFrame({"name": ["a", "b"]})))
        spec = _open_spec(FieldSpec(name="customer_id", type=UniversalType.INTEGER))
        dag.add(
            "orders",
            ma.relation(pl.DataFrame({"customer_id": [1, 2]})).conform(spec),
        )
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))

        coll = dag.collect_with_drift("orders")

        assert coll.drifts[0].key_changes == [
            KeyDrift(
                kind="dangling_reference", fields=["customer_id"],
                reference="customers", action="ignore",
            )
        ]

    def test_reference_resource_not_resolvable(self):
        """Direct constraint_metadata poke (mirrors
        test_constraint_metadata.py's topology-only-edge test) exercises the
        schema_of() KeyError branch, which add_constraint()'s target
        validation makes unreachable through the public API."""
        dag = RelationDAG()
        spec = _open_spec(FieldSpec(name="customer_id", type=UniversalType.INTEGER))
        dag.add(
            "orders",
            ma.relation(pl.DataFrame({"customer_id": [1, 2]})).conform(spec),
        )
        fk = _fk(["customer_id"], "ghost", ["id"])
        edge = ("ghost", "orders")
        dag.constraint_edges.add(edge)
        dag.constraint_metadata[edge] = [fk]

        coll = dag.collect_with_drift("orders")

        assert coll.drifts[0].key_changes == [
            KeyDrift(
                kind="dangling_reference", fields=["customer_id"],
                reference="ghost", action="ignore",
            )
        ]


class TestFkTypeMismatch:
    """finding 8: only assessed when BOTH sides' canonical dtypes are known;
    links the data_type dimension's 'evolve' policy to the keys dimension --
    an evolved child column's actual (not declared) dtype is compared
    against the parent's declared dtype."""

    def test_evolved_child_column_links_to_keys_dimension(self):
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))  # I64
        spec = _open_spec(FieldSpec(name="customer_id", type=UniversalType.INTEGER))
        dag.add(
            "orders",
            ma.relation(pl.DataFrame({"customer_id": ["1", "2"]})).conform(
                spec, contract={"data_type": "evolve"},
            ),
        )
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))

        coll = dag.collect_with_drift("orders")

        assert coll.drifts[0].key_changes == [
            KeyDrift(
                kind="fk_type_mismatch", fields=["customer_id"],
                reference="customers", declared=MountainashDtype.I64,
                actual=MountainashDtype.STRING, action="ignore",
            )
        ]

    def test_safe_cast_is_not_a_mismatch(self):
        """actual I32 -> declared I64 is a safe widening cast: no drift."""
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))  # I64
        spec = _open_spec(FieldSpec(name="customer_id", type=UniversalType.INTEGER))
        dag.add(
            "orders",
            ma.relation(pl.DataFrame({"customer_id": pl.Series([1, 2], dtype=pl.Int32)}))
            .conform(spec, contract={"data_type": "evolve"}),
        )
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))

        coll = dag.collect_with_drift("orders")

        assert coll.drifts[0].key_changes == []


class TestPerNodeContextInDependencyLoop:
    """A bare-conformed DEPENDENCY compiled inside dag.collect(<other target>)
    must have its key assessment run against ITS OWN name/constraints — the
    DAG re-points key_context.resource_name per node in the dependency loop
    (dag.py _compile_with_refs), never leaving it pinned to the top-level
    target."""

    @staticmethod
    def _dag_with_conformed_dependency(orders_frame: pl.DataFrame) -> RelationDAG:
        """customers <- clean_orders (bare .conform() dep) <- active_orders (target).

        clean_orders carries its own FK (customer_id -> customers.id).
        active_orders (the collected target) carries a DIFFERENT FK on a
        field ("status") that clean_orders' conformed output never emits —
        deliberate bait: if the dependency's assessment were misattributed
        to the target's name, that FK would spuriously trip as
        fk_field_dropped against the dependency's output.
        """
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))
        spec = _open_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="customer_id", type=UniversalType.INTEGER),
        )
        dag.add("clean_orders", ma.relation(orders_frame).conform(spec))
        dag.add("active_orders", dag.ref("clean_orders").filter(ma.col("id").gt(0)))
        dag.add_constraint(
            "clean_orders", _fk(["customer_id"], "customers", ["id"]),
        )
        dag.add_constraint(
            "active_orders", _fk(["status"], "customers", ["id"]),
        )
        return dag

    def test_clean_dependency_no_spurious_drift_from_target_name(self):
        """The dependency satisfies its FK; collecting a DIFFERENT target
        must assess it against clean_orders' own constraints (clean), never
        misattribute the target's would-trip "status" FK to it."""
        dag = self._dag_with_conformed_dependency(
            pl.DataFrame({"id": [1, 2], "customer_id": [1, 2]})
        )

        coll = dag.collect_with_drift("active_orders")

        # Exactly one conform node compiled (the dependency's); assessed
        # against clean_orders' own FK, which is satisfied -> assessed clean.
        assert len(coll.drifts) == 1
        assert coll.drifts[0].key_changes == []

    def test_dependency_own_violation_caught_under_different_target(self):
        """The dependency's OWN FK violation (its source frame lacks
        customer_id -> fk_field_dropped) is caught even though a different,
        unconstrained target is what's being collected."""
        dag = self._dag_with_conformed_dependency(
            pl.DataFrame({"id": [1, 2]})  # no customer_id -> open/skip drops it
        )

        coll = dag.collect_with_drift("active_orders")

        assert len(coll.drifts) == 1
        assert coll.drifts[0].key_changes == [
            KeyDrift(
                kind="fk_field_dropped", fields=["customer_id"],
                reference="customers", action="ignore",
            )
        ]


class TestFreezePolicy:
    """keys='freeze' raises SchemaDriftError with the KeyDrift attached,
    before compiling -- mirrors data_type/columns freeze behaviour."""

    def test_freeze_raises_with_key_drift_attached(self):
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))
        spec = _open_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="customer_id", type=UniversalType.INTEGER),
        )
        dag.add(
            "orders",
            ma.relation(pl.DataFrame({"id": [1, 2]})).conform(
                spec, contract={"keys": "freeze"},
            ),
        )
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))

        with pytest.raises(SchemaDriftError) as exc_info:
            dag.collect("orders")

        drift = exc_info.value.drift
        assert drift.key_changes == [
            KeyDrift(
                kind="fk_field_dropped", fields=["customer_id"],
                reference="customers", action="freeze",
            )
        ]

    def test_ignore_policy_does_not_raise(self):
        """Default keys='ignore' policy reports but never raises."""
        dag = RelationDAG()
        dag.add("customers", ma.relation(pl.DataFrame({"id": [1, 2]})))
        spec = _open_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="customer_id", type=UniversalType.INTEGER),
        )
        dag.add("orders", ma.relation(pl.DataFrame({"id": [1, 2]})).conform(spec))
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))

        result = dag.collect("orders")  # must not raise

        assert result is not None
