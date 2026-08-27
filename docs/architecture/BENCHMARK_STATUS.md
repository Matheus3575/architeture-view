# Benchmark and Quality Status

## M2.2 baseline

The benchmark has 10 deterministic fixtures. Ground truth is separated by
responsibility: source origins, symbol resolutions, Raw Graph edges,
Architectural Graph edges, expected unresolved calls, decorator/alias
evidence and edge support.

Partial ground truth does not define Raw Graph precision over every observed
edge. `wrong_resolution_rate` is calculated only over explicitly evaluated
symbol-resolution entries.

| Fixture | Correct | Correct unknown | Wrong | Flow resolutions | Deterministic |
|---|---:|---:|---:|---:|---|
| `fastapi_sample` | 2 | 1 | 0 | 0 | yes |
| `simple_python_layered` | 2 | 0 | 0 | 0 | yes |
| `src_layout` | 2 | 0 | 0 | 1 | yes |
| `monorepo` | n/a | 0 | 0 | 0 | yes |
| `namespace_package` | 1 | 0 | 0 | 0 | yes |
| `ambiguous_short_name` | 1 | 1 | 0 | 0 | yes |
| `scoped_type_hints` | 2 | 0 | 0 | 2 | yes |
| `duplicate_edge_evidence` | 2 | 0 | 0 | 0 | yes |
| `dynamic_dispatch` | 0 | 1 | 0 | 0 | yes |
| `basic_data_flow` | 2 | 0 | 0 | 2 | yes |

Aggregate covered-resolution results:

```yaml
resolution_evaluated: 14
correct_resolution_count: 14
correct_unresolved_count: 3
unresolved_resolution_count: 0
wrong_resolution_count: 0
wrong_resolution_rate: 0.0
symbol_precision: 1.0
symbol_recall: 1.0
deterministic: true
```

These values are a baseline, not a universal accuracy claim. They measure
only the facts represented in the current ground truths.

## M3 status

The benchmark now contains 11 deterministic fixtures, including
`benchmarks/fixtures/fastapi_semantics/`. Its ground truth evaluates required
framework facts, forbidden generic-router facts, expected UNKNOWN dependency
resolution, `FRAMEWORK_ADAPTER` evidence and repeatability. The M3 fixture and
the ten previous fixtures pass the quality gate.

The runner reports elapsed time for the two analyses used by each determinism
check. This is an operational measurement, not a hard performance threshold.
The adapter performs bounded indexed interpretation and does not add a source
parse or repository scan.

## M4 status

The benchmark now contains 12 deterministic fixtures, including
`benchmarks/fixtures/component_detection/`. The M4 ground truth evaluates
exact candidate membership, required evidence types, forbidden groupings,
unassigned modules, evidence traceability and determinism.

The M4 fixture results are:

```yaml
component_recall: 1.0
member_precision: 1.0
member_recall: 1.0
false_grouping_rate: 0.0
unassigned_recall: 1.0
evidence_recall: 1.0
deterministic: true
```

The candidate detector is module-level and uses a bounded affinity pass. It
does not use directory/name-only grouping, machine learning, LLMs, CFG/SSA or
additional parsing.

## Test status

- Before M2.2: 42 tests.
- After M2.2: 47 tests collected and passing.
- After M3: 55 tests collected and passing.
- After M4: 61 tests collected and passing.
- Required checks: pytest, benchmark runner and `compileall`.

The controlled M2.2 fixture is `benchmarks/fixtures/basic_data_flow/`.

The final M4 benchmark run passed all 12 fixtures. Its aggregate reported
analysis time was 44.087 seconds across the runner's two deterministic
analyses per fixture; the new component fixture reported 5.580 seconds. No
pre-M4 aggregate timing was retained, so a before/after speedup is not claimed.

## Quality gates

Execution status and quality status are separate. A benchmark can execute
successfully while failing its ground-truth quality gate. The current M2.2
baseline passes both for all fixtures.

## Limitations of the measurement

- Architectural Graph precision is not measured from Raw Graph ground truth.
- Unlisted valid observations are not classified as false positives.
- Performance is observed operationally, not used as a pass/fail threshold.
- New benchmark cases are required before claiming coverage for new semantics.

## M5 status

The benchmark now contains 13 deterministic fixtures, including
benchmarks/fixtures/infrastructure_semantics/. Its ground truth covers
Dockerfile and Compose resource discovery, database/cache/container/UNKNOWN
classification, service dependencies, environment configuration mapping,
code-to-infrastructure relations, forbidden false relations, evidence
traceability and repeatability.

