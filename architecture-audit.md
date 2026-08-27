# Architecture Projection Audit

## Summary

- repository: `C:/Users/pichau/AppData/Local/Temp/architecture-recovery-b638j4_4/repository`
- files: 5358
- symbols: 36041
- raw nodes / edges: 43969 / 139300
- architectural nodes / edges: 162 / 268
- projected nodes / edges: 17 / 44
- context roots: 2 (strong: 2)
- navigation roots: 1
- context root strengths: {'strong': 2}
- framework context roots: 2
- framework boundary candidates / qualified / rejected: 3 / 2 / 1
- owned framework applications / local usage: 2 / 0
- supporting-only global memberships: 0
- semantic details: 160
- external dependencies: 129
- evidence groups: 28
- traceability: yes
- determinism: yes

## Application Boundary Audit

### application:repository

- application provenance: repository_aggregate
- boundary evidence kind: repository_membership
- projected: no
- significance: low
- observed/inferred: inferred
- executable/entrypoint evidence: no
- evidence count/group: 52056 / evidence-group-c883f11d7c8d0908aa57

## Framework Boundary Audit

### component:examples

- qualification: REJECTED
- scope: unresolved
- fact ownership: UNRESOLVED
- boundary evidence: none
- context root: no
- evidence count/group: 68006 / evidence-group-fc550bc329ff7b29a4fc

### component:integrations

- qualification: QUALIFIED_GLOBAL
- scope: global
- fact ownership: OWNED_APPLICATION_BOUNDARY
- boundary evidence: deployment_execution_boundary
- context root: yes
- evidence count/group: 93858 / evidence-group-78bd97508794d88de2ad

### component:prefect

- qualification: QUALIFIED_GLOBAL
- scope: global
- fact ownership: OWNED_APPLICATION_BOUNDARY
- boundary evidence: application_router_endpoint_association
- context root: yes
- evidence count/group: 93953 / evidence-group-bfc634e63807af079f36

### component:tests

- qualification: REJECTED
- scope: local
- fact ownership: RELATED_FRAMEWORK_BOUNDARY
- boundary evidence: none
- context root: yes
- evidence count/group: 100541 / evidence-group-9cbba9785fabfc118ec5

## Projected Nodes

### component:Dockerfile

- role: container
- significance: medium
- score: 0.39
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:integrations
- context chain: component:integrations → repository:repository → component:Dockerfile
- strong reasons: none
- supporting reasons: evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPLOYS, participates in an architecture hypothesis
- evidence count: 4
- evidence group: none
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:benches

- role: component
- significance: medium
- score: 0.48
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: none
- membership strength: weak
- globally contextualized: no
- locally significant: yes
- boundary justification: none
- context root IDs: none
- context chain: missing
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON
- evidence count: 67978
- evidence group: evidence-group-1d093b287fdd26397204
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:client

- role: component
- significance: medium
- score: 0.61
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:integrations
- context chain: component:integrations → repository:repository → component:client
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, participates in an architecture hypothesis
- evidence count: 67883
- evidence group: evidence-group-566738482d9263778582
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:examples

- role: component
- significance: medium
- score: 0.48
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: none
- membership strength: weak
- globally contextualized: no
- locally significant: yes
- boundary justification: none
- context root IDs: none
- context chain: missing
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, framework fact candidate: SCHEMA
- evidence count: 68006
- evidence group: evidence-group-fc550bc329ff7b29a4fc
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: REJECTED
- framework scope: unresolved
- framework fact ownership: UNRESOLVED
- framework boundary evidence: none

### component:hatch_build.py

- role: component
- significance: medium
- score: 0.3
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: none
- membership strength: weak
- globally contextualized: no
- locally significant: yes
- boundary justification: none
- context root IDs: none
- context chain: missing
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON
- evidence count: 26
- evidence group: evidence-group-be354cb472b02dd690b3
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:integration-tests

- role: component
- significance: medium
- score: 0.84
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: none
- membership strength: weak
- globally contextualized: no
- locally significant: yes
- boundary justification: none
- context root IDs: none
- context chain: missing
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON
- evidence count: 68169
- evidence group: evidence-group-cac96c56de4d88d4ce2a
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:integrations

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
- context root IDs: component:integrations
- context chain: component:integrations
- strong reasons: framework fact associated with the principal application context
- supporting reasons: application boundary: owned framework application, architectural context root: owned framework application boundary, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, framework boundary has observed cross-component flow, framework fact candidate: APPLICATION, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 93858
- evidence group: evidence-group-78bd97508794d88de2ad
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: QUALIFIED_GLOBAL
- framework scope: global
- framework fact ownership: OWNED_APPLICATION_BOUNDARY
- framework boundary evidence: deployment_execution_boundary

### component:load_testing

