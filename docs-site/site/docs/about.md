---
title: 'About This Manual'
description: 'What this manual is, who wrote it, and how it relates to the mountainash code repository'
---

# About This Manual

**Mountainash Core** is an intelligent textbook — a guided, chapter-by-chapter manual for the [mountainash](https://github.com/mountainash-io/mountainash) Python library, a cross-backend data expression and relational pipeline engine that compiles a single fluent API to Polars, pandas, PyArrow, DuckDB, Snowflake, BigQuery, and every backend that Ibis and Narwhals reach.

This site is not the library itself, and it is not API reference documentation. It is a companion manual that explains *why* mountainash is designed the way it is: how the expression system, relation AST, type system, conformance pipeline, ternary logic, and DAG orchestration fit together, and how to use them effectively in real projects. Where API reference tells you what a function does, this manual builds the mental model underneath it — with interactive diagrams (MicroSims) alongside the prose to make the architecture tangible rather than abstract.

## What's Here

- **[Home](index.md)** — the manual's landing page: what mountainash is, who it's for, and what you'll get out of working through it
- **[Chapters](chapters/index.md)** — 15 chapters and 200 concepts, ordered so each builds on the last, covering core infrastructure through the expression and relation systems to pipelines and DAG orchestration
- **Learning Graph** — the concept dependency structure underlying the chapter ordering
- **MicroSims** — interactive diagrams illustrating backend routing, AST construction, the conform pipeline, DAG validation, and more

See the [Package Overview](course-description.md) for a course-style breakdown of audience, prerequisites, and learning outcomes.

## Relationship to the Code Repository

This manual documents [mountainash-io/mountainash](https://github.com/mountainash-io/mountainash), the actual Python package. The manual and the library are versioned and maintained separately: the repository holds the source, tests, and API surface; this site holds the explanatory material built on top of it. If something in this manual is unclear, missing, or drifts from the library's current behavior, issues and contributions are welcome on the [GitHub repository](https://github.com/mountainash-io/mountainash).

## Authorship and License

This manual was written by **Nathaniel Ramm**, author of mountainash.

Copyright © 2026 Nathaniel Ramm. The content of this manual is licensed under [CC BY-NC-SA 4.0](license.md) (Attribution-NonCommercial-ShareAlike 4.0 International) — you're free to share and adapt it for non-commercial purposes with attribution, under the same license. See the [License](license.md) page for the full terms, and [Contact](contact.md) for commercial licensing inquiries or feedback on the manual itself.
