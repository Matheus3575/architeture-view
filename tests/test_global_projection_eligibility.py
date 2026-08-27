from architecture_recovery.ir import (
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    InfrastructureRelation,
    InfrastructureResource,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.visualization import (
    ArchitecturalProjectionBuilder,
    VisualizationReadModelBuilder,
)
from architecture_recovery.visualization.projection_audit import audit_projection


def _evidence(*identifiers: str) -> list[Evidence]:
    return [
        Evidence(
            id=identifier,
            source_type=EvidenceSource.AST,
            detail=identifier,
            source=SourceRef(path="neutral_fixture.py", start_line=1),
        )
        for identifier in identifiers
    ]


def _node(identifier: str, node_type: NodeType, evidence: str, **metadata) -> Node:
    return Node(
        id=identifier,
        type=node_type,
        name=identifier,
        origin=SourceOrigin.FIRST_PARTY,
        status=EvidenceStatus.OBSERVED,
        evidence_refs=[evidence],
        metadata=metadata,
    )


def _ir() -> ArchitectureIR:
    nodes = [
        _node("repository:envelope", NodeType.REPOSITORY, "repository"),
        _node("application:main", NodeType.APPLICATION, "application"),
        _node("component:api", NodeType.COMPONENT, "api"),
        _node("component:domain", NodeType.COMPONENT, "domain"),
        _node("component:persistence", NodeType.COMPONENT, "persistence"),
        _node("component:local-high", NodeType.COMPONENT, "local-high", architectural_role="application"),
        _node("component:local-medium", NodeType.COMPONENT, "local-medium", architectural_role="framework"),
        _node("api:independent", NodeType.API, "independent-api"),
    ]
    edges = [
        Edge(
            id="route-api",
            source="application:main",
            target="component:api",
            type=EdgeType.ROUTES_TO,
            evidence_refs=["route-api"],
        ),
        Edge(
            id="route-domain",
            source="component:api",
            target="component:domain",
            type=EdgeType.ROUTES_TO,
            evidence_refs=["route-domain"],
        ),
        Edge(
            id="query-persistence",
            source="component:domain",
            target="component:persistence",
            type=EdgeType.QUERIES,
            evidence_refs=["query-persistence"],
        ),
        Edge(
            id="local-flow",
            source="component:local-high",
            target="component:local-medium",
            type=EdgeType.ROUTES_TO,
            evidence_refs=["local-flow"],
        ),
    ]
    resource = InfrastructureResource(
        id="database:main",
        name="database:main",
        kind="DATABASE",
        evidence_refs=["database"],
    )
    infrastructure_relation = InfrastructureRelation(
        id="persistence-database",
        source="component:persistence",
        target=resource.id,
        type="QUERIES",
        evidence_refs=["database-link"],
    )
    evidence_ids = [
        "repository", "application", "api", "domain", "persistence",
        "local-high", "local-medium", "independent-api", "route-api",
        "route-domain", "query-persistence", "local-flow", "database",
        "database-link",
    ]
    return ArchitectureIR(
        repository=RepositoryInfo(name="global-eligibility", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=[]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        infrastructure_resources=[resource],
        infrastructure_relations=[infrastructure_relation],
        evidence=_evidence(*evidence_ids),
    )


def test_local_significance_is_preserved_but_not_projected_without_global_context():
    ir = _ir()
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    explanations = {item.subject_id: item for item in audit.node_explanations}

    assert explanations["component:local-high"].significance.value == "high"
    assert explanations["component:local-high"].locally_significant is True
    assert explanations["component:local-high"].globally_contextualized is False
    assert "component:local-high" not in projection.projected_node_ids
    assert "component:local-medium" not in projection.projected_node_ids
    assert audit.local_only_significant_count >= 2
    assert audit.local_only_projected_count == 0
    assert audit.projected_without_global_justification_count == 0


def test_root_membership_and_independent_boundary_are_projected():
    ir = _ir()
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    assert {
        "application:main",
        "component:api",
        "component:domain",
        "component:persistence",
        "database:main",
        "api:independent",
    } <= set(projection.projected_node_ids)
    assert "repository:envelope" not in projection.projected_node_ids
    assert audit.navigation_only_projected_count == 0
    assert audit.globally_eligible_projected_count == len(projection.projected_node_ids)
    assert all(
        edge.source in projection.projected_node_ids
        and edge.target in projection.projected_node_ids
        for edge in projection.projected_edges
    )


def test_read_model_closure_traceability_and_determinism_hold_after_gate():
    ir = _ir()
    first_projection = ArchitecturalProjectionBuilder().build(ir)
    second_projection = ArchitecturalProjectionBuilder().build(ir)
    assert first_projection.model_dump_json() == second_projection.model_dump_json()

    first = VisualizationReadModelBuilder().build(ir)
    second = VisualizationReadModelBuilder().build(ir)
    assert first.model_dump_json() == second.model_dump_json()
    node_ids = {node.id for node in first.nodes}
    assert node_ids == set(first_projection.projected_node_ids)
    assert all(edge.source in node_ids and edge.target in node_ids for edge in first.edges)
    assert first.metadata["projection_traceability"] is True
    assert first.metadata["projected_edge_validity"] is True
    assert {item.subject for item in first.architectural_significance} >= {
        "component:local-high", "component:local-medium", "repository:envelope",
    }