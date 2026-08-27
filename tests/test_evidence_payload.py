from xml.etree import ElementTree

from architecture_recovery.ir import (
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.rendering import render_svg
from architecture_recovery.visualization import (
    INLINE_EVIDENCE_REF_LIMIT,
    VisualizationReadModelBuilder,
    validate_visualization_read_model,
)
from architecture_recovery.visualization.projection import ArchitecturalProjectionBuilder


def _stress_ir(count: int = 1200) -> ArchitectureIR:
    refs = [f"stress-{index:04d}" for index in range(count)]
    evidence = [
        Evidence(
            id=ref,
            source_type=EvidenceSource.CALL_GRAPH,
            detail=f"synthetic observation {index}",
            source=SourceRef(path="stress_fixture.py", start_line=(index % 20) + 1),
        )
        for index, ref in enumerate(refs)
    ]
    repository = Node(
        id="repository:stress",
        type=NodeType.REPOSITORY,
        name="stress",
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=[refs[0]],
    )
    application = Node(
        id="application:stress",
        type=NodeType.APPLICATION,
        name="stress-app",
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=refs + refs[:50],
        metadata={"entrypoint": True},
    )
    boundary = Node(
        id="api:stress",
        type=NodeType.API,
        name="stress-api",
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=refs,
    )
    edge = Edge(
        id="edge:stress",
        source=application.id,
        target=boundary.id,
        type=EdgeType.DEPENDS_ON,
        evidence_refs=refs + refs[:25],
    )
    nodes = [repository, application, boundary]
    return ArchitectureIR(
        repository=RepositoryInfo(name="evidence_payload_stress", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=[edge]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=[edge]),
        evidence=evidence,
    )


def _rendered_element(svg: str, read_model_id: str):
    root = ElementTree.fromstring(svg)
    return next(
        element
        for element in root.iter()
        if element.attrib.get("data-read-model-id") == read_model_id
    )


def test_large_associations_use_one_shared_group_and_preserve_all_refs():
    ir = _stress_ir()
    model = VisualizationReadModelBuilder().build(ir)

    application = next(node for node in model.nodes if node.id == "application:stress")
    edge = next(item for item in model.edges if item.source == "application:stress")
    assert application.evidence_count == 1200
    assert edge.evidence_count == 1200
    assert application.evidence_refs == []
    assert edge.evidence_refs == []
    assert application.evidence_group_ref == edge.evidence_group_ref
    assert len(model.evidence_groups) == 1
    group = model.evidence_groups[0]
    assert group.evidence_count == 1200
    assert len(group.evidence_refs) == 1200
    assert group.summary == {"CALL_GRAPH": 1200}
    assert model.metadata["evidence_group_count"] == 1
    assert model.metadata["inline_evidence_reference_count"] < INLINE_EVIDENCE_REF_LIMIT


def test_small_associations_remain_inline_and_are_counted():
    model = VisualizationReadModelBuilder().build(_stress_ir(count=3))
    application = next(node for node in model.nodes if node.id == "application:stress")

    assert model.evidence_groups == []
    assert application.evidence_group_ref is None
    assert application.evidence_count == 3
    assert application.evidence_refs == ["stress-0000", "stress-0001", "stress-0002"]


def test_svg_payload_is_materially_smaller_without_changing_projection():
    ir = _stress_ir()
    projection_before = ArchitecturalProjectionBuilder().build(ir).model_dump(mode="json")
    model = VisualizationReadModelBuilder().build(ir)
    projection_after = ArchitecturalProjectionBuilder().build(ir).model_dump(mode="json")
    compact_svg = render_svg(model)

    full_refs = [f"stress-{index:04d}" for index in range(1200)]
    legacy = model.model_copy(update={
        "evidence_groups": [],
        "nodes": [
            node.model_copy(update={
                "evidence_refs": full_refs if node.id == "application:stress" else node.evidence_refs,
                "evidence_group_ref": None,
                "evidence_count": len(full_refs) if node.id == "application:stress" else node.evidence_count,
            })
            for node in model.nodes
        ],
        "edges": [
            edge.model_copy(update={
                "evidence_refs": full_refs if edge.id == "edge:stress" else edge.evidence_refs,
                "evidence_group_ref": None,
                "evidence_count": len(full_refs) if edge.id == "edge:stress" else edge.evidence_count,
            })
            for edge in model.edges
        ],
    })
    legacy_svg = render_svg(legacy)

    assert projection_before == projection_after
    assert len(compact_svg) < len(legacy_svg) * 0.7
    application_element = _rendered_element(compact_svg, "application:stress")
    assert application_element.attrib["data-evidence-group"] == next(node for node in model.nodes if node.id == "application:stress").evidence_group_ref
    assert application_element.attrib["data-evidence-count"] == "1200"
    assert "data-evidence-refs" not in application_element.attrib
    assert "Evidence count:" in compact_svg
    assert "Showing first " in compact_svg
    assert "slice(0, 20)" in compact_svg


def test_grouped_evidence_is_traceable_deterministic_and_does_not_mutate_ir():
    ir = _stress_ir()
    before = ir.model_dump_json()
    first = VisualizationReadModelBuilder().build(ir)
    second = VisualizationReadModelBuilder().build(ir)

    assert first.model_dump_json() == second.model_dump_json()
    assert ir.model_dump_json() == before
    report = validate_visualization_read_model(first, {item.id for item in ir.evidence})
    assert report.valid
    assert all(ref in {item.id for item in ir.evidence} for group in first.evidence_groups for ref in group.evidence_refs)
    assert all(edge.source in {node.id for node in first.nodes} and edge.target in {node.id for node in first.nodes} for edge in first.edges)


def test_unknown_visual_elements_keep_compact_contract():
    model = VisualizationReadModelBuilder().build(_stress_ir(count=1))
    unknown = next((node for node in model.nodes if node.status.value == "unknown"), None)
    if unknown is not None:
        assert unknown.evidence_count == len(unknown.evidence_refs)
        assert unknown.evidence_group_ref is None