- role: component
- significance: medium
- score: 0.32
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:integrations
- context chain: component:integrations → repository:repository → component:load_testing
- strong reasons: none
- supporting reasons: evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS
- evidence count: 26
- evidence group: evidence-group-f8a54ed07a312f8fa584
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:prefect

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
- context root IDs: component:prefect
- context chain: component:prefect
- strong reasons: framework fact associated with the principal application context
- supporting reasons: application boundary: owned framework application, architectural context root: owned framework application boundary, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, framework boundary has observed cross-component flow, framework fact candidate: APPLICATION, framework fact candidate: CONTROLLER_LIKE, framework fact candidate: FRAMEWORK_DEPENDENCY, framework fact candidate: HTTP_ENDPOINT, framework fact candidate: ROUTER, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 93953
- evidence group: evidence-group-bfc634e63807af079f36
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: QUALIFIED_GLOBAL
- framework scope: global
- framework fact ownership: OWNED_APPLICATION_BOUNDARY
- framework boundary evidence: application_router_endpoint_association

### component:scripts

- role: component
- significance: medium
- score: 0.83
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPENDS_ON,DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:integrations
- context chain: component:integrations → component:tests → component:scripts; component:integrations → repository:repository → component:scripts
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, participates in an architecture hypothesis
- evidence count: 68114
- evidence group: evidence-group-009382091c6f9b8b9f57
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### component:tests

- role: component
- significance: high
- score: 1.0
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPENDS_ON,DEPLOYS,FRAMEWORK_CONTEXT
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:integrations, component:prefect
- context chain: component:integrations → component:scripts → component:tests; component:integrations → repository:repository → component:tests; component:prefect → component:tests
- strong reasons: framework fact associated with the principal application context
- supporting reasons: component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON, evidence-backed architectural relation: DEPLOYS, framework boundary has observed cross-component flow, framework fact candidate: CONTROLLER_LIKE, framework fact candidate: FRAMEWORK_DEPENDENCY, framework fact candidate: HTTP_ENDPOINT, framework fact candidate: SCHEMA, participates in an architecture hypothesis
- evidence count: 100541
- evidence group: evidence-group-9cbba9785fabfc118ec5
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: REJECTED
- framework scope: local
- framework fact ownership: RELATED_FRAMEWORK_BOUNDARY
- framework boundary evidence: none

### component:ui-v2

- role: component
- significance: medium
- score: 0.26
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: none
- membership strength: weak
- globally contextualized: no
- locally significant: yes
- boundary justification: none
- context root IDs: none
- context chain: missing
- strong reasons: none
- supporting reasons: bounded support from a significant component relation, component detection evidence (structural, not sufficient alone), evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPENDS_ON
- evidence count: 68454
- evidence group: evidence-group-cb87eea1e2a1a89523da
- application provenance: none
- boundary evidence kind: none
- observed/inferred: inferred
- executable/entrypoint evidence: no
- ownership: structural_rejected via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### external.fastapi

- role: APPLICATION_FRAMEWORK
- significance: high
- score: 0.55
- projection eligible: yes
- context root: no
- root strength/kind: none / none
- membership source: none
- membership strength: weak
- globally contextualized: no
- locally significant: yes
- boundary justification: none
- context root IDs: none
- context chain: missing
- strong reasons: principal framework used by an application or router
- supporting reasons: dependency role candidate: GENERAL_LIBRARY
- evidence count: 34
- evidence group: evidence-group-e873e44e5068113396fd
- application provenance: none
- boundary evidence kind: none
- observed/inferred: observed
- executable/entrypoint evidence: no
- ownership: none via none
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:collector

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
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:jaeger

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
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:prometheus

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
- framework qualification: none
- framework scope: none
- framework fact ownership: none
- framework boundary evidence: none

### repository:repository

- role: repository
- significance: medium
- score: 1.0
- projection eligible: yes
- context root: yes
- root strength/kind: strong / FRAMEWORK_APPLICATION_BOUNDARY
- membership source: propagated:DEPLOYS
- membership strength: strong
- globally contextualized: yes
- locally significant: no
- boundary justification: none
- context root IDs: component:integrations, component:prefect
- context chain: component:integrations → component:tests → repository:repository; component:integrations → component:load_testing → repository:repository; component:integrations → repository:repository
- strong reasons: none
- supporting reasons: evidence-backed architectural relation: CONTAINS, evidence-backed architectural relation: DEPLOYS, repository context retained for navigation
- evidence count: 22
- evidence group: evidence-group-4cf4fca1e7386b87c71d
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

### projection-edge:component:Dockerfile:component:benches:CONTAINS

- component:Dockerfile → component:benches
- canonical kind: CONTAINS
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:client:CONTAINS

- component:Dockerfile → component:client
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:examples:CONTAINS

- component:Dockerfile → component:examples
- canonical kind: CONTAINS
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:hatch_build.py:CONTAINS

- component:Dockerfile → component:hatch_build.py
- canonical kind: CONTAINS
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:integration-tests:CONTAINS

- component:Dockerfile → component:integration-tests
- canonical kind: CONTAINS
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:integrations:CONTAINS

- component:Dockerfile → component:integrations
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:load_testing:CONTAINS

