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


def test_svg_renderer_embeds_interaction_indices_and_inspection_panel():
    model = _read_model()
    svg = render_svg(model)

    assert '<script type="application/ecmascript">' in svg
    assert "const DATA =" in svg
    assert 'id="inspection-panel"' in svg
    assert "select(kind, id)" in svg
    assert "classList.toggle" in svg
    assert "data-selection-kind=\"node\"" in svg
    assert "data-selection-kind=\"edge\"" in svg
    assert "data-selection-kind=\"hypothesis\"" in svg
    for item in [*model.nodes, *model.edges, *model.evidence]:
        assert item.id in svg
    for hypothesis in model.hypotheses:
        assert hypothesis.pattern in svg


def test_svg_renderer_inspection_payload_preserves_unknown_evidence():
    model = _read_model()
    hypothesis = model.hypotheses[0].model_copy(
        update={"supporting_evidence": ["missing-evidence-ref"]}
    )
    model = model.model_copy(update={"hypotheses": [hypothesis, *model.hypotheses[1:]]})
    svg = render_svg(model)

    assert "missing-evidence-ref" in svg
    assert 'if (!evidence)' in svg
    assert "UNKNOWN" in svg
    assert "expression: UNKNOWN" in svg


def test_svg_renderer_interaction_keeps_structural_ids_stable():
    model = _read_model()
    first = render_svg(model)
    second = render_svg(model)

    assert first == second
    for item in [*model.nodes, *model.edges]:
        assert f'data-read-model-id="{item.id}"' in first


def test_svg_renderer_static_is_default_and_has_no_active_motion_mode():
    model = _read_model()
    default_svg = render_svg(model)
    explicit_svg = render_svg(model, mode="static")
    root = ElementTree.fromstring(default_svg)

    assert default_svg == explicit_svg
    assert root.attrib["data-animation-mode"] == "static"
    assert "mode-static" in root.attrib["class"]
    assert 'data-animation-mode="animated"' in default_svg


def test_svg_renderer_animated_mode_is_valid_and_deterministic():
    model = _read_model()
    first = render_svg(model, mode="animated")
    second = render_svg(model, mode="animated")
    root = ElementTree.fromstring(first)

    assert first == second
    assert root.attrib["data-animation-mode"] == "animated"
    assert "mode-animated" in root.attrib["class"]
    assert "@keyframes flowPulse" in first
    assert "data-animation-semantic=\"resource-identified\"" in first
    assert "data-read-model-id=" in first
    assert "data-evidence-refs=" in first


def test_svg_renderer_does_not_animate_unknown_infrastructure():
    from architecture_recovery.ir import EvidenceStatus

    model = _read_model()
    database = next(node for node in model.nodes if node.kind == "database")
    unknown_database = database.model_copy(
        update={"status": EvidenceStatus.UNKNOWN, "confidence": 0.0}
    )
    model = model.model_copy(update={
        "nodes": [
            unknown_database if node.id == database.id else node
            for node in model.nodes
        ]
    })
    root = ElementTree.fromstring(render_svg(model, mode="animated"))
    rendered = next(
        element for element in root.iter()
        if element.attrib.get("data-read-model-id") == database.id
    )

    assert rendered.find(".//*[@data-animation-semantic]") is None


def test_svg_renderer_animated_mode_preserves_read_model_and_inspection():
    model = _read_model()
    before = model.model_dump_json()
    svg = render_svg(model, mode="animated")
    after = model.model_dump_json()

    assert before == after
    assert 'id="inspection-panel"' in svg
    assert "select(kind, id)" in svg
    for item in [*model.nodes, *model.edges]:
        assert f'data-read-model-id="{item.id}"' in svg


def test_svg_renderer_rejects_unknown_animation_mode():
    model = _read_model()

    try:
        render_svg(model, mode="pulse")
    except ValueError as exc:
        assert "static" in str(exc).lower()
        assert "animated" in str(exc).lower()
    else:
        raise AssertionError("renderer accepted an unknown animation mode")
