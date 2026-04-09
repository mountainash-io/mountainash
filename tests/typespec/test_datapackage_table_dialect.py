from mountainash.typespec.datapackage import TableDialect


def test_default_dialect_round_trips_to_empty_dict():
    d = TableDialect()
    assert d.to_descriptor() == {}


def test_csv_dialect_round_trips():
    raw = {
        "delimiter": ";",
        "lineTerminator": "\r\n",
        "quoteChar": "'",
        "doubleQuote": False,
        "escapeChar": "\\",
        "nullSequence": "NA",
        "skipInitialSpace": True,
        "header": True,
        "headerRows": [1],
        "headerJoin": " ",
        "commentChar": "#",
        "caseSensitiveHeader": False,
        "csvddfVersion": "1.2",
    }
    d = TableDialect.from_descriptor(raw)
    assert d.to_descriptor() == raw


def test_unknown_keys_are_dropped_silently():
    raw = {"delimiter": ",", "futureFlag": True}
    d = TableDialect.from_descriptor(raw)
    assert "futureFlag" not in d.to_descriptor()


def test_polars_kwargs_translation():
    d = TableDialect.from_descriptor(
        {"delimiter": "|", "header": True, "skipInitialSpace": True}
    )
    kw = d.to_polars_read_csv_kwargs()
    assert kw == {"separator": "|", "has_header": True}