The M5 fixture results are:

infrastructure_resource_precision: 1.0
infrastructure_resource_recall: 1.0
infrastructure_relation_precision: 1.0
infrastructure_relation_recall: 1.0
infrastructure_evidence_recall: 1.0
false_infrastructure_relation_rate: 0.0
deterministic: true

The fixture analysis remained bounded and static. It does not execute Docker,
make network calls or inspect local container state.
## M6.1 status

A 14th fixture, `benchmarks/fixtures/hypothesis_engine/`, validates the
minimal hypothesis engine. It requires a Layered hypothesis, traceability and
forbids MVC and Microservices. The fixture is analyzed twice and must remain
deterministic. The observed Layered result is `inferred` with confidence
`0.666667` from two evidence-bearing cross-layer relations; no pattern certainty
is asserted.

## M6.2 status

The benchmark now contains 17 deterministic fixtures. The M6.2 cases cover a
clear API -> service -> repository -> PostgreSQL chain, names-only structure,
reverse repository -> API dependency and conflicting evidence. Ground truth
checks hypothesis status, support/contradiction presence, forbidden patterns,
traceability and determinism. The four hypothesis fixtures pass with
hypothesis recall 1.0 and traceability recall 1.0; the names-only case reports
UNKNOWN with zero supporting evidence.
## M6.3 status

The benchmark suite now contains 22 deterministic fixtures, including five MVC cases: positive semantic MVC, names-only UNKNOWN, MVC with a direct contradiction, MVC/Layered coexistence, and a clearly non-MVC case. Ground truths evaluate MVC status, hypothesis recall, traceability recall, false-positive count for expected UNKNOWN, supporting evidence, contradicting evidence and determinism. All five MVC cases pass; MVC hypothesis recall and traceability recall are 1.0, names-only/non-MVC false-positive count is 0, and contradiction evidence is present in the contradiction case.
## M6.4 status

The 22-fixture benchmark suite now measures complete FastAPI framework-fact precision in addition to recall. The FastAPI semantic fixture reports framework fact recall 1.0, precision 1.0, UNKNOWN recall 1.0, complete fact traceability and determinism. Alias application/Depends resolution, endpoint-router-handler facts, controller-like roles, dependencies, response schemas, router inclusion, dynamic UNKNOWN behavior and generic-router false positives are covered. All 22 benchmarks pass. The observed full runner time was 8.976 seconds across the runner's two analyses per fixture; no directly comparable M6.3 timing baseline was retained.
## M7.1 status

The benchmark suite now contains 23 deterministic fixtures, including `visualization_read_model`. The new case validates endpoint and infrastructure nodes, ROUTES_TO and ROUTER_INCLUSION edges, edge validity, evidence preservation, hypothesis preservation and determinism. All 23 benchmarks pass; the read-model case produced 9 nodes and 7 edges with valid edges, traceability and deterministic output. The observed full runner time was approximately 9.279 seconds across two analyses per fixture; this is operational data, not a hard threshold.
## M7.2 status

The `visualization_read_model` benchmark now validates the SVG output in addition to the read model. It requires valid SVG, all read-model nodes/edges represented, and deterministic repeated rendering. The case passes with 9 nodes and 7 edges; read-model edge validity, SVG validity, completeness and determinism are all true. The complete suite contains 23 passing benchmark cases.

## M7.3 status

The visualization benchmark now checks semantic layout groups, architectural/structural relation classes, complete inspection metadata, valid SVG, element completeness and deterministic repeated rendering. The 23-case suite passes; the visualization fixture produces 9 nodes and 7 edges with all required groups and relation classes.

## M7.4 status

The visualization tests now cover interaction payload presence, stable IDs, inspection panel metadata and UNKNOWN evidence behavior. Existing architectural benchmark metrics were not changed. The full controlled benchmark suite remains the source of regression validation.

## M7.5 status

The visualization benchmark now measures static and animated SVG validity, deterministic repeated rendering for both modes, animation semantic preservation, Read Model immutability and output sizes. The 23-case suite passes; the visualization fixture reports valid deterministic outputs in both modes and unchanged Read Model data.

## M7.6 status

The visualization benchmark now reports web_static_available, web_animated_available, accessibility_metadata and web_output_deterministic separately from architectural quality metrics. The 23-case suite passes; static and animated routes are available, accessibility metadata is present and served output remains deterministic.

## M6.5 status

