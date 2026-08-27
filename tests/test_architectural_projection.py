from architecture_recovery.ir import (
    ArchitecturalGraph,
    ArchitectureIR,
    ArchitectureAnalysis,
    Component,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    FrameworkFact,
    InfrastructureResource,
    InfrastructureRelation,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.visualization import ArchitecturalProjectionBuilder, VisualizationReadModelBuilder, SignificanceLevel


def _evidence(*names):
    return [
        Evidence(id=name, source_type=EvidenceSource.CALL_GRAPH, detail=name, source=SourceRef(path="fixture.py", start_line=1))
        for name in names
    ]


def _projection_ir():
    arch_nodes = [
        Node(id="repository:demo", type=NodeType.REPOSITORY, name="demo", evidence_refs=["repo"]),

        Node(id="application:demo", type=NodeType.APPLICATION, name="demo-app", evidence_refs=["app"], metadata={"entrypoint": True}),
        Node(id="component:users", type=NodeType.COMPONENT, name="users", evidence_refs=["component"], metadata={"raw_node_ids": ["module:users", "module:users_model"]}),
        Node(id="module:entry", type=NodeType.MODULE, name="entry", evidence_refs=["entry"]),
        Node(id="module:utility", type=NodeType.MODULE, name="utility", evidence_refs=["utility"]),
        Node(id="database:postgres", type=NodeType.DATABASE, name="postgres", evidence_refs=["database"]),
        Node(id="external:service", type=NodeType.EXTERNAL_SERVICE, name="service", evidence_refs=["service"]),
    ] + [Node(id=f"module:internal_{index}", type=NodeType.MODULE, name=f"internal_{index}") for index in range(12)]
    raw_nodes = [
        Node(id="module:users", type=NodeType.MODULE, name="users", evidence_refs=["users"]),
        Node(id="module:users_model", type=NodeType.MODULE, name="users_model", evidence_refs=["users-model"]),
    ]
    edges = [
        Edge(id=f"edge-{index}", source="component:users", target="database:postgres", type=EdgeType.DEPENDS_ON, evidence_refs=[f"edge-{index}"])
        for index in range(3)
    ]
    edges.insert(0, Edge(id="app-users", source="application:demo", target="component:users", type=EdgeType.ROUTES_TO, evidence_refs=["app"]))
    edges.extend([
        Edge(id="app-contains", source="application:demo", target="component:users", type=EdgeType.CONTAINS, evidence_refs=["app"]),
        Edge(id="app-deploys", source="application:demo", target="database:postgres", type=EdgeType.DEPLOYS, evidence_refs=["app"]),
        Edge(id="app-service", source="application:demo", target="external:service", type=EdgeType.DEPENDS_ON, evidence_refs=["service"]),
    ])
    edges.extend(
        Edge(id=f"utility-{index}", source="module:utility", target="component:users", type=EdgeType.CALLS, evidence_refs=["utility"])
        for index in range(5)
    )
    edges.append(Edge(id="entry-flow", source="module:entry", target="component:users", type=EdgeType.CALLS, evidence_refs=["entry-flow"]))
    framework = [FrameworkFact(kind="HTTP_ENDPOINT", subject="module:entry", evidence_refs=["http"])]
    resources = [InfrastructureResource(id="database:postgres", name="postgres", kind="DATABASE", evidence_refs=["database"])]
    evidence = _evidence("repo", "app", "component", "service", "entry", "utility", "database", "users", "users-model", "http", "entry-flow", "edge-0", "edge-1", "edge-2")
    return ArchitectureIR(
        repository=RepositoryInfo(name="demo", path="."),
        raw_graph=RawCodeGraph(nodes=raw_nodes, edges=[]),
        architectural_graph=ArchitecturalGraph(nodes=arch_nodes, edges=edges),
        framework_facts=framework,
        infrastructure_resources=resources,
        infrastructure_relations=[InfrastructureRelation(id="infra-db", source="component:users", target="database:postgres", type="depends_on", evidence_refs=["database"])],
        architecture=ArchitectureAnalysis(hypotheses=[]),
        component_candidates=[Component(id="candidate:users", name="users", node_ids=["module:users", "module:users_model"], evidence_refs=["component"])],
        evidence=evidence,
    )


def test_significance_promotes_semantic_boundary_and_infrastructure():
    projection = ArchitecturalProjectionBuilder().build(_projection_ir())
    levels = {item.subject: item.significance for item in projection.significances}
    assert levels["component:users"] == SignificanceLevel.HIGH
    assert levels["module:entry"] == SignificanceLevel.HIGH
    assert levels["database:postgres"] == SignificanceLevel.HIGH


def test_connected_utility_is_not_promoted_by_degree_alone():
    projection = ArchitecturalProjectionBuilder().build(_projection_ir())
    utility = next(item for item in projection.significances if item.subject == "module:utility")
    assert utility.significance in {SignificanceLevel.LOW, SignificanceLevel.UNKNOWN}
    assert "module:utility" not in projection.projected_node_ids


def test_low_and_unknown_elements_are_preserved_for_drill_down():
    projection = ArchitecturalProjectionBuilder().build(_projection_ir())
    assert "module:utility" in projection.low_significance_refs or "module:utility" in projection.unknown_refs
    assert any(item.subject == "module:internal_0" for item in projection.significances)


def test_projection_aggregates_edges_and_preserves_support():
    projection = ArchitecturalProjectionBuilder().build(_projection_ir())
    edge = next(item for item in projection.projected_edges if item.source == "component:users" and item.target == "database:postgres" and item.kind == "DEPENDS_ON")
    assert edge.support_count == 3
    assert {"edge-0", "edge-1", "edge-2"} <= set(edge.raw_edge_ids)
    assert edge.evidence_refs


def test_read_model_projection_has_no_orphan_edges_and_is_traceable():
    ir = _projection_ir()
    model = VisualizationReadModelBuilder().build(ir)
    node_ids = {node.id for node in model.nodes}
    assert all(edge.source in node_ids and edge.target in node_ids for edge in model.edges)
    assert model.metadata["projected_edge_validity"] is True
    assert model.metadata["projection_traceability"] is True
    assert model.architectural_significance
    assert model.metadata["high_level_node_count"] < model.metadata["detailed_node_count"]


def test_projection_is_deterministic():
    ir = _projection_ir()
    builder = VisualizationReadModelBuilder()
    assert builder.build(ir).model_dump_json() == builder.build(ir).model_dump_json()