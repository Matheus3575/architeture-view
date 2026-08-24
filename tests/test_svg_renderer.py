from pathlib import Path
from xml.etree import ElementTree

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.rendering import render_svg
from architecture_recovery.visualization import VisualizationReadModelBuilder


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "visualization_read_model"


def _read_model():
    return VisualizationReadModelBuilder().build(analyze_repository(FIXTURE))


def test_svg_renderer_returns_valid_self_contained_svg_with_all_elements():
    model = _read_model()
    svg = render_svg(model)
    root = ElementTree.fromstring(svg)

    assert root.tag.endswith("svg")
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    rendered_nodes = {
        element.attrib["data-read-model-id"]
        for element in root.iter()
        if "data-read-model-id" in element.attrib
        and element.attrib.get("id", "").startswith("node-")
    }
    rendered_edges = {
        element.attrib["data-read-model-id"]
        for element in root.iter()
        if "data-read-model-id" in element.attrib
        and element.attrib.get("id", "").startswith("edge-")
    }
    rendered_hypotheses = {
        element.attrib["data-read-model-id"]
        for element in root.iter()
        if "data-read-model-id" in element.attrib
        and element.attrib.get("id", "").startswith("hypothesis-")
    }
    assert rendered_nodes == {node.id for node in model.nodes}
    assert rendered_edges == {edge.id for edge in model.edges}
    assert rendered_hypotheses == {hypothesis.pattern for hypothesis in model.hypotheses}
    assert "Raw Graph" not in svg
    assert "Architecture hypotheses" in svg


def test_svg_renderer_preserves_traceability_and_status_attributes():
    model = _read_model()
    svg = render_svg(model)

    assert 'data-status="inferred"' in svg or 'data-status="observed"' in svg
    assert 'data-evidence-refs="' in svg
    assert 'data-origin-ref="' in svg
    assert "ROUTER_INCLUSION" in svg
    assert "ROUTES_TO" in svg


def test_svg_renderer_is_deterministic():
    model = _read_model()
    assert render_svg(model) == render_svg(model)


def test_svg_renderer_rejects_orphan_edges():
    model = _read_model()
    broken = model.model_copy(update={
        "edges": [
            *model.edges,
            model.edges[0].model_copy(update={"id": "orphan-edge", "target": "missing"}),
        ]
    })
    try:
        render_svg(broken)
    except ValueError as exc:
        assert "orphan" in str(exc).lower() or "does not exist" in str(exc)
    else:
        raise AssertionError("renderer accepted an orphan edge")


def test_svg_renderer_uses_semantic_group_order_and_explicit_layers():
    model = _read_model()
    svg = render_svg(model)
    root = ElementTree.fromstring(svg)
    groups = [
        element.attrib["data-layout-group"]
        for element in root.iter()
        if element.attrib.get("data-layout-group")
    ]

    assert groups[:6] == [
        "presentation",
        "application",
        "domain",
        "persistence",
        "infrastructure",
        "external",
    ]


def test_svg_renderer_distinguishes_relation_classes_and_routes():
    model = _read_model()
    svg = render_svg(model)
    root = ElementTree.fromstring(svg)

    relation_classes = {
        element.attrib["data-kind"]: element.attrib["data-relation-class"]
        for element in root.iter()
        if element.attrib.get("data-kind") in {"CONTAINS", "ROUTES_TO", "DEPLOYS"}
    }

    assert relation_classes["CONTAINS"] == "structural"
    assert relation_classes["ROUTES_TO"] == "architectural"
    assert relation_classes["DEPLOYS"] == "architectural"
    assert all(
        element.find("{http://www.w3.org/2000/svg}path") is not None
        for element in root.iter()
        if element.attrib.get("id", "").startswith("edge-")
    )


def test_svg_renderer_exposes_inspection_metadata_and_hypothesis_links():
    model = _read_model()
    hypothesis = next(item for item in model.hypotheses if item.pattern == "mvc")
    node = model.nodes[0].model_copy(
        update={"evidence_refs": [hypothesis.evidence_refs[0]]}
    )
    edge = model.edges[0].model_copy(
        update={"evidence_refs": [hypothesis.evidence_refs[0]]}
    )
    inspected = model.model_copy(update={"nodes": [node, *model.nodes[1:],], "edges": [edge, *model.edges[1:]]})
    root = ElementTree.fromstring(render_svg(inspected))

    rendered_node = next(
        element for element in root.iter()
        if element.attrib.get("data-read-model-id") == node.id
    )
    rendered_edge = next(
        element for element in root.iter()
        if element.attrib.get("data-read-model-id") == edge.id
    )
    rendered_hypothesis = next(
        element for element in root.iter()
        if element.attrib.get("data-read-model-id") == "mvc"
    )

    assert rendered_node.attrib["data-label"] == node.label
    assert rendered_node.attrib["data-related-edge-ids"]
    assert rendered_node.attrib["data-hypothesis-associations"] == "mvc"
    assert rendered_edge.attrib["data-source"] == edge.source
    assert rendered_edge.attrib["data-target"] == edge.target
    assert rendered_edge.attrib["data-hypothesis-associations"] == "mvc"
    assert rendered_hypothesis.attrib["data-supporting-evidence"]
    assert rendered_hypothesis.attrib["data-contradicting-evidence"] == ""


def test_svg_renderer_keeps_unknown_nodes_identifiable():
    from architecture_recovery.ir import EvidenceStatus

    model = _read_model()
    unknown = model.nodes[0].model_copy(
        update={
            "id": "unknown:dynamic-provider",
            "kind": "unknown",
            "label": "dynamic provider",
            "role": None,
            "status": EvidenceStatus.UNKNOWN,
            "confidence": 0.0,
        }
    )
    model = model.model_copy(update={"nodes": [*model.nodes, unknown]})
    svg = render_svg(model)

    assert 'data-kind="unknown"' in svg
    assert 'data-status="unknown"' in svg
    assert "polygon" in svg
