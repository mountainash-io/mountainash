"""Nested member/element requirements report their own path, severity and uniqueness scope.

Nested requirements are checked by the existing ValueRule machinery: a failed
row reports each violated member/element location (RFC 6901 pointer, literal
member names) through the same ``instance_path``/``validator`` failure columns
JSON Schema diagnostics use. Each definition's own severity (or the system
default; never the enclosing field's) decides whether its failure blocks.
Uniqueness keeps the field meaning in its active row domain: a struct member is
unique across the containing records, an element definition within each
containing collection.
"""

import polars as pl

from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation import ValidationRunner


def _record(**members):
    return FieldDefinition(type=UniversalType.OBJECT, fields=members)


def _collection(element, **kwargs):
    return FieldDefinition(type=UniversalType.ARRAY, element=element, **kwargs)


def _integer(**kwargs):
    return FieldDefinition(type=UniversalType.INTEGER, **kwargs)


def _run(definition, values, dtype):
    """Conform and check one nested column; ``k`` identifies each source row."""
    plan = compile_datacontract(
        TableSchema(fields_match="open", fields={"payload": definition})
    )
    frame = pl.DataFrame(
        {
            "k": list(range(len(values))),
            "payload": pl.Series("payload", values, dtype=dtype),
        }
    )
    return ValidationRunner().validate_relation(frame, plan=plan)


def _cases(result, check_id):
    return result.failure_cases.filter(pl.col("check_id") == check_id)


def _failed_rows(result, check_id_prefix):
    """Source row keys that failed any check whose id starts with the prefix."""
    cases = result.failure_cases.filter(
        pl.col("check_id").str.starts_with(check_id_prefix)
    )
    if cases.height == 0:
        return []
    return sorted(set(cases["row"].struct.field("k").to_list()))


def _summary(result, check_id):
    frame = result.check_summaries.filter(pl.col("check_id") == check_id)
    assert frame.height == 1, (check_id, result.check_summaries["check_id"].to_list())
    return frame.row(0, named=True)


# -- member / element paths ---------------------------------------------------


def test_member_violation_reports_its_member_path_and_constraint() -> None:
    definition = _record(age=_integer(minimum=0))
    result = _run(definition, [{"age": -1}, {"age": 5}], pl.Struct({"age": pl.Int64}))

    cases = _cases(result, "payload_nested")
    assert cases["instance_path"].to_list() == ["/age"]
    assert cases["validator"].to_list() == ["minimum"]
    assert cases["row"].struct.field("k").to_list() == [0]


def test_missing_required_member_reports_the_member_path() -> None:
    definition = _record(age=_integer(required=True))
    result = _run(definition, [{"age": None}], pl.Struct({"age": pl.Int64}))

    cases = _cases(result, "payload_nested")
    assert cases["instance_path"].to_list() == ["/age"]
    assert cases["validator"].to_list() == ["required"]


def test_element_violation_reports_the_element_index() -> None:
    definition = _collection(_integer(minimum=0))
    result = _run(definition, [[1, -1]], pl.List(pl.Int64))

    assert _cases(result, "payload_nested")["instance_path"].to_list() == ["/1"]


def test_every_violation_in_one_row_is_reported_once_per_location() -> None:
    definition = _collection(_record(qty=_integer(minimum=1)))
    dtype = pl.List(pl.Struct({"qty": pl.Int64}))
    result = _run(definition, [[{"qty": 0}, {"qty": 1}, {"qty": 0}]], dtype)

    cases = _cases(result, "payload_nested")
    assert sorted(cases["instance_path"].to_list()) == ["/0/qty", "/2/qty"]
    assert _summary(result, "payload_nested")["fail_count"] == 1  # one failing source row


