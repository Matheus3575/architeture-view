# Architecture Projection Audit

## Summary

- repository: `C:/Users/pichau/AppData/Local/Temp/architecture-recovery-1bwpzqq_/repository`
- files: 5358
- symbols: 36041
- raw nodes / edges: 43969 / 139300
- architectural nodes / edges: 162 / 268
- projected nodes / edges: 1 / 0
- context roots: 1 (strong: 1)
- navigation roots: 1
- context root strengths: {'strong': 1}
- framework context roots: 1
- framework boundary candidates / qualified / rejected: 3 / 1 / 2
- owned framework applications / local usage: 1 / 1
- supporting-only global memberships: 0
- globally eligible projected: 1
- local-only significant / projected: 15 / 0
- projected without global justification: 0
- navigation-only projected: 0
- independent global boundaries projected: 0
- DEPLOYS total / can propagate / supporting / non-propagating: 6 / 0 / 0 / 6
- DEPLOYS provenance: {'navigation_derived': 6}
- deployment memberships / navigation transit: 0 / 0
- deployment boundary candidates / qualified global / rejected-local: 6 / 0 / 6
- positive evidence produced / accepted / rejected / absent: 41 / 29 / 12 / 10
- semantic memberships / explicit deployment ownership / directional propagation: 0 / 0 / 0
- positive evidence rejection reasons: {'application boundary was not admitted as a global root': 1, 'deployment provenance does not establish global context': 6, 'framework fact lacks an accepted global context association': 5}
- semantic details: 176
- external dependencies: 129
- evidence groups: 8
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

- qualification: REJECTED
- scope: local
- fact ownership: LOCAL_FRAMEWORK_USAGE
- boundary evidence: none
- context root: no
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

## Projected Relations

## DEPENDS_ON Audit

- total: 0
- ONLY_RELATION: 0
- AGGREGATED_STRUCTURAL_SUPPORT: 0
- SHADOWED_BY_STRONGER_RELATION: 0
- SAME_CONTEXT: 0
- CROSS_CONTEXT: 0
- weak-only reachable projected nodes: 0
- projected without strong context: 0
- local-only significance: 0
- weak evidence saturation: 8
- structural ownership rejected: 16
- globally contextualized by ownership: 0
- framework context roots: 1
- framework candidates / qualified / rejected: 3 / 1 / 2
- owned framework applications / local usage: 1 / 1
- supporting-only global memberships: 0
- globally eligible projected: 1
- local-only significant / projected: 15 / 0
- projected without global justification: 0
- navigation-only projected: 0
- independent global boundaries projected: 0
- DEPLOYS total / can propagate / supporting / non-propagating: 6 / 0 / 0 / 6
- DEPLOYS provenance: {'navigation_derived': 6}
- deployment memberships / navigation transit: 0 / 0
- deployment boundary candidates / qualified global / rejected-local: 6 / 0 / 6
- positive evidence produced / accepted / rejected / absent: 41 / 29 / 12 / 10
- semantic memberships / explicit deployment ownership / directional propagation: 0 / 0 / 0
- positive evidence rejection reasons: {'application boundary was not admitted as a global root': 1, 'deployment provenance does not establish global context': 6, 'framework fact lacks an accepted global context association': 5}

## Hypothesis Context Audit

### hexagonal

- supporting evidence: 17783
- contradicting evidence: 17380
- context-root support: 17782
- local-only support: 1
- cross-context support: 0
- unclassified support: 0

### layered

- supporting evidence: 2994
- contradicting evidence: 2456
- context-root support: 2994
- local-only support: 0
- cross-context support: 0
- unclassified support: 0

### microservices

- supporting evidence: 14
- contradicting evidence: 14
- context-root support: 7
- local-only support: 5
- cross-context support: 0
- unclassified support: 2

### mvc

- supporting evidence: 72
- contradicting evidence: 0
- context-root support: 26
- local-only support: 46
- cross-context support: 0
- unclassified support: 0

## Positive Evidence Ledger

### application:repository — application_boundary

- producer: GraphAggregation
- accepted: no
- provenance: repository_aggregate
- source relation / owner / direction: APPLICATION_BOUNDARY / application:repository / none
- role: APPLICATION
- rejection reason: application boundary was not admitted as a global root
- evidence count / group: 1 / none

### component:Dockerfile — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:bd15b19e05b7d6e8 / repository:repository / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 2 / none

### component:benches — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: component
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### component:client — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:c5cd40a76d3f0a53 / repository:repository / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 2 / none

### component:examples — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: component
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### component:hatch_build.py — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: component
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### component:integration-tests — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: component
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### component:integrations — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:a65d8130ab5eb0dd / repository:repository / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 4 / none

