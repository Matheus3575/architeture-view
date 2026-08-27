# Algorithm Next Steps

This roadmap is subordinate to accepted ADRs and is an implementation guide,
not a new architectural decision.

## M4 result

M4 is complete. The engine produces conservative, evidence-based first-party
component candidates and preserves unassigned modules. Component detection and
architecture pattern inference remain separate.

## M5 result

M5 is complete. Docker and Compose now produce infrastructure-neutral,
evidence-backed resources and relations without changing Component Detection.
UNKNOWN and unsupported configuration remain explicit.

## Recommended next milestone: M6.3 Additional Pattern Detector

M6.2 now provides a conservative evidence-based Layered detector. The next
step is to add one separately validated pattern detector while preserving UNKNOWN
and traceability.

## Alternatives

### Repository Boundary Advanced

This remains important for editable installs, multiple Python environments,
complex Poetry configurations, namespace packages and local/installed module
name collisions. Choose it before inference only if source-origin errors appear
in a real target repository or these cases become a priority.

## Later sequence

Component Detection
        -> Infrastructure Semantics
        -> Architecture Pattern Inference
        -> Optional LLM interpretation

## Do not do next

- Do not add LLM reasoning to compensate for weak observations.
- Do not implement general Python data-flow analysis as part of M2.2.
- Do not infer MVC, Clean, Hexagonal or Microservices from directory names.
- Do not make the renderer responsible for analysis.
- Do not turn Infrastructure Semantics into a generic DevOps analyzer.

## M6.1 result

M6.1 is complete with one bounded Layered detector. MVC, Clean, Hexagonal,
Microservices and LLM-assisted interpretation remain future work.



## M6.2 result

M6.2 is complete. Layered hypotheses require evidence-bearing directional
relations; names-only structures remain UNKNOWN and reverse/conflicting
relations remain traceable.
## M6.3 result

M6.3 is complete. MVC is an independent evidence-based hypothesis and does not force a single winning architecture. The next recommended milestone is a bounded additional detector or repository-boundary hardening; Clean, Hexagonal, Microservices and LLM reasoning remain deferred.
## M6.4 result

M6.4 is complete. Framework Facts are richer and more traceable while remaining separate from architectural inference. The next recommended milestone is a bounded visualization/read-model preparation layer or additional framework adapter coverage, subject to preserving UNKNOWN and the renderer boundary.
## M7.1 result

M7.1 is complete. ArchitectureIR can now be projected into a renderer-neutral read model without exposing Raw Graph interpretation to a future renderer. The next recommended milestone is a renderer-specific consumer or a read-model contract review before implementing visual layout.
## M7.2 result

M7.2 is complete. The engine now has a first semantic SVG presentation layer consuming only VisualizationReadModel. The next recommended milestone is renderer/read-model contract hardening or a separate interactive consumer, while keeping discovery and layout responsibilities separated.

## M7.3 result

M7.3 is complete. The SVG renderer now provides semantic grouping, bounded orthogonal routing, relation prioritization and inspection metadata while preserving all Read Model elements and hypotheses. The next recommended milestone is a small evidence inspection consumer or a renderer contract hardening pass; interactive UI remains deferred.

## M7.4 result

M7.4 is complete as interactive inspection only. The SVG can select nodes, edges and hypotheses, highlight related elements, clear selection and expose traceable evidence without rerunning analysis. The next recommended milestone is a dedicated evidence/read-model API or a browser consumer if richer navigation is required; discovery remains outside the renderer.

## M7.5 result

M7.5 is complete as optional motion and visual semantics only. STATIC remains the default; ANIMATED provides restrained CSS-based flow/resource indicators without runtime simulation or architectural inference. The next recommended milestone is an optional browser-facing delivery layer or accessibility hardening, while the renderer boundary remains unchanged.

## M7.6 result

M7.6 is complete. Pre-generated SVG files can be opened offline or served locally through the fixed-route standard-library web consumer. STATIC is the default browser presentation and ANIMATED remains optional. The next recommended milestone is accessibility hardening or packaging a small user-facing command, without moving inference into the web layer.

Operational usage:

~~~powershell
python -c "from pathlib import Path; from architecture_recovery.pipeline import analyze_repository; from architecture_recovery.visualization import VisualizationReadModelBuilder; from architecture_recovery.rendering import render_svg; model=VisualizationReadModelBuilder().build(analyze_repository('URL_DO_REPOSITORIO')); Path('architecture.svg').write_text(render_svg(model, mode='static'), encoding='utf-8'); Path('architecture-animated.svg').write_text(render_svg(model, mode='animated'), encoding='utf-8')"
Start-Process .\architecture.svg
python -m architecture_recovery.web --static-svg architecture.svg --animated-svg architecture-animated.svg
~~~

