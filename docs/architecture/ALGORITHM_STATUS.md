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

## M7.7 status

Visualization CLI is implemented as a thin orchestration layer. `visualize` and `serve` call `analyze_repository()` once, build one VisualizationReadModel, and render the requested artifacts without changing inference. Static output remains the default; `--animated` renders a second mode from the same read model. The optional server receives pre-generated paths and performs no repository analysis.

## M6.5 status

The Hexagonal detector is implemented inside ArchitectureHypothesisEngine and reuses EvidenceScorer. It identifies port candidates only from existing `INTERFACE`/`ports` semantics or an evidence-bearing `IMPLEMENTS`/`EXTENDS` boundary, and never confirms from names alone. It requires at least two support categories for an INFERRED result, preserves contradicting evidence for direct core-to-concrete-infrastructure dependencies, and emits UNKNOWN when evidence is insufficient. No Raw Graph, parser, scanner or ArchitectureIR schema change was introduced.

## M6.6 — Evidence-Based Microservices Detector

M6.6 adds an independent `microservices` hypothesis to the existing
`ArchitectureHypothesisEngine`. It consumes indexed ArchitectureIR nodes,
component memberships, framework `APPLICATION` facts, graph relations and
existing infrastructure facts. A positive result requires at least two
independently observed application units and explicit cross-unit communication;
containers, Compose resources and infrastructure are complementary signals
only. Directory names, multiple modules, Compose alone and shared infrastructure
alone remain insufficient.

The detector preserves evidence and contradictions, including single-entrypoint
and shared-infrastructure signals, and returns `UNKNOWN` when independent
boundaries or communication cannot be established. It uses bounded indexes and
no additional scan, parser, symbol resolution, renderer or schema change.

## M8.1 — Architectural Significance and High-Level Projection

M8.1 introduces a renderer-neutral `ArchitecturalProjectionBuilder` between
ArchitectureIR and VisualizationReadModel. It explicitly distinguishes a
structural fact from architectural significance, and the detailed architecture
model from the high-level architecture projection. Significance is represented
per subject with HIGH, MEDIUM, LOW or UNKNOWN, score, reasons, evidence refs
and `contains_refs` for future drill-down.

Promotion requires evidence-backed semantic anchors such as application or
component detection, entrypoints/framework facts, explicit infrastructure or
architectural relations, or observed infrastructure resources. Degree alone,
names, directory placement and size do not promote a node. LOW and UNKNOWN
subjects remain in the significance model even when omitted from the primary
projection. Projected edges are grouped by projected endpoints and relation,
with support count, raw edge IDs, observations and evidence refs preserved.

The read model now consumes the high-level projection without changing
ArchitectureIR or renderer responsibilities. The project treats architecture
in two dimensions: relevant high-level structures and materialized technical
decisions. Decision recovery remains a future milestone and no human intent is
inferred here.
## M8.1.1 status

Evidence payload serialization is now shared and bounded. `EvidenceGroup` is the Read Model auxiliary schema: `id`, `evidence_count`, complete deduplicated `evidence_refs`, deterministic source-type `summary` and `source_refs`. Group IDs are SHA-1-derived from sorted evidence IDs and are stable across repeated builds. `INLINE_EVIDENCE_REF_LIMIT = 20` is an explicit serialization threshold; it never changes significance or projection.

The builder performs one indexed pass over visual evidence associations. Large node, edge and hypothesis associations are represented by group references and counts, while small lists remain inline. SVG elements expose stable IDs, status, confidence, origin, count and group reference. The inspection panel resolves the shared index and displays at most the first 20 evidence items. Read Model validation checks group identity, counts and all group references against the complete evidence set.

This milestone preserves the distinction: traceability is provided by references and indexes, not by duplicating the complete evidence set inside every visual element. ArchitectureIR and HighLevelArchitectureProjection are unchanged semantically.

## M8.1.2 status

Macro profiling is opt-in through AnalysisProfile and the CLI --profile option on analyze, visualize and serve. It reports stage elapsed time and bounded cardinalities without changing analysis inputs, ordering, IDs, evidence refs, confidence, UNKNOWN results, hypotheses or projection.