### component:integrations — framework_boundary

- producer: FrameworkAdapter
- accepted: no
- provenance: LOCAL_FRAMEWORK_USAGE
- source relation / owner / direction: APPLICATION / app / fact
- role: APPLICATION
- rejection reason: framework fact lacks an accepted global context association
- evidence count / group: 1 / none

### component:integrations — framework_boundary

- producer: FrameworkAdapter
- accepted: no
- provenance: LOCAL_FRAMEWORK_USAGE
- source relation / owner / direction: APPLICATION / app / fact
- role: APPLICATION
- rejection reason: framework fact lacks an accepted global context association
- evidence count / group: 1 / none

### component:integrations — framework_boundary

- producer: FrameworkAdapter
- accepted: no
- provenance: LOCAL_FRAMEWORK_USAGE
- source relation / owner / direction: APPLICATION / app / fact
- role: APPLICATION
- rejection reason: framework fact lacks an accepted global context association
- evidence count / group: 1 / none

### component:integrations — framework_boundary

- producer: FrameworkAdapter
- accepted: no
- provenance: LOCAL_FRAMEWORK_USAGE
- source relation / owner / direction: APPLICATION / kv_api_app / fact
- role: APPLICATION
- rejection reason: framework fact lacks an accepted global context association
- evidence count / group: 1 / none

### component:integrations — framework_boundary

- producer: FrameworkAdapter
- accepted: no
- provenance: LOCAL_FRAMEWORK_USAGE
- source relation / owner / direction: APPLICATION / app / fact
- role: APPLICATION
- rejection reason: framework fact lacks an accepted global context association
- evidence count / group: 1 / none

### component:load_testing — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:7920b9b776d4e05d / repository:repository / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 4 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / login_api / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / ui_app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / api_app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / webserver / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / status_app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: APPLICATION / app / fact
- role: APPLICATION
- rejection reason: none
- evidence count / group: 1 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:prefect / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:prefect / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / login_api / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / login_api / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: ROUTER / router / fact
- role: ROUTER
- rejection reason: none
- evidence count / group: 32 / evidence-group-10c13b5b90638a556633

### component:prefect — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: OWNED_APPLICATION_BOUNDARY
- source relation / owner / direction: ROUTER / router / fact
- role: ROUTER
- rejection reason: none
- evidence count / group: 32 / evidence-group-8ca28d9ccc930c0773e7

### component:scripts — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:fefc13938a729391 / repository:repository / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 4 / none

### component:tests — deployment_ownership

- producer: GraphAggregation
- accepted: no
- provenance: navigation_derived
- source relation / owner / direction: DEPLOYS:arch-edge:6cecba8964de0bad / repository:repository / forward
- role: DEPLOYS
- rejection reason: deployment provenance does not establish global context
- evidence count / group: 5 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 7 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 7 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 7 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 7 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 7 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: CONTROLLER_LIKE / component:tests / fact
- role: CONTROLLER_LIKE
- rejection reason: none
- evidence count / group: 3 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / kv_api_app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / kv_api_app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:tests — framework_boundary

- producer: FrameworkAdapter
- accepted: yes
- provenance: RELATED_FRAMEWORK_BOUNDARY
- source relation / owner / direction: HTTP_ENDPOINT / kv_api_app / fact
- role: HTTP_ENDPOINT
- rejection reason: none
- evidence count / group: 2 / none

### component:ui-v2 — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: component
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### external.fastapi — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: APPLICATION_FRAMEWORK
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:collector — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: container
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:jaeger — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: container
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### infrastructure:compose:load_testing/local-telemetry/docker-compose.yml:prometheus — global_context

- producer: not_observed
- accepted: no
- provenance: absent
- source relation / owner / direction: none / none / none
- role: container
- rejection reason: no positive architectural context evidence was produced
- evidence count / group: 0 / none

### repository:repository — global_context

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

