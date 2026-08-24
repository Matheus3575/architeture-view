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
| M6.1 hypothesis engine | Complete with bounded coverage | Deterministic evidence scoring and minimal Layered hypothesis detector |
| M6.2 evidence-based Layered detector | Complete with bounded coverage | Directional structural relations, semantic signals and conservative contradictions |

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

## M6.2 status

The Layered detector now consumes the complete ArchitectureIR and combines
relation direction, CALLS, IMPORTS, INSTANTIATES, data-flow metadata, framework
roles, Architectural Graph edges and infrastructure terminals when available.
A relation is required; directory or component names alone produce UNKNOWN.
Dependency direction has higher weights than naming metadata, while reverse
skip-layer relations receive an additional contradiction penalty. The global
M6.1 scorer and status contract remain unchanged.
## M6.3 status

MVC detection is complete with bounded coverage. The detector reuses the M6.1 scorer and evaluates independent evidence contributions from ArchitectureIR raw/architectural relations and framework facts. It preserves contradiction refs and emits UNKNOWN when names are the only available signal. Layered behavior and the hypothesis contract remain compatible.
## M6.4 status

Framework Facts are strengthened with bounded indexed interpretation. Existing APPLICATION, ROUTER, HTTP_ENDPOINT, FRAMEWORK_DEPENDENCY, RESPONSE_SCHEMA, SCHEMA and ROUTER_INCLUSION facts remain framework-neutral; CONTROLLER_LIKE is emitted only for a resolved HTTP route handler with definition evidence. Facts retain expression, source and raw-evidence traceability metadata. No architectural pattern inference was added to the adapter.
## M7.1 status

The Visualization Read Model is complete with bounded linear-style transformation over existing IR collections. It provides deterministic nodes, edges, hypotheses, evidence, unknown markers, semantic layer hints and origin refs. A dedicated validator rejects duplicate IDs, orphan edges, missing identities and invalid evidence references. Infrastructure-backed nodes remain distinguishable from application components.
## M7.2 status

The semantic SVG renderer MVP is complete. It provides a bounded layout over read-model nodes and edges, semantic shapes for components, endpoints, infrastructure, external and unknown nodes, and separate hypothesis presentation. It rejects invalid read models before rendering and emits self-contained XML SVG without coordinates in ArchitectureIR or the Read Model.

## M7.3 status

Semantic SVG layout and inspection are complete with bounded deterministic behavior. Existing layer/group/preferred-layer hints take precedence; fallback grouping uses only existing semantic kind, role and entrypoint hints. Relation kinds are preserved and visually classified without removing Read Model edges. Cross-band routes are simple orthogonal paths. SVG metadata preserves element identity, relationships, evidence and hypothesis associations. No Raw Graph, parser, scanner or architectural inference is accessed.

## M7.4 status

Interactive evidence inspection is complete as a renderer-only capability. The SVG includes stable selection metadata, deterministic precomputed lookup payloads, node/edge/hypothesis selection, related-element highlighting, clear selection and an evidence panel. Structural Read Model IDs and data are unchanged; absent evidence fields remain UNKNOWN. No analysis stage or architectural detector was modified.

## M7.5 status

Optional SVG motion is complete as a renderer-only feature. render_svg(model, mode="static") is the default; mode="animated" enables deterministic CSS classes and shared keyframes. Architectural flow animation is limited to observed/inferred relevant relations, and infrastructure indicators are emitted only for known observed/inferred resources. STATIC and ANIMATED preserve IDs, evidence, inspection and Read Model contents. No runtime behavior is simulated.

## M7.6 status

Web consumption and basic accessibility are complete without changing the analysis pipeline. The standard-library consumer serves pre-generated SVG bytes through fixed routes only. The SVG exposes title/description, semantic roles, keyboard-selectable nodes/edges/hypotheses, an aria-live inspection panel and keyboard-accessible mode controls. The web layer performs no discovery, inference, parsing or repository access.
