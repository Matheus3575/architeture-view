# Algorithm Next Steps

This roadmap is subordinate to accepted ADRs and is an implementation guide,
not a new architectural decision.

## M4 result

M4 is complete. The engine now produces conservative, evidence-based
first-party component candidates and explicitly preserves unassigned modules.
M3 framework-neutral facts remain inputs, while architectural pattern
inference remains separate.

The implemented reference adapter interprets, without re-parsing source ad hoc:

- `APIRouter` construction;
- `@app.get` and `@router.get`;
- `Depends`;
- Pydantic schema references;
- `response_model`;
- endpoint registration.

It should add framework evidence and semantic relations only where the
existing ontology supports them. It must not replace Raw Graph observations
or create architectural relations without evidence.

## Recommended next milestone: Infrastructure Semantics

The M4 benchmark has perfect covered candidate/member/evidence recall, zero
false groupings and no source-origin regression across 12 fixtures. The next
useful evidence layer is richer infrastructure semantics so component
candidates can later be evaluated across Docker, Compose, Kubernetes and CI
boundaries.

## Alternatives

### Repository Boundary Advanced

This remains important for editable installs, multiple Python environments,
complex Poetry configurations, namespace packages and local/installed module
name collisions. The current boundary handles ordinary roots, `src` layouts,
monorepos and namespace fixtures, but these advanced cases are not fully
covered.

Choose this before Infrastructure Semantics only if source-origin errors
appear in a real target repository or editable-install/namespace cases become
a priority.

### Infrastructure Semantics

This is now the recommended next milestone for richer Docker, Compose,
Kubernetes and CI facts. It must remain separate from component detection and
architecture pattern inference.

## Later sequence

```text
Component Detection
        -> Infrastructure Semantics
        -> Architecture Pattern Inference
        -> Optional LLM interpretation
```

Component Detection and Architecture Pattern Inference must remain separate:
the first proposes components; the second evaluates architecture hypotheses
from the resulting component graph and supporting evidence.

## Do not do next

- Do not add LLM reasoning to compensate for weak observations.
- Do not implement general Python data-flow analysis as part of M2.2.
- Do not infer MVC, Clean, Hexagonal or Microservices from directory names.
- Do not make the renderer responsible for analysis.
