# Architecture Projection Audit

## Summary

- repository: `C:/Users/pichau/Documents/Projetos/architeture-view`
- files: 335
- symbols: 898
- raw nodes / edges: 1561 / 4028
- architectural nodes / edges: 54 / 51
- projected nodes / edges: 16 / 19
- context roots: 1 (strong: 1)
- navigation roots: 1
- context root strengths: {'strong': 1}
- semantic details: 60
- external dependencies: 25
- evidence groups: 11
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
- evidence count/group: 1543 / evidence-group-d33465667243e4d82656

## Projected Nodes

### component:architecture_recovery

- role: component
- significance: medium
- score: 0.3
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPENDS_ON
- membership strength: supporting
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:benchmarks
- context chain: component:benchmarks → component:architecture_recovery; component:benchmarks → external.tree_sitter → component:architecture_recovery; component:benchmarks → external.yaml → component:architecture_recovery
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, framework fact candidate: SCHEMA
- evidence count: 3337
- evidence group: evidence-group-45bb96dd8df7a10f88c8
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none

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
- boundary justification: architectural context root: framework application boundary
- context root IDs: component:benchmarks
- context chain: component:benchmarks
- strong reasons: component owns an explicitly related infrastructure resource, framework fact associated with the principal application context
- supporting reasons: application boundary: framework application with observed boundary, architectural context root: framework application boundary, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONNECTS_TO, evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, framework boundary has observed cross-component flow, framework fact candidate: APPLICATION, framework fact candidate: CONTROLLER_LIKE, framework fact candidate: FRAMEWORK_DEPENDENCY, framework fact candidate: HTTP_ENDPOINT, framework fact candidate: RESPONSE_SCHEMA, framework fact candidate: ROUTER, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 3271
- evidence group: evidence-group-e9f6461d9a77835fe146
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none

### component:examples

- role: component
- significance: medium
- score: 0.85
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:CONNECTS_TO,DEPENDS_ON,DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:benchmarks
- context chain: component:benchmarks → component:examples; component:benchmarks → external.fastapi → component:examples; component:benchmarks → external.app → component:examples
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, evidence-backed architectural relation: CONNECTS_TO, evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, framework fact candidate: CONTROLLER_LIKE, framework fact candidate: FRAMEWORK_DEPENDENCY, framework fact candidate: HTTP_ENDPOINT, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 49
- evidence group: evidence-group-52c48ba914ee3a3ee4dc
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none

### component:tests

- role: component
- significance: medium
- score: 0.3
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPENDS_ON
- membership strength: supporting
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:benchmarks
- context chain: component:benchmarks → component:architecture_recovery → component:tests; component:benchmarks → component:tests; component:benchmarks → external.pytest → component:tests
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON
- evidence count: 2770
- evidence group: evidence-group-22f15e620b5bc85e47e5
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none

### external.fastapi

- role: APPLICATION_FRAMEWORK
- significance: high
- score: 0.55
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPENDS_ON
- membership strength: supporting
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:benchmarks
- context chain: component:benchmarks → component:examples → external.fastapi; component:benchmarks → external.fastapi
- strong reasons: principal framework used by an application or router
- supporting reasons: dependency role candidate: GENERAL_LIBRARY
- evidence count: 4
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:api

- role: container
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
- supporting reasons: observed infrastructure candidate: CONTAINER
- evidence count: 3
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:postgres

- role: database
- significance: high
- score: 0.55
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
- supporting reasons: observed infrastructure candidate: DATABASE
- evidence count: 2
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:redis

- role: cache
- significance: high
- score: 0.55
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
- supporting reasons: observed infrastructure candidate: CACHE
- evidence count: 2
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:api

- role: container
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
- supporting reasons: observed infrastructure candidate: CONTAINER
- evidence count: 3
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:postgres

- role: database
- significance: high
- score: 0.55
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
- supporting reasons: observed infrastructure candidate: DATABASE
- evidence count: 2
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:redis

- role: cache
- significance: high
- score: 0.55
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
- supporting reasons: observed infrastructure candidate: CACHE
- evidence count: 2
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

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

### infrastructure:compose:examples/compose_stack/docker-compose.yml:api

- role: container
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
- supporting reasons: observed infrastructure candidate: CONTAINER
- evidence count: 3
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:examples/compose_stack/docker-compose.yml:cache

- role: cache
- significance: high
- score: 0.55
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
- supporting reasons: observed infrastructure candidate: CACHE
- evidence count: 2
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### infrastructure:compose:examples/compose_stack/docker-compose.yml:database

