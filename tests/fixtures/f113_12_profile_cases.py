"""Shared profile and marker cases for F113-12 parity tests."""


_V1_PROFILE_PATHS_BY_HOST = {
    "datapackage.org": tuple(
        f"/profiles/1.0/{name}.json"
        for name in ("datapackage", "dataresource", "tabledialect", "tableschema")
    ),
    "specs.frictionlessdata.io": tuple(
        f"/schemas/{name}.json"
        for name in (
            "data-package",
            "data-resource",
            "tabular-data-resource",
            "tabular-data-package",
            "fiscal-data-package",
            "table-schema",
            "csv-dialect",
        )
    ),
    "frictionlessdata.io": tuple(
        f"/schemas/{name}.json"
        for name in (
            "data-package",
            "data-resource",
            "tabular-data-resource",
            "tabular-data-package",
            "fiscal-data-package",
            "table-schema",
            "csv-dialect",
        )
    ),
}

V1_PROFILE_URIS = tuple(
    f"{scheme}://{www}{host}{path}"
    for scheme in ("http", "https")
    for host, paths in _V1_PROFILE_PATHS_BY_HOST.items()
    for www in (("", "www.") if host != "datapackage.org" else ("",))
    for path in paths
)

# Each value is present-marker input plus the exact public required_form.
V1_DIALECT_MARKERS = (
    ({"caseSensitiveHeader": None}, "v2 dialect properties"),
    ({"csvddfVersion": None}, "v2 dialect properties"),
)
