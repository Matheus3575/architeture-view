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