The controlled benchmark suite now contains 29 cases, including six Hexagonal fixtures. Ground truths cover positive support, infrastructure presence, names-only UNKNOWN, direct core-to-infrastructure contradiction, ambiguous support plus contradiction and a negative case. All six pass with Hexagonal hypothesis recall 1.0, traceability recall 1.0, zero false positives in UNKNOWN cases, preserved contradiction evidence and deterministic analysis. The full suite remains deterministic and prior Layered/MVC metrics remain unchanged.

## M6.6 status

The benchmark suite adds eight Microservices fixtures covering clear HTTP and messaging boundaries, containers, modular monoliths, names-only structures, container-only structures, ambiguity and a negative case. Ground truths evaluate status, traceability, support, UNKNOWN correctness, contradiction preservation and deterministic analysis.

## M8.1 status

The benchmark suite adds a synthetic many-module projection case. It measures significance recall/precision, detailed versus high-level node counts, reduction ratio, projected edge validity, projection traceability, LOW/UNKNOWN preservation and determinism. The reduction ratio is reported as an operational metric and is not treated as quality by itself.
## M8.1.1 status

The suite adds `evidence_payload_stress`, a controlled one-application fixture with benchmark-only synthetic evidence augmentation. The projection and its node/edge signatures are compared before and after payload augmentation; only Read Model serialization is measured.

Observed stress metrics:

```yaml
projected_nodes: unchanged
projected_edges: unchanged
evidence_reference_count: 12035
inline_evidence_reference_count: 26
evidence_group_count: 3
evidence_traceability: true
evidence_projection_semantics_unchanged: true
legacy_inline_svg_bytes: 1125373
svg_payload_bytes: 345145
evidence_payload_reduction_ratio: 0.693306
```

The complete collection remains recoverable through the Read Model groups, duplicate associations are deterministic, and SVG/inspection output remains valid. The reduction is a representation metric, not an architectural quality metric.

## M8.1.2 status

The separate scale benchmark exercises 50/200/400 Python modules with imports, aliases, functions, classes and calls, then builds the VisualizationReadModel. One observed final run reported:

50_modules: {files: 51, symbols: 150, raw_nodes: 254, raw_edges: 352, evidence: 356, architectural_nodes: 3, architectural_edges: 2, projected_nodes: 2, projected_edges: 1, evidence_groups: 1, total_seconds: 0.403}
200_modules: {files: 201, symbols: 600, raw_nodes: 1004, raw_edges: 1402, evidence: 1406, architectural_nodes: 3, architectural_edges: 2, projected_nodes: 2, projected_edges: 1, evidence_groups: 1, total_seconds: 1.083}
400_modules: {files: 401, symbols: 1200, raw_nodes: 2004, raw_edges: 2802, evidence: 2806, architectural_nodes: 3, architectural_edges: 2, projected_nodes: 2, projected_edges: 1, evidence_groups: 1, total_seconds: 2.180}
growth_200_to_400: {input_ratio: 2.0, runtime_ratio: 2.012}
profile_enabled_semantic_equivalence: true

The comparable analysis-only measurement was 2.761 seconds before the measured Raw Graph optimizations and 1.949 seconds after; Raw Graph changed from 1.315 to 0.393 seconds in those observed runs. Timing is operational data, not a CI threshold. The regular benchmark runner remains separate.'

## M8.1.3 status

The benchmark suite adds `significance_calibration`, a controlled real-world-like fixture with a FastAPI application, domain and persistence flow, Compose database/cache resources, auxiliary tests/tooling/benchmarks and multiple external libraries. It validates detailed-model preservation, high-level selection, external dependency levels, LOW/UNKNOWN preservation, edge validity, projection traceability and deterministic repeated analysis.

Observed fixture metrics:

```yaml
detailed_node_count: 24
high_level_node_count: 11
projection_reduction_ratio: 0.541667
external_dependency_detailed_count: 9
external_dependency_projected_count: 2
significance_precision: 1.0
significance_recall: 1.0
external_dependency_promotion_precision: 1.0
false_architectural_promotion_count: 0
projected_edge_validity: true
projection_traceability: true
deterministic: true
```

`fastapi` is HIGH and `redis` is MEDIUM. `PIL`, `anyio`, `dateutil`, `psycopg`, `pytest`, `requests` and `yaml` remain LOW. Auxiliary components remain LOW. The complete benchmark runner passed, including the pre-existing projection, visualization, architecture-pattern, evidence and renderer cases. Timing remains diagnostic and is not a quality threshold.
'
## M8.1.4 status

The regression benchmark now reports projection closure and semantic-detail
cardinalities in addition to existing significance, evidence and SVG metrics.
The neutral controlled closure fixtures are covered by
tests/test_projection_closure.py.

