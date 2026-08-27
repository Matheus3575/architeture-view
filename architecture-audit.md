# Architecture Projection Audit

## Summary

- repository: `C:/Users/pichau/Documents/Projetos/architeture-view`
- files: 340
- symbols: 967
- raw nodes / edges: 1644 / 4413
- architectural nodes / edges: 54 / 51
- projected nodes / edges: 4 / 5
- context roots: 2 (strong: 2)
- navigation roots: 1
- context root strengths: {'strong': 2}
- framework context roots: 1
- framework boundary candidates / qualified / rejected: 2 / 1 / 1
- owned framework applications / local usage: 1 / 0
- supporting-only global memberships: 0
- globally eligible projected: 4
- local-only significant / projected: 12 / 0
- projected without global justification: 0
- navigation-only projected: 0
- independent global boundaries projected: 1
- DEPLOYS total / can propagate / supporting / non-propagating: 2 / 0 / 0 / 2
- DEPLOYS provenance: {'navigation_derived': 2}
- deployment memberships / navigation transit: 0 / 0
- deployment boundary candidates / qualified global / rejected-local: 2 / 0 / 2
- positive evidence produced / accepted / rejected / absent: 98 / 90 / 8 / 13
- semantic memberships / explicit deployment ownership / directional propagation: 1 / 0 / 0
- positive evidence rejection reasons: {'application boundary was not admitted as a global root': 1, 'deployment provenance does not establish global context': 2, 'raw positive relation has no architectural aggregation': 1, 'relation does not connect a root to an established context member': 4}
- entrypoints total / resolved / unresolved: 3 / 3 / 0
- first-party / accepted / rejected entrypoints: 3 / 3 / 0
- entrypoint roots: 1
- semantic details: 72
- external dependencies: 25
- evidence groups: 6
- traceability: yes
- determinism: yes

## Application Boundary Audit

### application:architeture-view

- application provenance: repository_aggregate
- boundary evidence kind: repository_membership
- projected: no
- significance: low
- observed/inferred: inferred
- executable/entrypoint evidence: no
- evidence count/group: 1634 / evidence-group-8621b2987f4e5bee030d

## Executable Entrypoints

### python -m architecture_recovery.repository

- provenance: MAIN_MODULE
- declared target: architecture_recovery.repository.__main__
- resolved target: module:architecture_recovery.repository.__main__
- owner: component:architecture_recovery
- accepted: yes
- status: observed
- rejection reason: none
- evidence count / group: 1 / none

### architecture-recovery

- provenance: PROJECT_SCRIPT
- declared target: architecture_recovery.cli:main
- resolved target: architecture_recovery.cli.main
- owner: component:architecture_recovery
- accepted: yes
- status: observed
- rejection reason: none
- evidence count / group: 1 / none

### python -m architecture_recovery

- provenance: MAIN_MODULE
- declared target: architecture_recovery.__main__
- resolved target: module:architecture_recovery.__main__
- owner: component:architecture_recovery
- accepted: yes
- status: observed
- rejection reason: none
- evidence count / group: 1 / none

## Framework Boundary Audit

### component:architecture_recovery

- qualification: REJECTED
- scope: unresolved
- fact ownership: UNRESOLVED
- boundary evidence: none
- context root: yes
- evidence count/group: 3825 / evidence-group-33cff2a6abf835f8cb10

### component:benchmarks

- qualification: QUALIFIED_GLOBAL
- scope: global
- fact ownership: OWNED_APPLICATION_BOUNDARY
- boundary evidence: application_router_endpoint_association
- context root: yes
- evidence count/group: 3656 / evidence-group-6f06e7640e261b2fd5ba

### component:examples

- qualification: REJECTED
- scope: local
- fact ownership: RELATED_FRAMEWORK_BOUNDARY
- boundary evidence: none
- context root: yes
- evidence count/group: 49 / evidence-group-52c48ba914ee3a3ee4dc

## Projected Nodes

### component:architecture_recovery

