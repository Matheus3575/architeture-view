from __future__ import annotations

from architecture_recovery.ir import (
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
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
    audit_projection,
)


def _evidence(ids: list[str]) -> list[Evidence]:
    return [
        Evidence(
            id=item,
            source_type=EvidenceSource.AST,
            detail=item,
            source=SourceRef(path="fixture.py", start_line=1),
        )
        for item in ids
    ]


def _ir(
    name: str,
    nodes: list[Node],
    edges: list[Edge] | None = None,
    resources: list[InfrastructureResource] | None = None,
    relations: list[InfrastructureRelation] | None = None,
    evidence_ids: list[str] | None = None,
) -> ArchitectureIR:
    edges = edges or []
    resources = resources or []
    relations = relations or []
    ids = set(evidence_ids or [])
    ids.update(ref for node in nodes for ref in node.evidence_refs)
    ids.update(ref for edge in edges for ref in edge.evidence_refs)
    ids.update(ref for item in resources for ref in item.evidence_refs)
    ids.update(ref for item in relations for ref in item.evidence_refs)
    return ArchitectureIR(
        repository=RepositoryInfo(name=name, path=f"/{name}"),
        raw_graph=RawCodeGraph(nodes=nodes, edges=[]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        infrastructure_resources=resources,
        infrastructure_relations=relations,
        evidence=_evidence(sorted(ids)),
    )


def test_repository_envelope_is_navigation_not_strong_context_root():
    ir = _ir(
        "envelope",
        [Node(id="repository:envelope", type=NodeType.REPOSITORY, name="envelope", evidence_refs=["repo"])],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)

    assert projection.context_root_ids == []
    assert projection.navigation_root_ids == ["repository:envelope"]
    audit = audit_projection(ir, projection)
    assert audit.strong_context_root_count == 0
    assert audit.weak_navigation_root_count == 1


def test_multiple_observed_applications_remain_strong_roots():
    ir = _ir(
        "apps",
        [
            Node(id="repository:apps", type=NodeType.REPOSITORY, name="apps"),
            Node(id="application:a", type=NodeType.APPLICATION, name="a", evidence_refs=["a"]),
            Node(id="application:b", type=NodeType.APPLICATION, name="b", evidence_refs=["b"]),
        ],
        evidence_ids=["a", "b"],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    assert set(projection.context_root_ids) == {"application:a", "application:b"}
    assert projection.context_root_strengths == {"application:a": "strong", "application:b": "strong"}
    assert audit.strong_context_root_count == 2


def test_generic_depends_on_chain_does_not_establish_context_membership():
    ir = _ir(
        "weak-chain",
        [
            Node(id="application:root", type=NodeType.APPLICATION, name="root", evidence_refs=["root"]),
            Node(id="api:entry", type=NodeType.API, name="entry", evidence_refs=["entry"]),
            Node(id="infrastructure:local", type=NodeType.INFRASTRUCTURE, name="local", evidence_refs=["local"]),
        ],
        [
            Edge(id="weak-root-entry", source="application:root", target="api:entry", type=EdgeType.DEPENDS_ON, evidence_refs=["weak-1"]),
            Edge(id="weak-entry-local", source="api:entry", target="infrastructure:local", type=EdgeType.DEPENDS_ON, evidence_refs=["weak-2"]),
        ],
        evidence_ids=["root", "entry", "local", "weak-1", "weak-2"],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    report = {item.subject_id: item for item in audit.node_explanations}

    assert "api:entry" in projection.projected_node_ids
    assert "infrastructure:local" not in projection.projected_node_ids
    assert report["api:entry"].context_root_ids == []
    assert report["infrastructure:local"].context_root_ids == []
    assert report["api:entry"].globally_contextualized is False
    assert report["infrastructure:local"].globally_contextualized is False
    assert audit.nodes_reachable_only_by_weak_relation >= 1
    assert audit.propagation_relation_kind_counts.get("DEPENDS_ON:does_not_propagate_context", 0) >= 1


def test_two_bounded_semantic_hops_propagate_context():
    ir = _ir(
        "strong-chain",
        [
            Node(id="application:root", type=NodeType.APPLICATION, name="root", evidence_refs=["root"]),
            Node(id="component:api", type=NodeType.COMPONENT, name="api"),
            Node(id="component:persistence", type=NodeType.COMPONENT, name="persistence"),
        ],
        [
            Edge(id="route", source="application:root", target="component:api", type=EdgeType.ROUTES_TO, evidence_refs=["route"]),
            Edge(id="query", source="component:api", target="component:persistence", type=EdgeType.QUERIES, evidence_refs=["query"]),
        ],
        evidence_ids=["root", "route", "query"],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    persistence = next(item for item in audit.node_explanations if item.subject_id == "component:persistence")

    assert {"component:api", "component:persistence"} <= set(projection.projected_node_ids)
    assert persistence.context_root_ids == ["application:root"]
    assert persistence.context_membership_source.startswith("propagated:")
    assert persistence.context_membership_strength == "strong"
    assert audit.nodes_contextualized_by_strong_relation >= 2


def test_shared_broker_has_cross_root_context_membership():
    ir = _ir(
        "shared-broker",
        [
            Node(id="application:a", type=NodeType.APPLICATION, name="a", evidence_refs=["a"]),
            Node(id="application:b", type=NodeType.APPLICATION, name="b", evidence_refs=["b"]),
        ],
        resources=[
            InfrastructureResource(id="broker:shared", name="shared", kind="MESSAGE_BROKER", evidence_refs=["broker"]),
        ],
        relations=[
            InfrastructureRelation(id="connect-a", source="application:a", target="broker:shared", type="CONNECTS_TO", evidence_refs=["a-broker"]),
            InfrastructureRelation(id="connect-b", source="application:b", target="broker:shared", type="CONNECTS_TO", evidence_refs=["b-broker"]),
        ],
        evidence_ids=["a", "b", "broker", "a-broker", "b-broker"],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    broker = next(item for item in audit.node_explanations if item.subject_id == "broker:shared")

    assert "broker:shared" in projection.projected_node_ids
    assert set(broker.context_root_ids) == {"application:a", "application:b"}
    assert audit.depends_on_cross_context_count == 0
    assert audit.strong_context_root_count == 2


def test_weak_evidence_volume_is_saturated_without_high_significance():
    weak_edges = [
        Edge(
            id=f"weak-{index}",
            source="api:entry",
            target="component:utility",
            type=EdgeType.DEPENDS_ON,
            evidence_refs=[f"weak-evidence-{index}"],
        )
        for index in range(1000)
    ]
    ir = _ir(
        "weak-volume",
        [
            Node(id="application:root", type=NodeType.APPLICATION, name="root", evidence_refs=["root"]),
            Node(id="api:entry", type=NodeType.API, name="entry", evidence_refs=["entry"]),
            Node(id="component:utility", type=NodeType.COMPONENT, name="utility"),
        ],
        [
            Edge(id="route", source="application:root", target="api:entry", type=EdgeType.ROUTES_TO, evidence_refs=["route"]),
            *weak_edges,
        ],
        evidence_ids=["root", "entry", "route", *[f"weak-evidence-{index}" for index in range(1000)]],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    utility = next(item for item in projection.significances if item.subject == "component:utility")

    assert utility.significance.value in {"low", "unknown"}
    assert utility.score <= 0.12
    assert projection.weak_evidence_saturation_count >= 1


def test_context_metadata_and_read_model_remain_deterministic():
    ir = _ir(
        "deterministic",
        [
            Node(id="repository:deterministic", type=NodeType.REPOSITORY, name="deterministic", evidence_refs=["repo"]),
            Node(id="application:root", type=NodeType.APPLICATION, name="root", evidence_refs=["root"]),
        ],
        evidence_ids=["repo", "root"],
    )
    builder = ArchitecturalProjectionBuilder()
    first = builder.build(ir)
    second = builder.build(ir)
    assert first.model_dump_json() == second.model_dump_json()

    model = VisualizationReadModelBuilder().build(ir)
    assert model.metadata["context_root_strengths"] == {"application:root": "strong"}
    assert model.metadata["navigation_root_ids"] == ["repository:deterministic"]


def test_isolated_infrastructure_resource_remains_detailed_only():
    ir = _ir(
        "isolated-resource",
        [Node(id="application:aux", type=NodeType.APPLICATION, name="aux", evidence_refs=["aux"])],
        resources=[
            InfrastructureResource(
                id="database:isolated",
                name="isolated",
                kind="DATABASE",
                evidence_refs=["database"],
            )
        ],
        evidence_ids=["aux", "database"],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)

    assert "database:isolated" not in projection.projected_node_ids
    assert next(item for item in projection.significances if item.subject == "database:isolated").significance.value == "low"