- `evidence-group-10c13b5b90638a556633`: 32 refs; summary={'FRAMEWORK_ADAPTER': 1, 'SYMBOL_RESOLUTION': 31}; sources=src/prefect/server/api/admin.py, src/prefect/server/api/artifacts.py, src/prefect/server/api/automations.py, src/prefect/server/api/block_capabilities.py, src/prefect/server/api/block_documents.py, src/prefect/server/api/block_schemas.py, src/prefect/server/api/block_types.py, src/prefect/server/api/collections.py, src/prefect/server/api/concurrency_limits.py, src/prefect/server/api/concurrency_limits_v2.py, src/prefect/server/api/csrf_token.py, src/prefect/server/api/deployments.py, src/prefect/server/api/events.py, src/prefect/server/api/flow_run_states.py, src/prefect/server/api/flow_runs.py, src/prefect/server/api/flows.py, src/prefect/server/api/logs.py, src/prefect/server/api/root.py, src/prefect/server/api/saved_searches.py, src/prefect/server/api/task_run_states.py; source refs truncated
- `evidence-group-65e1fa38aa837155be96`: 33450 refs; summary={'AST': 397, 'CALL_GRAPH': 23099, 'GRAPH_AGGREGATION': 1, 'IMPORT': 4624, 'SYMBOL_RESOLUTION': 5329}; sources=architecture-graph, tests/_experimental/bundles/test_bundles.py, tests/_experimental/bundles/test_dependency_validation.py, tests/_experimental/bundles/test_execute.py, tests/_experimental/bundles/test_file_collector.py, tests/_experimental/bundles/test_ignore_filter.py, tests/_experimental/bundles/test_include_files_integration.py, tests/_experimental/bundles/test_path_resolver.py, tests/_experimental/bundles/test_zip_builder.py, tests/_experimental/bundles/test_zip_extractor.py, tests/_internal/analytics/conftest.py, tests/_internal/analytics/test_ci_detection.py, tests/_internal/analytics/test_client.py, tests/_internal/analytics/test_device_id.py, tests/_internal/analytics/test_events.py, tests/_internal/analytics/test_milestones.py, tests/_internal/analytics/test_notice.py, tests/_internal/analytics/test_service.py, tests/_internal/compatibility/test_async_dispatch.py, tests/_internal/compatibility/test_backports.py; source refs truncated
- `evidence-group-78bd97508794d88de2ad`: 93858 refs; summary={'AST': 12963, 'CALL_GRAPH': 57692, 'COMPONENT_DETECTION': 3, 'DOCKERFILE': 3, 'FRAMEWORK_ADAPTER': 481, 'GRAPH_AGGREGATION': 85, 'IMPORT': 13771, 'SYMBOL_RESOLUTION': 8860}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py, integration-tests/test_flow_suspension.py; source refs truncated
- `evidence-group-8ca28d9ccc930c0773e7`: 32 refs; summary={'FRAMEWORK_ADAPTER': 1, 'SYMBOL_RESOLUTION': 31}; sources=src/prefect/runner/server.py, src/prefect/server/api/admin.py, src/prefect/server/api/artifacts.py, src/prefect/server/api/automations.py, src/prefect/server/api/block_capabilities.py, src/prefect/server/api/block_documents.py, src/prefect/server/api/block_schemas.py, src/prefect/server/api/block_types.py, src/prefect/server/api/collections.py, src/prefect/server/api/concurrency_limits.py, src/prefect/server/api/concurrency_limits_v2.py, src/prefect/server/api/csrf_token.py, src/prefect/server/api/deployments.py, src/prefect/server/api/events.py, src/prefect/server/api/flow_run_states.py, src/prefect/server/api/flow_runs.py, src/prefect/server/api/flows.py, src/prefect/server/api/logs.py, src/prefect/server/api/root.py, src/prefect/server/api/saved_searches.py; source refs truncated
- `evidence-group-9cbba9785fabfc118ec5`: 100541 refs; summary={'AST': 27336, 'CALL_GRAPH': 49451, 'COMPONENT_DETECTION': 11, 'DOCKERFILE': 4, 'FRAMEWORK_ADAPTER': 486, 'GRAPH_AGGREGATION': 58, 'IMPORT': 13863, 'SYMBOL_RESOLUTION': 9332}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/run_dbt_with_prefect.py, hatch_build.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py, integration-tests/test_docker_deploy.py, integration-tests/test_flow_pauses.py, integration-tests/test_flow_results.py; source refs truncated
- `evidence-group-bfc634e63807af079f36`: 93953 refs; summary={'AST': 12658, 'CALL_GRAPH': 56359, 'COMPONENT_DETECTION': 6, 'FRAMEWORK_ADAPTER': 486, 'GRAPH_AGGREGATION': 81, 'IMPORT': 15029, 'SYMBOL_RESOLUTION': 9334}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_import.py, benches/bench_tasks.py, client/client_deploy.py, client/client_flow.py, component-detection, docs/conftest.py, docs/myproject/flows.py, docs/myproject/tasks.py, examples/ai_data_analyst_with_pydantic_ai.py, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/resume_flow_run_on_pr_merge.py, examples/run_api_sourced_etl.py, examples/run_dbt_with_prefect.py; source refs truncated
- `evidence-group-c883f11d7c8d0908aa57`: 52056 refs; summary={'AST': 51180, 'CALL_GRAPH': 844, 'DOCKERFILE': 10, 'DOCKER_COMPOSE': 5, 'GRAPH_AGGREGATION': 17}; sources=Dockerfile, architecture-graph, benches/__main__.py, benches/bench_block_schemas.py, benches/bench_cli.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_import.py, benches/bench_tasks.py, client/Dockerfile, client/client_deploy.py, client/client_flow.py, docs/conftest.py, docs/myproject/cool.py, docs/myproject/db.py, docs/myproject/flows.py, docs/myproject/tasks.py, docs/myproject/utils.py, docs/script.js, examples/ai_data_analyst_with_pydantic_ai.py; source refs truncated
- `evidence-group-fc550bc329ff7b29a4fc`: 68006 refs; summary={'AST': 1582, 'CALL_GRAPH': 44581, 'COMPONENT_DETECTION': 1, 'FRAMEWORK_ADAPTER': 476, 'GRAPH_AGGREGATION': 11, 'IMPORT': 12535, 'SYMBOL_RESOLUTION': 8820}; sources=architecture-graph, benches/bench_block_schemas.py, benches/bench_count_flow_runs.py, benches/bench_flows.py, benches/bench_tasks.py, client/client_deploy.py, component-detection, examples/ai_data_analyst_with_pydantic_ai.py, examples/ai_database_cleanup_with_approval.py, examples/atproto_dashboard_with_prefect_assets.py, examples/hello_world.py, examples/per_worker_task_concurrency.py, examples/resume_flow_run_on_pr_merge.py, examples/run_api_sourced_etl.py, examples/run_dbt_with_prefect.py, examples/simple_web_scraper.py, integration-tests/test_automation_assessments.py, integration-tests/test_client_context_lifespan.py, integration-tests/test_concurrency_leases.py, integration-tests/test_deploy.py; source refs truncated