- role: component
- significance: high
- score: 1.0
- projection eligible: yes
- context root: yes
- root strength/kind: strong / EXECUTABLE_ENTRYPOINT
- membership source: context_root
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: architectural context root: executable entrypoint, architectural context root: independently justified application boundary
- context root IDs: component:architecture_recovery
- context chain: component:architecture_recovery
- strong reasons: framework fact associated with the principal application context
- supporting reasons: architectural context root: executable entrypoint, architectural context root: independently justified application boundary, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, executable entrypoint owned by first-party component, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 3825
- evidence group: evidence-group-33cff2a6abf835f8cb10
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: yes
- ownership: structural_rejected via none
- framework qualification: REJECTED
- framework scope: unresolved
- framework fact ownership: UNRESOLVED
- framework boundary evidence: none

### component:benchmarks

- role: component
- significance: high
- score: 1.0
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: context_root
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: architectural context root: owned framework application boundary
- context root IDs: component:benchmarks
- context chain: component:benchmarks
- strong reasons: component owns an explicitly related infrastructure resource, framework fact associated with the principal application context
- supporting reasons: application boundary: owned framework application, architectural context root: owned framework application boundary, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONNECTS_TO, evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, framework boundary has observed cross-component flow, framework fact candidate: APPLICATION, framework fact candidate: CONTROLLER_LIKE, framework fact candidate: FRAMEWORK_DEPENDENCY, framework fact candidate: HTTP_ENDPOINT, framework fact candidate: RESPONSE_SCHEMA, framework fact candidate: ROUTER, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 3656
- evidence group: evidence-group-6f06e7640e261b2fd5ba
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: QUALIFIED_GLOBAL
- framework scope: global
- framework fact ownership: OWNED_APPLICATION_BOUNDARY
- framework boundary evidence: application_router_endpoint_association

### component:examples

- role: component
- significance: medium
- score: 0.85
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:CONNECTS_TO,DEPENDS_ON
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:benchmarks
- context chain: component:benchmarks → component:examples; component:benchmarks → external.app → component:examples
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, evidence-backed architectural relation: CONNECTS_TO, evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, framework fact candidate: CONTROLLER_LIKE, framework fact candidate: FRAMEWORK_DEPENDENCY, framework fact candidate: HTTP_ENDPOINT, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 49
- evidence group: evidence-group-52c48ba914ee3a3ee4dc
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: REJECTED
- framework scope: local
- framework fact ownership: RELATED_FRAMEWORK_BOUNDARY
- framework boundary evidence: none

### infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres

- role: database
- significance: high
- score: 1.0
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: independent_boundary
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: explicit infrastructure boundary relation
- context root IDs: none
- context chain: missing
- strong reasons: explicit infrastructure boundary relation
- supporting reasons: evidence-backed architectural relation: CONNECTS_TO, evidence-backed architectural relation: DEPENDS_ON, observed infrastructure candidate: DATABASE, participates in an architecture hypothesis
- evidence count: 5
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

## Projected Relations

### projection-edge:component:architecture_recovery:component:benchmarks:CONTAINS

- component:architecture_recovery → component:benchmarks
- canonical kind: CONTAINS
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context; relation crosses independent context roots
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:architecture_recovery:component:examples:CONTAINS

- component:architecture_recovery → component:examples
- canonical kind: CONTAINS
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context; relation crosses independent context roots
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:benchmarks:component:architecture_recovery:DEPENDS_ON

- component:benchmarks → component:architecture_recovery
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation crosses independent context roots
- support count: 1
- evidence count / group: 68 / evidence-group-573ba43d2341ea67d006
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:benchmarks:component:examples:CONNECTS_TO

- component:benchmarks → component:examples
- canonical kind: CONNECTS_TO
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 2 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:component:benchmarks:infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres:DEPENDS_ON

- component:benchmarks → infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 3
- evidence count / group: 4 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

## DEPENDS_ON Audit

