# Architecture Analysis Log

This document records experiments, observations, unexpected behavior, hypotheses and unresolved architectural questions.

Entries in this document are NOT automatically architectural decisions.

Accepted decisions belong in ADRs.

---

# Entry 001 — Initial Raw Architecture Output

## Status

Completed observation.

## Context

The first architecture output demonstrated that the analyzer could successfully extract low-level program information.

The generated graph contained:

* functions;
* methods;
* imports;
* calls;
* source locations;
* evidence references;
* confidence;
* observation status.

## Observation

When analyzing framework-heavy repositories, implementation details from frameworks can dominate the output.

Examples include framework-internal symbols conceptually similar to:

```text
fastapi.routing.get_request_handler
fastapi.routing.run_endpoint_function
fastapi.routing.serialize_response
fastapi.param_functions.Depends
```

These nodes may be correct program-analysis observations.

They are not necessarily appropriate architectural components.

## Conclusion

A low-level program graph and an architectural graph have different responsibilities.

Low-level information must not be destroyed simply because it is inappropriate for visualization.

This observation contributed to ADR-003.

---

# Entry 002 — Source-Origin Classification

## Status

Completed observation with unresolved questions.

## Context

Source-origin classification was introduced.

The analyzer began distinguishing concepts equivalent to:

```text
FIRST_PARTY
THIRD_PARTY
STANDARD_LIBRARY
UNKNOWN
```

and retaining classification reasons.

## Positive Result

The classification infrastructure improved explainability.

External packages can now be distinguished from repository-owned source when sufficient evidence exists.

## Important Benchmark Detail

The repository used during one test was the FastAPI repository itself.

Therefore:

```text
fastapi.*
```

being classified as FIRST_PARTY is correct for that experiment.

This experiment does NOT by itself prove that a separate application using FastAPI will correctly classify:

```text
application code → FIRST_PARTY
FastAPI → THIRD_PARTY
```

## Observation

A non-trivial number of symbols remained UNKNOWN.

Examples conceptually included packages/modules such as:

```text
routing
websockets
requests
responses
rich
ruff
sqlalchemy
```

UNKNOWN is preferable to incorrect classification.

However, excessive UNKNOWN classification indicates that source/package resolution requires further investigation.

## Conclusion

Classification appears promising but must be evaluated separately from aggregation.

Correctly identifying third-party symbols does not prove that the Architectural Graph properly aggregates them.

---

# Entry 003 — Required Controlled FastAPI Experiment

## Status

Completed experiment.

## Goal

Validate source-origin classification and graph aggregation using a repository whose ground truth is known.

## Fixture

Create a small repository conceptually similar to:

```text
test_project/
├── app/
│   ├── main.py
│   ├── routers/
│   │   └── users.py
│   ├── services/
│   │   └── users.py
│   └── repositories/
│       └── users.py
├── requirements.txt
└── docker-compose.yml
```

Expected first-party components:

```text
app.main
app.routers
app.services
app.repositories
```

Expected third-party dependencies:

```text
FastAPI
Uvicorn
SQLAlchemy
```

where applicable.

## Expected Raw Graph Behavior

The Raw Code Graph should preserve low-level observations such as:

```text
UserRouter.get_users
    CALLS
UserService.get_users

UserService.get_users
    CALLS
UserRepository.find_all
```

It may also preserve external references involving FastAPI.

## Expected Architectural Graph Behavior

The Architectural Graph should move toward abstractions similar to:

```text
API
    DEPENDS_ON
Application

Application
    DEPENDS_ON
Persistence

API
    USES
FastAPI
```

The exact component names are not yet mandated.

The important property is that FastAPI implementation internals do not dominate the Architectural Graph.

## Validation Questions

The experiment should answer:

1. Is application source correctly classified as FIRST_PARTY?
2. Is FastAPI correctly classified as THIRD_PARTY?
3. Does the Raw Code Graph preserve external observations?
4. Does the Architectural Graph aggregate framework internals?
5. Can every aggregated edge be traced to raw evidence?
6. Are UNKNOWN classifications explainable?
7. Does aggregation introduce unsupported relationships?