- component:Dockerfile → component:load_testing
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:prefect:CONTAINS

- component:Dockerfile → component:prefect
- canonical kind: CONTAINS
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context; relation crosses independent context roots
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:scripts:CONTAINS

- component:Dockerfile → component:scripts
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:tests:CONTAINS

- component:Dockerfile → component:tests
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:Dockerfile:component:ui-v2:CONTAINS

- component:Dockerfile → component:ui-v2
- canonical kind: CONTAINS
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:benches:component:prefect:DEPENDS_ON

- component:benches → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 51 / evidence-group-a2ecc346929cd1832911
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:client:component:prefect:DEPENDS_ON

- component:client → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation crosses independent context roots
- support count: 1
- evidence count / group: 20 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:examples:component:integrations:DEPENDS_ON

- component:examples → component:integrations
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 9 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:examples:component:prefect:DEPENDS_ON

- component:examples → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 47 / evidence-group-f917c5fe8bfd23a18b71
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:integration-tests:component:prefect:DEPENDS_ON

- component:integration-tests → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 225 / evidence-group-2bfe503c9eb615331f2f
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:integration-tests:external.fastapi:DEPENDS_ON

- component:integration-tests → external.fastapi
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 5 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:integrations:component:integration-tests:DEPENDS_ON

- component:integrations → component:integration-tests
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 29 / evidence-group-b8346b1ab543bcc185e2
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:integrations:component:prefect:DEPENDS_ON

- component:integrations → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation crosses independent context roots
- support count: 1
- evidence count / group: 2443 / evidence-group-5f3361573cce88ca2bc7
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:integrations:component:tests:DEPENDS_ON

- component:integrations → component:tests
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 13 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:component:prefect:component:integration-tests:DEPENDS_ON

- component:prefect → component:integration-tests
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 22 / evidence-group-10be4faecad105b7b65f
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:prefect:component:integrations:DEPENDS_ON

- component:prefect → component:integrations
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation crosses independent context roots
- support count: 1
- evidence count / group: 151 / evidence-group-8617c1fcb47b001d4c19
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:prefect:external.fastapi:DEPENDS_ON

- component:prefect → external.fastapi
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 844 / evidence-group-ea373e011811d5a43976
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:scripts:component:integration-tests:DEPENDS_ON

- component:scripts → component:integration-tests
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 2 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:scripts:component:prefect:DEPENDS_ON

- component:scripts → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: CROSS_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation crosses independent context roots
- support count: 1
- evidence count / group: 26 / evidence-group-46436839d7bd4d90aa35
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:scripts:external.fastapi:DEPENDS_ON

- component:scripts → external.fastapi
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 4 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:benches:DEPENDS_ON

- component:tests → component:benches
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 30 / evidence-group-558020277547fe8085c8
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:hatch_build.py:DEPENDS_ON

- component:tests → component:hatch_build.py
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 10 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:integration-tests:DEPENDS_ON

- component:tests → component:integration-tests
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 56 / evidence-group-28009d7497b03e74f7fa
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:integrations:DEPENDS_ON

- component:tests → component:integrations
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 198 / evidence-group-484b80ceb1fe0df202b1
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:prefect:DEPENDS_ON

- component:tests → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 33450 / evidence-group-65e1fa38aa837155be96
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:component:scripts:DEPENDS_ON

- component:tests → component:scripts
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 2 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:tests:external.fastapi:DEPENDS_ON

- component:tests → external.fastapi
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 87 / evidence-group-671fec98518da576d5dc
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:component:ui-v2:component:prefect:DEPENDS_ON

- component:ui-v2 → component:prefect
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: AGGREGATED_STRUCTURAL_SUPPORT
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 15 / none
- stronger relation kinds: none
- context propagation: supports_context

### projection-edge:infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:collector:infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:jaeger:DEPENDS_ON

- infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:collector → infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:jaeger
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:collector:infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:prometheus:DEPENDS_ON

- infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:collector → infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:prometheus
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:jaeger:infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:prometheus:DEPENDS_ON

- infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:jaeger → infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:prometheus
- canonical kind: DEPENDS_ON
- relation strength: weak
- context scope: UNCONTEXTUALIZED
- DEPENDS_ON category: ONLY_RELATION
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: none
- context propagation: does_not_propagate_context

### projection-edge:repository:repository:component:Dockerfile:CONTAINS

- repository:repository → component:Dockerfile
- canonical kind: CONTAINS
- relation strength: weak
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence; relation is valid but does not propagate context; stronger relation exists for the same directed pair
- support count: 1
- evidence count / group: 1 / none
- stronger relation kinds: DEPLOYS
- context propagation: does_not_propagate_context

### projection-edge:repository:repository:component:Dockerfile:DEPLOYS

- repository:repository → component:Dockerfile
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 2 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:repository:repository:component:client:DEPLOYS

- repository:repository → component:client
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 2 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:repository:repository:component:integrations:DEPLOYS