- total: 2
- ONLY_RELATION: 0
- AGGREGATED_STRUCTURAL_SUPPORT: 2
- SHADOWED_BY_STRONGER_RELATION: 0
- SAME_CONTEXT: 0
- CROSS_CONTEXT: 1
- weak-only reachable projected nodes: 0
- projected without strong context: 0
- local-only significance: 0
- weak evidence saturation: 5
- structural ownership rejected: 5
- globally contextualized by ownership: 0
- framework context roots: 1
- framework candidates / qualified / rejected: 2 / 1 / 1
- owned framework applications / local usage: 1 / 0
- supporting-only global memberships: 0
- globally eligible projected: 4
- local-only significant / projected: 12 / 0
- projected without global justification: 0
- navigation-only projected: 0
- independent global boundaries projected: 1
- DEPLOYS total / can propagate / supporting / non-propagating: 2 / 0 / 0 / 2
- DEPLOYS provenance: {'navigation_derived': 2}
- deployment memberships / navigation transit: 0 / 0
- deployment boundary candidates / qualified global / rejected-local: 2 / 0 / 2
- positive evidence produced / accepted / rejected / absent: 98 / 90 / 8 / 13
- semantic memberships / explicit deployment ownership / directional propagation: 1 / 0 / 0
- positive evidence rejection reasons: {'application boundary was not admitted as a global root': 1, 'deployment provenance does not establish global context': 2, 'raw positive relation has no architectural aggregation': 1, 'relation does not connect a root to an established context member': 4}

## Hypothesis Context Audit

### hexagonal

- supporting evidence: 71
- contradicting evidence: 0
- context-root support: 71
- local-only support: 0
- cross-context support: 0
- unclassified support: 0

### layered

- supporting evidence: 72
- contradicting evidence: 0
- context-root support: 72
- local-only support: 0
- cross-context support: 68
- unclassified support: 0

### microservices

- supporting evidence: 21
- contradicting evidence: 21
- context-root support: 20
- local-only support: 0
- cross-context support: 0
- unclassified support: 1

### mvc

- supporting evidence: 128
- contradicting evidence: 74
- context-root support: 128
- local-only support: 0
- cross-context support: 68
- unclassified support: 0

## Positive Evidence Ledger

### application:architeture-view — application_boundary

- producer: GraphAggregation
- accepted: no
- provenance: repository_aggregate
- source relation / owner / direction: APPLICATION_BOUNDARY / application:architeture-view / none
- role: APPLICATION
- rejection reason: application boundary was not admitted as a global root
- evidence count / group: 1 / none

### component:architecture_recovery — executable_entrypoint

- producer: EntrypointAnalyzer
- accepted: yes
- provenance: MAIN_MODULE
- source relation / owner / direction: architecture_recovery.__main__ / component:architecture_recovery / declaration_to_target_to_owner
- role: EXECUTABLE_ENTRYPOINT
- rejection reason: none
- evidence count / group: 1 / none

### component:architecture_recovery — executable_entrypoint

- producer: EntrypointAnalyzer
- accepted: yes
- provenance: PROJECT_SCRIPT
- source relation / owner / direction: architecture_recovery.cli:main / component:architecture_recovery / declaration_to_target_to_owner
- role: EXECUTABLE_ENTRYPOINT
- rejection reason: none
- evidence count / group: 1 / none

### component:architecture_recovery — executable_entrypoint

- producer: EntrypointAnalyzer
- accepted: yes
- provenance: MAIN_MODULE
- source relation / owner / direction: architecture_recovery.repository.__main__ / component:architecture_recovery / declaration_to_target_to_owner
- role: EXECUTABLE_ENTRYPOINT
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:309a8a8a6287c5a8 / repository:architeture-view / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 21 / evidence-group-b5bb7212a45e330d64b0

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / application / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / application / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / users_router / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / users_router / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / router / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:benchmarks / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / users_router / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / application / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / users_router / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / router / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / users_router / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / users_router / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: ROUTER / router / fact
- role: ROUTER
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: ROUTER / users_router / fact
- role: ROUTER
- rejection reason: none
- evidence count / group: 1 / none

### component:benchmarks — raw_relation

- producer: RawGraph
- accepted: no
- provenance: lost_before_architecture
- source relation / owner / direction: CONNECTS_TO:edge:c0d23720b16b58d5 / configuration:DATABASE_URL / observed
- role: CONNECTS_TO
- rejection reason: raw positive relation has no architectural aggregation
- evidence count / group: 4 / none

### component:examples — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:f3e76a4986dc0eb1 / repository:architeture-view / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 2 / none