The measured optimization covers two proven Raw Graph costs: edge deduplication now uses a deterministic identity index, and repeated local import boundary resolution uses a canonical-import cache. Existing origin path caching and longest-local-module matching remain unchanged. Edge evidence refs, raw edge IDs, supporting observations and support counts are merged exactly as before.

The synthetic scale harness lives in benchmarks/scale_profile.py and uses temporary repositories at 50, 200 and 400 modules. It records raw and architectural cardinalities, projection/read-model cardinalities and growth ratios. The profile remains a diagnostic boundary; ArchitectureIR and the high-level projection contracts are unchanged semantically.

The remaining measured hotspot is source text reading in StackDetector; it is intentionally deferred until source-content reuse can be designed and measured without changing stack evidence.'

## M8.1.3 status

Architectural significance is calibrated independently from structural graph presence. External dependencies default to LOW when observed but semantically unsupported, rather than inheriting significance from node type or import count. The principal framework package is promoted only when an application/router fact identifies its framework symbol; persistence technologies and explicit architectural roles provide bounded additional support. Framework facts remain evidence, not automatic high-level nodes.

Component detection remains structural evidence. Component candidates do not automatically become HIGH. Direct application/endpoint/infrastructure facts provide strong support; framework dependency/schema facts provide medium support; one bounded contextual pass can support a component only through an evidence-backed semantic raw relation. LOW and UNKNOWN records remain in `HighLevelArchitectureProjection` for future drill-down.

The deterministic capped formula uses strong weights 0.55 for primary semantic anchors, 0.45 for explicit roles/infrastructure relations and 0.40 for strong architectural relations; medium weights range from 0.15 to 0.30; generic aggregated relations contribute 0.04 only. HIGH requires strong support with score >= 0.55; MEDIUM requires strong or medium support with score >= 0.15. ArchitectureIR and renderer responsibilities are unchanged.
'
## M8.1.4 status

High-Level Architecture Projection is authoritative for high-level visualization.
The ReadModel performs closure, not semantic expansion: a visual node must be in
the projection or have an explicit boundary justification. Semantic facts remain
in the ReadModel detail channel for future drill-down.

The bounded rules are:
- HTTP_ENDPOINT and ROUTER facts are detail-only unless an existing fact explicitly
  carries architectural_boundary evidence.
- APPLICATION may remain high-level when its application/boundary evidence is
  selected by significance.
- DATABASE, CACHE and MESSAGE_BROKER resources need an evidence-backed relation to
  a selected application/component; CONTAINER needs an equivalent explicit relation.
- framework fact strength does not override weak architectural context.
- projected edges are closed over selected endpoints and cannot promote LOW/UNKNOWN
  nodes.

The implementation uses set membership and deterministic dictionaries, with one
bounded contextual pass already used by significance. No renderer filtering,
blacklist, iterative convergence, graph ranking or ArchitectureIR semantic change
was added. The ReadModel records projection/read-model counts, semantic details,
boundary exceptions, endpoint/router/application/framework/infrastructure/container
high/detail counts, projected edge validity and projection traceability.

## M8.1.5 status

Architectural dependency significance is now context-calibrated. Observed
dependency, dependency frequency and framework usage remain structural facts
unless a role and architectural context are both supported.

The score rules are:
- principal APPLICATION_FRAMEWORK evidence can provide strong support;
- persistence, messaging, cache, deployment and external-service roles require
  an existing strong relation to a significant endpoint;
- generic DEPENDS_ON contributes weak traceability only and cannot promote an
  external dependency;
- framework internals and auxiliary framework facts do not inherit significance;
- hypothesis evidence complements existing strong/medium support but cannot
  create significance on its own.

The dependency role is additive to ArchitecturalSignificance and is exposed in
the deterministic result for auditability. ReadModel metadata reports role
counts, generic DEPENDS_ON promotion count, external dependency cardinalities,
precision/recall placeholders for benchmark evaluation, projected-edge validity
and traceability. The implementation remains bounded and uses one contextual
pass with set membership; no filesystem rescan, reparse, resolver rerun,
ranking or propagation to convergence was added.

## Algorithm refinement investigation status