## Result

The controlled fixture is implemented at:

```text
examples/fastapi_sample/
```

The experiment confirmed that application code is classified as
`FIRST_PARTY`, FastAPI and Pydantic references as `THIRD_PARTY`, and standard
library imports such as `os` as `STANDARD_LIBRARY`. External symbols remain in
the Raw Code Graph while the Architectural Graph aggregates them into package
nodes. Aggregated edges retain `raw_edge_ids` and evidence references, and the
full suite passes with 32 tests.

The exact first-party component names remain intentionally unresolved; the
current grouping is structural and must not be treated as architecture proof.

---

# Entry 004 — Next Research Question

## Status

Open.

After controlled source-origin and aggregation tests succeed, investigate component aggregation.

The core question is:

> How should low-level first-party nodes be grouped into architectural components without relying only on directory names?

---

# M3 — Framework Adapter Foundation + FastAPI Adapter v1

## Status

Completed implementation and benchmark experiment.

## Motivation

M2.1 and M2.2 made symbol resolution, decorator evidence, constructor flow,
simple returns and bounded local data flow sufficiently precise for a semantic
adapter to consume existing observations. FastAPI was selected as the first
reference implementation to validate the adapter boundary. FastAPI is not the
architectural target of the engine.

## Contract

`FrameworkAdapter` receives the existing Raw Code Graph, parsed facts and
`SymbolIndex`. It can detect framework evidence and produce framework-neutral
semantic facts plus `Evidence`; it cannot parse source, scan the repository,
replace symbol resolution, mutate the Raw Graph, classify components or infer
architecture. A registry lets the pipeline run adapters without a FastAPI
branch in its analysis stages.

The additive `ArchitectureIR.framework_facts` field carries these facts while
keeping them separate from raw/architectural graph nodes and architecture
hypotheses. It is optional and keeps schema version `0.2` for backward
compatibility. Every fact has status, confidence, source and evidence refs.

## FastAPI reference semantics

The v1 adapter produces `APPLICATION`, `ROUTER`, `HTTP_ENDPOINT`,
`FRAMEWORK_DEPENDENCY`, `RESPONSE_SCHEMA`, `SCHEMA` and `ROUTER_INCLUSION`
facts. It recognizes resolved `FastAPI`, `APIRouter` and `Depends` imports,
aliases, route methods/paths/handlers, response models, clear Pydantic
`BaseModel` inheritance and observed include-router metadata.

The fact vocabulary is independent of FastAPI. Django `path(..., view)` and
Flask `@app.route(...)` could produce the same HTTP endpoint concept with a
different adapter implementation.

## UNKNOWN and negative behavior

Dynamic providers such as `Depends(registry["service"])`, unresolved schema
references and missing route paths remain `UNKNOWN`. A receiver named
`router`, a fake router class and a router from another framework are not
classified as FastAPI without import/resolution evidence. No service,
controller, repository, DTO, MVC, Clean, Hexagonal, Layered or Microservices
claim is produced by the adapter.

## Evidence and performance

Facts reuse Raw Graph evidence where available and add deterministic
`FRAMEWORK_ADAPTER` evidence at the observed source location. The adapter
uses parsed-fact and symbol indexes in one pass over the existing facts; it
does not parse files or rescan the repository. M3 adds only small local
binding indexes for framework application/router identity. It deliberately
does not compose include-router paths or inspect Pydantic internals.

The controlled fixture is `benchmarks/fixtures/fastapi_semantics/` and its
ground truth separates required, forbidden and expected-unknown facts,
traceability and determinism. The new fixture and all previous fixtures pass
the benchmark quality gate after the implementation.

## Architectural impact

No component detection or architecture inference rule was added. The adapter
ends at framework semantic evidence; component detection remains the next
separate interpretation boundary.

Potential evidence includes:

```text
dependency direction
call relationships
imports
framework semantics
entrypoints
deployment boundaries
configuration
graph communities
directory structure
naming conventions
```