## Profile

- total seconds: 142.8858489000704

- repository_acquisition: 8.411099 s; counts={}
- scanner: 2.235907 s; counts={'files': 5358, 'file_count': 5358, 'source_files': 2513}
- stack_detection: 13.014372 s; counts={'evidence': 129}
- parser: 15.557144 s; counts={'parsed_files': 1901, 'definitions': 36405, 'imports': 25844, 'calls': 158176}
- basic_data_flow: 0.227413 s; counts={'assignments': 75029, 'returns': 12277, 'scopes': 4200, 'flow_entries': 0}
- symbol_resolution: 0.742450 s; counts={'symbols': 36041, 'symbol_count': 36041, 'unresolved_calls': 113890, 'flow_entries': 3971}
- source_origin: 2.694252 s; counts={'local_modules': 1803, 'classified_nodes': 43969, 'raw_node_count': 43969, 'classifications': 43969}
- raw_graph: 39.397837 s; counts={'nodes': 43954, 'raw_node_count': 43954, 'edges': 139282, 'raw_edge_count': 139282, 'evidence': 178829, 'evidence_count': 178829, 'unresolved_calls': 66399}
- framework_adapters: 20.470359 s; counts={'facts': 506, 'evidence': 519}
- infrastructure_semantics: 0.100468 s; counts={'resources': 15, 'relations': 3, 'evidence': 18}
- architectural_graph: 1.294333 s; counts={'nodes': 147, 'edges': 268, 'evidence': 179260}
- component_detection: 1.988386 s; counts={'components': 15, 'component_count': 15, 'unassigned_nodes': 392, 'pairs': 8159}
- architecture_ir: 8.764425 s; counts={'nodes': 162, 'edges': 268, 'evidence': 179923, 'raw_nodes': 43969, 'raw_edges': 139300, 'architectural_nodes': 162, 'architectural_edges': 268, 'components': 15, 'projected_nodes': 0, 'projected_edges': 0, 'evidence_groups': 0}
- architecture_hypotheses: 10.623078 s; counts={'hypotheses': 4}
- architecture_validation: 6.698790 s; counts={'valid': True, 'warnings': 15}
- architectural_significance_projection: 5.136791 s; counts={'detailed_nodes': 177, 'projected_nodes': 1, 'projected_edges': 0}
- projection_audit: 5.528745 s; counts={'projected_nodes': 1, 'projected_edges': 0, 'evidence_coverage': 1.0}
- projection_audit_report: 0.000000 s; counts={'evidence_groups': 8, 'projected_nodes': 1, 'projected_edges': 0, 'components': 30, 'architectural_components': 15, 'component_candidates': 15}
