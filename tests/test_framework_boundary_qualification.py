from __future__ import annotations

from architecture_recovery.ir import (
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    FrameworkFact,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceRef,
)
from architecture_recovery.visualization import ArchitecturalProjectionBuilder, audit_projection


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


def _ir(nodes, edges=None, raw_edges=None, facts=None, evidence_ids=None):
    edges = edges or []
    raw_edges = raw_edges or []
    facts = facts or []
    refs = set(evidence_ids or [])
    refs.update(ref for item in [*nodes, *edges, *raw_edges, *facts] for ref in item.evidence_refs)
    return ArchitectureIR(
        repository=RepositoryInfo(name="framework-qualification", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=raw_edges),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        framework_facts=facts,
        evidence=_evidence(sorted(refs)),
    )


def test_framework_fact_volume_without_owned_application_boundary_is_rejected():
    nodes = [Node(id="component:local", type=NodeType.COMPONENT, name="local", evidence_refs=["component"])]
    facts = [
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject="component:local",
            attributes={"path": f"/item/{index}"},
            evidence_refs=[f"endpoint-{index}"],
        )
        for index in range(300)
    ]
    ir = _ir(nodes, facts=facts, evidence_ids=["component", *[f"endpoint-{index}" for index in range(300)]])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    item = next(item for item in audit.node_explanations if item.subject_id == "component:local")

    assert projection.context_root_ids == []
    assert item.framework_boundary_qualification == "REJECTED"
    assert item.framework_fact_ownership == "RELATED_FRAMEWORK_BOUNDARY"
    assert audit.rejected_framework_boundary_count >= 1


def test_owned_declarative_framework_application_is_a_qualified_root():
    nodes = [
        Node(
            id="component:api",
            type=NodeType.COMPONENT,
            name="api",
            evidence_refs=["component"],
            metadata={"raw_node_ids": ["module:api"]},
        )
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="app",
            attributes={"application": "app", "module": "api", "architectural_boundary": True},
            evidence_refs=["application"],
        ),
        FrameworkFact(
            kind="ROUTER",
            subject="router",
            attributes={"router": "router", "module": "api"},
            evidence_refs=["router"],
        ),
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject="handler",
            attributes={"owner": "app", "module": "api", "path": "/items"},
            evidence_refs=["endpoint"],
        ),
    ]
    ir = _ir(nodes, facts=facts, evidence_ids=["component", "application", "router", "endpoint"])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    item = next(item for item in audit.node_explanations if item.subject_id == "component:api")

    assert projection.context_root_ids == ["component:api"]
    assert item.framework_boundary_qualification == "QUALIFIED_GLOBAL"
    assert item.framework_fact_ownership == "OWNED_APPLICATION_BOUNDARY"
    assert "application_router_endpoint_association" in item.framework_boundary_evidence
    assert audit.owned_framework_application_count == 1


def test_supporting_relation_does_not_establish_context_membership():
    nodes = [
        Node(id="application:root", type=NodeType.APPLICATION, name="root", evidence_refs=["root"]),
        Node(id="api:entry", type=NodeType.API, name="entry", evidence_refs=["api"]),
        Node(id="raw:root", type=NodeType.MODULE, name="root"),
        Node(id="raw:entry", type=NodeType.MODULE, name="entry"),
    ]
    raw = Edge(id="raw-call", source="raw:root", target="raw:entry", type=EdgeType.CALLS, evidence_refs=["call"])
    edge = Edge(
        id="call",
        source="application:root",
        target="api:entry",
        type=EdgeType.CALLS,
        raw_edge_ids=["raw-call"],
        evidence_refs=["call"],
    )
    ir = _ir(nodes, [edge], [raw], evidence_ids=["root", "api", "call"])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    api = next(item for item in audit.node_explanations if item.subject_id == "api:entry")

    assert "api:entry" in projection.projected_node_ids
    assert api.context_root_ids == []
    assert api.globally_contextualized is False
    assert audit.membership_established_by_relation_kind == {}
    assert audit.supporting_only_global_membership_count == 0
    assert audit.propagation_relation_kind_counts.get("CALLS:supports_context", 0) >= 1


def test_supporting_dependency_only_enriches_existing_membership():
    nodes = [
        Node(id="application:root", type=NodeType.APPLICATION, name="root", evidence_refs=["root"]),
        Node(id="api:entry", type=NodeType.API, name="entry", evidence_refs=["api"]),
    ]
    edges = [
        Edge(id="route", source="application:root", target="api:entry", type=EdgeType.ROUTES_TO, evidence_refs=["route"]),
        Edge(id="depends", source="application:root", target="api:entry", type=EdgeType.DEPENDS_ON, raw_edge_ids=["raw-call"], evidence_refs=["depends"]),
    ]
    raw = Edge(id="raw-call", source="raw:root", target="raw:entry", type=EdgeType.CALLS, evidence_refs=["raw-call"])
    ir = _ir(nodes, edges, [raw], evidence_ids=["root", "api", "route", "depends", "raw-call"])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    api = next(item for item in audit.node_explanations if item.subject_id == "api:entry")

    assert api.context_root_ids == ["application:root"]
    assert audit.membership_established_by_relation_kind["ROUTES_TO"] >= 1
    assert audit.membership_supported_by_relation_kind["DEPENDS_ON"] >= 1
    assert audit.supporting_only_global_membership_count == 0


