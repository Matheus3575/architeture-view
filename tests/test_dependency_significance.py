from __future__ import annotations

from architecture_recovery.ir import (
    ArchitectureAnalysis,
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
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
from architecture_recovery.visualization import (
    SignificanceLevel,
    VisualizationReadModelBuilder,
)


def _evidence(identifier: str) -> Evidence:
    return Evidence(
        id=identifier,
        source_type=EvidenceSource.CALL_GRAPH,
        detail=identifier,
        source=SourceRef(path="neutral.py", start_line=1, end_line=1),
    )


def _node(identifier: str, node_type: NodeType, evidence: str | None = None, **metadata) -> Node:
    return Node(
        id=identifier,
        type=node_type,
        name=identifier,
        origin=SourceOrigin.THIRD_PARTY if node_type == NodeType.EXTERNAL_DEPENDENCY else SourceOrigin.FIRST_PARTY,
        evidence_refs=[evidence] if evidence else [],
        metadata=metadata,
    )


def _edge(identifier: str, source: str, target: str, edge_type: EdgeType, evidence: str) -> Edge:
    return Edge(
        id=identifier,
        source=source,
        target=target,
        type=edge_type,
        evidence_refs=[evidence],
    )


def _ir(
    name: str,
    nodes: list[Node],
    edges: list[Edge],
    facts: list[FrameworkFact],
    resources: list[InfrastructureResource] | None = None,
    relations: list[InfrastructureRelation] | None = None,
) -> ArchitectureIR:
    evidence_ids = {
        ref
        for node in nodes
        for ref in node.evidence_refs
    } | {
        ref
        for edge in edges
        for ref in edge.evidence_refs
    } | {
        ref
        for fact in facts
        for ref in fact.evidence_refs
    } | {
        ref
        for resource in resources or []
        for ref in resource.evidence_refs
    } | {
        ref
        for relation in relations or []
        for ref in relation.evidence_refs
    }
    return ArchitectureIR(
        repository=RepositoryInfo(name=name, path=f"/{name}"),
        raw_graph=RawCodeGraph(nodes=list(nodes), edges=[]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        architecture=ArchitectureAnalysis(),
        evidence=[_evidence(identifier) for identifier in sorted(evidence_ids)],
        framework_facts=facts,
        infrastructure_resources=resources or [],
        infrastructure_relations=relations or [],
    )


def alpha_dependency_fixture() -> ArchitectureIR:
    nodes = [
        _node("application:alpha", NodeType.APPLICATION, "alpha-app"),
        _node("component:domain", NodeType.COMPONENT, "alpha-domain"),
        _node("component:auxiliary", NodeType.COMPONENT, "alpha-aux"),
        _node("component:utility", NodeType.COMPONENT, "alpha-utility"),
        _node("external:framework", NodeType.EXTERNAL_DEPENDENCY, "alpha-framework", external_package="framework"),
        _node("external:framework_internal", NodeType.EXTERNAL_DEPENDENCY, "alpha-internal", external_package="framework.internal"),
        _node("external:orm", NodeType.EXTERNAL_DEPENDENCY, "alpha-orm", external_package="orm", architectural_role="persistence_technology"),
        _node("external:driver", NodeType.EXTERNAL_DEPENDENCY, "alpha-driver", external_package="driver", architectural_role="database_driver"),
        _node("external:messaging", NodeType.EXTERNAL_DEPENDENCY, "alpha-messaging", external_package="messaging", architectural_role="message_transport"),
        _node("external:client", NodeType.EXTERNAL_DEPENDENCY, "alpha-client", external_package="client", architectural_role="external_service_client"),
        _node("external:general", NodeType.EXTERNAL_DEPENDENCY, "alpha-general", external_package="general"),
        _node("external:ambiguous", NodeType.EXTERNAL_DEPENDENCY),
    ]
    edges = [
        _edge("alpha-contains", "application:alpha", "component:domain", EdgeType.CONTAINS, "alpha-app"),
        _edge("alpha-query", "component:domain", "external:orm", EdgeType.QUERIES, "alpha-query"),
        _edge("alpha-messaging", "application:alpha", "external:messaging", EdgeType.CONNECTS_TO, "alpha-messaging"),
        _edge("alpha-client", "component:domain", "external:client", EdgeType.CONNECTS_TO, "alpha-client"),
        _edge("alpha-framework", "application:alpha", "external:framework", EdgeType.DEPENDS_ON, "alpha-framework"),
        _edge("alpha-internal", "application:alpha", "external:framework_internal", EdgeType.DEPENDS_ON, "alpha-internal"),
        _edge("alpha-driver", "component:domain", "external:driver", EdgeType.DEPENDS_ON, "alpha-driver"),
        _edge("alpha-general", "application:alpha", "external:general", EdgeType.DEPENDS_ON, "alpha-general"),
        _edge("alpha-general-domain", "component:domain", "external:general", EdgeType.DEPENDS_ON, "alpha-general"),
        *[
            _edge(f"alpha-utility-{index}", "component:utility", "external:general", EdgeType.DEPENDS_ON, "alpha-general")
            for index in range(5)
        ],
        _edge("alpha-aux", "component:auxiliary", "external:framework_internal", EdgeType.DEPENDS_ON, "alpha-aux"),
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="application:alpha",
            attributes={"symbol": "framework.Core"},
            evidence_refs=["alpha-framework"],
        ),
        FrameworkFact(
            kind="APPLICATION",
            subject="component:auxiliary",
            attributes={"symbol": "framework.Core"},
            evidence_refs=["alpha-aux"],
        ),
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject="aux.endpoint",
            attributes={"owner": "component:auxiliary", "path": "/test-only"},
            evidence_refs=["alpha-aux"],
        ),
    ]
    return _ir("dependency-alpha", nodes, edges, facts)