- role: database
- significance: high
- score: 0.55
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
- supporting reasons: observed infrastructure candidate: DATABASE
- evidence count: 2
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

### repository:architeture-view

- role: repository
- significance: medium
- score: 0.44
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:benchmarks
- context chain: component:benchmarks → repository:architeture-view; component:benchmarks → component:examples → repository:architeture-view
- strong reasons: none
- supporting reasons: evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPLOYS, repository context retained for navigation
- evidence count: 24
- evidence group: evidence-group-1c4368e9190b1e1f9ee1
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none

## Projected Relations

### projection-edge:component:architecture_recovery:component:benchmarks:CONTAINS

- component:architecture_recovery → component:benchmarks
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:architecture_recovery:component:examples:CONTAINS

- component:architecture_recovery → component:examples
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:architecture_recovery:component:tests:CONTAINS

- component:architecture_recovery → component:tests
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:benchmarks:component:architecture_recovery:DEPENDS_ON

- component:benchmarks → component:architecture_recovery
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
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

### projection-edge:component:benchmarks:external.fastapi:DEPENDS_ON

- component:benchmarks → external.fastapi
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 49 / evidence-group-68000fd1653a0a441895
- stronger relation kinds: none
- context propagation: supports_context

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

### projection-edge:component:examples:external.fastapi:DEPENDS_ON

- component:examples → external.fastapi
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 5 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:architecture_recovery:DEPENDS_ON

- component:tests → component:architecture_recovery
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 969 / evidence-group-86d9a5e5e6a6e40e08d0
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:benchmarks:DEPENDS_ON

- component:tests → component:benchmarks
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 20 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:api:infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:postgres:DEPENDS_ON

- infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:api → infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:postgres
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:api:infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:redis:DEPENDS_ON

- infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:api → infrastructure:compose:benchmarks/fixtures/infrastructure_semantics/docker-compose.yml:redis
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:api:infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:postgres:DEPENDS_ON

- infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:api → infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:postgres
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:api:infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:redis:DEPENDS_ON

- infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:api → infrastructure:compose:benchmarks/fixtures/significance_calibration/docker-compose.yml:redis
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:examples/compose_stack/docker-compose.yml:api:infrastructure:compose:examples/compose_stack/docker-compose.yml:cache:DEPENDS_ON

- infrastructure:compose:examples/compose_stack/docker-compose.yml:api → infrastructure:compose:examples/compose_stack/docker-compose.yml:cache
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:examples/compose_stack/docker-compose.yml:api:infrastructure:compose:examples/compose_stack/docker-compose.yml:database:DEPENDS_ON

- infrastructure:compose:examples/compose_stack/docker-compose.yml:api → infrastructure:compose:examples/compose_stack/docker-compose.yml:database
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:repository:architeture-view:component:architecture_recovery:CONTAINS

- repository:architeture-view → component:architecture_recovery
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:repository:architeture-view:component:benchmarks:DEPLOYS

- repository:architeture-view → component:benchmarks
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 21 / evidence-group-b5bb7212a45e330d64b0
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:repository:architeture-view:component:examples:DEPLOYS

- repository:architeture-view → component:examples
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 2 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

## DEPENDS_ON Audit

- total: 12
- ONLY_RELATION: 6
- AGGREGATED_STRUCTURAL_SUPPORT: 6
- SHADOWED_BY_STRONGER_RELATION: 0
- SAME_CONTEXT: 5
- CROSS_CONTEXT: 0
- weak-only reachable projected nodes: 0
- projected without strong context: 0
- local-only significance: 0
- weak evidence saturation: 5
- structural ownership rejected: 5
- globally contextualized by ownership: 0

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
- cross-context support: 0
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
- cross-context support: 0
- unclassified support: 0

## Diagnostics

- **diagnostic_signal** `structural_ownership_rejected`: Structural application containment was not used as architectural ownership.
- **diagnostic_signal** `weak_evidence_saturation`: Repeated weak evidence was capped by semantic reason class.

## Evidence Groups