def test_two_explicit_framework_boundaries_remain_independent_roots():
    nodes = [
        Node(id="component:alpha", type=NodeType.COMPONENT, name="alpha", metadata={"raw_node_ids": ["module:alpha"]}),
        Node(id="component:beta", type=NodeType.COMPONENT, name="beta", metadata={"raw_node_ids": ["module:beta"]}),
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="alpha_app",
            attributes={"application": "alpha_app", "module": "alpha", "architectural_boundary": True},
            evidence_refs=["alpha-app"],
        ),
        FrameworkFact(
            kind="APPLICATION",
            subject="beta_app",
            attributes={"application": "beta_app", "module": "beta", "architectural_boundary": True},
            evidence_refs=["beta-app"],
        ),
    ]
    ir = _ir(nodes, facts=facts, evidence_ids=["alpha-app", "beta-app"])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    assert projection.context_root_ids == ["component:alpha", "component:beta"]
    assert audit.framework_context_root_count == 2
    assert audit.qualified_framework_boundary_count == 2
    assert audit.traceability is True


def test_same_module_framework_facts_without_explicit_association_are_not_ownership():
    nodes = [
        Node(
            id="component:co_located",
            type=NodeType.COMPONENT,
            name="co_located",
            metadata={"raw_node_ids": ["module:api"]},
        )
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="app",
            attributes={"application": "app", "module": "api"},
            evidence_refs=["application"],
        ),
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject="handler",
            attributes={"path": "/items", "module": "api"},
            evidence_refs=["endpoint"],
        ),
    ]
    ir = _ir(nodes, facts=facts, evidence_ids=["application", "endpoint"])

    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    item = next(item for item in audit.node_explanations if item.subject_id == "component:co_located")

    assert projection.context_root_ids == []
    assert item.framework_fact_ownership == "LOCAL_FRAMEWORK_USAGE"
    assert item.framework_boundary_qualification == "REJECTED"
    assert item.framework_ownership_relations == []
    assert audit.qualified_local_framework_boundary_count == 0
    assert audit.framework_ownership_lost_count == 0


def test_framework_ownership_provenance_records_explicit_endpoint_association():
    nodes = [
        Node(
            id="component:api",
            type=NodeType.COMPONENT,
            name="api",
            metadata={"raw_node_ids": ["module:api"]},
        )
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="app",
            attributes={"application": "app", "module": "api"},
            evidence_refs=["application"],
        ),
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject="component:api",
            attributes={"owner": "app", "module": "different", "path": "/items"},
            evidence_refs=["endpoint"],
        ),
    ]
    ir = _ir(nodes, facts=facts, evidence_ids=["application", "endpoint"])

    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    item = next(item for item in audit.node_explanations if item.subject_id == "component:api")

    assert item.framework_fact_ownership == "OWNED_APPLICATION_BOUNDARY"
    assert item.framework_ownership_relations == ["HTTP_ENDPOINT_OWNER"]
    assert item.framework_ownership_evidence_refs == ["application", "endpoint"]
    assert audit.framework_ownership_evidence_count == 2

def test_framework_ownership_provenance_is_exposed_in_compact_audit_report():
    nodes = [
        Node(
            id="component:api",
            type=NodeType.COMPONENT,
            name="api",
            metadata={"raw_node_ids": ["module:api"]},
        )
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject="app",
            attributes={"application": "app", "module": "api"},
            evidence_refs=["application"],
        ),
        FrameworkFact(
            kind="HTTP_ENDPOINT",
            subject="component:api",
            attributes={"owner": "app", "module": "other", "path": "/items"},
            evidence_refs=["endpoint"],
        ),
    ]
    ir = _ir(nodes, facts=facts, evidence_ids=["application", "endpoint"])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    from architecture_recovery.visualization import build_projection_audit_report, render_projection_audit_json

    report = build_projection_audit_report(ir, projection, audit)
    payload = render_projection_audit_json(report)

    node = next(item for item in report["framework_boundary_nodes"] if item["subject_id"] == "component:api")
    assert node["framework_ownership_relations"] == ["HTTP_ENDPOINT_OWNER"]
    assert node["framework_ownership_evidence"]["evidence_count"] == 2
    assert '"framework_ownership_relations"' in payload
    assert report["summary"]["framework_ownership_evidence_count"] == 2