def test_literal_member_names_stay_distinct_from_nested_traversal() -> None:
    """A dotted or slashed member name is one segment; nesting is separate segments."""
    definition = _record(
        **{
            "a.b": _integer(minimum=0),
            "c/d": _integer(minimum=0),
            "x": _record(y=_integer(minimum=0)),
        }
    )
    dtype = pl.Struct({"a.b": pl.Int64, "c/d": pl.Int64, "x": pl.Struct({"y": pl.Int64})})
    result = _run(definition, [{"a.b": -1, "c/d": -1, "x": {"y": -1}}], dtype)

    assert sorted(_cases(result, "payload_nested")["instance_path"].to_list()) == [
        "/a.b",
        "/c~1d",
        "/x/y",
    ]


def test_member_json_schema_diagnostics_extend_the_member_path() -> None:
    meta = FieldDefinition(
        type=UniversalType.OBJECT,
        fields={"id": _integer()},
        json_schema={
            "type": "object",
            "properties": {"id": {"type": "integer", "minimum": 1}},
        },
    )
    definition = _record(meta=meta)
    dtype = pl.Struct({"meta": pl.Struct({"id": pl.Int64})})
    result = _run(definition, [{"meta": {"id": 0}}, {"meta": {"id": 3}}], dtype)

    cases = _cases(result, "payload_nested")
    assert cases["instance_path"].to_list() == ["/meta/id"]
    assert cases["validator"].to_list() == ["minimum"]
    assert cases["row"].struct.field("k").to_list() == [0]


def test_member_geojson_is_checked_and_reports_its_member_path() -> None:
    from mountainash.validation import ValueRule, ValueValidatorKey

    definition = _record(shape=FieldDefinition(type=UniversalType.GEOJSON))
    ring = pl.List(pl.List(pl.List(pl.Float64)))
    dtype = pl.Struct({"shape": pl.Struct({"type": pl.String, "coordinates": ring})})
    open_ring = [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]]
    closed_ring = [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]]
    frame = pl.DataFrame(
        {
            "k": [0, 1],
            "payload": pl.Series(
                "payload",
                [
                    {"shape": {"type": "Polygon", "coordinates": open_ring}},
                    {"shape": {"type": "Polygon", "coordinates": closed_ring}},
                ],
                dtype=dtype,
            ),
        }
    )
    import mountainash as ma

    result = ValidationRunner().validate_relation(
        ma.relation(frame),
        [
            ValueRule(
                id="payload_nested",
                fields=["payload"],
                validator=ValueValidatorKey.NESTED,
                options={"definition": definition},
            )
        ],
    )

    cases = _cases(result, "payload_nested")
    assert cases["instance_path"].to_list() == ["/shape/coordinates/0"]
    assert cases["validator"].to_list() == ["geojson.ring_closed"]
    assert cases["row"].struct.field("k").to_list() == [0]


# -- severity -----------------------------------------------------------------


def test_member_warning_does_not_block_while_member_blocking_does() -> None:
    definition = _record(
        advisory=_integer(minimum=0, severity="warning"),
        mandatory=_integer(minimum=0),
    )
    dtype = pl.Struct({"advisory": pl.Int64, "mandatory": pl.Int64})

    advisory_only = _run(definition, [{"advisory": -1, "mandatory": 1}], dtype)
    assert _summary(advisory_only, "payload_nested_warning")["status"] == "failed"
    assert _summary(advisory_only, "payload_nested_warning")["severity"] == "warning"
    assert _summary(advisory_only, "payload_nested")["status"] == "passed"
    assert _cases(advisory_only, "payload_nested_warning")["instance_path"].to_list() == [
        "/advisory"
    ]
    assert advisory_only.passes

    mandatory = _run(definition, [{"advisory": 1, "mandatory": -1}], dtype)
    assert _summary(mandatory, "payload_nested")["status"] == "failed"
    assert _summary(mandatory, "payload_nested")["severity"] == "blocking"
    assert _summary(mandatory, "payload_nested_warning")["status"] == "passed"
    assert not mandatory.passes


