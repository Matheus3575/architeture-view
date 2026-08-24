# ADR-002 — Evidence and Traceability

## Status

Accepted

## Context

Architecture recovery contains uncertainty.

Some relationships are directly observable.

Others are inferred from:

* multiple calls;
* configuration;
* framework conventions;
* deployment definitions;
* graph structure;
* heuristics.

Without explicit evidence, the engine cannot explain why an architectural relationship exists.

This also creates a risk that future LLM reasoning introduces unsupported architectural claims.

## Decision

Evidence and traceability are first-class properties of architecture recovery.

Important architectural claims must retain references to the observations supporting them.

Conceptually:

```text
Source
    ↓
Observation
    ↓
Raw Node / Edge
    ↓
Aggregation
    ↓
Architectural Node / Edge
    ↓
Architectural Hypothesis
```

Traceability should allow traversal in the opposite direction.

```text
Architectural Hypothesis
    ↓
Architectural Edge
    ↓
Raw Edge
    ↓
Source Location
```

## Observation Status

The engine must distinguish concepts equivalent to:

```text
OBSERVED
INFERRED
UNKNOWN
```

An inferred relationship must not be represented as directly observed.

## Confidence

Confidence may be associated with inference.

Example:

```json
{
  "status": "inferred",
  "confidence": 0.87
}
```

Confidence does not replace evidence.

## Aggregated Relationships

When multiple raw edges support an architectural relationship, the architectural edge should preserve references to them.

Conceptually:

```json
{
  "source": "component.api",
  "target": "component.application",
  "type": "DEPENDS_ON",
  "evidence": {
    "raw_edge_ids": [
      "edge_102",
      "edge_109",
      "edge_143"
    ]
  }
}
```

The exact schema is implementation-dependent.

The traceability requirement is not.

## Unknown

UNKNOWN is a valid result.

When evidence is insufficient, the engine should preserve uncertainty instead of manufacturing certainty.

## LLM Consequence

Future LLM reasoning may interpret architectural evidence.

It must not silently create deterministic facts.

LLM-derived claims must remain identifiable as inference.

## Validation Consequence

Architecture validation should eventually detect:

* edges referencing nonexistent nodes;
* missing evidence;
* invalid evidence references;
* inferred claims represented as observations;
* broken traceability.

## Consequences

The engine becomes auditable.

Users and developers can inspect why architectural conclusions were produced.

Architecture inference becomes testable against evidence rather than only against final diagrams.
