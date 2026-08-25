from __future__ import annotations

from architecture_recovery.ir import (
    ArchitectureAnalysis,
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    FrameworkFact,
    InfrastructureRelation,
    InfrastructureResource,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.visualization import VisualizationReadModelBuilder, validate_visualization_read_model


def _ev(identifier: str) -> Evidence:
    return Evidence(
        id=identifier,
        source_type=EvidenceSource.FRAMEWORK_ADAPTER,
        detail=identifier,
        source=SourceRef(path="fixture.py", start_line=1, end_line=1),
    )


def _node(identifier: str, node_type: NodeType, evidence: str, name: str | None = None) -> Node:
    return Node(
        id=identifier,
        type=node_type,
        name=name or identifier,
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=[evidence],
    )


def _edge(identifier: str, source: str, target: str, edge_type: EdgeType, evidence: str, raw_edge: str | None = None) -> Edge:
    return Edge(
        id=identifier,
        source=source,
        target=target,
        type=edge_type,
        evidence_refs=[evidence],
        raw_edge_ids=[raw_edge] if raw_edge else [],
    )


def _base_ir(
    name: str,
    nodes: list[Node],
    edges: list[Edge] | None = None,
    facts: list[FrameworkFact] | None = None,
    resources: list[InfrastructureResource] | None = None,
    relations: list[InfrastructureRelation] | None = None,
    raw_edges: list[Edge] | None = None,
    evidence_ids: set[str] | None = None,
) -> ArchitectureIR:
    all_evidence = evidence_ids or {
        ref for node in nodes for ref in node.evidence_refs
    } | {
        ref for edge in [*(edges or []), *(raw_edges or [])] for ref in edge.evidence_refs
    } | {
        ref for fact in (facts or []) for ref in fact.evidence_refs
    } | {
        ref for resource in (resources or []) for ref in resource.evidence_refs
    } | {
        ref for relation in (relations or []) for ref in relation.evidence_refs
    }
    architectural_edges = edges or []
    raw_graph_nodes = list(nodes)
    return ArchitectureIR(
        repository=RepositoryInfo(name=name, path=f"/{name}"),
        raw_graph=RawCodeGraph(nodes=raw_graph_nodes, edges=raw_edges or []),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=architectural_edges),
        architecture=ArchitectureAnalysis(),
        evidence=[_ev(identifier) for identifier in sorted(all_evidence)],
        framework_facts=facts or [],
        infrastructure_resources=resources or [],
        infrastructure_relations=relations or [],
    )


def _endpoint_facts(owner: str, count: int, evidence: str = "e-endpoint") -> list[FrameworkFact]:
    return [
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject=f"endpoint:{index}",
            attributes={"owner": owner, "path": f"/items/{index}"},
            evidence_refs=[evidence],
        )
        for index in range(count)
    ]


def alpha_fixture() -> ArchitectureIR:
    nodes = [
        _node("application:alpha", NodeType.APPLICATION, "e-app"),
        _node("component:api", NodeType.COMPONENT, "e-api"),
        _node("component:domain", NodeType.COMPONENT, "e-domain"),
        _node("component:persistence", NodeType.COMPONENT, "e-persistence"),
        _node("component:auxiliary", NodeType.COMPONENT, "e-aux"),
    ]
    edges = [
        _edge("a-contains-api", "application:alpha", "component:api", EdgeType.CONTAINS, "e-app"),
        _edge("a-api-domain", "component:api", "component:domain", EdgeType.DEPENDS_ON, "e-flow", "raw-api-domain"),
        _edge("a-domain-persistence", "component:domain", "component:persistence", EdgeType.DEPENDS_ON, "e-flow", "raw-domain-persistence"),
    ]
    raw_edges = [
        _edge("raw-api-domain", "component:api", "component:domain", EdgeType.CALLS, "e-flow"),
        _edge("raw-domain-persistence", "component:domain", "component:persistence", EdgeType.CALLS, "e-flow"),
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="component:api",
            attributes={"symbol": "fastapi.FastAPI"},
            evidence_refs=["e-framework"],
        ),
        FrameworkFact(
            kind="APPLICATION",
            subject="component:auxiliary",
            attributes={"symbol": "fastapi.FastAPI"},
            evidence_refs=["e-aux"],
        ),
        *_endpoint_facts("component:api", 12),
        *[
            FrameworkFact(
                kind="ROUTER",
                subject=f"router:{index}",
                attributes={"owner": "component:api", "prefix": f"/v{index}"},
                evidence_refs=["e-router"],
            )
            for index in range(3)
        ],
    ]
    database = InfrastructureResource(
        id="database:alpha",
        name="primary database",
        kind="DATABASE",
        evidence_refs=["e-database"],
    )
    return _base_ir(
        "projection-alpha",
        nodes,
        edges,
        facts,
        [database],
        [
            InfrastructureRelation(
                id="a-persistence-db",
                source="component:persistence",
                target=database.id,
                type="QUERIES",
                evidence_refs=["e-database"],
            )
        ],
        raw_edges,
        {
            "e-app", "e-api", "e-domain", "e-persistence", "e-aux",
            "e-flow", "e-framework", "e-endpoint", "e-router", "e-database",
        },
    )