- `evidence-group-1c4368e9190b1e1f9ee1`: 24 refs; summary={'DOCKERFILE': 1, 'DOCKER_COMPOSE': 20, 'GRAPH_AGGREGATION': 3}; sources=architecture-graph, benchmarks/fixtures/hex_infrastructure/docker-compose.yml, benchmarks/fixtures/hypothesis_engine/docker-compose.yml, benchmarks/fixtures/infrastructure_semantics/Dockerfile, benchmarks/fixtures/infrastructure_semantics/docker-compose.yml, benchmarks/fixtures/microservices_ambiguous/docker-compose.yml, benchmarks/fixtures/microservices_containers/docker-compose.yml, benchmarks/fixtures/microservices_containers_only/docker-compose.yml, benchmarks/fixtures/significance_calibration/docker-compose.yml, benchmarks/fixtures/visualization_read_model/docker-compose.yml, examples/compose_stack/docker-compose.yml
- `evidence-group-22f15e620b5bc85e47e5`: 2770 refs; summary={'AST': 340, 'CALL_GRAPH': 1525, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 34, 'GRAPH_AGGREGATION': 5, 'IMPORT': 660, 'SYMBOL_RESOLUTION': 205}; sources=architecture-graph, benchmarks/projection_audit.py, benchmarks/refinement_investigation.py, benchmarks/runner.py, benchmarks/scale_profile.py, component-detection, src/architecture_recovery/__main__.py, src/architecture_recovery/architecture/__init__.py, src/architecture_recovery/architecture/hypotheses.py, src/architecture_recovery/architecture/inference.py, src/architecture_recovery/classification/python.py, src/architecture_recovery/cli.py, src/architecture_recovery/components/__init__.py, src/architecture_recovery/components/detection.py, src/architecture_recovery/frameworks/__init__.py, src/architecture_recovery/frameworks/base.py, src/architecture_recovery/frameworks/fastapi.py, src/architecture_recovery/graph/__init__.py, src/architecture_recovery/graph/aggregation.py, src/architecture_recovery/graph/analysis.py; source refs truncated
- `evidence-group-45bb96dd8df7a10f88c8`: 3337 refs; summary={'AST': 669, 'CALL_GRAPH': 1745, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 34, 'GRAPH_AGGREGATION': 8, 'IMPORT': 675, 'SYMBOL_RESOLUTION': 205}; sources=architecture-graph, benchmarks/projection_audit.py, benchmarks/refinement_investigation.py, benchmarks/runner.py, benchmarks/scale_profile.py, component-detection, src/architecture_recovery/__init__.py, src/architecture_recovery/__main__.py, src/architecture_recovery/architecture/__init__.py, src/architecture_recovery/architecture/hypotheses.py, src/architecture_recovery/architecture/inference.py, src/architecture_recovery/classification/__init__.py, src/architecture_recovery/classification/base.py, src/architecture_recovery/classification/python.py, src/architecture_recovery/cli.py, src/architecture_recovery/components/__init__.py, src/architecture_recovery/components/detection.py, src/architecture_recovery/frameworks/__init__.py, src/architecture_recovery/frameworks/base.py, src/architecture_recovery/frameworks/fastapi.py; source refs truncated
- `evidence-group-52c48ba914ee3a3ee4dc`: 49 refs; summary={'AST': 26, 'CALL_GRAPH': 4, 'DOCKER_COMPOSE': 2, 'FRAMEWORK_ADAPTER': 4, 'GRAPH_AGGREGATION': 7, 'IMPORT': 6}; sources=architecture-graph, examples/compose_stack/app.py, examples/compose_stack/docker-compose.yml, examples/fastapi_sample/app/api.py, examples/fastapi_sample/app/services.py, examples/fastapi_sample/generated/schema_generated.py, examples/fastapi_sample/src/app/core.py, examples/simple_python_layered/app/controllers/user.py, examples/simple_python_layered/app/repositories/user.py, examples/simple_python_layered/app/services/user.py
- `evidence-group-573ba43d2341ea67d006`: 68 refs; summary={'CALL_GRAPH': 37, 'GRAPH_AGGREGATION': 1, 'IMPORT': 18, 'SYMBOL_RESOLUTION': 12}; sources=architecture-graph, benchmarks/projection_audit.py, benchmarks/refinement_investigation.py, benchmarks/runner.py, benchmarks/scale_profile.py
- `evidence-group-68000fd1653a0a441895`: 49 refs; summary={'CALL_GRAPH': 25, 'GRAPH_AGGREGATION': 1, 'IMPORT': 23}; sources=architecture-graph, benchmarks/fixtures/evidence_payload_stress/app.py, benchmarks/fixtures/fastapi_semantics/api.py, benchmarks/fixtures/fastapi_semantics/app.py, benchmarks/fixtures/hex_ambiguous/app/controllers/http.py, benchmarks/fixtures/hex_infrastructure/app/controllers/http.py, benchmarks/fixtures/hex_positive/app/controllers/http.py, benchmarks/fixtures/microservices_ambiguous/orders.py, benchmarks/fixtures/microservices_ambiguous/users.py, benchmarks/fixtures/microservices_broker/broker.py, benchmarks/fixtures/microservices_broker/users.py, benchmarks/fixtures/microservices_containers/orders.py, benchmarks/fixtures/microservices_containers/users.py, benchmarks/fixtures/microservices_http/orders.py, benchmarks/fixtures/microservices_http/users.py, benchmarks/fixtures/microservices_modular/app.py, benchmarks/fixtures/mvc_contradiction/app.py, benchmarks/fixtures/mvc_layered_coexist/app.py, benchmarks/fixtures/mvc_positive/app.py, benchmarks/fixtures/projection_many_modules/app.py; source refs truncated
- `evidence-group-86d9a5e5e6a6e40e08d0`: 969 refs; summary={'AST': 2, 'CALL_GRAPH': 583, 'GRAPH_AGGREGATION': 1, 'IMPORT': 279, 'SYMBOL_RESOLUTION': 104}; sources=architecture-graph, tests/test_application_boundary_provenance.py, tests/test_architectural_projection.py, tests/test_basic_data_flow.py, tests/test_benchmarks.py, tests/test_canonical_relations.py, tests/test_cli_visualization.py, tests/test_component_detection.py, tests/test_context_propagation.py, tests/test_context_roots.py, tests/test_dependency_significance.py, tests/test_evidence_payload.py, tests/test_framework_adapters.py, tests/test_graph_classification.py, tests/test_hypothesis_engine.py, tests/test_infrastructure_semantics.py, tests/test_integration.py, tests/test_parser.py, tests/test_pipeline.py, tests/test_profiling.py; source refs truncated
- `evidence-group-a88a9330329ddaca1008`: 240 refs; summary={'CALL_GRAPH': 222, 'GRAPH_AGGREGATION': 1, 'IMPORT': 17}; sources=architecture-graph, src/architecture_recovery/ir/models.py, src/architecture_recovery/visualization/evidence.py, src/architecture_recovery/visualization/projection.py, src/architecture_recovery/visualization/projection_audit.py, src/architecture_recovery/visualization/read_model.py
- `evidence-group-b5bb7212a45e330d64b0`: 21 refs; summary={'DOCKERFILE': 1, 'DOCKER_COMPOSE': 19, 'GRAPH_AGGREGATION': 1}; sources=architecture-graph, benchmarks/fixtures/hex_infrastructure/docker-compose.yml, benchmarks/fixtures/hypothesis_engine/docker-compose.yml, benchmarks/fixtures/infrastructure_semantics/Dockerfile, benchmarks/fixtures/infrastructure_semantics/docker-compose.yml, benchmarks/fixtures/microservices_ambiguous/docker-compose.yml, benchmarks/fixtures/microservices_containers/docker-compose.yml, benchmarks/fixtures/microservices_containers_only/docker-compose.yml, benchmarks/fixtures/significance_calibration/docker-compose.yml, benchmarks/fixtures/visualization_read_model/docker-compose.yml, examples/compose_stack/docker-compose.yml
- `evidence-group-d33465667243e4d82656`: 1543 refs; summary={'AST': 1524, 'CALL_GRAPH': 4, 'DOCKERFILE': 1, 'DOCKER_COMPOSE': 8, 'GRAPH_AGGREGATION': 6}; sources=architecture-graph, benchmarks/__init__.py, benchmarks/fixtures/ambiguous_short_name/consumer.py, benchmarks/fixtures/ambiguous_short_name/consumer_explicit.py, benchmarks/fixtures/ambiguous_short_name/module_a.py, benchmarks/fixtures/ambiguous_short_name/module_b.py, benchmarks/fixtures/basic_data_flow/logic.py, benchmarks/fixtures/basic_data_flow/main.py, benchmarks/fixtures/basic_data_flow/storage.py, benchmarks/fixtures/component_detection/api.py, benchmarks/fixtures/component_detection/isolated.py, benchmarks/fixtures/component_detection/logic.py, benchmarks/fixtures/component_detection/repository.py, benchmarks/fixtures/component_detection/schemas.py, benchmarks/fixtures/component_detection/suggested_service.py, benchmarks/fixtures/duplicate_edge_evidence/consumer.py, benchmarks/fixtures/duplicate_edge_evidence/services.py, benchmarks/fixtures/dynamic_dispatch/consumer.py, benchmarks/fixtures/evidence_payload_stress/app.py, benchmarks/fixtures/evidence_payload_stress/helper.py; source refs truncated
- `evidence-group-e9f6461d9a77835fe146`: 3271 refs; summary={'AST': 574, 'CALL_GRAPH': 1591, 'COMPONENT_DETECTION': 5, 'DOCKERFILE': 1, 'DOCKER_COMPOSE': 21, 'FRAMEWORK_ADAPTER': 94, 'GRAPH_AGGREGATION': 28, 'IMPORT': 744, 'SYMBOL_RESOLUTION': 213}; sources=architecture-graph, benchmarks/__init__.py, benchmarks/fixtures/ambiguous_short_name/consumer.py, benchmarks/fixtures/ambiguous_short_name/consumer_explicit.py, benchmarks/fixtures/ambiguous_short_name/module_a.py, benchmarks/fixtures/ambiguous_short_name/module_b.py, benchmarks/fixtures/basic_data_flow/logic.py, benchmarks/fixtures/basic_data_flow/main.py, benchmarks/fixtures/basic_data_flow/storage.py, benchmarks/fixtures/component_detection/api.py, benchmarks/fixtures/component_detection/isolated.py, benchmarks/fixtures/component_detection/logic.py, benchmarks/fixtures/component_detection/repository.py, benchmarks/fixtures/component_detection/schemas.py, benchmarks/fixtures/component_detection/suggested_service.py, benchmarks/fixtures/duplicate_edge_evidence/consumer.py, benchmarks/fixtures/duplicate_edge_evidence/services.py, benchmarks/fixtures/dynamic_dispatch/consumer.py, benchmarks/fixtures/evidence_payload_stress/app.py, benchmarks/fixtures/evidence_payload_stress/helper.py; source refs truncated