The investigation harness is complete and diagnostic-only. It measures
significance levels, component/dependency cardinalities, relation vocabulary,
evidence coverage including EvidenceGroups, projection closure, SVG dimensions,
layout groups and deterministic repeated output.

Observed priority order:

1. calibrate application/framework context so isolated auxiliary components do
   not inherit significance from local framework facts;
2. define a canonical relation vocabulary across infrastructure and architectural
   consumers without losing source semantics;
3. measure and improve SVG layout density after semantic inputs are corrected.

No ArchitectureIR, projection, ReadModel or renderer semantics were changed.

## Algorithm refinement status

The context-boundary, canonical-relation and semantic-layout refinement is
complete.

Architectural context is represented internally by deterministic justified
context-root IDs. Application boundaries and bounded semantic flow can support
context; isolated framework facts, infrastructure facts and generic dependency
relations cannot manufacture system context. Multiple independent application
roots remain supported.

Known relation spellings are canonicalized at the InfrastructureRelation/IR
boundary through shared helpers. Source spelling remains in metadata when it
differs. Relation strength is centralized for diagnostics and does not change
significance weights by itself.

The SVG renderer now packs large semantic groups into bounded rows. The
ReadModel remains the authority for node and edge identity, significance,
evidence and detail preservation. Layout metrics are diagnostic only.

No ADR was created: the existing ADR-001/002/003 contracts remain sufficient.
The next semantic opportunity is a bounded model for hypothesis evidence by
architectural context; the next visual opportunity is more readable routing
for crossing-heavy graphs without altering the ReadModel.

## M8.1.6 status

High-level projection explainability is implemented as a read-only audit layer
in `visualization.projection_audit`. It does not duplicate or replace
`ArchitecturalSignificance`; it derives structured explanations from the
existing projection and IR contracts.

Each node explanation distinguishes:

- independent/root boundary justification;
- bounded root chain and supporting relation/evidence;
- local significance versus global contextualization;
- projection eligibility and reasons;
- framework-fact count and semantic relation refs.

Each projected relation explanation records canonical kind, strength, endpoint
significance/context, evidence count, support count, raw IDs, stronger same-pair
relations, `DEPENDS_ON` category and projection reason. Categories are
`ONLY_RELATION`, `SHADOWED_BY_STRONGER_RELATION` and
`AGGREGATED_STRUCTURAL_SUPPORT`, with same/cross/uncontextualized scope.

M8.1.6 found no general real-fixture evidence that a high-level DEPENDS_ON was
redundant with a stronger relation, so no edge suppression was implemented.
The only semantic refinement is the proven context rule preventing isolated
framework evidence plus local component flow from becoming global context.
The renderer remains unchanged.

## M8.1.7 status

Repository projection audit reports are implemented as a read-only operational
layer. architecture-recovery audit <repository> reuses the existing
acquisition/analysis pipeline and does not introduce an alternate analyzer.

Supported output modes are both (default), markdown and json (with md as an
alias). Reports are written to --output-dir, defaulting to the current
directory. Existing files are protected by default and can only be replaced
with --force.

The report serializer is deterministic and schema-versioned ("1"). It
derives Markdown and JSON from one structured payload. Evidence associations
are compacted with the existing EvidencePayloadIndex: small sets use inline
refs, while large sets use stable EvidenceGroup IDs, counts, summaries and
source refs. The raw evidence is not duplicated into every node or edge and
the audit layer does not change evidence ownership or traceability.

--profile includes the existing macro profile and report cardinalities,
including files, symbols, raw/architectural/projected nodes and edges,
components and evidence groups. The command prints only a short terminal
summary; detailed explanations are persisted in the reports.

No ADR was created. ADR-001/002/003 and the existing read-only explainability
contracts remain sufficient.

## M8.1.8 status

Context Reachability != Architectural Context Membership. The projection now
classifies context roots as strong architectural roots or weak/navigation roots
and applies a bounded propagation policy separate from relation validity or
visual strength. Generic DEPENDS_ON remains observable, projectable and
traceable, but cannot establish global context alone. Strong semantic relations
can establish direct context and one bounded extension.

