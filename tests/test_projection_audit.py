from architecture_recovery.ir import (
    ArchitectureAnalysis,
    ArchitectureHypothesis,
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
from architecture_recovery.visualization import ArchitecturalProjectionBuilder, audit_projection


def _evidence(name: str) -> Evidence:
    return Evidence(
        id=name,
        source_type=EvidenceSource.AST,
        detail=name,
        source=SourceRef(path="neutral.py", start_line=1),
    )


def _audit_fixture() -> ArchitectureIR:
    nodes = [
        Node(id="application:a", type=NodeType.APPLICATION, name="a", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["root-a"]),
        Node(id="application:b", type=NodeType.APPLICATION, name="b", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["root-b"]),
        Node(id="application:c", type=NodeType.APPLICATION, name="c", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["root-c"]),
        Node(id="component:core", type=NodeType.COMPONENT, name="core", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["core"]),
    ]
    edges = [
        Edge(id="route-core", source="application:a", target="component:core", type=EdgeType.ROUTES_TO, evidence_refs=["route"]),
        Edge(id="depends-core", source="application:a", target="component:core", type=EdgeType.DEPENDS_ON, evidence_refs=["depends-core"]),
        Edge(id="query-db", source="component:core", target="database:main", type=EdgeType.QUERIES, evidence_refs=["query"]),
        Edge(id="depends-db", source="component:core", target="database:main", type=EdgeType.DEPENDS_ON, evidence_refs=["depends-db"]),
        Edge(id="depends-cross", source="application:a", target="application:b", type=EdgeType.DEPENDS_ON, evidence_refs=["depends-cross"]),
        Edge(id="connect-cross", source="application:a", target="application:b", type=EdgeType.CONNECTS_TO, evidence_refs=["connect-cross"]),
        Edge(id="depends-only", source="application:b", target="application:a", type=EdgeType.DEPENDS_ON, evidence_refs=["depends-only"]),
        Edge(id="depends-cross-only", source="application:a", target="application:c", type=EdgeType.DEPENDS_ON, evidence_refs=["depends-cross-only"]),
    ]
    database = InfrastructureResource(id="database:main", name="main", kind="DATABASE", evidence_refs=["database"])
    relation = InfrastructureRelation(id="relation-query-db", source="component:core", target="database:main", type="QUERIES", evidence_refs=["query"])
    all_ids = {
        "root-a", "root-b", "root-c", "core", "route", "depends-core", "query", "depends-db",
        "depends-cross", "connect-cross", "depends-only", "depends-cross-only", "database",
    }
    return ArchitectureIR(
        repository=RepositoryInfo(name="neutral-audit", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=[]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        framework_facts=[
            FrameworkFact(kind="APPLICATION", subject="application:a", attributes={"architectural_boundary": True}, evidence_refs=["root-a"]),
            FrameworkFact(kind="APPLICATION", subject="application:b", attributes={"architectural_boundary": True}, evidence_refs=["root-b"]),
            FrameworkFact(kind="APPLICATION", subject="application:c", attributes={"architectural_boundary": True}, evidence_refs=["root-c"]),
        ],
        infrastructure_resources=[database],
        infrastructure_relations=[relation],
        architecture=ArchitectureAnalysis(hypotheses=[
            ArchitectureHypothesis(pattern="microservices", supporting_evidence=["root-a", "connect-cross"], evidence_refs=["root-a", "connect-cross"]),
        ]),
        evidence=[_evidence(name) for name in sorted(all_ids)],
    )


def test_projection_audit_explains_roots_and_relation_categories():
    ir = _audit_fixture()
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    core = next(item for item in audit.node_explanations if item.subject_id == "component:core")
    assert core.projection_eligible is True
    assert set(core.context_root_ids) == {"application:a", "application:b"}
    assert core.globally_contextualized is True
    assert any(link.relation_kind == "ROUTES_TO" for link in core.context_chain)

    shadowed = [item for item in audit.relation_explanations if item.depends_on_category == "SHADOWED_BY_STRONGER_RELATION"]
    only = [item for item in audit.relation_explanations if item.depends_on_category == "ONLY_RELATION"]
    assert shadowed
    assert any("QUERIES" in item.stronger_relation_kinds for item in shadowed)
    assert only
    assert audit.depends_on_cross_context_count >= 1
    assert audit.depends_on_same_context_count >= 1
    assert audit.traceability is True
    assert audit.evidence_coverage == 1.0
    assert audit.hypothesis_contextual_support_count >= 1


def test_projection_audit_is_deterministic_and_does_not_mutate_inputs():
    ir = _audit_fixture()
    projection = ArchitecturalProjectionBuilder().build(ir)
    ir_before = ir.model_dump_json()
    projection_before = projection.model_dump_json()

    first = audit_projection(ir, projection)
    second = audit_projection(ir, projection)

    assert first.model_dump_json() == second.model_dump_json()
    assert ir.model_dump_json() == ir_before
    assert projection.model_dump_json() == projection_before