The web consumer serves only pre-generated files at fixed routes and performs no repository analysis.

## M7.7 result

M7.7 is complete. Generate a static visualization with:

    architecture-recovery visualize <repository>

Generate both modes with `architecture-recovery visualize <repository> --animated`. Start the local consumer with `architecture-recovery serve <repository> --animated --host 127.0.0.1 --port 8000`. The CLI only orchestrates existing analysis, read-model construction, rendering and artifact serving; it does not participate in inference.

## M6.5 result

M6.5 is complete. Hexagonal is an independent conservative hypothesis based on directional ports-and-adapters evidence. Names-only structures remain UNKNOWN, contradictions remain traceable and Layered/MVC hypotheses remain independent. The next recommended milestone is another bounded detector only if a distinct evidence contract is available; otherwise prioritize improving evidence coverage without adding new scans.

## M6.6 result

M6.6 is complete as a conservative Microservices detector. Independent application facts plus explicit cross-unit communication are required for inference; modular monoliths and infrastructure-only layouts remain UNKNOWN. The next recommended step is improving existing boundary evidence coverage, not adding another inference heuristic.

## M8.1 result

M8.1 is complete. High-level projection now decides architectural visibility before the renderer while preserving detailed significance records and traceability. The next recommended milestone is materialized Architectural Decision Recovery over existing evidence, not more visual filtering.
## M8.1.1 result

M8.1.1 is complete. Large evidence associations now use shared deterministic groups at the VisualizationReadModel/SVG boundary. Full traceability remains available through the Read Model; visual attributes contain stable group references and counts, and inspection is bounded to the first 20 observations. ArchitectureIR, Architectural Significance and High-Level Architecture Projection are unchanged.

The next recommended milestone is Architectural Decision Recovery over materialized evidence, with explicit separation between observed technical facts and inferred human intent. A future navigation milestone may consume `contains_refs` and evidence groups for drill-down without reintroducing duplicated SVG payloads.

## M8.1.2 result

M8.1.2 is complete as measured profiling and limited hotspot reduction. The CLI prints macro timings and cardinalities after execution, the synthetic harness covers small/medium/large inputs, and profile-enabled output is semantically identical to the unprofiled result.

The next recommended step is a focused measurement/design pass for duplicate source reads in StackDetector. If a representative local large repository is available, run it manually with --profile; PrefectHQ/prefect remains optional and is not a suite dependency. Do not introduce parallelism or change evidence semantics to hide the remaining hotspot.'

## M8.1.3 result

M8.1.3 is complete as a bounded evidence calibration. The next recommended milestone is a manual run against a locally available large repository, preferably Prefect if present, to validate framework/persistence role coverage without adding repository-specific rules. Remaining work should focus on evidence coverage for semantically critical external drivers and bounded drill-down consumption of preserved LOW/UNKNOWN records; do not move filtering into the renderer or add global graph ranking.
'
## M8.1.4 result

M8.1.4 is complete as projection closure and semantic expansion control. The
high-level projection is now authoritative for ReadModel/SVG nodes. Endpoints,
routers, framework facts and auxiliary infrastructure remain traceable semantic
details unless explicit boundary evidence exists. HIGH→LOW edges are omitted from
the high-level view rather than promoting LOW nodes. Neutral Alpha/Beta fixtures
cover application, worker, scheduler, persistence, broker/cache, tooling and
container context.

The next recommended milestone is a manual profile/read-model comparison on a
locally available large repository, preferably Prefect when present, followed by
bounded drill-down consumption of semantic_details and contains_refs. Do not
move filtering into the renderer or introduce project-specific rules.

## M8.1.5 result

M8.1.5 is complete as architectural dependency role and context calibration.
External dependencies are promoted by semantic role plus bounded main-system
context, not by import frequency, package presence, generic DEPENDS_ON or
isolated hypothesis/framework evidence. LOW/UNKNOWN dependencies remain
traceable in the detailed model, and projected edges remain closed and
deterministic.

The next recommended milestone is a manual large-repository comparison of
dependency roles and projected edge composition, followed by a bounded
consumer for dependency/detail inspection. Remaining generic DEPENDS_ON edges
may need a separate evidence-quality milestone; they must not be reinterpreted
as strong architecture relations here.

## Next steps after algorithm refinement investigation