- repository:repository → component:integrations
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 4 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:repository:repository:component:load_testing:DEPLOYS

- repository:repository → component:load_testing
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 4 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:repository:repository:component:scripts:DEPLOYS

- repository:repository → component:scripts
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 4 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

### projection-edge:repository:repository:component:tests:DEPLOYS

- repository:repository → component:tests
- canonical kind: DEPLOYS
- relation strength: medium
- context scope: SAME_CONTEXT
- DEPENDS_ON category: n/a
- projection reason: both endpoints are projection-eligible and the canonical relation has evidence
- support count: 1
- evidence count / group: 5 / none
- stronger relation kinds: none
- context propagation: can_propagate_context

## DEPENDS_ON Audit

- total: 26
- ONLY_RELATION: 5
- AGGREGATED_STRUCTURAL_SUPPORT: 21
- SHADOWED_BY_STRONGER_RELATION: 0
- SAME_CONTEXT: 4
- CROSS_CONTEXT: 4
- weak-only reachable projected nodes: 5
- projected without strong context: 6
- local-only significance: 6
- weak evidence saturation: 8
- structural ownership rejected: 16
- globally contextualized by ownership: 0
- framework context roots: 2
- framework candidates / qualified / rejected: 3 / 2 / 1
- owned framework applications / local usage: 2 / 0
- supporting-only global memberships: 0

## Hypothesis Context Audit

### hexagonal

- supporting evidence: 17783
- contradicting evidence: 17380
- context-root support: 17783
- local-only support: 0
- cross-context support: 0
- unclassified support: 0

### layered

- supporting evidence: 2994
- contradicting evidence: 2456
- context-root support: 2994
- local-only support: 0
- cross-context support: 2594
- unclassified support: 0

### microservices

- supporting evidence: 14
- contradicting evidence: 14
- context-root support: 12
- local-only support: 0
- cross-context support: 0
- unclassified support: 2

### mvc

- supporting evidence: 72
- contradicting evidence: 0
- context-root support: 72
- local-only support: 0
- cross-context support: 0
- unclassified support: 0

## Diagnostics

- **candidate_issue** `projected_without_context`: Projected nodes without a context root or explicit boundary require review.
- **diagnostic_signal** `structural_ownership_rejected`: Structural application containment was not used as architectural ownership.
- **candidate_issue** `local_only_framework_promotion`: Framework evidence is locally significant but lacks global context.
- **diagnostic_signal** `rejected_framework_boundary`: Framework boundary candidates lack coherent application ownership or boundary evidence.
- **diagnostic_signal** `weak_only_context_reachability`: Projected nodes are reachable from roots through weak-only relations but are not context members.
- **diagnostic_signal** `weak_evidence_saturation`: Repeated weak evidence was capped by semantic reason class.

## Evidence Groups

