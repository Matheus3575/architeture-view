from pathlib import Path

from architecture_recovery.ir import (
    ArchitecturalGraph,
    ArchitectureIR,
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
from architecture_recovery.visualization import ArchitecturalProjectionBuilder, SignificanceLevel, VisualizationReadModelBuilder
from benchmarks.refinement_investigation import generate_context_fixture


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _independent_app_ir():
    evidence = [
        Evidence(
            id=name,
            source_type=EvidenceSource.AST,
            detail=name,
            source=SourceRef(path=f"{name}.py", start_line=1),
        )
        for name in ("repo", "app-a", "app-b", "boundary-a", "boundary-b")
    ]
    nodes = [
        Node(id="repository:multi", type=NodeType.REPOSITORY, name="multi"),
        Node(id="application:a", type=NodeType.APPLICATION, name="a", evidence_refs=["app-a"]),
        Node(id="application:b", type=NodeType.APPLICATION, name="b", evidence_refs=["app-b"]),
    ]
    edges = [
        Edge(
            id="repo-a",
            source="repository:multi",
            target="application:a",
            type=EdgeType.CONTAINS,
            evidence_refs=["repo"],
        ),
        Edge(
            id="repo-b",
            source="repository:multi",
            target="application:b",
            type=EdgeType.CONTAINS,
            evidence_refs=["repo"],
        ),
    ]
    facts = [
        FrameworkFact(
            kind="APPLICATION",
            subject=subject,
            attributes={"architectural_boundary": True, "entrypoint": True},
            evidence_refs=[ref],
        )
        for subject, ref in (("application:a", "boundary-a"), ("application:b", "boundary-b"))
    ]
    return ArchitectureIR(
        repository=RepositoryInfo(name="multi", path="."),
        raw_graph=RawCodeGraph(),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        framework_facts=facts,
        evidence=evidence,
    )


def test_isolated_framework_context_is_not_promoted():
    with __import__("tempfile").TemporaryDirectory() as value:
        ir = analyze_repository(generate_context_fixture(Path(value) / "neutral"))
    projection = ArchitecturalProjectionBuilder().build(ir)
    levels = {item.subject: item.significance for item in projection.significances}

    assert levels["component:support.py"] == SignificanceLevel.LOW
    assert "component:support.py" not in projection.projected_node_ids
    assert levels["component:entry.py"] == SignificanceLevel.HIGH
    assert "application:neutral" in projection.context_root_ids
    assert projection.context_root_ids == sorted(projection.context_root_ids)


def test_independent_applications_are_both_context_roots():
    projection = ArchitecturalProjectionBuilder().build(_independent_app_ir())

    assert set(projection.context_root_ids) == {"application:a", "application:b"}
    assert {"application:a", "application:b"} <= set(projection.projected_node_ids)
    assert all(
        item.significance == SignificanceLevel.HIGH
        for item in projection.significances
        if item.subject in {"application:a", "application:b"}
    )


def test_context_roots_are_traceable_in_read_model_metadata():
    model = VisualizationReadModelBuilder().build(_independent_app_ir())

    assert model.metadata["context_root_ids"] == ["application:a", "application:b"]
    assert model.metadata["context_root_count"] == 2
    assert model.metadata["projection_traceability"] is True
    assert model.metadata["projected_edge_validity"] is True