Directory structure should be treated as evidence, not proof.

## Current implementation note

The current implementation provides a deterministic structural grouping based
on repository paths. It is explicitly provisional and does not claim that
directories such as `app`, `services` or `repositories` are architectural
components. A future decision should combine dependency direction, framework
signals, entrypoints and deployment boundaries before assigning architectural
roles.

This question may eventually require a dedicated ADR.

---

# Entry 005 — Evidence Improvement Roadmap and Symbol Resolution

## Status

In progress.

## Experimental development strategy

The next evidence-quality stages are intentionally ordered as:

```text
Symbol Resolution
        ↓
Repository Boundary / Source Origin
        ↓
Benchmark Infrastructure
        ↓
Framework Adapters
        ↓
Infrastructure Analysis
        ↓
Component Detection
        ↓
Architecture Inference
```

The strategy is to improve observations first, then evidence, then component
hypotheses and only later architecture hypotheses. `UNKNOWN` remains a valid
result. Component Detection and Architecture Pattern Inference are different
problems and must remain conceptually separate.

## Symbol-resolution assessment

Before this entry, the resolver indexed definitions and could match direct
names or unique short names. Imports were recorded, but aliases, relative
imports, re-exports, receiver instances, type hints and cross-module bases
were not used consistently. Decorator expressions and assignments were not
preserved as graph evidence. Calls that could not be resolved were generally
omitted, making dynamic dispatch indistinguishable from a missing observation.

The incremental implementation now normalizes relative imports, follows
common re-exports, resolves aliased class instantiation and receiver method
calls when evidence is sufficient, uses type hints as supporting evidence,
resolves cross-module inheritance, and preserves decorators. Dynamic and
otherwise unresolved calls are retained in the Raw Code Graph with an
explicit reason instead of receiving a fabricated target.

The resolver still does not execute code or reliably resolve reflection,
registry lookups, `getattr`, monkey-patching, overloaded dispatch, wildcard
imports, or runtime-generated symbols. Those remain unresolved by design.

The controlled fixture and tests now provide a reproducible base for measuring
these cases; a formal precision/recall benchmark remains the next step after
this resolver pass.

## Boundary limitations observed

The current `RepositoryBoundary` and Python classifier handle ordinary
repositories, root-package layouts and the conventional `src/` layout. They
still need dedicated evidence and fixtures for monorepos with several package
roots, namespace packages without `__init__.py`, editable installs, multiple
Python environments, Poetry/complex dependency constraints, and conflicts
between a local module and an installed package with the same import name.

---

# Entry 007 — M2.1 Raw Graph Precision Sprint

## Status

Completed.

## Scope and strategy

This milestone improves Raw Code Graph precision only. `Symbol Resolution`
and `Data Flow Analysis` remain separate problems: symbol resolution is now
more conservative, while general interprocedural data flow remains outside
this milestone.

The intended progression was:

```text
reduce false resolutions
        ↓
improve evidence quality
        ↓
establish trustworthy ground truth
        ↓
measure again
```

The repository-wide short-name fallback was removed. Direct references now
need lexical/module or explicit import evidence; unresolved is preferred to a
globally guessed target. Type hints are collected for every parsed file and
remain scoped evidence rather than runtime truth.

Duplicate Raw Graph edges remain deduplicated, but now merge evidence
references, support counts and distinct observation metadata. Call edges retain
the semantic caller, callee, source path and line. Decorators now retain
structured expression, arguments, owner and AST evidence. Alias imports retain
local name, imported name, resolved target and import evidence.

Dynamic dispatch remains unresolved with an explicit reason.

## Benchmark model

The benchmark no longer treats every observed Raw Graph edge outside a partial
ground truth as a false positive. Its universes are separated into:

```text
source_origins
raw_nodes
symbol_resolutions
raw_edges
architectural_edges
expected_unresolved_calls
decorator_evidence
alias_evidence
edge_support
determinism
```

