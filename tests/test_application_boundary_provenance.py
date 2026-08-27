from __future__ import annotations

from pathlib import Path

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
from architecture_recovery.pipeline import analyze_repository
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


def _ir(nodes: list[Node], edges: list[Edge] | None = None, facts: list[FrameworkFact] | None = None) -> ArchitectureIR:
    edges = edges or []
    facts = facts or []
    evidence_ids = {
        ref
        for item in [*nodes, *edges, *facts]
        for ref in item.evidence_refs
    }
    return ArchitectureIR(
        repository=RepositoryInfo(name="provenance", path="."),
        raw_graph=RawCodeGraph(),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        framework_facts=facts,
        evidence=_evidence(sorted(evidence_ids)),
    )


def test_repository_application_aggregate_is_not_a_boundary_or_owner():
    ir = _ir(
        [
            Node(id="application:repo", type=NodeType.APPLICATION, name="repo", status="inferred", evidence_refs=["membership"], metadata={
                "raw_node_ids": ["raw:a"],
                "application_provenance": "repository_aggregate",
                "boundary_evidence_kind": "repository_membership",
            }),
            Node(id="component:a", type=NodeType.COMPONENT, name="a", evidence_refs=["component"]),
        ],
        [Edge(id="contains", source="application:repo", target="component:a", type=EdgeType.CONTAINS, evidence_refs=["membership"])],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    assert projection.context_root_ids == []
    assert "application:repo" not in projection.projected_node_ids
    assert audit.structural_ownership_rejected_count == 1
    app = next(item for item in audit.node_explanations if item.subject_id == "application:repo")
    component = next(item for item in audit.node_explanations if item.subject_id == "component:a")
    assert app.application_provenance == "repository_aggregate"
    assert app.boundary_evidence_kind == "repository_membership"
    assert component.ownership_kind == "structural_rejected"
    assert component.context_root_ids == []


def test_explicit_application_boundary_and_architectural_ownership_are_traceable():
    ir = _ir(
        [
            Node(id="application:main", type=NodeType.APPLICATION, name="main", evidence_refs=["entrypoint"], metadata={
                "application_provenance": "explicit_boundary",
                "boundary_evidence_kind": "executable_entrypoint",
                "entrypoint": True,
            }),
            Node(id="api:main", type=NodeType.API, name="main", evidence_refs=["api"]),
        ],
        [Edge(id="owns", source="application:main", target="api:main", type=EdgeType.CONTAINS, evidence_refs=["ownership"], metadata={
            "ownership_kind": "architectural",
            "architectural_ownership": True,
        })],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    app = next(item for item in audit.node_explanations if item.subject_id == "application:main")
    api = next(item for item in audit.node_explanations if item.subject_id == "api:main")

    assert projection.context_root_ids == ["application:main"]
    assert {"application:main", "api:main"} <= set(projection.projected_node_ids)
    assert audit.architectural_ownership_count == 1
    assert audit.globally_contextualized_by_ownership_count == 1
    assert app.application_provenance == "explicit_boundary"
    assert app.boundary_evidence_kind == "executable_entrypoint"
    assert app.executable_entrypoint_evidence is True
    assert api.ownership_kind == "architectural"
    assert api.ownership_source_relation == "APPLICATION_CONTEXT_OWNERSHIP"
    assert api.ownership_evidence_refs == ["ownership"]
    assert audit.traceability is True


def test_framework_application_component_can_be_a_boundary_without_promoting_repository_envelope(tmp_path: Path):
    (tmp_path / "entry.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'ok': True}\n",
        encoding="utf-8",
    )
    ir = analyze_repository(tmp_path)
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    application = next(node for node in ir.architectural_graph.nodes if node.type == NodeType.APPLICATION)
    explanation = next(item for item in audit.node_explanations if item.subject_id == application.id)
    assert application.metadata["application_provenance"] == "repository_aggregate"
    assert explanation.application_provenance == "repository_aggregate"
    assert application.id not in projection.context_root_ids
    assert projection.context_root_ids == []
    assert audit.strong_application_boundary_count == 0
    assert audit.qualified_framework_boundary_count >= 1
    assert audit.traceability is True


def test_two_explicit_applications_remain_independent_roots():
    ir = _ir([
        Node(id="application:a", type=NodeType.APPLICATION, name="a", evidence_refs=["a"], metadata={
            "application_provenance": "explicit_boundary", "boundary_evidence_kind": "entrypoint", "entrypoint": True,
        }),
        Node(id="application:b", type=NodeType.APPLICATION, name="b", evidence_refs=["b"], metadata={
            "application_provenance": "explicit_boundary", "boundary_evidence_kind": "deployment", "executable": True,
        }),
    ])
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)

    assert projection.context_root_ids == ["application:a", "application:b"]
    assert audit.strong_application_boundary_count == 2
    assert audit.observed_application_boundary_count == 2
    assert audit.inferred_application_boundary_count == 0
    assert audit.deterministic is True
    assert projection.model_dump_json() == ArchitecturalProjectionBuilder().build(ir).model_dump_json()


def test_application_framework_fact_without_boundary_does_not_create_global_root():
    ir = _ir(
        [Node(id="component:local", type=NodeType.COMPONENT, name="local", evidence_refs=["local"])],
        facts=[FrameworkFact(kind="APPLICATION", subject="component:local", attributes={"symbol": "runtime.Application"}, evidence_refs=["framework"])],
    )
    projection = ArchitecturalProjectionBuilder().build(ir)

    assert projection.context_root_ids == []
    assert "component:local" not in projection.projected_node_ids
