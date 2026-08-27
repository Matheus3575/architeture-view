from architecture_recovery.ir import (
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
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
    DeploymentProvenance,
    VisualizationReadModelBuilder,
    audit_projection,
    context_propagation_kind,
)
from architecture_recovery.visualization.context import ContextPropagation


def _evidence(ids: list[str]) -> list[Evidence]:
    return [
        Evidence(
            id=item,
            source_type=EvidenceSource.DOCKER_COMPOSE if "deploy" in item or "navigation" in item else EvidenceSource.AST,
            detail=item,
            source=SourceRef(path="neutral_deployment.py", start_line=1),
        )
        for item in ids
    ]


def _node(identifier: str, node_type: NodeType, evidence: str, **metadata) -> Node:
    return Node(
        id=identifier,
        type=node_type,
        name=identifier,
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=[evidence],
        metadata=metadata,
    )


def _ir() -> ArchitectureIR:
    nodes = [
        _node("application:main", NodeType.APPLICATION, "app", entrypoint=True),
        _node("component:service", NodeType.COMPONENT, "service"),
        _node("component:local", NodeType.COMPONENT, "local"),
        _node("repository:envelope", NodeType.REPOSITORY, "repository"),
        _node("container:explicit", NodeType.CONTAINER, "explicit"),
        _node("container:aggregated", NodeType.CONTAINER, "aggregated"),
        _node("container:navigation", NodeType.CONTAINER, "navigation"),
    ]
    edges = [
        Edge(
            id="route-service",
            source="application:main",
            target="component:service",
            type=EdgeType.ROUTES_TO,
            evidence_refs=["route"],
        ),
        Edge(
            id="deploy-explicit",
            source="application:main",
            target="container:explicit",
            type=EdgeType.DEPLOYS,
            evidence_refs=["deploy-explicit"],
            metadata={"deployment_execution_boundary": True},
        ),
        Edge(
            id="deploy-aggregated",
            source="component:local",
            target="container:aggregated",
            type=EdgeType.DEPLOYS,
            evidence_refs=["deploy-aggregated"],
        ),
        Edge(
            id="deploy-navigation",
            source="repository:envelope",
            target="container:navigation",
            type=EdgeType.DEPLOYS,
            evidence_refs=["deploy-navigation"],
        ),
    ]
    evidence_ids = [
        "app", "service", "local", "repository", "explicit", "aggregated",
        "navigation", "route", "deploy-explicit", "deploy-aggregated",
        "deploy-navigation",
    ]
    return ArchitectureIR(
        repository=RepositoryInfo(name="deployment-provenance", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=[]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        infrastructure_resources=[
            InfrastructureResource(
                id="container:resource",
                name="resource",
                kind="CONTAINER",
                evidence_refs=["resource"],
            )
        ],
        evidence=_evidence(evidence_ids + ["resource"]),
    )


def test_deploys_provenance_separates_validity_from_context_propagation():
    assert context_propagation_kind(EdgeType.DEPLOYS) == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT
    assert context_propagation_kind(
        EdgeType.DEPLOYS,
        deployment_provenance=DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT,
    ) == ContextPropagation.CAN_PROPAGATE_CONTEXT
    assert context_propagation_kind(
        EdgeType.DEPLOYS,
        deployment_provenance=DeploymentProvenance.AGGREGATED_DEPLOYMENT,
    ) == ContextPropagation.SUPPORTS_CONTEXT


def test_explicit_deployment_propagates_but_navigation_and_aggregation_do_not():
    ir = _ir()
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    explanations = {item.subject_id: item for item in audit.node_explanations}

    assert "container:explicit" in projection.projected_node_ids
    assert "container:aggregated" not in projection.projected_node_ids
    assert "container:navigation" not in projection.projected_node_ids
    assert explanations["container:explicit"].context_root_ids == ["application:main"]
    assert explanations["container:aggregated"].context_root_ids == []
    assert explanations["container:navigation"].context_root_ids == []
    assert audit.deploys_total == 3
    assert audit.deploys_by_provenance == {
        "aggregated_deployment": 1,
        "explicit_execution_deployment": 1,
        "navigation_derived": 1,
    }
    assert audit.deploys_can_propagate_count == 1
    assert audit.deploys_supporting_count == 1
    assert audit.deploys_non_propagating_count == 1
    assert audit.membership_established_by_deploys == 1
    assert audit.navigation_transit_membership_count == 0
    assert audit.qualified_global_deployment_boundary_count == 1
    assert audit.rejected_local_deployment_boundary_count == 2


def test_deployment_relation_and_details_remain_traceable_and_closed():
    ir = _ir()
    before = ir.model_dump_json()
    projection = ArchitecturalProjectionBuilder().build(ir)
    model = VisualizationReadModelBuilder().build(ir)

    node_ids = {node.id for node in model.nodes}
    assert all(edge.source in node_ids and edge.target in node_ids for edge in model.edges)
    assert any(detail.subject == "container:aggregated" for detail in model.semantic_details)
    assert any(detail.subject == "container:navigation" for detail in model.semantic_details)
    assert any(edge.type == EdgeType.DEPLOYS for edge in ir.architectural_graph.edges)
    assert ir.model_dump_json() == before
    assert projection.model_dump_json() == ArchitecturalProjectionBuilder().build(ir).model_dump_json()
    assert model.model_dump_json() == VisualizationReadModelBuilder().build(ir).model_dump_json()

def test_deployment_context_propagation_respects_application_to_runtime_direction():
    ir = _ir()
    original = next(edge for edge in ir.architectural_graph.edges if edge.id == "deploy-explicit")
    reversed_edge = original.model_copy(update={
        "id": "deploy-explicit-reversed",
        "source": "container:explicit",
        "target": "application:main",
    })
    ir.architectural_graph.edges = [
        reversed_edge if edge.id == original.id else edge
        for edge in ir.architectural_graph.edges
    ]

    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    assert "container:explicit" not in projection.projected_node_ids
    assert not any(
        link.subject_id == "container:explicit" and link.establishes_membership
        for item in audit.node_explanations
        for link in item.context_chain
    )
    assert any(
        item.provenance == "explicit_execution_deployment"
        and item.accepted is False
        and item.subject_id == "application:main"
        for item in audit.positive_evidence_ledger
    )
    assert audit.directional_propagation_count == 0


def test_positive_evidence_ledger_distinguishes_lost_from_rejected_evidence():
    ir = _ir()
    ir.raw_graph.edges = [Edge(
        id="raw-route-not-aggregated",
        source="application:main",
        target="component:service",
        type=EdgeType.ROUTES_TO,
        evidence_refs=["route"],
    )]

    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    lost = [
        item for item in audit.positive_evidence_ledger
        if item.provenance == "lost_before_architecture"
    ]
    assert any(item.source_relation == "ROUTES_TO:raw-route-not-aggregated" for item in lost)
    assert audit.positive_evidence_absent_count >= 0
    assert audit.positive_evidence_produced_count == (
        audit.positive_evidence_accepted_count + audit.positive_evidence_rejected_count
    )
    assert audit.traceability is True