### component:examples — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:examples / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:examples — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / application / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:examples — semantic_relation

- producer: GraphAggregation
- accepted: yes
- provenance: inferred_architectural_relation
- source relation / owner / direction: CONNECTS_TO:arch-edge:f0f2d77c5407f6fa / component:benchmarks / directed
- role: CONNECTS_TO
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: component
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### configuration:DATABASE_URL — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: configuration
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: APPLICATION / external.app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: HTTP_ENDPOINT / external.app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### external.app — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: framework_fact
- source relation / owner / direction: ROUTER_INCLUSION / external.app / fact
- role: ROUTER_INCLUSION
- rejection reason: none
- evidence count / group: 1 / none

### external.fastapi — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: APPLICATION_FRAMEWORK
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:api — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: container
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:postgres — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: database
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:redis — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: cache
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:api — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: container
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:postgres — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: database
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:redis — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: cache
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres — semantic_relation

- producer: GraphAggregation
- accepted: no
- provenance: inferred_architectural_relation
- source relation / owner / direction: CONNECTS_TO:arch-edge-env-configuration:DATABASE_URL-infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres / configuration:DATABASE_URL / directed
- role: CONNECTS_TO
- rejection reason: relation does not connect a root to an established context member
- evidence count / group: 2 / none

### infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres — semantic_relation

- producer: GraphAggregation
- accepted: no
- provenance: inferred_architectural_relation
- source relation / owner / direction: CONNECTS_TO:arch-edge-env-configuration:DATABASE_URL-infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres / configuration:DATABASE_URL / directed
- role: CONNECTS_TO
- rejection reason: relation does not connect a root to an established context member
- evidence count / group: 2 / none

### infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres — semantic_relation

- producer: GraphAggregation
- accepted: no
- provenance: inferred_architectural_relation
- source relation / owner / direction: CONNECTS_TO:arch-edge-env-configuration:DATABASE_URL-infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres / configuration:DATABASE_URL / directed
- role: CONNECTS_TO
- rejection reason: relation does not connect a root to an established context member
- evidence count / group: 2 / none

### infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres — semantic_relation

- producer: InfrastructureAnalyzer
- accepted: no
- provenance: inferred_architectural_relation
- source relation / owner / direction: CONNECTS_TO:infra-relation:configuration:DATABASE_URL:infrastructure:compose:benchmarks/fixtures/visualization_read_model/docker-compose.yml:postgres / configuration:DATABASE_URL / directed
- role: CONNECTS_TO
- rejection reason: relation does not connect a root to an established context member
- evidence count / group: 2 / none

### infrastructure:compose:examples/compose_stack/docker-compose.yml:api — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: container
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:examples/compose_stack/docker-compose.yml:cache — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: cache
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:examples/compose_stack/docker-compose.yml:database — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: database
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### repository:architeture-view — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: repository
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

## Diagnostics

- **diagnostic_signal** `structural_ownership_rejected`: Structural application containment was not used as architectural ownership.
- **diagnostic_signal** `rejected_framework_boundary`: Framework boundary candidates lack coherent application ownership or boundary evidence.
- **diagnostic_signal** `positive_evidence_absent`: Significant subjects have no positive architectural context evidence from a producer.
- **diagnostic_signal** `weak_evidence_saturation`: Repeated weak evidence was capped by semantic reason class.

## Evidence Groups