The next implementation milestone should address the residual contextual
promotion of auxiliary framework components using an evidence chain to the
primary application or an explicit independent boundary. Add neutral positive
and negative fixtures before changing weights or propagation.

After that, define canonical relation identity across InfrastructureRelation,
ArchitectureIR and the renderer-neutral ReadModel, preserving evidence and
compatibility. Only then start a renderer-only layout-density milestone for
fixed-band width, labels and edge routing.

The investigation harness and report are available at
`benchmarks/refinement_investigation.py` and
`docs/architecture/ALGORITHM_REFINEMENT_INVESTIGATION.md`. A real large
repository remains optional and was not available locally; the workspace is
not a substitute because it contains benchmark fixtures and examples.

## After context/relation/layout refinement

Completed:

- bounded architectural context roots prevent isolated local framework facts
  from promoting auxiliary components;
- canonical relation identity is established at the IR boundary while source
  spelling remains traceable;
- relation composition and hypothesis-context diagnostics are reproducible;
- deterministic multi-row semantic SVG packing reduces fixed-band width without
  changing the VisualizationReadModel.

Recommended next milestones:

1. Run the profile/read-model comparison against a locally available large
   repository, if one becomes available, without adding repository-specific
   rules.
2. Define a bounded hypothesis-context evidence contract if measurements show
   auxiliary evidence materially affecting global hypotheses. Preserve all
   detailed evidence and avoid a subsystem-level hypothesis engine.
3. Improve orthogonal edge routing and label handling for crossing-heavy graphs
   using the unchanged ReadModel. Keep layout metrics diagnostic and avoid
   force-directed or probabilistic layout.
4. Revisit remaining generic `DEPENDS_ON` relations only in a separate evidence
   quality milestone; do not reinterpret them as strong architecture relations
   without existing semantic evidence.

The raw-graph performance hotspot recorded by M8.1.2 remains separate and is
not reopened by this refinement.

## After M8.1.6

M8.1.6 establishes structured answers to “why is this node/edge projected?”
without moving analysis into the renderer. The next recommended work is:

1. Run `benchmarks.projection_audit --json` against a locally available large
   repository and review local-only, no-context and generic-relation counts.
2. If a real repository demonstrates substantial same-endpoint redundancy,
   implement one narrowly scoped high-level suppression rule only after
   provenance/direction/evidence equivalence is proven; retain both relations
   in the Detailed Model.
3. If hypothesis audits show material local-only support, design a bounded
   context-aware hypothesis contract before changing detector scoring. Do not
   introduce a subsystem-level hypothesis engine yet.
4. Keep renderer/layout unchanged while this semantic audit is evaluated.

## After M8.1.7

The operational audit reports now make projection explanations usable on
arbitrary repositories without copying terminal output. Recommended next
steps are:

1. Run architecture-recovery audit <large-repository> --profile when a local
   large repository is available and review persisted diagnostics.
2. Use report evidence-group IDs to select any future provenance export or
   drill-down contract; do not duplicate raw evidence in visual elements.
3. Investigate only failure classes reproducible in neutral fixtures, such as
   uncontextualized promotions or semantically redundant generic relations.
4. Keep report generation read-only and preserve the existing ArchitectureIR,
   projection, ReadModel and renderer contracts.

## After M8.1.8

1. Run `architecture-recovery audit <large-repository> --profile --force` when a
   local large repository is available and compare strong-root, weak-only and
   local/global-boundary metrics.
2. Review hypothesis context contamination reported by the audit before changing
   Layered/MVC/Hexagonal/Microservices scoring.
3. Investigate only remaining false promotions reproducible in neutral fixtures;
   preserve UNKNOWN/detailed-only when semantic context is absent.
4. Keep generic DEPENDS_ON in the Detailed Model and defer any high-level
   suppression until provenance/direction/subsumption is proven.
5. Treat any future repository cardinality anomaly as a profiling/reporting issue
   first, not as permission to add repository-specific heuristics.

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

## M8.1.11 - next steps

Completed: separate local significance from final global projection eligibility.
The projection selector now excludes local-only HIGH/MEDIUM nodes and
navigation-only repository envelopes, retains detailed semantic information,
and enforces projected-edge closure. The invariant
`local_only_projected_count == 0` is covered by neutral tests and audit output.

The next investigation should audit remaining global-boundary admission and
DEPLOYS/infrastructure provenance on a locally available large repository. It
must not compensate for missing context with score or cardinality thresholds.
Keep the policy bounded, evidence-based, deterministic, and prefer detailed-only
or UNKNOWN over an unsupported global promotion.