<!--
DRAFT ONLY — NOT FILED.

Tracked internally as DP-V2-03 in the Frictionless v2 upstream discrepancy
backlog. No matching issue or pull request was found in
https://github.com/frictionlessdata/datapackage as of 2026-08-19.
Copy the section below the divider into a new upstream issue when someone
decides to file it. Do not open the upstream issue as part of landing this
file.
-->

# Draft: v2 Table Dialect profile has a v1 `$schema` default

---

## Bug

In `public/profiles/2.0/tabledialect.json`, the default for the `$schema`
property points to the v1 Table Dialect profile:

```text
https://datapackage.org/profiles/1.0/tabledialect.json
```

The containing profile is version 2.0. A validator or model generator can
therefore add a v1 profile URI to a v2 descriptor.

### Expected behavior

The v2 profile should either use the v2 Table Dialect profile URI as its
default or define no default.

### Suggested fix

Change the default to the v2 profile URI, or remove the default when no
implicit profile should be selected.

### Affected source

- `public/profiles/2.0/tabledialect.json`
- `properties.$schema.default`

Verified at commit:
`6a201af8ed2eacbb3a2440e82e4c55d5807f9c09`.

### Downstream impact

A model generator can insert a v1 Table Dialect URI into v2 output. That URI
can select the wrong version during later descriptor processing.