## Profile

- total seconds: 3.114350200165063

- scanner: 0.624935 s; counts={'files': 335, 'file_count': 335, 'source_files': 243}
- stack_detection: 0.046708 s; counts={'evidence': 17}
- parser: 0.621368 s; counts={'parsed_files': 243, 'definitions': 898, 'imports': 1005, 'calls': 6204}
- basic_data_flow: 0.005941 s; counts={'assignments': 2917, 'returns': 667, 'scopes': 89, 'flow_entries': 0}
- symbol_resolution: 0.015615 s; counts={'symbols': 898, 'symbol_count': 898, 'unresolved_calls': 4668, 'flow_entries': 65}
- source_origin: 0.438940 s; counts={'local_modules': 241, 'classified_nodes': 1560, 'raw_node_count': 1560, 'classifications': 1560}
- raw_graph: 0.845379 s; counts={'nodes': 1551, 'raw_node_count': 1551, 'edges': 4008, 'raw_edge_count': 4008, 'evidence': 4829, 'evidence_count': 4829, 'unresolved_calls': 4108}
- framework_adapters: 0.043706 s; counts={'facts': 101, 'evidence': 101}
- infrastructure_semantics: 0.009012 s; counts={'resources': 22, 'relations': 11, 'evidence': 33}
- architectural_graph: 0.016075 s; counts={'nodes': 32, 'edges': 42, 'evidence': 4928}
- component_detection: 0.011889 s; counts={'components': 5, 'component_count': 5, 'unassigned_nodes': 150, 'pairs': 249}
- architecture_ir: 0.138240 s; counts={'nodes': 54, 'edges': 51, 'evidence': 5055, 'raw_nodes': 1561, 'raw_edges': 4028, 'architectural_nodes': 54, 'architectural_edges': 51, 'components': 5, 'projected_nodes': 0, 'projected_edges': 0, 'evidence_groups': 0}
- architecture_hypotheses: 0.057296 s; counts={'hypotheses': 4}
- architecture_validation: 0.137303 s; counts={'valid': True, 'warnings': 20}
- architectural_significance_projection: 0.056982 s; counts={'detailed_nodes': 76, 'projected_nodes': 16, 'projected_edges': 19}
- projection_audit: 0.044962 s; counts={'projected_nodes': 16, 'projected_edges': 19, 'evidence_coverage': 1.0}
- projection_audit_report: 0.000000 s; counts={'evidence_groups': 11, 'projected_nodes': 16, 'projected_edges': 19, 'components': 10, 'architectural_components': 5, 'component_candidates': 5}