- `evidence-group-009382091c6f9b8b9f57`: 68114 refs; summary={'AST': 1666, 'CALL_GRAPH': 44591, 'COMPONENT_DETECTION': 2, 'DOCKERFILE': 1, 'DOCKER_COMPOSE': 2, 'FRAMEWORK_ADAPTER': 475, 'GRAPH_AGGREGATION': 18, 'IMPORT': 12539, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py, integration-tests/test_flow_suspension.py; source refs truncated
- `evidence-group-10be4faecad105b7b65f`: 22 refs; summary={'CALL_GRAPH': 21, 'GRAPH_AGGREGATION': 1}; sources=architecture-graph, src/prefect/cli/_cloud_utils.py, src/prefect/client/base.py, src/prefect/client/cloud.py, src/prefect/client/orchestration/__init__.py, src/prefect/events/clients.py, src/prefect/events/worker.py, src/prefect/logging/clients.py, src/prefect/logging/handlers.py, src/prefect/runner/runner.py, src/prefect/runtime/flow_run.py, src/prefect/utilities/urls.py, src/prefect/workers/base.py
- `evidence-group-1d093b287fdd26397204`: 67978 refs; summary={'AST': 1578, 'CALL_GRAPH': 44573, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 475, 'GRAPH_AGGREGATION': 9, 'IMPORT': 12522, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/__main__.py, benches/bench_block_schemas.py, benches/bench_cli.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_import.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py; source refs truncated
- `evidence-group-28009d7497b03e74f7fa`: 56 refs; summary={'CALL_GRAPH': 55, 'GRAPH_AGGREGATION': 1}; sources=architecture-graph, tests/blocks/test_system.py, tests/cli/test_deploy.py, tests/cli/test_worker.py, tests/client/test_cloud_client.py, tests/conftest.py, tests/deployment/test_flow_runs.py, tests/events/client/instrumentation/test_block_events_instrumentation.py, tests/events/client/test_events_client.py, tests/fixtures/collections_registry.py, tests/runner/test_runner.py, tests/runtime/test_flow_run.py, tests/runtime/test_task_run.py, tests/server/orchestration/api/test_block_types.py, tests/test-projects/flows/uses_block.py, tests/test_flows.py, tests/test_settings.py, tests/testing/test_utilites.py, tests/workers/test_base_worker.py
- `evidence-group-2bfe503c9eb615331f2f`: 225 refs; summary={'CALL_GRAPH': 99, 'GRAPH_AGGREGATION': 1, 'IMPORT': 110, 'SYMBOL_RESOLUTION': 15}; sources=architecture-graph, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_concurrent_subflows.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py, integration-tests/test_flow_retries.py, integration-tests/test_flow_retries_with_subflows.py, integration-tests/test_flow_suspension.py, integration-tests/test_hello_tasks.py, integration-tests/test_hello_world.py, integration-tests/test_load_flows_concurrently.py, integration-tests/test_multiprocessing_flow.py, integration-tests/test_nested_cancellation.py, integration-tests/test_runner_resilience.py, integration-tests/test_schedule_statefulness.py, integration-tests/test_secret_block.py; source refs truncated
- `evidence-group-46436839d7bd4d90aa35`: 26 refs; summary={'CALL_GRAPH': 6, 'GRAPH_AGGREGATION': 1, 'IMPORT': 19}; sources=architecture-graph, scripts/generate_cli_docs.py, scripts/generate_mintlify_openapi_docs.py, scripts/generate_oss_openapi_schema.py, scripts/generate_prefect_yaml_schema.py, scripts/generate_settings_ref.py, scripts/generate_settings_schema.py, scripts/generate_settings_types.py, scripts/proxy-test/client.py, scripts/run-integration-flows.py, scripts/test_unc_paths.py, scripts/wait-for-server.py
- `evidence-group-484b80ceb1fe0df202b1`: 198 refs; summary={'CALL_GRAPH': 189, 'GRAPH_AGGREGATION': 1, 'IMPORT': 8}; sources=architecture-graph, tests/_experimental/bundles/test_include_files_integration.py, tests/_internal/concurrency/test_services.py, tests/cli/test_deploy.py, tests/client/schemas/test_schedules.py, tests/deployment/test_flow_runs.py, tests/docker/test_registry_pushes.py, tests/events/client/test_events_related_from_context.py, tests/events/client/test_resource_schema.py, tests/events/jinja_filters/test_ui_url.py, tests/events/server/conftest.py, tests/events/server/test_clients.py, tests/events/server/test_in_memory_ordering.py, tests/public/flows/test_flow_with_mapped_tasks.py, tests/results/test_flow_results.py, tests/results/test_result_store.py, tests/runner/test_runner.py, tests/server/orchestration/api/test_block_types.py, tests/server/utilities/test_messaging.py, tests/test_context.py; source refs truncated
- `evidence-group-4cf4fca1e7386b87c71d`: 22 refs; summary={'DOCKERFILE': 10, 'DOCKER_COMPOSE': 5, 'GRAPH_AGGREGATION': 7}; sources=Dockerfile, architecture-graph, client/Dockerfile, load_testing/local-telemetry/docker-compose.yml, scripts/proxy-test/Dockerfile, scripts/proxy-test/docker-compose.yml, src/integrations/prefect-aws/Dockerfile, src/integrations/prefect-azure/Dockerfile, src/integrations/prefect-gcp/Dockerfile, tests/docker/contexts/bad-base/Dockerfile, tests/docker/contexts/broken/Dockerfile, tests/docker/contexts/missing-file/Dockerfile, tests/docker/contexts/tiny/Dockerfile
- `evidence-group-558020277547fe8085c8`: 30 refs; summary={'CALL_GRAPH': 29, 'GRAPH_AGGREGATION': 1}; sources=architecture-graph, tests/cli/test_work_pool.py, tests/cli/test_work_queues.py, tests/client/test_prefect_client.py, tests/runtime/test_deployment.py, tests/runtime/test_flow_run.py, tests/test-projects/wrapped_flow_project/utils.py, tests/test_flow_engine.py, tests/test_flows.py
- `evidence-group-566738482d9263778582`: 67883 refs; summary={'AST': 1512, 'CALL_GRAPH': 44554, 'COMPONENT_DETECTION': 1, 'DOCKERFILE': 1, 'FRAMEWORK_ADAPTER': 475, 'GRAPH_AGGREGATION': 4, 'IMPORT': 12516, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/Dockerfile, client/client_deploy.py, client/client_flow.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py; source refs truncated
- `evidence-group-5f3361573cce88ca2bc7`: 2443 refs; summary={'CALL_GRAPH': 930, 'GRAPH_AGGREGATION': 1, 'IMPORT': 1381, 'SYMBOL_RESOLUTION': 131}; sources=architecture-graph, src/integrations/prefect-aws/prefect_aws/_cli/utils.py, src/integrations/prefect-aws/prefect_aws/batch.py, src/integrations/prefect-aws/prefect_aws/bundles/execute.py, src/integrations/prefect-aws/prefect_aws/client_waiter.py, src/integrations/prefect-aws/prefect_aws/credentials.py, src/integrations/prefect-aws/prefect_aws/decorators.py, src/integrations/prefect-aws/prefect_aws/deployments/steps.py, src/integrations/prefect-aws/prefect_aws/glue_job.py, src/integrations/prefect-aws/prefect_aws/lambda_function.py, src/integrations/prefect-aws/prefect_aws/observers/ecs.py, src/integrations/prefect-aws/prefect_aws/plugins.py, src/integrations/prefect-aws/prefect_aws/s3.py, src/integrations/prefect-aws/prefect_aws/secrets_manager.py, src/integrations/prefect-aws/prefect_aws/settings.py, src/integrations/prefect-aws/prefect_aws/utilities.py, src/integrations/prefect-aws/prefect_aws/workers/ecs_worker.py, src/integrations/prefect-aws/tests/cli/test_ecs_worker.py, src/integrations/prefect-aws/tests/conftest.py, src/integrations/prefect-aws/tests/experimental/test_decorators.py; source refs truncated
- `evidence-group-65e1fa38aa837155be96`: 33450 refs; summary={'AST': 397, 'CALL_GRAPH': 23099, 'GRAPH_AGGREGATION': 1, 'IMPORT': 4624, 'SYMBOL_RESOLUTION': 5329}; sources=architecture-graph, tests/_experimental/bundles/test_bundles.py, tests/_experimental/bundles/test_dependency_validation.py, tests/_experimental/bundles/test_execute.py, tests/_experimental/bundles/test_file_collector.py, tests/_experimental/bundles/test_ignore_filter.py, tests/_experimental/bundles/test_include_files_integration.py, tests/_experimental/bundles/test_path_resolver.py, tests/_experimental/bundles/test_zip_builder.py, tests/_experimental/bundles/test_zip_extractor.py, tests/_internal/analytics/conftest.py, tests/_internal/analytics/test_ci_detection.py, tests/_internal/analytics/test_client.py, tests/_internal/analytics/test_device_id.py, tests/_internal/analytics/test_events.py, tests/_internal/analytics/test_milestones.py, tests/_internal/analytics/test_notice.py, tests/_internal/analytics/test_service.py, tests/_internal/compatibility/test_async_dispatch.py, tests/_internal/compatibility/test_backports.py; source refs truncated
- `evidence-group-671fec98518da576d5dc`: 87 refs; summary={'CALL_GRAPH': 49, 'GRAPH_AGGREGATION': 1, 'IMPORT': 37}; sources=architecture-graph, tests/client/test_prefect_client.py, tests/events/server/gateway/conftest.py, tests/events/server/gateway/test_gateway_in.py, tests/events/server/test_automations_api.py, tests/fixtures/api.py, tests/fixtures/client.py, tests/fixtures/storage.py, tests/server/api/test_dependencies.py, tests/server/api/test_docket_task_keys.py, tests/server/api/test_middleware.py, tests/server/api/test_pagination.py, tests/server/api/test_server.py, tests/server/orchestration/api/test_concurrency_limits_v2.py, tests/server/orchestration/api/test_deployment_schedules.py, tests/server/orchestration/api/test_flow_runs.py, tests/server/orchestration/api/test_run_history.py, tests/server/orchestration/api/test_task_run_subscriptions.py, tests/server/orchestration/api/test_validation.py, tests/server/orchestration/api/ui/test_task_runs.py; source refs truncated
- `evidence-group-78bd97508794d88de2ad`: 93858 refs; summary={'AST': 12963, 'CALL_GRAPH': 57692, 'COMPONENT_DETECTION': 3, 'DOCKERFILE': 3, 'FRAMEWORK_ADAPTER': 481, 'GRAPH_AGGREGATION': 85, 'IMPORT': 13771, 'SYMBOL_RESOLUTION': 8860}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py, integration-tests/test_flow_suspension.py; source refs truncated
- `evidence-group-8617c1fcb47b001d4c19`: 151 refs; summary={'AST': 1, 'CALL_GRAPH': 147, 'GRAPH_AGGREGATION': 1, 'IMPORT': 2}; sources=architecture-graph, src/prefect/_flow_run_suspension.py, src/prefect/_internal/concurrency/services.py, src/prefect/_internal/waiters.py, src/prefect/assets/core.py, src/prefect/blocks/core.py, src/prefect/bundles/__init__.py, src/prefect/cli/_prompts.py, src/prefect/cli/deploy/_actions.py, src/prefect/cli/transfer/_commands.py, src/prefect/client/attribution.py, src/prefect/client/utilities.py, src/prefect/concurrency/_events.py, src/prefect/concurrency/v1/_events.py, src/prefect/deployments/flow_runs.py, src/prefect/docker/docker_image.py, src/prefect/events/clients.py, src/prefect/events/related.py, src/prefect/flow_engine.py, src/prefect/flow_runs.py; source refs truncated
- `evidence-group-9cbba9785fabfc118ec5`: 100541 refs; summary={'AST': 27336, 'CALL_GRAPH': 49451, 'COMPONENT_DETECTION': 11, 'DOCKERFILE': 4, 'FRAMEWORK_ADAPTER': 486, 'GRAPH_AGGREGATION': 58, 'IMPORT': 13863, 'SYMBOL_RESOLUTION': 9332}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, hatch_build.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py; source refs truncated
- `evidence-group-a2ecc346929cd1832911`: 51 refs; summary={'CALL_GRAPH': 35, 'GRAPH_AGGREGATION': 1, 'IMPORT': 11, 'SYMBOL_RESOLUTION': 4}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_import.py, benches/bench_tasks.py
- `evidence-group-b8346b1ab543bcc185e2`: 29 refs; summary={'CALL_GRAPH': 28, 'GRAPH_AGGREGATION': 1}; sources=architecture-graph, src/integrations/prefect-aws/prefect_aws/observers/ecs.py, src/integrations/prefect-aws/tests/cli/test_ecs_worker.py, src/integrations/prefect-aws/tests/experimental/test_decorators.py, src/integrations/prefect-azure/tests/experimental/tests_decorators.py, src/integrations/prefect-docker/prefect_docker/worker.py, src/integrations/prefect-docker/tests/experimental/test_decorators.py, src/integrations/prefect-gcp/tests/experimental/test_decorators.py, src/integrations/prefect-kubernetes/integration_tests/src/prefect_kubernetes_integration_tests/utils/prefect_core.py, src/integrations/prefect-kubernetes/tests/experimental/test_decorator.py, src/integrations/prefect-kubernetes/tests/test_worker.py, src/integrations/prefect-snowflake/prefect_snowflake/experimental/workers/spcs.py
- `evidence-group-be354cb472b02dd690b3`: 26 refs; summary={'AST': 8, 'CALL_GRAPH': 8, 'COMPONENT_DETECTION': 1, 'GRAPH_AGGREGATION': 4, 'IMPORT': 5}; sources=architecture-graph, component-detection, hatch_build.py, tests/test_ui_build_validation.py
- `evidence-group-bfc634e63807af079f36`: 93953 refs; summary={'AST': 12658, 'CALL_GRAPH': 56359, 'COMPONENT_DETECTION': 6, 'FRAMEWORK_ADAPTER': 486, 'GRAPH_AGGREGATION': 81, 'IMPORT': 15029, 'SYMBOL_RESOLUTION': 9334}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_import.py, benches/bench_tasks.py, client/client_deploy.py, client/client_flow.py, component-detection, docs/conftest.py, docs/myproject/flows.py, docs/myproject/tasks.py, examples/ai_data_analyst_with_pydantic_ai.py, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/resume_flow_run_on_pr_merge.py, examples/run_api_sourced_etl.py, examples/run_dbt_with_prefect.py; source refs truncated
- `evidence-group-c883f11d7c8d0908aa57`: 52056 refs; summary={'AST': 51180, 'CALL_GRAPH': 844, 'DOCKERFILE': 10, 'DOCKER_COMPOSE': 5, 'GRAPH_AGGREGATION': 17}; sources=Dockerfile, architecture-graph, benches/__main__.py, benches/bench_block_schemas.py, benches/bench_cli.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_import.py, benches/bench_tasks.py, client/Dockerfile, client/client_deploy.py, client/client_flow.py, docs/conftest.py, docs/myproject/cool.py, docs/myproject/db.py, docs/myproject/flows.py, docs/myproject/tasks.py, docs/myproject/utils.py, docs/script.js, examples/ai_data_analyst_with_pydantic_ai.py; source refs truncated
- `evidence-group-cac96c56de4d88d4ce2a`: 68169 refs; summary={'AST': 1723, 'CALL_GRAPH': 44602, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 475, 'GRAPH_AGGREGATION': 12, 'IMPORT': 12536, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_concurrent_subflows.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py; source refs truncated
- `evidence-group-cb87eea1e2a1a89523da`: 68454 refs; summary={'AST': 2091, 'CALL_GRAPH': 44554, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 475, 'GRAPH_AGGREGATION': 3, 'IMPORT': 12510, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py, integration-tests/test_flow_suspension.py; source refs truncated
- `evidence-group-e873e44e5068113396fd`: 34 refs; summary={'GRAPH_AGGREGATION': 1, 'IMPORT': 33}; sources=architecture-graph, integration-tests/test_client_context_lifespan.py, scripts/proxy-test/server.py, src/prefect/cli/_cloud_utils.py, src/prefect/flows.py, src/prefect/runner/server.py, src/prefect/server/api/admin.py, src/prefect/server/api/artifacts.py, src/prefect/server/api/automations.py, src/prefect/server/api/block_documents.py, src/prefect/server/api/dependencies.py, src/prefect/server/api/events.py, src/prefect/server/api/flow_runs.py, src/prefect/server/api/flows.py, src/prefect/server/api/server.py, src/prefect/server/utilities/server.py, tests/client/test_prefect_client.py, tests/events/server/gateway/conftest.py, tests/events/server/test_automations_api.py
- `evidence-group-ea373e011811d5a43976`: 844 refs; summary={'CALL_GRAPH': 674, 'GRAPH_AGGREGATION': 1, 'IMPORT': 169}; sources=architecture-graph, src/prefect/cli/_cloud_utils.py, src/prefect/flows.py, src/prefect/runner/server.py, src/prefect/server/api/admin.py, src/prefect/server/api/artifacts.py, src/prefect/server/api/automations.py, src/prefect/server/api/block_capabilities.py, src/prefect/server/api/block_documents.py, src/prefect/server/api/block_schemas.py, src/prefect/server/api/block_types.py, src/prefect/server/api/collections.py, src/prefect/server/api/concurrency_limits.py, src/prefect/server/api/concurrency_limits_v2.py, src/prefect/server/api/csrf_token.py, src/prefect/server/api/dependencies.py, src/prefect/server/api/deployments.py, src/prefect/server/api/events.py, src/prefect/server/api/flow_run_states.py, src/prefect/server/api/flow_runs.py; source refs truncated
- `evidence-group-f8a54ed07a312f8fa584`: 26 refs; summary={'AST': 4, 'CALL_GRAPH': 8, 'DOCKER_COMPOSE': 3, 'GRAPH_AGGREGATION': 5, 'IMPORT': 6}; sources=architecture-graph, load_testing/local-telemetry/docker-compose.yml, load_testing/track_cnx.py
- `evidence-group-f917c5fe8bfd23a18b71`: 47 refs; summary={'CALL_GRAPH': 16, 'GRAPH_AGGREGATION': 1, 'IMPORT': 27, 'SYMBOL_RESOLUTION': 3}; sources=architecture-graph, examples/ai_data_analyst_with_pydantic_ai.py, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/resume_flow_run_on_pr_merge.py, examples/run_api_sourced_etl.py, examples/run_dbt_with_prefect.py, examples/simple_web_scraper.py
- `evidence-group-fc550bc329ff7b29a4fc`: 68006 refs; summary={'AST': 1582, 'CALL_GRAPH': 44581, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 476, 'GRAPH_AGGREGATION': 11, 'IMPORT': 12535, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_data_analyst_with_pydantic_ai.py, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/resume_flow_run_on_pr_merge.py, examples/run_api_sourced_etl.py, examples/run_dbt_with_prefect.py, examples/simple_web_scraper.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py; source refs truncated

## Profile

- total seconds: 152.07837870006915

- repository_acquisition: 10.405906 s; counts={}
- scanner: 2.154749 s; counts={'files': 5358, 'file_count': 5358, 'source_files': 2513}
- stack_detection: 11.315415 s; counts={'evidence': 129}
- parser: 15.931564 s; counts={'parsed_files': 1901, 'definitions': 36405, 'imports': 25844, 'calls': 158176}
- basic_data_flow: 0.211965 s; counts={'assignments': 75029, 'returns': 12277, 'scopes': 4200, 'flow_entries': 0}
- symbol_resolution: 0.667216 s; counts={'symbols': 36041, 'symbol_count': 36041, 'unresolved_calls': 113890, 'flow_entries': 3971}
- source_origin: 2.590369 s; counts={'local_modules': 1803, 'classified_nodes': 43969, 'raw_node_count': 43969, 'classifications': 43969}
- raw_graph: 44.701563 s; counts={'nodes': 43954, 'raw_node_count': 43954, 'edges': 139282, 'raw_edge_count': 139282, 'evidence': 178829, 'evidence_count': 178829, 'unresolved_calls': 66399}
- framework_adapters: 19.299794 s; counts={'facts': 506, 'evidence': 519}
- infrastructure_semantics: 0.101402 s; counts={'resources': 15, 'relations': 3, 'evidence': 18}
- architectural_graph: 1.256964 s; counts={'nodes': 147, 'edges': 268, 'evidence': 179260}
- component_detection: 2.003463 s; counts={'components': 15, 'component_count': 15, 'unassigned_nodes': 392, 'pairs': 8159}
- architecture_ir: 10.274471 s; counts={'nodes': 162, 'edges': 268, 'evidence': 179923, 'raw_nodes': 43969, 'raw_edges': 139300, 'architectural_nodes': 162, 'architectural_edges': 268, 'components': 15, 'projected_nodes': 0, 'projected_edges': 0, 'evidence_groups': 0}
- architecture_hypotheses: 13.756872 s; counts={'hypotheses': 4}
- architecture_validation: 7.317635 s; counts={'valid': True, 'warnings': 15}
- architectural_significance_projection: 6.229560 s; counts={'detailed_nodes': 177, 'projected_nodes': 17, 'projected_edges': 44}
- projection_audit: 3.859471 s; counts={'projected_nodes': 17, 'projected_edges': 44, 'evidence_coverage': 1.0}
- projection_audit_report: 0.000000 s; counts={'evidence_groups': 28, 'projected_nodes': 17, 'projected_edges': 44, 'components': 30, 'architectural_components': 15, 'component_candidates': 15}
