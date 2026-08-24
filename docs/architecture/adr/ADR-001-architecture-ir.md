# ADR-001 — Architecture IR as the Analysis Contract

## Status

Accepted

## Context

The engine must eventually support multiple consumers of recovered architecture, including:

* Mermaid;
* Graphviz;
* Cytoscape;
* APIs;
* graph databases;
* architecture validators;
* LLM reasoning;
* architecture comparison tools.

If architectural meaning is embedded directly into a renderer, architecture recovery becomes coupled to visualization.

This also creates a risk that a renderer invents missing relationships in order to produce a visually coherent diagram.

## Decision

Introduce and maintain an Architecture Intermediate Representation:

```text
Architecture IR
```

Architecture IR is the structured contract between architecture analysis and downstream consumers.

Conceptually:

```text
Repository
    ↓
Analysis
    ↓
Architectural Graph
    ↓
Architecture IR
    ↓
Consumers
```

Consumers may include:

```text
Validator
Renderer
LLM Reasoner
Graph Exporter
API
```

## Architecture IR Responsibilities

The IR may contain:

```text
repository metadata
stack
nodes
edges
components
evidence
confidence
architectural hypotheses
validation information
```

The exact schema may evolve.

It must be versioned.

Example:

```json
{
  "schema_version": "0.2"
}
```

## Renderer Rule

Renderers MUST NOT create architectural truth.

A renderer may:

* choose layout;
* choose visual grouping;
* choose labels;
* hide information according to presentation settings.

A renderer may NOT:

* invent edges;
* invent components;
* resolve symbols;
* infer architecture;
* convert disconnected nodes into connected nodes without evidence.

## Consequences

Architecture IR must remain independent from specific visualization technologies.

Schema changes require deliberate compatibility consideration.

Testing should validate the IR separately from rendering.

## Rejected Alternative

```text
Source → Renderer-specific architecture discovery
```

Rejected because it couples analysis to visualization and makes architectural claims difficult to validate independently.
