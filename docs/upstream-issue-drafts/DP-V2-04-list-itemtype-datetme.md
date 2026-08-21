<!--
DRAFT ONLY — NOT FILED.

Tracked internally as DP-V2-04 in the Frictionless v2 upstream discrepancy
backlog. No matching issue or pull request was found in
https://github.com/frictionlessdata/datapackage as of 2026-08-19.
Copy the section below the divider into a new upstream issue when someone
decides to file it. Do not open the upstream issue as part of landing this
file.
-->

# Draft: Table Schema `list.itemType` documentation misspells `datetime` as `datetme`

---

## Bug

The `list` section of the v2 Table Schema documentation lists `datetme` as
an allowed `itemType` value:

https://datapackage.org/standard/table-schema/#list

The standard field type is `datetime`. `datetme` is not a standard field type.

### Expected behavior

The documented `itemType` vocabulary should use `datetime`.

### Suggested fix

Change `datetme` to `datetime` in the v2 Table Schema `list` section.

### Downstream impact

A reader can treat the misspelled token as part of the normative vocabulary.
A generated allow-list can reject the correct token or accept the wrong token.

Verified at commit:
`6a201af8ed2eacbb3a2440e82e4c55d5807f9c09`.