`raw_edge_precision` is explicitly `null` for partial edge universes. Symbol
resolution reports correct targets, unresolved expected targets, correct
abstentions and wrong targets. `wrong_resolution_rate` is calculated only over
the explicitly evaluated resolution cases. Execution status is separate from
the exact ground-truth quality gate.

The baseline now covers nine deterministic cases, including ambiguous short
names, scoped type hints, duplicate edge evidence and dynamic dispatch. The
old partial-graph precision values are not comparable with this baseline.

No new ADR was required; the changes implement the evidence, uncertainty and
Raw/Architectural separation already required by ADR-001, ADR-002 and ADR-003.

---

# Entry 008 — M2.2 Basic Data Flow

## Status

Implemented with bounded semantic coverage.

## Scope

The Raw Code Graph now receives evidence from a small local-flow pass for
direct constructor assignments, one-step local aliases, constructor argument
bindings, contextual `self.attribute` assignments and a single unambiguous
factory return. The resolver keeps these bindings indexed by lexical scope or
class/attribute pair. Conflicting assignments, branches with multiple
candidates and dynamic factories remain `UNKNOWN`.

This milestone deliberately does not add SSA, CFG construction, general
interprocedural data flow, reflection handling, framework adapters or
architectural inference. `Symbol Resolution` and `Data Flow Analysis` remain
distinct concerns: the former identifies symbols, while this pass propagates
only a few local identities that have direct evidence.

## Benchmark impact

The benchmark gained a neutral `basic_data_flow` fixture covering local
instantiation, constructor injection and `self.attribute` resolution. It
reports `data_flow_resolution_count` in addition to the M2.1 resolution
metrics. The controlled benchmark continues to evaluate only explicit ground
truth universes; it does not treat unlisted Raw Graph facts as false positives.

## Precision and cost

The M2.2 baseline reports zero wrong resolutions across the covered fixtures,
with deterministic output and explicit unresolved cases. The implementation
uses the existing symbol/import indexes plus three bounded passes over parsed
assignments and returns. It does not scan every symbol for every variable and
does not reanalyze dependency implementations.

## Remaining limitations

Path-sensitive branches, loops, chained/transitive factories, complex return
propagation, dynamic registries, reflection and interprocedural data flow are
future work. These limitations are intentional so that unknown remains safer
than a speculative target.

---

# Entry 006 — Repository Boundary and Benchmark Baseline

## Status

Completed baseline.

## Result

`RepositoryBoundary` now exposes import roots and deterministic module
candidates. Roots are discovered from the repository root, conventional
`src/` directories, package-level `pyproject.toml` files, setuptools
`package-dir` declarations and Poetry package roots. Local module resolution
checks the most specific root first, supports namespace packages and returns
`UNKNOWN` when multiple local candidates are possible.

The classifier now prefers an unambiguous repository module over the execution
environment. Vendor/dependency paths remain excluded, while generated code
keeps its distinct origin.

The benchmark harness is available through:

```text
python -m benchmarks.runner
```

Its initial five cases cover FastAPI, a simple layered project, `src-layout`,
a two-package monorepo and a namespace package. Each case has ground truth for
selected origins/nodes/edges and reports symbol/edge recall, origin accuracy,
unknown rate, graph sizes and determinism. All initial cases pass.

This benchmark intentionally validates observed facts only. It does not claim
that directory or package boundaries are architectural components.

---

# M4 — Evidence-Based Component Detection

## Status

Completed implementation and controlled benchmark experiment.

## Motivation and boundary

M3 supplied framework-neutral facts, but the engine still needed a cautious
layer to answer which first-party entities may belong together. M4 creates
component candidates only. It does not infer MVC, MVT, Layered, Clean,
Hexagonal, Microservices, Monolith, bounded contexts or author intent.

The legacy `components` collection produced by `ArchitecturalGraphBuilder`
remains available for backward compatibility and is still structural. M4
uses separate `ArchitectureIR.component_candidates` and
`component_unassigned_node_ids`, so directory aggregation cannot be mistaken
for evidence-based detection.

## Model and heuristics