def beta_fixture() -> ArchitectureIR:
    nodes = [
        _node("application:worker", NodeType.APPLICATION, "b-worker"),
        _node("application:scheduler", NodeType.APPLICATION, "b-scheduler"),
        _node("component:tooling", NodeType.COMPONENT, "b-tooling"),
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="application:worker",
            attributes={"symbol": "worker.runtime"},
            evidence_refs=["b-worker"],
        ),
        FrameworkFact(
            kind="APPLICATION",
            subject="application:scheduler",
            attributes={"symbol": "scheduler.runtime"},
            evidence_refs=["b-scheduler"],
        ),
        FrameworkFact(
            kind="APPLICATION",
            subject="component:tooling",
            attributes={"symbol": "worker.runtime"},
            evidence_refs=["b-tooling"],
        ),
    ]
    resources = [
        InfrastructureResource(
            id="broker:beta",
            name="jobs broker",
            kind="MESSAGE_BROKER",
            evidence_refs=["b-broker"],
        ),
        InfrastructureResource(
            id="cache:beta",
            name="state cache",
            kind="CACHE",
            evidence_refs=["b-cache"],
        ),
        InfrastructureResource(
            id="container:build",
            name="build container",
            kind="CONTAINER",
            evidence_refs=["b-container"],
        ),
    ]
    relations = [
        InfrastructureRelation(
            id="b-worker-broker",
            source="application:worker",
            target="broker:beta",
            type="CONNECTS_TO",
            evidence_refs=["b-broker"],
        ),
        InfrastructureRelation(
            id="b-scheduler-cache",
            source="application:scheduler",
            target="cache:beta",
            type="CONNECTS_TO",
            evidence_refs=["b-cache"],
        ),
    ]
    return _base_ir(
        "projection-beta",
        nodes,
        facts=facts,
        resources=resources,
        relations=relations,
        evidence_ids={
            "b-worker", "b-scheduler", "b-tooling", "b-broker", "b-cache", "b-container",
        },
    )


def test_alpha_projection_is_authoritative_and_keeps_semantic_children_as_details():
    model = VisualizationReadModelBuilder().build(alpha_fixture())
    node_ids = {node.id for node in model.nodes}
    details = model.semantic_details

    assert {"application:alpha", "component:api", "component:domain", "component:persistence", "database:alpha"} <= node_ids
    assert model.metadata["read_model_high_level_node_count"] == model.metadata["projection_node_count"]
    assert model.metadata["endpoint_high_level_count"] == 0
    assert model.metadata["endpoint_detail_count"] == 12
    assert model.metadata["router_high_level_count"] == 0
    assert model.metadata["router_detail_count"] == 3
    assert not any(item.id.startswith("endpoint:") for item in model.nodes)
    assert not any(item.id.startswith("router:") for item in model.nodes)
    assert any(item.kind == "framework_fact" and item.owner == "component:api" for item in details)
    assert "component:auxiliary" not in node_ids
    assert model.metadata["projected_edge_validity"] is True
    assert model.metadata["projection_traceability"] is True


def test_beta_promotes_bound_resources_but_not_tooling_or_isolated_container():
    model = VisualizationReadModelBuilder().build(beta_fixture())
    node_ids = {node.id for node in model.nodes}

    assert {"application:worker", "application:scheduler", "broker:beta", "cache:beta"} <= node_ids
    assert "component:tooling" not in node_ids
    assert "container:build" not in node_ids
    assert model.metadata["infrastructure_high_level_count"] == 2
    assert model.metadata["container_high_level_count"] == 0
    assert model.metadata["container_detail_count"] == 1
    assert all(edge.source in node_ids and edge.target in node_ids for edge in model.edges)


def test_framework_fact_does_not_promote_auxiliary_component_without_context():
    model = VisualizationReadModelBuilder().build(alpha_fixture())
    significance = {
        item.subject: item for item in model.architectural_significance
    }

    assert significance["component:auxiliary"].significance.value == "low"
    assert "component:auxiliary" not in {node.id for node in model.nodes}
    assert any(
        item.subject == "component:auxiliary" and item.kind == "framework_fact"
        for item in model.semantic_details
    )


