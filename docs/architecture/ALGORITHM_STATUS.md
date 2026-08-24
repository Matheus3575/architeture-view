# Algorithm Development Status

> Status snapshot: 2026-08-24. This document describes the current implementation. Accepted ADRs remain authoritative.

## Current status

```yaml
overall_status: implemented_with_semantic_limitations
deterministic: true
raw_graph: structurally_faithful_and_evidence_preserving
symbol_resolution: moderate
basic_data_flow: implemented_bounded
data_flow_analysis: intentionally_limited
architectural_graph: provisional
architecture_inference: provisional
llm: not_implemented
```

The engine is reliable at preserving structural observations and tracing them
back to source. Its main remaining limitations are semantic: complex data
flow, dynamic dispatch, framework meaning and architectural role inference.

## Pipeline

```text
Repository
  -> Scanner
  -> Python Parser
  -> Symbol Resolution
  -> Raw Code Graph
  -> Framework Adapters / Semantic Facts
  -> Infrastructure Semantics / Infrastructure Facts
  -> Source-Origin Classification
  -> Graph Aggregation
  -> Architectural Graph
  -> Evidence-Based Component Candidates
  -> Architecture IR
  -> Validation / Rendering
```

The Raw Code Graph preserves first-party, third-party, standard-library,
generated and unknown origins. The Architectural Graph is a separate,
provisional abstraction and must not invent relationships without Raw Graph
evidence. Renderers consume the IR and do not perform analysis.

## Milestones

| Milestone | Status | Result |
|---|---|---|
| M1 | Complete | Raw/Architectural Graph and Architecture IR separation |
| M2.1 | Complete | Conservative resolution, evidence preservation and measurable ground truth |
| M2.2 | Complete with bounded coverage | Local assignments, aliases, constructor flow, `self.attribute` and simple returns |
| M3 | Complete | FrameworkAdapter foundation, FastAPI reference semantics, evidence and UNKNOWN benchmark |
| M4 | Complete | Conservative first-party component candidates, unassigned nodes and traceable affinity evidence |
| M5 | Complete | Docker/Compose infrastructure facts, conservative resource kinds, explicit configuration mapping and traceable relations |
| Framework semantics | Complete v1 | FastAPI reference adapter; Django/Flask remain future adapters |
| Component detection | Complete with bounded coverage | Module-level candidates; no architectural pattern inference |
| Architecture inference | Future | Pattern hypotheses with confidence and traceability |

## Safety policy

```text
CORRECT > UNKNOWN >> WRONG
```

Ambiguous branches, dynamic factories, registries, reflection and complex
returns remain unresolved rather than receiving speculative targets.

## Authority and maintenance

For architectural interpretation, consult `DECISIONS.md` and accepted ADRs
before this status document. Update this file when a milestone changes the
observable algorithm or its guarantees; record experiments in
`ANALYSIS_LOG.md` and durable cross-cutting decisions in an ADR.
| Next implementation step | Recommended | Architecture Pattern Inference, with infrastructure remaining evidence rather than architecture proof |