Candidates are module-level `Component` values with `UNCERTAIN` status,
member node IDs, internal and external raw edge IDs, semantic hints, roles,
supporting observations, confidence and evidence references. Confidence is a
bounded heuristic score, not a probability.

The detector builds a small affinity index over first-party module pairs:

| Signal | Weight |
|---|---:|
| `CALLS` | 3.0 |
| `INSTANTIATES` | 3.0 |
| `CALLS` with local-flow evidence | +1.0 |
| `EXTENDS` | 2.0 |
| `IMPORTS` | 1.0 |
| `FRAMEWORK_DEPENDENCY` | 2.5 |
| `ROUTER_INCLUSION` | 2.5 |
| `RESPONSE_SCHEMA` | 1.5 |

A pair must reach the explicit threshold `3.0`; qualifying pairs are joined
with deterministic union-find. Names, directory names and class names never
contribute to the score. First-party module identity comes from existing Raw
Graph nodes and source-origin classification.

## Traceability and boundaries

Each candidate records raw internal and external edge IDs, supporting raw and
framework observations, and a deterministic `COMPONENT_DETECTION` evidence
record. External nodes are never members of first-party candidates. Modules
without a qualifying group remain in `component_unassigned_node_ids`.

The detector consumes the existing Raw Graph, Architectural Graph and
framework facts. It performs no source scan, reparsing, new symbol resolution,
data-flow analysis or external dependency inspection.

Dependency direction is retained in each supporting observation. When both
directions are present for a module pair, the candidate records a separate
`RECIPROCAL_RELATION` observation rather than treating the cycle as an
undifferentiated edge.

## Benchmark result

`benchmarks/fixtures/component_detection/` contains a first-party group
connected by calls, instantiation and local data flow, an external `requests`
relationship, a name-only `UserService`, an isolated `UserController` and a
weakly related schema. Its ground truth evaluates exact members, forbidden
groupings, unassigned nodes, evidence source, traceability and determinism.

The fixture achieved 1.0 component recall, 1.0 member precision, 1.0 member
recall, 0.0 false grouping rate, 1.0 unassigned recall and 1.0 evidence
recall. All previous M3 and earlier fixtures remained green.

## Limitations

M4 is intentionally module-granular and conservative. It does not represent
multiple competing candidate groups for the same module, calculate semantic
similarity, perform sophisticated community detection or infer architectural
roles such as service/repository/controller. These belong to later work.

---

# M5 - Infrastructure Semantics

## Status

Completed implementation and controlled benchmark experiment.

## Scope

M5 adds a small infrastructure-neutral fact layer for Dockerfiles and Docker
Compose. It performs static parsing only; it does not execute containers,
resolve shell commands, access Docker, pull images or make network calls.

The implemented adapters expose:

- Dockerfile FROM, EXPOSE, ENV, WORKDIR, COPY, ENTRYPOINT and CMD;
- Compose service names, images, builds, ports, environment, env_file,
  volumes, networks and depends_on;
- explicit Compose service dependency relations;
- conservative classifications for databases, caches, message brokers,
  containers and UNKNOWN resources.

Resource classification uses image and service-name evidence. Generic names such
as database without corroborating evidence remain UNKNOWN.

## Code-to-infrastructure relations

A bounded configuration pass recognizes statically observed environment variable
accesses such as os.getenv("DATABASE_URL") and os.environ.get("REDIS_URL").
It only connects the variable to a Compose service when the Compose value
explicitly names that service. Dynamic environment names, unresolved URLs and
unmatched services remain unconnected.

The IR preserves:

- observed module to configuration relations;
- observed configuration to Compose target relations;
- inferred component to infrastructure relations;
- evidence references and confidence/status on each relation.

Infrastructure resources remain outside first-party component membership. The Raw
Graph retains low-level container/configuration nodes and edges.

## Performance and limitations

The adapters make one bounded pass over infrastructure files. Code mapping uses
indexed parsed calls, Compose services and environment maps; it does not scan
all symbols per component. Dockerfile continuation semantics, Compose
interpolation, env-file contents, Kubernetes, CI, Terraform and runtime
behavior remain future extensions.