def test_high_to_low_edges_do_not_reintroduce_low_nodes():
    ir = _base_ir(
        "high-low",
        [
            _node("application:main", NodeType.APPLICATION, "h-app"),
            _node("component:utility", NodeType.COMPONENT, "h-util"),
        ],
        [
            _edge("h-edge", "application:main", "component:utility", EdgeType.DEPENDS_ON, "h-edge"),
        ],
        evidence_ids={"h-app", "h-util", "h-edge"},
    )
    model = VisualizationReadModelBuilder().build(ir)
    node_ids = {node.id for node in model.nodes}

    assert "component:utility" not in node_ids
    assert not any(edge.source == "application:main" and edge.target == "component:utility" for edge in model.edges)
    assert any(item.subject == "component:utility" and item.kind == "projection_detail" for item in model.semantic_details)


def test_unknown_and_explicit_boundary_are_distinct_and_traceable():
    unknown_ir = _base_ir(
        "unknown",
        [Node(id="component:unknown", type=NodeType.COMPONENT, name="unknown", origin=SourceOrigin.UNKNOWN)],
        evidence_ids=set(),
    )
    unknown_model = VisualizationReadModelBuilder().build(unknown_ir)
    unknown_significance = next(
        item for item in unknown_model.architectural_significance
        if item.subject == "component:unknown"
    )
    assert unknown_significance.significance.value == "unknown"
    assert "component:unknown" not in {node.id for node in unknown_model.nodes}

    boundary_ir = _base_ir(
        "boundary",
        [_node("application:main", NodeType.APPLICATION, "b-app")],
        facts=[
            FrameworkFact(
                kind="HTTP_ENDPOINT",
                subject="boundary-endpoint",
                attributes={"owner": "application:main", "path": "/health", "architectural_boundary": True},
                evidence_refs=["b-endpoint"],
            )
        ],
        evidence_ids={"b-app", "b-endpoint"},
    )
    boundary_model = VisualizationReadModelBuilder().build(boundary_ir)
    assert boundary_model.metadata["boundary_exception_count"] == 1
    assert boundary_model.metadata["read_model_high_level_node_count"] == boundary_model.metadata["projection_node_count"] + 1
    assert boundary_model.metadata["projected_edge_validity"] is True
    assert any(node.layout_hints.get("projection_boundary") for node in boundary_model.nodes)


def test_projection_closure_validation_rejects_unjustified_nodes():
    model = VisualizationReadModelBuilder().build(beta_fixture())
    bad_node = model.nodes[0].model_copy(update={"id": "unjustified"})
    broken = model.model_copy(update={"nodes": [*model.nodes, bad_node]})
    report = validate_visualization_read_model(broken, {item.id for item in model.evidence})
    assert not report.valid
    assert any("outside projection closure" in error for error in report.errors)


def test_projection_outputs_are_deterministic_for_alpha_and_beta():
    builder = VisualizationReadModelBuilder()
    for ir in (alpha_fixture(), beta_fixture()):
        first = builder.build(ir)
        second = builder.build(ir)
        assert first.model_dump_json() == second.model_dump_json()
        assert all(edge.source in {node.id for node in first.nodes} and edge.target in {node.id for node in first.nodes} for edge in first.edges)

def test_endpoint_architectural_node_requires_explicit_boundary_evidence():
    ir = _base_ir(
        "endpoint-node",
        [
            _node("application:main", NodeType.APPLICATION, "ep-app"),
            _node("endpoint:health", NodeType.ENDPOINT, "ep-fact"),
        ],
        [
            _edge("ep-route", "application:main", "endpoint:health", EdgeType.ROUTES_TO, "ep-route"),
        ],
        [
            FrameworkFact(
                kind="HTTP_ENDPOINT",
                subject="endpoint:health",
                attributes={"owner": "application:main", "path": "/health"},
                evidence_refs=["ep-fact"],
            )
        ],
        evidence_ids={"ep-app", "ep-fact", "ep-route"},
    )
    projection = VisualizationReadModelBuilder().build(ir)
    significance = next(
        item for item in projection.architectural_significance
        if item.subject == "endpoint:health"
    )

    assert significance.significance.value == "low"
    assert "endpoint:health" not in set(projection.metadata["projection_node_ids"])
    assert not any(
        edge.source == "application:main" and edge.target == "endpoint:health"
        for edge in projection.edges
    )