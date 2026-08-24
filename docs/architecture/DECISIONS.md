# Architecture Decisions

This document is the index of architectural decisions governing the Architecture Recovery Engine.

Detailed rationale lives in Architecture Decision Records under:

```text
docs/architecture/adr/
```

---

# Decision Status

| ADR     | Decision                                                                | Status   |
| ------- | ----------------------------------------------------------------------- | -------- |
| ADR-001 | Architecture IR is a renderer-independent contract                      | Accepted |
| ADR-002 | Architectural claims require evidence and traceability                  | Accepted |
| ADR-003 | Raw and Architectural Graphs are separate and source origin is explicit | Accepted |

---

# ADR-001 — Architecture IR

Architecture IR is the boundary between architecture analysis and downstream consumers.

Consequences:

* renderers do not perform architecture discovery;
* visualization technology must not determine IR semantics;
* schema changes must be deliberate and versioned;
* downstream reasoning should consume the IR rather than reconstructing architecture from diagrams.

See:

```text
adr/ADR-001-architecture-ir.md
```

---

# ADR-002 — Evidence and Traceability

Important architectural claims must retain evidence.

Consequences:

* observed and inferred information remain distinct;
* architectural edges must be explainable;
* aggregation must preserve references to lower-level observations;
* UNKNOWN is preferable to fabricated certainty.

See:

```text
adr/ADR-002-evidence-and-traceability.md
```

---

# ADR-003 — Graph Separation and Source Origin

The engine maintains conceptually distinct Raw Code and Architectural Graphs.

Source code is classified by origin when possible.

Consequences:

```text
FIRST_PARTY
THIRD_PARTY
STANDARD_LIBRARY
GENERATED
UNKNOWN
```

are meaningful source-origin states.

Third-party implementation details may remain in the Raw Code Graph but should normally be aggregated in the Architectural Graph.

See:

```text
adr/ADR-003-graph-separation-and-source-origin.md
```

---

# Framework Adapter Boundary

Framework adapters are semantic interpretation layers between the Raw Code
Graph and later component detection. They may produce framework-neutral facts
such as HTTP endpoints, dependencies, schemas and router inclusion, while
preserving evidence and UNKNOWN states. They must not classify components or
infer architecture patterns.

FastAPI is the first reference implementation, not the product target of the
engine. Adding another adapter must not require changing the parser, symbol
resolver, Raw Code Graph, component detection or architecture inference
contracts.

This boundary is documented as the M3 implementation contract. No new ADR was
created because the existing separation and evidence decisions already govern
the behavior; a new ADR is warranted only if this boundary becomes a durable
cross-cutting decision beyond the current implementation documentation.

---

# Updating This File

When an ADR is accepted:

1. add it to the decision table;
2. summarize its consequences;
3. reference its path.

When an ADR is superseded:

1. preserve the original ADR;
2. mark it `Superseded`;
3. identify the replacing ADR;
4. update this index.

Do not delete architectural history merely because a decision changed.