## M6.1 — Architecture Hypothesis Engine

M6.1 introduced a small deterministic `ArchitectureHypothesisEngine` over the
existing ArchitectureIR. The IR contract was extended additively with support
and contradiction evidence references; the canonical evidence list remains the
single traceability system. The scorer discounts INFERRED, UNCERTAIN and
UNKNOWN evidence relative to OBSERVED evidence and keeps contradictory
relations visible in the explanation.

The first detector is deliberately limited to Layered. It requires existing
layer metadata plus evidence-bearing cross-layer CALLS, IMPORTS or DEPENDS_ON
relations, so directory naming alone cannot create a hypothesis. A controlled
fixture demonstrates a controller -> service -> repository chain, and tests
cover contradiction preservation, UNKNOWN and deterministic output. No LLM,
new parser, dynamic analysis or additional repository scan was added.

## M6.2 — Evidence-Based Layered Detector

M6.2 refined Layered detection to consume the complete ArchitectureIR. The
engine now indexes raw and architectural nodes, component roles and framework
entrypoint facts, and combines directional structural relations with data-flow
metadata and infrastructure terminal relations when resolvable. Names remain
only a way to interpret existing layer metadata; they cannot create a signal.

The benchmark adds names-only, reverse-dependency and ambiguous fixtures. Names
without relations return UNKNOWN; reverse-only evidence remains traceable as a
contradiction and returns UNKNOWN; mixed forward/reverse evidence returns
UNCERTAIN. The global deterministic scorer was preserved. No parser, scanner,
framework adapter or infrastructure adapter was changed.
## M6.3 � MVC evidence detector

M6.3 adds an independent deterministic `mvc` hypothesis to the existing engine. It consumes indexed ArchitectureIR relations and existing HTTP/framework facts only. Support requires semantic controller-to-model and model-to-persistence direction, with optional HTTP/controller and controller/view signals. Direct controller-to-persistence and reverse persistence-to-controller relations remain contradictory evidence. Directory names without semantic relations remain UNKNOWN. The five controlled MVC fixtures pass with deterministic output; no parser, scan, Raw Graph or renderer changes were introduced.
## M6.4 � Strengthened framework facts

M6.4 strengthened the existing FastAPI adapter without adding a parser, repository scan or architectural detector. Framework-neutral facts now preserve resolved application/router expressions, endpoint router and handler relationships, `CONTROLLER_LIKE` facts for resolved HTTP route handlers, endpoint-associated dependencies, and observation metadata containing source location and raw evidence refs. Alias imports continue to resolve through the existing import index. Dynamic providers, generic routers and unresolved schemas remain UNKNOWN or absent. The complete FastAPI ground truth passes with deterministic output.
## M7.1 � Architecture Visualization Read Model

M7.1 adds a deterministic renderer-neutral projection from ArchitectureIR to a serializable VisualizationReadModel. The projection consumes only Architectural Graph nodes/edges, components, infrastructure resources/relations, framework facts, evidence and hypotheses already present in the IR. It creates explicit endpoint and UNKNOWN target nodes only from evidenced framework facts, preserves original relation kinds/status/confidence/evidence refs, and keeps hypotheses separate from visual facts. No renderer, layout algorithm, parser or repository scan was added.
## M7.2 � Semantic SVG Renderer MVP

M7.2 adds a deterministic SVG renderer that consumes only VisualizationReadModel. It uses fixed semantic bands, stable node ordering, fixed spacing and status-aware edge styles. SVG elements preserve read-model IDs, origin refs, evidence refs, status and confidence through data attributes. Architecture hypotheses are rendered in a separate panel and are not converted into structural facts. No source, Raw Graph, parser, resolver, framework adapter or layout dependency is accessed by the renderer.

## M7.3 — Semantic Visualization Layout & Inspection

M7.3 evolves the SVG consumer without changing ArchitectureIR, discovery or the VisualizationReadModel contract. The renderer now prioritizes explicit layer/group/preferred-layer hints, then bounded semantic fallback from existing node kind, role and hints. Entrypoints are placed in presentation, application/domain/persistence/infrastructure/external groups when supported by existing data.

