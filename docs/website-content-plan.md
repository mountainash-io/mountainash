# mountainash Website Content Plan

This document outlines the canonical narrative, structure, and key copy for the mountainash project website.

---

## 1. Hero: The One-Sentence Pitch

**"The Shared Language for the Data Ecosystem."**

*mountainash is an open-source data quality and rules platform that lets you write data logic once and run it everywhere — one schema drives validation, conformance, business rules, and test data generation across any analytical backend.*

---

## 2. The Core Product: Composable Data Logic

At its heart, mountainash is not just another dataframe library. It is a **composable logic layer** that serves as a modular shared language for the modern data ecosystem.

### Why Composability & Interoperability?
In the **Composable Data Stack**, organizations must be able to swap compute engines, transformation tools, and storage layers without rewriting their core business logic. mountainash enables this by providing a **modular, serializable format** for your operations.

*   **Build once, compose anywhere**: Author logic in a familiar, Polars-aligned Python API. Build complex pipelines from small, reusable, and testable components.
*   **Engine Interoperability**: Run the same logic on Polars, Ibis (SQL), Narwhals (pandas/PyArrow), or directly on high-performance engines like DataFusion.
*   **The Connective Tissue**: mountainash acts as the bridge between modular components, ensuring your data quality, rules, and transformations remain consistent across the entire stack.

---

## 3. Use Cases: Composable Logic in Action

The composable logic layer is the foundation; these are the primary use-cases built on top of it.

### Data Quality & Transformation
*   **Structural Conformance (`ma.conform`)**: Compile industry-standard schemas into automatic type casting, renaming, and null handling.
*   **Semantic Validation (`ma.datacontracts`)**: Define data contracts where business rules and column constraints run seamlessly on any backend.
*   **Frictionless Integration**: Native support for DataPackage and Table Schema, turning static descriptors into executable pipelines.

### Business Rules Engine (`mountainash-rules`)
*   **Combinatorial Logic**: Handle thousands of rules across hundreds of products using a high-performance decision-logic engine.
*   **Ternary Logic**: Built-in 3-valued (TRUE/FALSE/UNKNOWN) semantics for robust handling of missing or ambiguous data.
*   **Production Proven**: Replaced legacy systems with massive compression ratios and near-instant rule-to-live latency.

### Rule Interchange & Bridges (`Babel`)
*   **Format Portability**: Translate rules between DMN, CSV, FlagD, and mountainash.
*   **Ecosystem Bridges**: Export to SQL for data warehouses, or standards like Substrait for cross-engine execution.

### Test Data Generation (`syntheticdata`)
*   **Schema-Driven Generation**: Automatically generate realistic, constraint-aware test data from the same definitions used for validation.
*   **Closed-Loop Quality**: Catch contradictory rules at design time by running validation logic against generated data.

---

## 4. Case Study: Enterprise Pricing at Scale

**The Challenge**: A "Big 4" bank was managing 2,000 logical rules for mortgage pricing, which had expanded into an unmaintainable 500 million enumerated rows in a legacy system.

**The Solution**: mountainash-rules built a compressed decision-logic model using advanced set-membership algorithms.

**The Result**:
*   **250,000x compression**: 2,000 logical rules replaced 500M rows.
*   **< 1 hour latency**: Rule changes went from weeks to minutes.
*   **Zero maintenance**: The system ran for 2 years unattended, handling every margin, adjustment, and rate override for the bank's entire mortgage book.

---

## 5. Technical Deep-Dive: Under the Hood

For engineers and architects, mountainash is built on a **Substrait-aligned, cross-backend expression system**.

*   **Transparent Structures**: Expressions are stored as inspectable trees that can be walked, modified, and serialized.
*   **Unified Visitor**: A single architectural pattern translates these trees into native operations for Polars, Ibis, or SQL.
*   **Universal IR**: The system serves as an Intermediate Representation, allowing mountainash to act as a query planner for any engine.