- `evidence-group-33cff2a6abf835f8cb10`: 3825 refs; summary={'AST': 724, 'CALL_GRAPH': 2046, 'COMPONENT_DETECTION': 1, 'CONFIGURATION': 1, 'FRAMEWORK_ADAPTER': 36, 'GRAPH_AGGREGATION': 8, 'IMPORT': 768, 'SYMBOL_RESOLUTION': 241}; sources=architecture-graph, benchmarks/projection_audit.py, benchmarks/refinement_investigation.py, benchmarks/runner.py, benchmarks/scale_profile.py, component-detection, pyproject.toml, src/architecture_recovery/__init__.py, src/architecture_recovery/__main__.py, src/architecture_recovery/architecture/__init__.py, src/architecture_recovery/architecture/hypotheses.py, src/architecture_recovery/architecture/inference.py, src/architecture_recovery/classification/__init__.py, src/architecture_recovery/classification/base.py, src/architecture_recovery/classification/python.py, src/architecture_recovery/cli.py, src/architecture_recovery/components/__init__.py, src/architecture_recovery/components/detection.py, src/architecture_recovery/entrypoints.py, src/architecture_recovery/frameworks/__init__.py; source refs truncated
- `evidence-group-52c48ba914ee3a3ee4dc`: 49 refs; summary={'AST': 26, 'CALL_GRAPH': 4, 'DOCKER_COMPOSE': 2, 'FRAMEWORK_ADAPTER': 4, 'GRAPH_AGGREGATION': 7, 'IMPORT': 6}; sources=architecture-graph, examples/compose_stack/app.py, examples/compose_stack/docker-compose.yml, examples/fastapi_sample/app/api.py, examples/fastapi_sample/app/services.py, examples/fastapi_sample/generated/schema_generated.py, examples/fastapi_sample/src/app/core.py, examples/simple_python_layered/app/controllers/user.py, examples/simple_python_layered/app/repositories/user.py, examples/simple_python_layered/app/services/user.py
- `evidence-group-573ba43d2341ea67d006`: 68 refs; summary={'CALL_GRAPH': 37, 'GRAPH_AGGREGATION': 1, 'IMPORT': 18, 'SYMBOL_RESOLUTION': 12}; sources=architecture-graph, benchmarks/projection_audit.py, benchmarks/refinement_investigation.py, benchmarks/runner.py, benchmarks/scale_profile.py
- `evidence-group-6f06e7640e261b2fd5ba`: 3656 refs; summary={'AST': 576, 'CALL_GRAPH': 1843, 'COMPONENT_DETECTION': 5, 'DOCKERFILE': 1, 'DOCKER_COMPOSE': 21, 'FRAMEWORK_ADAPTER': 96, 'GRAPH_AGGREGATION': 28, 'IMPORT': 837, 'SYMBOL_RESOLUTION': 249}; sources=architecture-graph, benchmarks/__init__.py, benchmarks/fixtures/ambiguous_short_name/consumer.py, benchmarks/fixtures/ambiguous_short_name/consumer_explicit.py, benchmarks/fixtures/ambiguous_short_name/module_a.py, benchmarks/fixtures/ambiguous_short_name/module_b.py, benchmarks/fixtures/basic_data_flow/logic.py, benchmarks/fixtures/basic_data_flow/main.py, benchmarks/fixtures/basic_data_flow/storage.py, benchmarks/fixtures/component_detection/api.py, benchmarks/fixtures/component_detection/isolated.py, benchmarks/fixtures/component_detection/logic.py, benchmarks/fixtures/component_detection/repository.py, benchmarks/fixtures/component_detection/schemas.py, benchmarks/fixtures/component_detection/suggested_service.py, benchmarks/fixtures/duplicate_edge_evidence/consumer.py, benchmarks/fixtures/duplicate_edge_evidence/services.py, benchmarks/fixtures/dynamic_dispatch/consumer.py, benchmarks/fixtures/evidence_payload_stress/app.py, benchmarks/fixtures/evidence_payload_stress/helper.py; source refs truncated
- `evidence-group-8621b2987f4e5bee030d`: 1634 refs; summary={'AST': 1615, 'CALL_GRAPH': 4, 'DOCKERFILE': 1, 'DOCKER_COMPOSE': 8, 'GRAPH_AGGREGATION': 6}; sources=architecture-graph, benchmarks/__init__.py, benchmarks/fixtures/ambiguous_short_name/consumer.py, benchmarks/fixtures/ambiguous_short_name/consumer_explicit.py, benchmarks/fixtures/ambiguous_short_name/module_a.py, benchmarks/fixtures/ambiguous_short_name/module_b.py, benchmarks/fixtures/basic_data_flow/logic.py, benchmarks/fixtures/basic_data_flow/main.py, benchmarks/fixtures/basic_data_flow/storage.py, benchmarks/fixtures/component_detection/api.py, benchmarks/fixtures/component_detection/isolated.py, benchmarks/fixtures/component_detection/logic.py, benchmarks/fixtures/component_detection/repository.py, benchmarks/fixtures/component_detection/schemas.py, benchmarks/fixtures/component_detection/suggested_service.py, benchmarks/fixtures/duplicate_edge_evidence/consumer.py, benchmarks/fixtures/duplicate_edge_evidence/services.py, benchmarks/fixtures/dynamic_dispatch/consumer.py, benchmarks/fixtures/evidence_payload_stress/app.py, benchmarks/fixtures/evidence_payload_stress/helper.py; source refs truncated
- `evidence-group-b5bb7212a45e330d64b0`: 21 refs; summary={'DOCKERFILE': 1, 'DOCKER_COMPOSE': 19, 'GRAPH_AGGREGATION': 1}; sources=architecture-graph, benchmarks/fixtures/hex_infrastructure/docker-compose.yml, benchmarks/fixtures/hypothesis_engine/docker-compose.yml, benchmarks/fixtures/infrastructure_semantics/Dockerfile, benchmarks/fixtures/infrastructure_semantics/docker-compose.yml, benchmarks/fixtures/microservices_ambiguous/docker-compose.yml, benchmarks/fixtures/microservices_containers/docker-compose.yml, benchmarks/fixtures/microservices_containers_only/docker-compose.yml, benchmarks/fixtures/significance_calibration/docker-compose.yml, benchmarks/fixtures/visualization_read_model/docker-compose.yml, examples/compose_stack/docker-compose.yml