Observed controlled fixture metrics:

yaml
alpha:
  detailed_node_count: 6
  projection_node_count: 5
  read_model_high_level_node_count: 5
  semantic_detail_node_count: 18
  endpoint_detail_count: 12
  router_detail_count: 3
  projected_edge_validity: true
  projection_traceability: true
beta:
  detailed_node_count: 6
  projection_node_count: 4
  read_model_high_level_node_count: 4
  semantic_detail_node_count: 5
  infrastructure_high_level_count: 2
  container_detail_count: 1
  projected_edge_validity: true
  projection_traceability: true

The full benchmark runner remains the regression gate; timing is diagnostic only.
Real repositories are used for symptom discovery, not for project-specific
heuristics.

## M8.1.5 status

The dependency calibration tests add neutral Alpha and Beta scenarios covering
general libraries, principal framework technology, framework internals,
persistence technology, database drivers without context, message transport,
external-service clients, generic high-degree dependencies, auxiliary framework
components, UNKNOWN and deterministic traceability.

The existing real-world-like fixture was recalibrated so persistence component
and redis remain LOW when only generic imports/technology matching are present.
Observed benchmark metrics:

```yaml
significance_calibration:
  detailed_node_count: 24
  projection_node_count: 9
  external_dependency_detailed_count: 9
  external_dependency_projected_count: 1
  architectural_dependency_precision: 1.0
  architectural_dependency_recall: 1.0
  false_dependency_promotion_count: 0
  generic_depends_on_promotion_count: 0
  component_false_promotion_count: 0
  projected_edge_validity: true
  projection_traceability: true
```

The complete benchmark runner remains the regression gate. Timing remains
diagnostic; no absolute performance threshold was added.

## Algorithm refinement investigation benchmark

`benchmarks/refinement_investigation.py` provides a reproducible diagnostic
matrix for significance calibration, ReadModel closure, infrastructure
semantics, many-module projection, the workspace and a generated neutral
context. It records structural cardinalities, significance distribution,
relation vocabulary, effective evidence coverage, SVG dimensions/bytes and
repeatability. Timing is reported only for diagnosis.

The baseline revision produced deterministic results in every scenario. The
workspace had 52 architectural nodes, 16 projected nodes, 131 semantic details,
19 projected edges, 24 detailed external dependencies with 1 projected, and a
2,040 x 784 static SVG. The neutral context exposed one residual isolated
framework-component promotion. The infrastructure fixture exposed both
lowercase and uppercase relation forms.

The investigation harness also evaluates existing ground truths when available.
`significance_calibration` reports significance precision 1.0, recall 1.0 and
zero false architectural promotions. Generated scenarios intentionally report
observations without being CI ground truths.

## Algorithm refinement benchmark status

The reproducible harness `benchmarks/refinement_investigation.py` now records
context roots, significance quality, canonical relation kinds and strengths,
degree/hub metrics, parallel aggregation, cross-group relations, effective
evidence coverage, hypothesis context, SVG dimensions, rows per group, route
proxies, label-overflow proxy, whitespace proxy, overlap and determinism.
Timing remains diagnostic and is not a CI threshold.

Validated representative results:

```yaml
significance_calibration:
  projected_nodes: 9
  projected_edges: 11
  significance_precision: 1.0
  significance_recall: 1.0
  false_architectural_promotions: 0
  svg: 1080x784

infrastructure_semantics:
  projected_nodes: 9
  projected_edges: 13
  mixed_relation_groups: {}
  max_out_degree: 6
  svg: 1080x740

workspace:
  architectural_nodes: 52
  projected_nodes: 16
  projected_edges: 19
  external_detailed: 24
  external_projected: 1
  route_crossing_proxy_count: 2
  node_overlap_count: 0
  svg: 1080x937
```

The baseline file preserves the previous revision and explicitly explains the
intentional differences: context contamination removal, relation identity
aggregation, deterministic band packing and current working-tree cardinality.
All controlled projected edges retain effective evidence coverage of 1.0.

The complete benchmark runner and full pytest suite remain the regression gate.
No Prefect or other network-dependent manual run was available locally.

## M8.1.6 audit benchmark status

`python -m benchmarks.projection_audit` and `--json` provide compact and
machine-readable projection audits. The audit reports projected node counts,
roots, contextualized nodes, independent boundaries, nodes without context,
local-only framework promotions, relation kinds/strengths, DEPENDS_ON
composition, hypothesis context and traceability.

Representative final counters:

```yaml
significance_calibration:
  projected_nodes: 9
  context_roots: 1
  contextualized_projected: 7
  independent_boundaries: 4
  projected_without_context: 2
  local_only_framework_promotions: 0
  projected_edges: 11
  depends_on: {total: 6, only: 3, shadowed: 0, aggregated: 3}
  evidence_coverage: 1.0

workspace:
  projected_nodes: 16
  context_roots: 1
  contextualized_projected: 15
  independent_boundaries: 10
  projected_without_context: 1
  local_only_framework_promotions: 0
  projected_edges: 19
  depends_on: {total: 11, only: 6, shadowed: 0, aggregated: 5}
  evidence_coverage: 1.0

neutral_context_generated:
  projected_nodes: 5
  local_only_framework_promotions: 0
  projected_without_context: 1
  evidence_coverage: 1.0
```

A dedicated neutral audit fixture covers root chains, independent roots,
local framework flow, same/cross context, only/shadowed/aggregated generic
relations and hypothesis evidence. Timing is not used as a quality threshold.

## M8.1.7 report benchmark status

The new regression coverage exercises:

- local repository audit with both, Markdown-only and JSON-only output;
- output directory creation and safe overwrite/--force;
- one analysis invocation for the report pair;
- deterministic Markdown and JSON;
- schema sections, context/relations/hypothesis diagnostics;
- profile embedding;
- compact 10,000-reference evidence associations.

The stress fixture verifies a stable EvidenceGroup reference and correct
evidence count without serializing the 10,000 IDs inline. Timing is recorded
by the existing profile when requested but is not a flaky benchmark threshold.

No large real-world repository was available locally. Real-world validation
remains optional and is not required for the fixture regression suite.

## M8.1.8 benchmark status

Neutral regression coverage now exercises repository envelopes, multiple strong
application roots, weak DEPENDS_ON chains, bounded ROUTES_TO/QUERIES chains,
shared cross-root brokers, isolated infrastructure, explicit deployment
boundaries, weak-evidence volume saturation and deterministic context metadata.
The report stress case uses 10,000 evidence references and verifies compact
EvidenceGroup output without inline duplication.

Quality checks focus on context membership, weak-only reachability, root strength,
local/global boundary classification, projection closure, traceability and
determinism. Timing remains diagnostic rather than a flaky CI threshold. The
existing controlled benchmarks and SVG/read-model regressions remain covered;
layout code was not changed.

No network-dependent large repository was available for a separate real-world
run in this milestone.

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

## M8.1.11 - measured projection gate

The neutral gate fixture measured 8 detailed subjects/resources and 6 projected
nodes. It retained 2 locally significant subjects as detailed-only:
`local_only_significant_count=2` and `local_only_projected_count=0`.
The projected set was root-anchored application/API/domain/persistence/database
plus one independently justified API; projected edges had valid endpoints.

Current benchmark observations after the gate (diagnostic, not timing contracts):

| scenario | projected nodes | local-only significant | local-only projected | without global justification |
|---|---:|---:|---:|---:|
| significance_calibration | 1 | 7 | 0 | 0 |
| visualization_read_model | 0 | 6 | 0 | 0 |
| infrastructure_semantics | 0 | 8 | 0 | 0 |
| projection_many_modules | 1 | 2 | 0 | 0 |
| workspace | 3 | 12 | 0 | 0 |
| neutral_context_generated | 1 | 2 | 0 | 0 |

The existing isolated infrastructure fixture now remains detailed-only, so its
high-level relation count is zero while its infrastructure semantic details are
preserved. No large real-world repository was available locally for a manual
comparison.

## M8.1.12 - deployment provenance measurements

The neutral provenance fixture contains 7 architectural/resource subjects and 3 audited DEPLOYS relations. It measured:

| provenance | count | context behavior |
|---|---:|---|
| explicit_execution_deployment | 1 | can propagate |
| aggregated_deployment | 1 | supporting only |
| navigation_derived | 1 | does not propagate |

The resulting audit values were `deploys_total=3`, `membership_established_by_deploys=1`, and `navigation_transit_membership_count=0`. The workspace manual run found 338 files, 926 symbols, 1,595 raw nodes, 4,239 raw edges, 5,361 evidence items, 54 architectural nodes, 51 architectural edges, 3 projected nodes and 3 projected edges. Its two DEPLOYS relations were both navigation-derived and non-propagating. Profile total was 3.208 seconds. The temporary report sizes were 44,458 bytes JSON and 16,982 bytes Markdown. These are observations, not timing/cardinality contracts.

The focused deployment/projection tests passed. No large real-world repository was available locally for a separate comparison.