Independent Boundary != Globally Significant Boundary: infrastructure receives
global eligibility only from explicit architectural linkage to a significant
subject or a directly justified execution boundary. Navigation context and
repository containment are retained for detail and traceability, not promoted
into application significance. Configuration and other semantic details do not
become high-level peers merely because a relation exists.

Repeated Weak Evidence != Strong Architectural Evidence. Weak score contribution
is saturated by reason class, while explicit application/deployment and semantic
flow evidence retain their existing positive behavior. ReadModel closure remains
authoritative and does not reintroduce demoted nodes.

The implementation is bounded at O(nodes + architectural edges + infrastructure
relations + facts) for context membership and uses shared propagation helpers in
projection and audit. No fixed-point traversal, renderer inference, or
project-specific library/path rule was added.

No ADR was created; ADR-001/002/003 remain sufficient.

## M8.1.9 - application boundary provenance and ownership calibration

The investigation located the remaining false global-context source in
graph/aggregation.py: every repository received a synthetic
application:<repository> node with inferred GRAPH_AGGREGATION evidence based
on repository membership. visualization/projection.py then admitted every
application node with evidence as a strong context root. Its broad CONTAINS
edges could therefore be interpreted as APPLICATION_CONTEXT_OWNERSHIP and
contextualize unrelated components.

The aggregate now carries explicit provenance:
application_provenance=repository_aggregate,
boundary_evidence_kind=repository_membership, and
architectural_boundary=false. It remains available in the Detailed Model,
but is not a strong root. Standalone explicit application nodes remain
supported for compatibility; framework application components become roots only
when their own application evidence has an observed boundary (explicit boundary
or boundary fact plus semantic flow). A lone framework fact or application
count is insufficient.

Repository/application containment is structural by default and is never
treated as architectural ownership. APPLICATION_CONTEXT_OWNERSHIP is accepted
only from explicit edge provenance (architectural_ownership or
ownership_kind=architectural). The audit reports structural ownership
rejections, application provenance, boundary evidence kind, observed/inferred
status, framework/entrypoint/deployment evidence and ownership refs.

This implements:
Application detected != Application boundary.
Application boundary != Global context root.
Structural ownership != Architectural context ownership.
Navigation context != Architectural significance.

No significance weights, relation semantics, hypothesis scoring, renderer or
layout behavior was changed. No repository-specific names, paths or library
rules were introduced. The bounded policy remains linear in architectural
nodes, edges and framework facts.

## M8.1.10 - framework boundary qualification and context membership consistency

The audit isolated two independent causes. Framework application components became
`FRAMEWORK_APPLICATION_BOUNDARY` when APPLICATION plus endpoint/router facts
and any local flow were present, without proving that the component owned a
coherent application boundary. Separately, SUPPORTS_CONTEXT relations were
allowed into the same bounded frontier as establishing relations, so a supporting
relation could create global context membership.

The policy now classifies framework facts by provenance and ownership. An
APPLICATION fact is `OWNED_APPLICATION_BOUNDARY` only when it is associated with
an explicit boundary, a coherent owned router/endpoint boundary, deployment, or
an equivalent semantic boundary. Unowned framework usage is reported as
`LOCAL_FRAMEWORK_USAGE`, related facts as `RELATED_FRAMEWORK_BOUNDARY`, and
unresolved associations remain `UNRESOLVED`. A coherent isolated boundary may
remain `QUALIFIED_LOCAL`; it becomes a global context root only with explicit
boundary/deployment evidence or a bounded semantic flow to another component.

`CAN_PROPAGATE_CONTEXT` establishes membership. `SUPPORTS_CONTEXT` can be
retained as supporting provenance only for a subject already established by a
strong relation; it cannot create membership. `DOES_NOT_PROPAGATE_CONTEXT` never
establishes membership. DEPENDS_ON remains intact in the Architectural Graph and
projection. No significance weights, hypothesis scoring, renderer behavior or
repository-specific rule changed.

The neutral fixtures cover high framework-fact volume without ownership, owned
declarative applications, isolated local boundaries, multiple explicit framework
applications, supporting-only and strong-plus-supporting relation chains,
determinism and traceability. The new audit metrics separate framework candidates,
qualified roots, local usage, established membership and supporting membership.