## Profile

- total seconds: 3.5997177999815904

- scanner: 0.574518 s; counts={'files': 340, 'file_count': 340, 'source_files': 248}
- stack_detection: 0.053357 s; counts={'evidence': 17}
- parser: 0.717753 s; counts={'parsed_files': 248, 'definitions': 967, 'imports': 1110, 'calls': 7042}
- basic_data_flow: 0.006932 s; counts={'assignments': 3319, 'returns': 739, 'scopes': 106, 'flow_entries': 0}
- symbol_resolution: 0.018141 s; counts={'symbols': 967, 'symbol_count': 967, 'unresolved_calls': 5254, 'flow_entries': 66}
- source_origin: 0.474841 s; counts={'local_modules': 246, 'classified_nodes': 1643, 'raw_node_count': 1643, 'classifications': 1643}
- raw_graph: 0.979801 s; counts={'nodes': 1634, 'raw_node_count': 1634, 'edges': 4393, 'raw_edge_count': 4393, 'evidence': 5375, 'evidence_count': 5375, 'unresolved_calls': 4632}
- framework_adapters: 0.052342 s; counts={'facts': 103, 'evidence': 103}
- infrastructure_semantics: 0.012440 s; counts={'resources': 22, 'relations': 11, 'evidence': 33}
- architectural_graph: 0.018290 s; counts={'nodes': 32, 'edges': 42, 'evidence': 5474}
- component_detection: 0.016392 s; counts={'components': 5, 'component_count': 5, 'unassigned_nodes': 150, 'pairs': 276}
- entrypoints: 0.002816 s; counts={'entrypoints': 3, 'resolved_entrypoints': 3, 'accepted_entrypoints': 3}
- architecture_ir: 0.195073 s; counts={'nodes': 54, 'edges': 51, 'evidence': 5606, 'raw_nodes': 1644, 'raw_edges': 4413, 'architectural_nodes': 54, 'architectural_edges': 51, 'components': 5, 'projected_nodes': 0, 'projected_edges': 0, 'evidence_groups': 0}
- architecture_hypotheses: 0.071077 s; counts={'hypotheses': 4}
- architecture_validation: 0.193794 s; counts={'valid': True, 'warnings': 20}
- architectural_significance_projection: 0.084954 s; counts={'detailed_nodes': 76, 'projected_nodes': 4, 'projected_edges': 5}
- projection_audit: 0.127197 s; counts={'projected_nodes': 4, 'projected_edges': 5, 'evidence_coverage': 1.0}
- projection_audit_report: 0.000000 s; counts={'evidence_groups': 6, 'projected_nodes': 4, 'projected_edges': 5, 'components': 10, 'architectural_components': 5, 'component_candidates': 5}
