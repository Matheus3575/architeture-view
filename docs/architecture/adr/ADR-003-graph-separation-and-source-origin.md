# ADR-003 — Raw Graph, Architectural Graph, and Source Origin

## Status

Accepted

## Context

Initial analyzer output demonstrated that low-level static analysis can produce a large amount of correct information.

However, framework implementation details can dominate the graph.

For example, an application using FastAPI may reference internal framework symbols.

Those relationships are useful to static analysis but normally should not appear as hundreds of framework functions in an architecture diagram.

Simply deleting external nodes is also undesirable because this destroys evidence.

We therefore require different graph abstraction levels.

## Decision

The engine conceptually maintains two different graph representations:

```text
Raw Code Graph
```

and:

```text
Architectural Graph
```

They have different responsibilities.

---

# Raw Code Graph

The Raw Code Graph preserves low-level observations.

It may contain:

```text
files
modules
classes
interfaces
functions
methods
imports
calls
inheritance
instantiation
external symbols
framework symbols
standard-library symbols
```

The Raw Code Graph prioritizes fidelity over visual simplicity.

Third-party nodes must not be removed merely because they are inappropriate for architecture visualization.

---

# Source Origin

When possible, nodes should be classified using source-origin states equivalent to:

```text
FIRST_PARTY
THIRD_PARTY
STANDARD_LIBRARY
GENERATED
UNKNOWN
```

## FIRST_PARTY

Code belonging to the repository or internal packages under analysis.

## THIRD_PARTY

External dependencies.

Examples may include:

```text
FastAPI
Pydantic
SQLAlchemy
Starlette
```

when those packages are dependencies of the repository being analyzed.

If the FastAPI repository itself is being analyzed, FastAPI source is FIRST_PARTY.

Origin is contextual to the repository boundary.

## STANDARD_LIBRARY

Runtime/platform standard-library code.

## GENERATED

Generated source when detectable.

## UNKNOWN

Origin cannot be established with sufficient evidence.

UNKNOWN is preferable to incorrect classification.

---

# Repository Boundary

Source-origin classification must consider repository boundaries.

It must not assume that every Python file is FIRST_PARTY.

Potential evidence includes:

```text
repository root
package layout
src layout
dependency manifests
resolved module locations
installed package metadata
virtual environment boundaries
```

The mechanism should remain extensible to monorepos and future languages.

---

# Architectural Graph

The Architectural Graph represents higher-level architecture.

It should avoid exposing unnecessary implementation details from external libraries.

For example, a Raw Code Graph may contain:

```text
ApplicationFunction
    CALLS
fastapi.internal.function_a

fastapi.internal.function_a
    CALLS
fastapi.internal.function_b
```

while the Architectural Graph may represent:

```text
Application
    USES
FastAPI
```

provided sufficient evidence exists.

---

# Aggregation

Aggregation transforms lower-level relationships into higher-level relationships.

Conceptually:

```text
Raw Code Graph
      ↓
Source Classification
      ↓
Graph Aggregation
      ↓
Architectural Graph
```

Aggregation MUST preserve traceability.

An architectural edge should reference the raw observations that justify it.

---

# Analysis Depth

Default analysis policy should move toward:

```text
FIRST_PARTY
    → deep analysis

THIRD_PARTY
    → enough analysis for dependency identity and relevant boundary interactions

STANDARD_LIBRARY
    → normally aggregated or omitted from architectural visualization

UNKNOWN
    → preserved and reported
```

This policy should remain configurable where practical.

---

# Important Non-Decision

This ADR does NOT define how first-party code is grouped into components such as:

```text
API
Application
Domain
Persistence
```

That remains a separate architecture recovery problem.

Directory names alone must not determine those components.

Future component aggregation should consider multiple evidence sources.

---

# Consequences

The engine can preserve detailed static-analysis information without overwhelming architectural output.

External frameworks remain visible as dependencies without exposing all internal implementation details.

Architecture recovery gains a formal abstraction boundary.

Raw graph analysis and architectural analysis can evolve independently while remaining traceable.

---

# Validation Requirements

At minimum, future validation should ensure:

1. Raw observations are not silently destroyed during classification.
2. Architectural edges reference valid nodes.
3. Aggregated edges retain evidence.
4. Third-party internals do not automatically flood the Architectural Graph.
5. UNKNOWN remains representable.
6. Source-origin classification remains contextual to the repository being analyzed.