No new ADR was required; this refines the evidence/uncertainty and graph/renderer
separation contracts from ADR-001, ADR-002 and ADR-003.

## M8.1.11 - Global Projection Eligibility Gate

Projection eligibility is now a final global gate, separate from local
architectural significance. HIGH/MEDIUM alone is insufficient. Eligibility
requires a strong/root-anchored context membership, an existing explicit global
role, or an infrastructure resource with an explicit relation to a root-anchored
subject. Navigation/repository envelopes are excluded unless independently
justified. Local-only HIGH/MEDIUM nodes retain their significance and evidence
but are detailed-only. This preserves `CORRECT > UNKNOWN >> WRONG` and prevents
ReadModel reintroduction through projection closure.

The implementation does not recalibrate significance, context propagation,
framework boundaries, DEPLOYS, dependencies, hypotheses, or the renderer. It
uses a bounded indexed pass and preserves deterministic IDs, evidence refs,
Detailed Model records, and projected-edge endpoint validity.

## M8.1.12 - Deployment Provenance & Context Transit Calibration

DEPLOYS is now represented by provenance separately from observed relation validity. Only `EXPLICIT_EXECUTION_DEPLOYMENT` and `EXPLICIT_DEPLOYMENT_OWNERSHIP` are `CAN_PROPAGATE_CONTEXT`. `AGGREGATED_DEPLOYMENT` and `LOCAL_DEPLOYMENT` are supporting-only; `NAVIGATION_DERIVED` and `UNRESOLVED` do not propagate. A repository envelope containing Docker/Compose evidence is therefore not treated as runtime ownership. Explicit application-to-deployable relations remain eligible for global deployment context.

The bounded context passes use the provenance-aware classification. Navigation nodes cannot relay global membership through aggregated deployment evidence. DEPLOYS remains in the Architectural Graph, Detailed Model and projection when both endpoints are otherwise eligible. Framework deployment qualification also requires explicit execution/ownership provenance.

Projection Audit exposes deployment totals, provenance counts, propagation counts, deployment membership count, candidate/qualified/rejected boundary counts and navigation-transit memberships. This preserves `CORRECT > UNKNOWN >> WRONG`, determinism and traceability.

## M8.1.13 - Positive Evidence Ledger and directional deployment context

Projection audit now exposes a read-only positive-evidence ledger. It reports evidence produced by GraphAggregation, FrameworkAdapter, InfrastructureAnalyzer or RawGraph, including provenance, owner, direction, acceptance and rejection reason. Compact reports retain evidence counts/groups rather than duplicating raw references.

The only inference correction was directional: `DEPLOYS` is a source-to-target relation and can no longer establish context membership through reverse traversal. Aggregated, navigation-derived or unresolved deployment observations remain valid detailed facts but do not gain propagation strength. No new positive evidence producer was invented because the audit did not prove a generally safe missing producer for entrypoints or application ownership.

This preserves `CORRECT > UNKNOWN >> WRONG`, deterministic projection, raw/architectural traceability and the separation between relation validity and context propagation. No significance weights, hypothesis scoring, ArchitectureIR semantics or renderer behavior changed.

## M8.1.13a - Executable Entrypoint Provenance

Executable-boundary evidence is now produced by a read-only, deterministic `EntrypointAnalyzer`. Supported sources are literal `pyproject.toml` scripts and entry-point tables, Poetry scripts, `setup.cfg`, literal `setup.py` entry-point configuration, and `__main__.py`. Arbitrary setup/configuration code is never executed. An entrypoint is accepted only after target resolution, first-party origin validation and unambiguous ownership by an existing component/application index. Otherwise it remains UNKNOWN with a reason.

The additive `ArchitectureIR.entrypoints` records declaration provenance, target/owner resolution, status, acceptance and evidence refs. The projection uses accepted owner evidence through the existing global-root policy; it does not treat repository existence or a filename alone as a global boundary. The Projection Audit and Positive Evidence Ledger expose compact entrypoint counts, owners and rejection reasons. Detailed graph and evidence collections remain intact. No significance, framework, deployment, propagation, hypothesis or renderer semantics changed.

No new ADR was required; this implements a positive evidence producer under ADR-001/002/003 without changing their contracts.