Relations remain present but are classified visually as architectural, structural or generic. Architectural relations receive stronger styling; structural relations remain visible with reduced emphasis. Cross-band edges use deterministic orthogonal paths anchored at node boundaries. SVG nodes, edges and hypotheses expose stable IDs and inspection metadata for labels, roles, layers, related edges, source/target, relation kind, statuses, confidence, evidence refs and hypothesis associations. No new analysis or inference is performed.

## M7.4 — Interactive Evidence Inspection

M7.4 adds interaction only to the SVG consumer. The renderer embeds deterministic, precomputed indices for Read Model nodes, edges, evidence and hypotheses. Clicking a node highlights related edges and displays node metadata; clicking an edge displays source, target and relation metadata; clicking a hypothesis displays its status, confidence and evidence references. A bounded in-SVG panel presents evidence source type, detail, file, lines and symbol when available, and explicitly shows UNKNOWN for absent fields. No Raw Graph, parser, resolver or new architectural inference is accessed.

## M7.5 — Optional Motion & Visual Semantics

M7.5 adds optional presentation-only motion to the SVG renderer. STATIC remains the default and safe mode; ANIMATED enables reusable CSS effects for supported architectural flow relations and known infrastructure resources. Animation is never runtime simulation or architectural inference. The same VisualizationReadModel is used in both modes, with no ArchitectureIR, Raw Graph or analysis changes. Unknown and uncertain facts do not receive confirmed-flow animation, and selected elements can suppress animation for readability.

## M7.6 — Web Consumption & Accessibility

M7.6 adds a minimal optional browser consumer using only Python's standard library. It serves a previously rendered static SVG at /architecture.svg, an optional animated SVG at /architecture-animated.svg and a small accessible HTML page at /. The HTTP layer has fixed routes and never accepts repository paths, commands or analysis requests. SVG remains the primary renderer, STATIC remains the default, and the Read Model is not reconstructed by the web layer.

## M7.7 � Visualization CLI

M7.7 adds high-level `visualize` and `serve` commands. Each invocation analyzes the repository once, builds one VisualizationReadModel, and delegates static/animated output to the existing SVG renderer. `serve` passes only already-generated SVG artifacts to the fixed-route web consumer. The CLI adds orchestration only; it does not participate in architectural inference or introduce a new analysis pass.

## M6.5 � Evidence-Based Hexagonal Architecture Detection

M6.5 adds an independent `hexagonal` hypothesis using only existing IR nodes, relations, framework facts, infrastructure semantics and evidence. Support requires multiple directional categories: input boundary to core, core dependency on a port contract, and/or an infrastructure adapter implementing/extending a port. Direct core-to-concrete-infrastructure relations are preserved as contradictions. Names-only fixtures remain UNKNOWN. Six controlled fixtures cover positive, infrastructure-backed, names-only, direct contradiction, ambiguous support/contradiction and negative cases.

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
## M8.1.1 — Evidence payload hardening

M8.1.1 hardens only the representation boundary between `VisualizationReadModel` and SVG. A structural association remains fully traceable, but a visual node, edge or hypothesis no longer repeats a large evidence ID list in its attributes. The Read Model now owns deterministic `EvidenceGroup` entries with a stable ID, unique complete references, count, source-type summary and source/origin paths. Elements carry `evidence_group_ref` and `evidence_count`; associations at or below the explicit 20-reference serialization threshold remain inline.

The SVG interaction payload carries each large reference collection once through the shared group index and includes evidence details only for the bounded first inspection window. Inspection reports the total count and the first 20 observations. The complete evidence collection remains available in the Read Model and the group's complete reference list. Duplicate associations are removed per element and equal sets share the same group ID.

The change does not alter ArchitectureIR, Architectural Significance, High-Level Architecture Projection, nodes, edges, hypotheses or architectural relations. It is a serialization/performance refinement only. No ADR was created because the existing evidence and renderer-boundary decisions remain sufficient.