def test_direct_nested_rule_owns_only_the_severity_it_declares() -> None:
    """A hand-built nested rule applies the same member severities as a compiled one."""
    import mountainash as ma
    from mountainash.validation import ValueRule, ValueValidatorKey

    definition = _record(
        advisory=_integer(minimum=0, severity="warning"),
        mandatory=_integer(minimum=0),
    )
    frame = pl.DataFrame(
        {"payload": pl.Series("payload", [{"advisory": -1, "mandatory": -1}],
                              dtype=pl.Struct({"advisory": pl.Int64, "mandatory": pl.Int64}))}
    )

    def paths(severity):
        result = ValidationRunner().validate_relation(
            ma.relation(frame),
            [
                ValueRule(
                    id="nested",
                    fields=["payload"],
                    validator=ValueValidatorKey.NESTED,
                    options={"definition": definition, "severity": severity},
                    severity=severity,
                )
            ],
        )
        return result.failure_cases["instance_path"].to_list()

    assert paths("warning") == ["/advisory"]
    assert paths("blocking") == ["/mandatory"]


def test_element_severity_comes_from_the_element_definition() -> None:
    definition = _collection(_integer(minimum=0, severity="warning"))
    result = _run(definition, [[1, -1]], pl.List(pl.Int64))

    assert _summary(result, "payload_nested_warning")["status"] == "failed"
    assert _cases(result, "payload_nested_warning")["instance_path"].to_list() == ["/1"]
    assert _summary(result, "payload_nested")["status"] == "passed"
    assert result.passes


def test_enclosing_field_severity_is_not_inherited_by_members() -> None:
    """Severity belongs to each definition; an unspecified member uses the system default."""
    definition = FieldDefinition(
        type=UniversalType.OBJECT,
        fields={"age": _integer(minimum=0)},
        severity="warning",
    )
    result = _run(definition, [{"age": -1}], pl.Struct({"age": pl.Int64}))

    assert _summary(result, "payload_nested")["severity"] == "blocking"
    assert _summary(result, "payload_nested")["status"] == "failed"
    assert not result.passes


# -- uniqueness scope ---------------------------------------------------------


def test_struct_member_unique_applies_across_the_containing_records() -> None:
    definition = _record(id=_integer(unique=True))
    dtype = pl.Struct({"id": pl.Int64})
    values = [{"id": 1}, {"id": 1}, {"id": 2}, {"id": None}, {"id": None}]

    result = _run(definition, values, dtype)

    assert _failed_rows(result, "payload_nested_unique") == [0, 1]  # nulls never collide
    assert result.failure_cases.select("instance_path", "validator").rows() == [
        ("/id", "unique"), ("/id", "unique")
    ]
    assert result.check_summaries["fail_count"].sum() == 2


def test_element_unique_applies_within_each_containing_collection() -> None:
    definition = _collection(_integer(unique=True))
    # the 1 repeated across unrelated arrays is not a duplicate
    result = _run(definition, [[1, 1, 1], [1, 2], [2]], pl.List(pl.Int64))

    assert _failed_rows(result, "payload_nested_unique") == [0]
    assert result.failure_cases.select("instance_path", "validator").rows() == [
        ("/0", "unique"), ("/1", "unique"), ("/2", "unique")
    ]
    assert result.check_summaries["fail_count"].sum() == 1


def test_struct_member_within_collection_elements_is_unique_per_collection() -> None:
    definition = _collection(_record(sku=FieldDefinition(type=UniversalType.STRING, unique=True)))
    dtype = pl.List(pl.Struct({"sku": pl.String}))
    values = [
        [{"sku": "a"}, {"sku": "a"}],
        [{"sku": "a"}, {"sku": "b"}],
        [{"sku": "a"}],
    ]

    result = _run(definition, values, dtype)

    assert _failed_rows(result, "payload_nested_unique") == [0]
    assert result.failure_cases.select("instance_path", "validator").rows() == [
        ("/0/sku", "unique"), ("/1/sku", "unique")
    ]
    assert result.check_summaries["fail_count"].sum() == 1


def test_root_collection_unique_still_compares_whole_cells_across_rows() -> None:
    definition = _collection(_integer(), unique=True)
    result = _run(definition, [[1], [1], [2]], pl.List(pl.Int64))

    assert _failed_rows(result, "payload_unique") == [0, 1]
    assert _failed_rows(result, "payload_nested_unique") == []
