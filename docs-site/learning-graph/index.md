# Learning Graph for Mountainash

This section contains the learning graph for the mountainash package. A learning graph is
a graph of concepts where each concept is represented by a node in a network graph.
Concepts are connected by directed edges that indicate
what concepts each node depends on before that concept is understood by the learner.

A learning graph is the foundational data structure for intelligent textbooks that can recommend learning paths.
A learning graph is like a roadmap of concepts to help learners arrive at their learning goals.

At the left of the learning graph are prerequisite or foundational concepts. They
have no outbound edges. They only have inbound edges for other concepts that depend on
understanding these foundational prerequisite concepts. At the far right
we have the most advanced concepts. To master these concepts you
must understand all the concepts that they point to.

## Course Description

We use the [Course Description](./course-description.md) as
the source document for the concepts that are included in this package.
The course description uses the 2001 Bloom taxonomy to order learning objectives.

## List of Concepts

We use generative AI to convert the course description into a [Concept List](./concept-list.md).
Each concept is in the form of a short Title Case label with most labels under 32 characters long.

## Concept Dependency List

We next use generative AI to create a Directed Acyclic Graph (DAG). DAGs do not have cycles where
concepts depend on themselves. We provide the DAG in two formats. One is a [CSV file](learning-graph.csv) and the other
format is a [JSON file](learning-graph.json) that uses the vis-network JavaScript library format. The vis-network format uses `nodes`, `edges` and `metadata`
elements with edges containing `from` and `to` properties.

## Analysis & Documentation

### Learning Graph Quality Validation

[View the Learning Graph Quality Validation](quality-metrics.md)

### Concept Taxonomy

[View the Concept Taxonomy](concept-taxonomy.md)

### Taxonomy Distribution

[View the Taxonomy Distribution Report](./taxonomy-distribution.md)