def beta_dependency_fixture() -> ArchitectureIR:
    nodes = [
        _node("application:worker", NodeType.APPLICATION, "beta-worker"),
        _node("application:scheduler", NodeType.APPLICATION, "beta-scheduler"),
        _node("external:messaging", NodeType.EXTERNAL_DEPENDENCY, "beta-messaging", external_package="messaging", architectural_role="message_transport"),
        _node("external:utility", NodeType.EXTERNAL_DEPENDENCY, "beta-utility", external_package="utility"),
    ]
    resources = [
        InfrastructureResource(id="broker:beta", name="broker", kind="MESSAGE_BROKER", evidence_refs=["beta-broker"]),
        InfrastructureResource(id="cache:beta", name="cache", kind="CACHE", evidence_refs=["beta-cache"]),
    ]
    relations = [
        InfrastructureRelation(
            id="beta-worker-broker",
            source="application:worker",
            target="broker:beta",
            type="CONNECTS_TO",
            evidence_refs=["beta-broker"],
        ),
        InfrastructureRelation(
            id="beta-scheduler-cache",
            source="application:scheduler",
            target="cache:beta",
            type="CONNECTS_TO",
            evidence_refs=["beta-cache"],
        ),
    ]
    edges = [
        _edge("beta-message", "application:worker", "external:messaging", EdgeType.CONNECTS_TO, "beta-message"),
        _edge("beta-utility", "application:worker", "external:utility", EdgeType.DEPENDS_ON, "beta-utility"),
    ]
    return _ir("dependency-beta", nodes, edges, [] , resources, relations)


def _significance(model):
    return {item.subject: item for item in model.architectural_significance}


def test_alpha_promotes_roles_but_not_frequency_or_generic_depends_on():
    model = VisualizationReadModelBuilder().build(alpha_dependency_fixture())
    significance = _significance(model)
    projected = {node.id for node in model.nodes}

    assert significance["external:framework"].significance == SignificanceLevel.HIGH
    assert significance["external:framework"].role == "APPLICATION_FRAMEWORK"
    assert significance["external:orm"].significance == SignificanceLevel.HIGH
    assert significance["external:orm"].role == "PERSISTENCE_TECHNOLOGY"
    assert significance["external:messaging"].significance == SignificanceLevel.MEDIUM
    assert significance["external:client"].significance == SignificanceLevel.MEDIUM
    assert significance["external:driver"].significance == SignificanceLevel.LOW
    assert significance["external:framework_internal"].significance == SignificanceLevel.LOW
    assert significance["external:general"].significance == SignificanceLevel.LOW
    assert significance["external:ambiguous"].significance == SignificanceLevel.UNKNOWN
    assert "external:framework_internal" not in projected
    assert "external:driver" not in projected
    assert "external:general" not in projected
    assert model.metadata["projected_edge_validity"] is True
    assert model.metadata["projection_traceability"] is True


def test_alpha_auxiliary_framework_and_endpoint_context_does_not_promote_component():
    model = VisualizationReadModelBuilder().build(alpha_dependency_fixture())
    significance = _significance(model)

    assert significance["component:auxiliary"].significance == SignificanceLevel.LOW
    assert "component:auxiliary" not in {node.id for node in model.nodes}
    assert model.metadata["endpoint_high_level_count"] == 0
    assert model.metadata["endpoint_detail_count"] == 1


def test_beta_generalizes_message_and_infrastructure_roles():
    model = VisualizationReadModelBuilder().build(beta_dependency_fixture())
    projected = {node.id for node in model.nodes}
    significance = _significance(model)

    assert {"application:worker", "application:scheduler", "broker:beta", "cache:beta"} <= projected
    assert "external:messaging" in projected
    assert significance["external:messaging"].role == "MESSAGE_TRANSPORT"
    assert "external:utility" not in projected
    assert significance["external:utility"].significance == SignificanceLevel.LOW
    assert model.metadata["projected_edge_validity"] is True


def test_generic_depends_on_never_promotes_dependency_or_creates_edge():
    model = VisualizationReadModelBuilder().build(alpha_dependency_fixture())
    projected = {node.id for node in model.nodes}

    assert not {"external:driver", "external:general", "external:framework_internal"} & projected
    assert not any(
        edge.target in {"external:driver", "external:general", "external:framework_internal"}
        for edge in model.edges
    )
    assert any(
        detail.subject == "external:driver" and detail.kind == "projection_detail"
        for detail in model.semantic_details
    )


def test_dependency_roles_metrics_and_determinism_are_traceable():
    builder = VisualizationReadModelBuilder()
    first = builder.build(alpha_dependency_fixture())
    second = builder.build(alpha_dependency_fixture())

    assert first.model_dump_json() == second.model_dump_json()
    assert first.metadata["dependency_role_counts"]["APPLICATION_FRAMEWORK"] == 1
    assert first.metadata["dependency_role_counts"]["PERSISTENCE_TECHNOLOGY"] == 2
    assert first.metadata["dependency_role_counts"]["GENERAL_LIBRARY"] >= 3
    evidence_ids = {item.id for item in first.evidence}
    assert all(
        ref in evidence_ids
        for item in [*first.nodes, *first.edges, *first.semantic_details, *first.architectural_significance]
        for ref in item.evidence_refs
    )
