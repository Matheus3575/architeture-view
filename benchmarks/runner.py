from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from xml.etree import ElementTree
from typing import Any

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.rendering import render_svg
from architecture_recovery.visualization import VisualizationEvidence, VisualizationReadModelBuilder
from architecture_recovery.web import create_visualization_server


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "benchmarks" / "manifest.json"


def run_benchmarks(manifest_path: str | Path = DEFAULT_MANIFEST) -> list[dict[str, Any]]:
    manifest_file = Path(manifest_path).resolve()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for case in manifest["cases"]:
        ground_truth_path = (manifest_file.parent / case["ground_truth"]).resolve()
        ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
        repository = (PROJECT_ROOT / case["repository"]).resolve()
        try:
            started = time.perf_counter()
            first = analyze_repository(repository)
            second = analyze_repository(repository)
            result = evaluate_case(first, second, ground_truth)
            result["metrics"]["analysis_seconds"] = time.perf_counter() - started
            result["execution_passed"] = True
        except Exception as exc:  # pragma: no cover - failure is reported by the harness
            result = {
                "execution_passed": False,
                "quality_gate_passed": None,
                "passed": False,
                "failures": [f"execution error: {type(exc).__name__}: {exc}"],
                "metrics": {},
            }
        result["name"] = case["name"]
        result["repository"] = case["repository"]
        results.append(result)
    return results


def evaluate_case(first, second, ground_truth: dict[str, Any]) -> dict[str, Any]:
    raw_nodes = {node.id for node in first.raw_graph.nodes}
    raw_edges = {_edge_key(edge) for edge in first.raw_graph.edges}
    architectural_edges = {_edge_key(edge) for edge in first.architectural_graph.edges}
    failures: list[str] = []

    source_origin_metrics = _evaluate_source_origins(first, ground_truth, failures)
    raw_node_metrics = _evaluate_node_universe(raw_nodes, ground_truth.get("raw_nodes", {}), "raw node", failures)
    raw_edge_metrics = _evaluate_edge_universe(
        raw_edges, ground_truth.get("raw_edges", {}), "raw edge", failures
    )
    architectural_edge_metrics = _evaluate_edge_universe(
        architectural_edges,
        ground_truth.get("architectural_edges", {}),
        "architectural edge",
        failures,
    )
    resolution_metrics = _evaluate_resolutions(first, ground_truth, failures)
    unresolved_metrics = _evaluate_unresolved_calls(first, ground_truth, failures)
    decorator_metrics = _evaluate_decorators(first, ground_truth, failures)
    alias_metrics = _evaluate_aliases(first, ground_truth, failures)
    evidence_metrics = _evaluate_edge_support(first, ground_truth, failures)
    framework_metrics = _evaluate_framework_facts(first, ground_truth, failures)
    component_metrics = _evaluate_component_detection(first, ground_truth, failures)
    infrastructure_metrics = _evaluate_infrastructure(first, ground_truth, failures)
    hypothesis_metrics = _evaluate_hypotheses(first, ground_truth, failures)
    read_model_metrics = _evaluate_read_model(first, second, ground_truth, failures)

    deterministic = first.model_dump_json() == second.model_dump_json()
    if not deterministic:
        failures.append("analysis is not deterministic between executions")

    metrics = {
        **source_origin_metrics,
        **raw_node_metrics,
        **raw_edge_metrics,
        **architectural_edge_metrics,
        **resolution_metrics,
        **unresolved_metrics,
        **decorator_metrics,
        **alias_metrics,
        **evidence_metrics,
        **framework_metrics,
        **component_metrics,
        **infrastructure_metrics,
        **hypothesis_metrics,
        **read_model_metrics,
        "unknown_node_rate": _unknown_node_rate(first),
        "raw_node_count": len(first.raw_graph.nodes),
        "raw_edge_count": len(first.raw_graph.edges),
        "architectural_node_count": len(first.architectural_graph.nodes),
        "architectural_edge_count": len(first.architectural_graph.edges),
        "data_flow_resolution_count": sum(
            1 for item in _resolution_observations(first).values() if item.get("flow_evidence")
        ),
        "deterministic": deterministic,
    }
    quality_gate_passed = not failures
    return {
        "execution_passed": True,
        "quality_gate_passed": quality_gate_passed,
        "passed": quality_gate_passed,
        "failures": failures,
        "metrics": metrics,
    }


def _evaluate_hypotheses(ir, ground_truth, failures):
    expected = ground_truth.get("hypotheses", {})
    actual = {item.pattern: item for item in ir.architecture.hypotheses}
    required = expected.get("required", [])
    traceable = 0
    for item in required:
        hypothesis = actual.get(item["pattern"])
        if not hypothesis:
            failures.append(f"missing architecture hypothesis: {item['pattern']}")
            continue
        if item.get("status") and hypothesis.status.value != item["status"]:
            failures.append(f"wrong hypothesis status: {item['pattern']} expected {item['status']} got {hypothesis.status.value}")
        if item.get("requires_traceability") and not hypothesis.evidence_refs:
            failures.append(f"untraceable architecture hypothesis: {item['pattern']}")
        elif item.get("requires_no_support") and hypothesis.supporting_evidence:
            failures.append(f"unexpected support for hypothesis: {item['pattern']}")
        elif item.get("requires_support") and not hypothesis.supporting_evidence:
            failures.append(f"missing support for hypothesis: {item['pattern']}")
        elif item.get("requires_contradiction") and not hypothesis.contradicting_evidence:
            failures.append(f"missing contradiction for hypothesis: {item['pattern']}")
        else:
            traceable += 1
    forbidden = sorted(set(expected.get("forbidden", [])) & set(actual))
    failures.extend(f"forbidden architecture hypothesis: {item}" for item in forbidden)
    false_positive_count = sum(
        1 for item in required
        if item.get("status") == "unknown"
        and actual.get(item["pattern"])
        and actual[item["pattern"]].status.value != "unknown"
    )
    microservices = actual.get("microservices")
    microservices_expected = next((item for item in required if item["pattern"] == "microservices"), None)
    return {
        "hypothesis_evaluated": len(required),
        "hypothesis_recall": _ratio(len(required) - sum(1 for item in required if item["pattern"] not in actual), len(required)),
        "hypothesis_traceability_recall": _ratio(traceable, len(required)),
        "hypothesis_forbidden_count": len(forbidden),
        "hypothesis_false_positive_count": false_positive_count,
        "hypothesis_supporting_count": sum(len(item.supporting_evidence) for item in actual.values()),
        "hypothesis_contradicting_count": sum(len(item.contradicting_evidence) for item in actual.values()),
        "microservices_status": microservices.status.value if microservices else None,
        "microservices_hypothesis_recall": _ratio(1 if microservices and microservices_expected else 0, 1 if microservices_expected else 0),
        "microservices_traceability_recall": _ratio(
            1 if microservices and microservices.evidence_refs and microservices_expected else 0,
            1 if microservices_expected and microservices_expected.get("requires_traceability") else 0,
        ),
        "microservices_false_positive": bool(
            microservices and microservices_expected and microservices_expected.get("status") == "unknown"
            and microservices.status.value != "unknown"
        ),
        "microservices_contradiction_count": len(microservices.contradicting_evidence) if microservices else 0,
    }

def _evaluate_read_model(first, second, ground_truth, failures):
    spec = ground_truth.get("read_model")
    empty = {
        "architectural_significance_recall": None,
        "architectural_significance_precision": None,
        "high_level_node_count": None,
        "projection_node_count": None,
        "read_model_high_level_node_count": None,
        "semantic_detail_node_count": None,
        "boundary_exception_count": None,
        "framework_high_level_count": None,
        "framework_detail_count": None,
        "endpoint_high_level_count": None,
        "endpoint_detail_count": None,
        "router_high_level_count": None,
        "router_detail_count": None,
        "infrastructure_high_level_count": None,
        "infrastructure_detail_count": None,
        "container_high_level_count": None,
        "container_detail_count": None,
        "projection_closure_valid": None,
        "architectural_dependency_precision": None,
        "architectural_dependency_recall": None,
        "false_dependency_promotion_count": None,
        "generic_depends_on_promotion_count": None,
        "dependency_role_counts": None,
        "component_false_promotion_count": None,
        "detailed_node_count": None,
        "projection_reduction_ratio": None,
        "projected_edge_validity": None,
        "projection_traceability": None,
        "low_significance_preservation": None,
        "read_model_node_count": None,
        "read_model_edge_count": None,
        "read_model_edges_valid": None,
        "read_model_traceability": None,
        "read_model_deterministic": None,
        "svg_valid": None,
        "svg_complete": None,
        "svg_deterministic": None,
        "svg_inspection_metadata": None,
        "svg_relation_classes": None,
        "svg_layout_groups": None,
        "static_svg_valid": None,
        "animated_svg_valid": None,
        "static_deterministic": None,
        "animated_deterministic": None,
        "animation_semantics_preserved": None,
        "read_model_unchanged": None,
        "static_svg_bytes": None,
        "animated_svg_bytes": None,
        "web_static_available": None,
        "web_animated_available": None,
        "accessibility_metadata": None,
        "web_output_deterministic": None,
    }
    if not spec:
        return empty
    builder = VisualizationReadModelBuilder()
    first_model = builder.build(first)
    second_model = builder.build(second)
    stress_spec = spec.get("stress_evidence", {})
    projection_node_ids_before = {node.id for node in first_model.nodes}
    projection_edge_signature_before = {
        (edge.source, edge.target, edge.kind) for edge in first_model.edges
    }
    if stress_spec:
        first_model = _augment_evidence_stress(first_model, stress_spec, builder)
        second_model = _augment_evidence_stress(second_model, stress_spec, builder)
    node_ids = {node.id for node in first_model.nodes}
    valid_edges = all(
        edge.source in node_ids and edge.target in node_ids
        for edge in first_model.edges
    )
    if spec.get("require_all_edges_valid") and not valid_edges:
        failures.append("visualization read model contains an orphan edge")
    projection_spec = spec.get("projection", {})
    actual_significance = {item.subject: item.significance.value for item in first_model.architectural_significance}
    expected_significant = set(projection_spec.get("required_significant", []))
    expected_low = set(projection_spec.get("required_low_or_unknown", []))
    matched_significant = len(expected_significant & set(actual_significance))
    if expected_significant:
        missing = sorted(expected_significant - set(actual_significance))
        if missing:
            failures.append(f"missing architectural significance subjects: {missing}")
    if projection_spec.get("forbid_projected", []):
        forbidden_projected = set(projection_spec["forbid_projected"]) & set(node_ids)
        failures.extend(f"forbidden high-level projection node: {item}" for item in sorted(forbidden_projected))
    expected_external_promoted = set(projection_spec.get("expected_external_promoted", []))
    actual_external_promoted = {
        node.id for node in first_model.nodes
        if node.kind == "external_dependency"
    }
    false_dependency_promotions = len(actual_external_promoted - expected_external_promoted) if expected_external_promoted else None
    if expected_external_promoted and false_dependency_promotions:
        failures.extend(
            f"unexpected architectural dependency promotion: {item}"
            for item in sorted(actual_external_promoted - expected_external_promoted)
        )
    expected_forbidden_components = set(projection_spec.get("forbid_components", []))
    if not expected_forbidden_components:
        expected_forbidden_components = {
            item
            for item in projection_spec.get("forbid_projected", [])
            if any(node.id == item and node.type.value == "component" for node in first.architectural_graph.nodes)
        }
    actual_forbidden_components = {
        node.id for node in first_model.nodes
        if node.kind == "component" and node.id in expected_forbidden_components
    }
    if projection_spec.get("require_no_generic_dependency_promotions") and first_model.metadata.get("generic_depends_on_promotion_count", 0):
        failures.append("generic DEPENDS_ON promoted an external dependency")
    if expected_low and not expected_low <= set(actual_significance):
        failures.append("low/unknown significance was not preserved")
    expected_levels = projection_spec.get("expected_significance", {})
    for subject, expected_level in sorted(expected_levels.items()):
        if actual_significance.get(subject) != expected_level:
            failures.append(f"wrong significance for {subject}: expected {expected_level} got {actual_significance.get(subject)}")
    projection_metadata = first_model.metadata
    closure_allowed = set(projection_metadata.get("projection_node_ids", [])) | set(projection_metadata.get("boundary_node_ids", []))
    projection_closure_valid = node_ids <= closure_allowed if closure_allowed else True
    if not projection_closure_valid:
        failures.append("visualization read model escaped projection closure")
    if projection_spec.get("require_projected_edges_valid") and not projection_metadata.get("projected_edge_validity"):
        failures.append("projected edges are invalid")
    if projection_spec.get("require_projection_traceability") and not projection_metadata.get("projection_traceability"):
        failures.append("projection is not traceable")
    actual_kinds = {node.kind for node in first_model.nodes}
    missing_node_kinds = sorted(
        set(spec.get("required_node_kinds", [])) - actual_kinds
    )
    if missing_node_kinds:
        failures.append(f"missing visualization node kinds: {missing_node_kinds}")
    actual_edge_kinds = {edge.kind for edge in first_model.edges}
    missing_edge_kinds = sorted(
        set(spec.get("required_edge_kinds", [])) - actual_edge_kinds
    )
    if missing_edge_kinds:
        failures.append(f"missing visualization edge kinds: {missing_edge_kinds}")
    if spec.get("require_hypotheses") and not first_model.hypotheses:
        failures.append("visualization read model has no hypotheses")
    evidence_ids = {item.id for item in first_model.evidence}
    traceable = (
        all(
            ref in evidence_ids
            for item in [*first_model.nodes, *first_model.edges, *first_model.semantic_details, *first_model.hypotheses, *first_model.architectural_significance]
            for ref in item.evidence_refs
        )
        and all(
            ref in evidence_ids
            for group in first_model.evidence_groups
            for ref in group.evidence_refs
        )
    )
    if spec.get("require_traceability") and not traceable:
        failures.append("visualization read model is not traceable")
    deterministic = first_model.model_dump_json() == second_model.model_dump_json()
    if spec.get("require_determinism") and not deterministic:
        failures.append("visualization read model is not deterministic")

    svg_valid = svg_complete = svg_deterministic = None
    svg_inspection_metadata = svg_relation_classes = svg_layout_groups = None
    static_svg_valid = animated_svg_valid = None
    static_deterministic = animated_deterministic = None
    animation_semantics_preserved = read_model_unchanged = None
    static_svg_bytes = animated_svg_bytes = None
    web_static_available = web_animated_available = None
    accessibility_metadata = web_output_deterministic = None
    stress_metrics = {
        "svg_payload_bytes": None,
        "legacy_inline_svg_bytes": None,
        "evidence_payload_reduction_ratio": None,
        "evidence_reference_count": first_model.metadata.get("evidence_reference_count"),
        "inline_evidence_reference_count": first_model.metadata.get("inline_evidence_reference_count"),
        "evidence_group_count": first_model.metadata.get("evidence_group_count"),
        "evidence_traceability": traceable,
        "evidence_projection_semantics_unchanged": None,
    }
    if spec.get("svg"):
        before_render = first_model.model_dump_json()
        first_svg = render_svg(first_model, mode="static")
        second_svg = render_svg(second_model, mode="static")
        first_animated_svg = render_svg(first_model, mode="animated")
        second_animated_svg = render_svg(second_model, mode="animated")
        if stress_spec:
            legacy_svg = render_svg(_inline_evidence_model(first_model))
            stress_metrics.update({
                "svg_payload_bytes": len(first_svg.encode("utf-8")),
                "legacy_inline_svg_bytes": len(legacy_svg.encode("utf-8")),
                "evidence_payload_reduction_ratio": _ratio(
                    len(legacy_svg.encode("utf-8")) - len(first_svg.encode("utf-8")),
                    len(legacy_svg.encode("utf-8")),
                ),
                "evidence_projection_semantics_unchanged": (
                    projection_node_ids_before == {node.id for node in first_model.nodes}
                    and projection_edge_signature_before == {
                        (edge.source, edge.target, edge.kind) for edge in first_model.edges
                    }
                ),
            })
        after_render = first_model.model_dump_json()
        read_model_unchanged = before_render == after_render
        static_deterministic = first_svg == second_svg
        animated_deterministic = first_animated_svg == second_animated_svg
        static_svg_bytes = len(first_svg.encode("utf-8"))
        animated_svg_bytes = len(first_animated_svg.encode("utf-8"))
        try:
            root = ElementTree.fromstring(first_svg)
            svg_valid = root.tag.endswith("svg")
        except ElementTree.ParseError:
            root = None
            svg_valid = False
        try:
            animated_root = ElementTree.fromstring(first_animated_svg)
            static_svg_valid = svg_valid
            animated_svg_valid = animated_root.tag.endswith("svg")
        except ElementTree.ParseError:
            animated_root = None
            static_svg_valid = svg_valid
            animated_svg_valid = False
        try:
            web_server = create_visualization_server(
                first_svg,
                first_animated_svg,
                port=0,
            )
            web_static_available = True
            web_animated_available = True
            web_server.server_close()
        except (OSError, ValueError):
            web_static_available = False
            web_animated_available = False
        accessibility_metadata = (
            root is not None
            and root.attrib.get("role") == "img"
            and root.find("{http://www.w3.org/2000/svg}title") is not None
            and root.find("{http://www.w3.org/2000/svg}desc") is not None
            and "inspection-panel" in first_svg
        )
        web_output_deterministic = static_deterministic and animated_deterministic
        animation_semantics_preserved = (
            svg_valid
            and animated_svg_valid
            and root is not None
            and animated_root is not None
            and root.attrib.get("data-animation-mode") == "static"
            and animated_root.attrib.get("data-animation-mode") == "animated"
            and "@keyframes flowPulse" in first_animated_svg
            and 'data-animation-mode="animated"' in first_animated_svg
            and read_model_unchanged
        )
        rendered = {
            item.attrib.get("data-read-model-id")
            for item in root.iter()
            if item.attrib.get("data-read-model-id")
        } if svg_valid and root is not None else set()
        expected = {node.id for node in first_model.nodes} | {
            edge.id for edge in first_model.edges
        }
        svg_complete = expected <= rendered
        svg_deterministic = static_deterministic
        rendered_nodes = [
            item for item in root.iter()
            if item.attrib.get("id", "").startswith("node-")
        ] if root is not None else []
        rendered_edges = [
            item for item in root.iter()
            if item.attrib.get("id", "").startswith("edge-")
        ] if root is not None else []
        def has_evidence_binding(item):
            return (
                "data-evidence-count" in item.attrib
                and (
                    "data-evidence-refs" in item.attrib
                    or "data-evidence-group" in item.attrib
                    or item.attrib.get("data-evidence-count") == "0"
                )
            )

        svg_inspection_metadata = (
            all(
                all(key in item.attrib for key in (
                    "data-read-model-id", "data-label", "data-related-edge-ids",
                    "data-status", "data-confidence",
                )) and has_evidence_binding(item)
                for item in rendered_nodes
            )
            and all(
                all(key in item.attrib for key in (
                    "data-read-model-id", "data-source", "data-target",
                    "data-kind", "data-relation-class",
                    "data-status", "data-confidence",
                )) and has_evidence_binding(item)
                for item in rendered_edges
            )
        )
        svg_relation_classes = {
            item.attrib.get("data-relation-class") for item in rendered_edges
        }
        svg_layout_groups = [
            item.attrib.get("data-layout-group")
            for item in root.iter()
            if item.attrib.get("data-layout-group")
        ] if root is not None else []
        svg_spec = spec["svg"]
        if svg_spec.get("require_valid") and not svg_valid:
            failures.append("renderer did not produce valid SVG")
        if svg_spec.get("require_all_elements") and not svg_complete:
            failures.append("renderer omitted read-model elements")
        if svg_spec.get("require_determinism") and not svg_deterministic:
            failures.append("SVG renderer is not deterministic")
        animation_spec = spec.get("animation", {})
        if animation_spec.get("require_static_valid") and not static_svg_valid:
            failures.append("static SVG renderer output is invalid")
        if animation_spec.get("require_animated_valid") and not animated_svg_valid:
            failures.append("animated SVG renderer output is invalid")
        if animation_spec.get("require_static_deterministic") and not static_deterministic:
            failures.append("static SVG renderer is not deterministic")
        if animation_spec.get("require_animated_deterministic") and not animated_deterministic:
            failures.append("animated SVG renderer is not deterministic")
        if animation_spec.get("require_semantics_preserved") and not animation_semantics_preserved:
            failures.append("SVG animation semantics were not preserved")
        if animation_spec.get("require_read_model_unchanged") and not read_model_unchanged:
            failures.append("rendering changed the VisualizationReadModel")
        web_spec = spec.get("web", {})
        if web_spec.get("require_static_available") and not web_static_available:
            failures.append("static web route is unavailable")
        if web_spec.get("require_animated_available") and not web_animated_available:
            failures.append("animated web route is unavailable")
        if web_spec.get("require_accessibility_metadata") and not accessibility_metadata:
            failures.append("web accessibility metadata is incomplete")
        if web_spec.get("require_deterministic_output") and not web_output_deterministic:
            failures.append("web output is not deterministic")
        if svg_spec.get("require_inspection_metadata") and not svg_inspection_metadata:
            failures.append("SVG inspection metadata is incomplete")
        missing_classes = set(svg_spec.get("required_relation_classes", [])) - svg_relation_classes
        if missing_classes:
            failures.append(f"SVG missing relation classes: {sorted(missing_classes)}")
        missing_groups = set(svg_spec.get("required_layout_groups", [])) - set(svg_layout_groups)
        if missing_groups:
            failures.append(f"SVG missing layout groups: {sorted(missing_groups)}")

    if stress_spec:
        if stress_spec.get("require_group") and not first_model.evidence_groups:
            failures.append("evidence payload stress did not produce an evidence group")
        if stress_spec.get("require_traceability") and not traceable:
            failures.append("evidence payload stress is not traceable")
        if stress_spec.get("require_material_reduction") and (
            stress_metrics["evidence_payload_reduction_ratio"] is None
            or stress_metrics["evidence_payload_reduction_ratio"] < 0.3
        ):
            failures.append("evidence payload reduction was not material")

    return {
        "architectural_significance_recall": _ratio(matched_significant, len(expected_significant)),
        "architectural_significance_precision": _ratio(len(expected_significant & set(node_ids)), projection_metadata.get("high_level_node_count") or 0),
        "high_level_node_count": projection_metadata.get("high_level_node_count"),
        "projection_node_count": projection_metadata.get("projection_node_count"),
        "read_model_high_level_node_count": projection_metadata.get("read_model_high_level_node_count"),
        "semantic_detail_node_count": projection_metadata.get("semantic_detail_node_count"),
        "boundary_exception_count": projection_metadata.get("boundary_exception_count"),
        "framework_high_level_count": projection_metadata.get("framework_high_level_count"),
        "framework_detail_count": projection_metadata.get("framework_detail_count"),
        "endpoint_high_level_count": projection_metadata.get("endpoint_high_level_count"),
        "endpoint_detail_count": projection_metadata.get("endpoint_detail_count"),
        "router_high_level_count": projection_metadata.get("router_high_level_count"),
        "router_detail_count": projection_metadata.get("router_detail_count"),
        "infrastructure_high_level_count": projection_metadata.get("infrastructure_high_level_count"),
        "infrastructure_detail_count": projection_metadata.get("infrastructure_detail_count"),
        "container_high_level_count": projection_metadata.get("container_high_level_count"),
        "container_detail_count": projection_metadata.get("container_detail_count"),
        "projection_closure_valid": projection_closure_valid,
        "detailed_node_count": projection_metadata.get("detailed_node_count"),
        "projection_reduction_ratio": projection_metadata.get("projection_reduction_ratio"),
        "projected_edge_validity": projection_metadata.get("projected_edge_validity"),
        "projection_traceability": projection_metadata.get("projection_traceability"),
        "low_significance_preservation": bool(expected_low <= set(actual_significance)) if expected_low else projection_metadata.get("low_significance_preservation"),
        "false_architectural_promotion_count": len(set(projection_spec.get("forbid_projected", [])) & set(node_ids)),
        "external_dependency_detailed_count": sum(1 for node in first.architectural_graph.nodes if node.type.value == "external_dependency"),
        "external_dependency_projected_count": len(actual_external_promoted),
        "architectural_dependency_precision": _ratio(len(expected_external_promoted & actual_external_promoted), len(actual_external_promoted)) if expected_external_promoted else None,
        "architectural_dependency_recall": _ratio(len(expected_external_promoted & actual_external_promoted), len(expected_external_promoted)) if expected_external_promoted else None,
        "false_dependency_promotion_count": false_dependency_promotions,
        "generic_depends_on_promotion_count": projection_metadata.get("generic_depends_on_promotion_count"),
        "dependency_role_counts": projection_metadata.get("dependency_role_counts", {}),
        "component_false_promotion_count": len(actual_forbidden_components),
        "external_dependency_promotion_precision": _ratio(
            len(set(projection_spec.get("expected_external_promoted", [])) & set(node_ids)),
            sum(1 for node in first.architectural_graph.nodes if node.type.value == "external_dependency" and node.id in node_ids),
        ),
        "read_model_node_count": len(first_model.nodes),
        "read_model_edge_count": len(first_model.edges),
        "read_model_edges_valid": valid_edges,
        "read_model_traceability": traceable,
        "read_model_deterministic": deterministic,
        "svg_valid": svg_valid,
        "svg_complete": svg_complete,
        "svg_deterministic": svg_deterministic,
        "svg_inspection_metadata": svg_inspection_metadata,
        "svg_relation_classes": sorted(svg_relation_classes) if svg_relation_classes is not None else None,
        "svg_layout_groups": svg_layout_groups,
        "static_svg_valid": static_svg_valid,
        "animated_svg_valid": animated_svg_valid,
        "static_deterministic": static_deterministic,
        "animated_deterministic": animated_deterministic,
        "animation_semantics_preserved": animation_semantics_preserved,
        "read_model_unchanged": read_model_unchanged,
        "static_svg_bytes": static_svg_bytes,
        "animated_svg_bytes": animated_svg_bytes,
        "web_static_available": web_static_available,
        "web_animated_available": web_animated_available,
        "accessibility_metadata": accessibility_metadata,
        "web_output_deterministic": web_output_deterministic,
        **stress_metrics,
    }



def _augment_evidence_stress(model, spec, builder):
    target_id = spec.get("target")
    target = next((node for node in model.nodes if node.id == target_id), None)
    if target is None:
        raise ValueError(f"stress evidence target is not in the read model: {target_id}")
    prefix = spec.get("prefix", "synthetic-stress")
    count = int(spec.get("count", 0))
    refs = [f"{prefix}-{index:05d}" for index in range(count)]
    evidence = [
        VisualizationEvidence(
            id=ref,
            source_type="CALL_GRAPH",
            detail=f"synthetic payload observation {index}",
            source=None,
            weight=1.0,
        )
        for index, ref in enumerate(refs)
    ]
    updated_target = target.model_copy(update={
        "evidence_refs": sorted(set(target.evidence_refs) | set(refs)),
    })
    updated_nodes = [updated_target if node.id == target_id else node for node in model.nodes]
    updated_edges = [
        edge.model_copy(update={
            "evidence_refs": sorted(set(edge.evidence_refs) | set(refs)),
        })
        if edge.source == target_id or edge.target == target_id else edge
        for edge in model.edges
    ]
    augmented = model.model_copy(update={
        "nodes": updated_nodes,
        "edges": updated_edges,
        "evidence": [*model.evidence, *evidence],
        "evidence_groups": [],
    })
    return builder._compact_evidence(augmented)


def _inline_evidence_model(model):
    groups = {group.id: group for group in model.evidence_groups}

    def expand(item, field, group_field, count_field):
        group = groups.get(getattr(item, group_field, None))
        if group is None:
            return item
        return item.model_copy(update={
            field: list(group.evidence_refs),
            group_field: None,
            count_field: group.evidence_count,
        })

    nodes = [expand(item, "evidence_refs", "evidence_group_ref", "evidence_count") for item in model.nodes]
    edges = [expand(item, "evidence_refs", "evidence_group_ref", "evidence_count") for item in model.edges]
    semantic_details = [expand(item, "evidence_refs", "evidence_group_ref", "evidence_count") for item in model.semantic_details]
    hypotheses = []
    for item in model.hypotheses:
        expanded = expand(item, "evidence_refs", "evidence_group_ref", "evidence_count")
        expanded = expand(expanded, "supporting_evidence", "supporting_evidence_group_ref", "supporting_evidence_count")
        expanded = expand(expanded, "contradicting_evidence", "contradicting_evidence_group_ref", "contradicting_evidence_count")
        hypotheses.append(expanded)
    return model.model_copy(update={
        "nodes": nodes,
        "edges": edges,
        "semantic_details": semantic_details,
        "hypotheses": hypotheses,
        "evidence_groups": [],
    })


def _evaluate_source_origins(ir, ground_truth, failures):
    actual = {
        node.source.path: node.origin.value
        for node in ir.raw_graph.nodes
        if node.type.value == "file" and node.source
    }
    expected = ground_truth.get("source_origins", [])
    correct = 0
    for item in expected:
        path = item["path"]
        origin = item["origin"]
        if actual.get(path) == origin:
            correct += 1
        else:
            failures.append(f"wrong source origin: {path} expected {origin} got {actual.get(path)}")
    return {
        "source_origin_evaluated": len(expected),
        "source_origin_correct": correct,
        "source_origin_accuracy": _ratio(correct, len(expected)),
    }


def _evaluate_node_universe(actual, expected, label, failures):
    required = set(expected.get("required", []))
    forbidden = set(expected.get("forbidden", []))
    missing = sorted(required - actual)
    present_forbidden = sorted(forbidden & actual)
    failures.extend(f"missing {label}: {item}" for item in missing)
    failures.extend(f"forbidden {label}: {item}" for item in present_forbidden)
    return {
        "raw_node_required": len(required),
        "raw_node_recall": _ratio(len(required - set(missing)), len(required)),
        "raw_node_forbidden_count": len(present_forbidden),
    }


def _evaluate_edge_universe(actual, expected, label, failures):
    required = {_edge_key_from_dict(item) for item in expected.get("required", [])}
    forbidden = {_edge_key_from_dict(item) for item in expected.get("forbidden", [])}
    missing = sorted(required - actual)
    present_forbidden = sorted(forbidden & actual)
    failures.extend(f"missing {label}: {item}" for item in missing)
    failures.extend(f"forbidden {label}: {item}" for item in present_forbidden)
    prefix = label.replace(" ", "_")
    return {
        f"{prefix}_required": len(required),
        f"{prefix}_recall": _ratio(len(required - set(missing)), len(required)),
        f"{prefix}_forbidden_count": len(present_forbidden),
        # Partial ground truth does not define precision over all observed edges.
        f"{prefix}_precision": None,
    }


def _evaluate_resolutions(ir, ground_truth, failures):
    observed = _resolution_observations(ir)
    expected = ground_truth.get("symbol_resolutions", [])
    correct = 0
    unresolved = 0
    wrong = 0
    correct_unresolved = 0
    for item in expected:
        key = (item["path"], item["line"], item["caller"], item["callee"])
        actual = observed.get(key, {"status": "unresolved", "target": None})
        expected_status = item["status"]
        expected_target = item.get("target")
        if expected_status == "resolved" and actual["status"] == "resolved":
            if actual["target"] == expected_target:
                correct += 1
            else:
                wrong += 1
                failures.append(
                    f"wrong resolution: {key} expected {expected_target} got {actual['target']}"
                )
        elif expected_status == "resolved":
            unresolved += 1
            failures.append(f"unresolved expected symbol: {key} -> {expected_target}")
        elif actual["status"] == "unresolved":
            correct_unresolved += 1
        else:
            wrong += 1
            failures.append(f"unexpected resolution: {key} -> {actual['target']}")
    known_targets = sum(item["status"] == "resolved" for item in expected)
    return {
        "resolution_evaluated": len(expected),
        "correct_resolution_count": correct,
        "unresolved_resolution_count": unresolved,
        "correct_unresolved_count": correct_unresolved,
        "wrong_resolution_count": wrong,
        "wrong_resolution_rate": _ratio(wrong, len(expected)),
        "symbol_precision": _ratio(correct, correct + wrong),
        "symbol_recall": _ratio(correct, known_targets),
        "resolution_universe": "explicit symbol_resolutions entries only",
    }


def _evaluate_unresolved_calls(ir, ground_truth, failures):
    actual = {
        (item.caller, item.callee, item.source.path, item.source.start_line, item.reason)
        for item in ir.raw_graph.unresolved_calls
    }
    expected = {
        (item["caller"], item["callee"], item["path"], item["line"], item["reason"])
        for item in ground_truth.get("expected_unresolved_calls", [])
    }
    missing = sorted(expected - actual)
    failures.extend(f"missing expected unresolved call: {item}" for item in missing)
    return {
        "unresolved_call_evaluated": len(expected),
        "unresolved_call_recall": _ratio(len(expected - set(missing)), len(expected)),
    }


def _evaluate_decorators(ir, ground_truth, failures):
    actual = {}
    for node in ir.raw_graph.nodes:
        decorators = node.metadata.get("decorator_evidence", [])
        if decorators:
            actual[node.id] = decorators
    expected = ground_truth.get("decorator_evidence", [])
    correct = 0
    for item in expected:
        if actual.get(item["node_id"]) == item["decorators"]:
            correct += 1
        else:
            failures.append(f"missing decorator evidence: {item['node_id']}")
    return {"decorator_evidence_evaluated": len(expected), "decorator_evidence_recall": _ratio(correct, len(expected))}


def _evaluate_aliases(ir, ground_truth, failures):
    actual = {
        (
            edge.source,
            edge.target,
            edge.metadata.get("local_name"),
            edge.metadata.get("imported_name"),
        )
        for edge in ir.raw_graph.edges
        if edge.type.value == "IMPORTS"
    }
    expected = {
        (item["source"], item["target"], item["local_name"], item["imported_name"])
        for item in ground_truth.get("alias_evidence", [])
    }
    missing = sorted(expected - actual)
    failures.extend(f"missing alias evidence: {item}" for item in missing)
    return {"alias_evidence_evaluated": len(expected), "alias_evidence_recall": _ratio(len(expected - set(missing)), len(expected))}


def _evaluate_edge_support(ir, ground_truth, failures):
    raw_by_key = {_edge_key(edge): edge for edge in ir.raw_graph.edges}
    expected = ground_truth.get("edge_support", [])
    correct = 0
    for item in expected:
        edge = raw_by_key.get(_edge_key_from_dict(item))
        if edge is not None and edge.metadata.get("support_count", 1) >= item["min_support_count"]:
            correct += 1
        else:
            failures.append(f"insufficient edge support: {item}")
    return {"edge_support_evaluated": len(expected), "edge_support_recall": _ratio(correct, len(expected))}


def _evaluate_framework_facts(ir, ground_truth, failures):
    expected = ground_truth.get("required_facts", [])
    actual = list(ir.framework_facts)
    matched = 0
    for item in expected:
        candidates = [fact for fact in actual if fact.kind == item["kind"]]
        candidates = [
            fact
            for fact in candidates
            if all(fact.attributes.get(key) == value for key, value in item.get("attributes", {}).items())
            and (item.get("subject") is None or fact.subject == item["subject"])
            and (item.get("target") is None or fact.target == item["target"])
            and (item.get("status") is None or fact.status.value == item["status"])
        ]
        if candidates:
            matched += 1
        else:
            failures.append(f"missing framework fact: {item}")

    forbidden = ground_truth.get("forbidden_facts", [])
    forbidden_present = []
    for item in forbidden:
        if any(
            fact.kind == item["kind"]
            and all(fact.attributes.get(key) == value for key, value in item.get("attributes", {}).items())
            for fact in actual
        ):
            forbidden_present.append(item)
    failures.extend(f"forbidden framework fact: {item}" for item in forbidden_present)

    unknown_expected = ground_truth.get("unknown_facts", [])
    unknown_matched = 0
    for item in unknown_expected:
        if any(
            fact.kind == item["kind"]
            and fact.status.value == "unknown"
            and (item.get("subject") is None or fact.subject == item["subject"])
            and (item.get("target") is None or fact.target == item["target"])
            for fact in actual
        ):
            unknown_matched += 1
        else:
            failures.append(f"missing expected unknown framework fact: {item}")

    evidence_ids = {evidence.id for evidence in ir.evidence}
    traceable = all(fact.evidence_refs and set(fact.evidence_refs) <= evidence_ids for fact in actual)
    if ground_truth.get("evidence", {}).get("all_facts_traceable") and not traceable:
        failures.append("framework fact without valid evidence traceability")
    required_source = ground_truth.get("evidence", {}).get("required_source_type")
    source_types = {evidence.source_type.value for evidence in ir.evidence}
    if required_source and required_source not in source_types:
        failures.append(f"missing framework evidence source: {required_source}")
    return {
        "framework_fact_required": len(expected),
        "framework_fact_recall": _ratio(matched, len(expected)),
        "framework_fact_forbidden_count": len(forbidden_present),
        "framework_unknown_expected": len(unknown_expected),
        "framework_unknown_recall": _ratio(unknown_matched, len(unknown_expected)),
        "framework_fact_count": len(actual),
        "framework_facts_traceable": traceable,
        "framework_fact_precision": _framework_fact_precision(actual, expected)
        if ground_truth.get("facts_complete") else None,
    }


def _framework_fact_precision(actual, expected):
    def key(item):
        if hasattr(item, "kind"):
            return (
                item.kind,
                item.subject,
                item.target,
                tuple(sorted(item.attributes.items())),
                item.status.value,
            )
        return (
            item["kind"],
            item.get("subject"),
            item.get("target"),
            tuple(sorted(item.get("attributes", {}).items())),
            item.get("status", "observed"),
        )
    expected_keys = {key(item) for item in expected}
    actual_keys = {key(item) for item in actual}
    if not actual_keys:
        return 1.0 if not expected_keys else 0.0
    return len(actual_keys & expected_keys) / len(actual_keys)


def _evaluate_component_detection(ir, ground_truth, failures):
    spec = ground_truth.get("component_detection")
    actual = list(ir.component_candidates)
    if spec is None:
        return {
            "component_candidate_count": len(actual),
            "component_required_recall": None,
            "component_member_precision": None,
            "component_member_recall": None,
            "component_false_grouping_rate": None,
            "component_unassigned_recall": None,
            "component_evidence_recall": None,
        }

    actual_members = [set(component.node_ids) for component in actual]
    required = spec.get("required_components", [])
    matched = 0
    member_precision_values = []
    member_recall_values = []
    evidence_matched = 0
    for expected in required:
        expected_members = set(expected["members"])
        candidates = [members for members in actual_members if members == expected_members]
        overlap_candidates = [members for members in actual_members if members & expected_members]
        best = max(overlap_candidates, key=lambda members: len(members & expected_members), default=set())
        intersection = len(best & expected_members)
        member_precision_values.append(intersection / len(best) if best else 0.0)
        member_recall_values.append(intersection / len(expected_members) if expected_members else 1.0)
        if candidates:
            candidate = next(component for component in actual if set(component.node_ids) == expected_members)
            matched += 1
            if expected.get("status") and candidate.status.value != expected["status"]:
                failures.append(f"wrong component candidate status: {expected}")
            observed_types = {item.get("type") for item in candidate.supporting_observations}
            missing_types = sorted(set(expected.get("required_evidence_types", [])) - observed_types)
            if missing_types:
                failures.append(f"missing component evidence types: {missing_types}")
            if len(candidate.evidence_refs) < expected.get("min_evidence_refs", 0):
                failures.append(f"insufficient component evidence refs: {expected}")
            if not missing_types and len(candidate.evidence_refs) >= expected.get("min_evidence_refs", 0):
                evidence_matched += 1
        else:
            failures.append(f"missing component candidate: {expected_members}")

    forbidden = spec.get("forbidden_groupings", [])
    forbidden_present = [
        grouping for grouping in forbidden
        if any(set(grouping) <= members for members in actual_members)
    ]
    failures.extend(f"forbidden component grouping: {grouping}" for grouping in forbidden_present)

    expected_unassigned = set(spec.get("expected_unassigned", []))
    actual_unassigned = set(ir.component_unassigned_node_ids)
    missing_unassigned = sorted(expected_unassigned - actual_unassigned)
    failures.extend(f"expected unassigned node was assigned: {node_id}" for node_id in missing_unassigned)

    evidence_ids = {evidence.id for evidence in ir.evidence}
    traceable = all(
        component.evidence_refs and set(component.evidence_refs) <= evidence_ids
        for component in actual
    )
    if spec.get("evidence_recall", {}).get("all_candidates_traceable") and not traceable:
        failures.append("component candidate without valid evidence traceability")
    required_source = spec.get("evidence_recall", {}).get("required_source_type")
    if required_source and not any(evidence.source_type.value == required_source for evidence in ir.evidence):
        failures.append(f"missing component evidence source: {required_source}")

    return {
        "component_candidate_count": len(actual),
        "component_required_recall": _ratio(matched, len(required)),
        "component_member_precision": sum(member_precision_values) / len(member_precision_values) if member_precision_values else None,
        "component_member_recall": sum(member_recall_values) / len(member_recall_values) if member_recall_values else None,
        "component_false_grouping_rate": _ratio(len(forbidden_present), len(forbidden)),
        "component_unassigned_recall": _ratio(len(expected_unassigned & actual_unassigned), len(expected_unassigned)),
        "component_evidence_recall": _ratio(evidence_matched, len(required)),
        "component_candidates_traceable": traceable,
    }


def _evaluate_infrastructure(ir, ground_truth, failures):
    spec = ground_truth.get("infrastructure")
    actual_resources = list(ir.infrastructure_resources)
    actual_relations = list(ir.infrastructure_relations)

    if spec is None:
        return {
            "infrastructure_resource_count": len(actual_resources),
            "infrastructure_relation_count": len(actual_relations),
            "infrastructure_resource_precision": None,
            "infrastructure_resource_recall": None,
            "infrastructure_relation_precision": None,
            "infrastructure_relation_recall": None,
            "infrastructure_evidence_recall": None,
            "false_infrastructure_relation_rate": None,
        }

    expected_resources = spec.get("required_resources", [])
    matched_resources = 0
    for expected in expected_resources:
        found = False
        for actual in actual_resources:
            if actual.id == expected["id"]:
                found = True
                if actual.kind != expected["kind"]:
                    failures.append(
                        f"wrong infrastructure resource kind for {actual.id}: expected {expected['kind']} got {actual.kind}"
                    )
                if actual.name != expected["name"]:
                    failures.append(
                        f"wrong infrastructure resource name for {actual.id}: expected {expected['name']} got {actual.name}"
                    )
                break
        if found:
            matched_resources += 1
        else:
            failures.append(f"missing required infrastructure resource: {expected['id']}")

    forbidden_resources = spec.get("forbidden_resources", [])
    present_forbidden_resources = []
    for forbidden in forbidden_resources:
        if any(actual.id == forbidden for actual in actual_resources):
            present_forbidden_resources.append(forbidden)
            failures.append(f"forbidden infrastructure resource found: {forbidden}")

    expected_relations = spec.get("required_relations", [])
    matched_relations = 0
    for expected in expected_relations:
        found = False
        for actual in actual_relations:
            if actual.source == expected["source"] and actual.target == expected["target"]:
                found = True
                if expected.get("type") and actual.type != expected["type"]:
                    failures.append(
                        f"wrong infrastructure relation type for {actual.source}->{actual.target}: expected {expected['type']} got {actual.type}"
                    )
                break
        if found:
            matched_relations += 1
        else:
            failures.append(f"missing required infrastructure relation: {expected['source']} -> {expected['target']}")

    forbidden_relations = spec.get("forbidden_relations", [])
    present_forbidden_relations = []
    for forbidden in forbidden_relations:
        if any(actual.source == forbidden["source"] and actual.target == forbidden["target"] for actual in actual_relations):
            present_forbidden_relations.append(forbidden)
            failures.append(f"forbidden infrastructure relation found: {forbidden['source']} -> {forbidden['target']}")

    evidence_ids = {evidence.id for evidence in ir.evidence}
    traceable = all(
        res.evidence_refs and set(res.evidence_refs) <= evidence_ids
        for res in actual_resources
    ) and all(
        rel.evidence_refs and set(rel.evidence_refs) <= evidence_ids
        for rel in actual_relations
    )
    if spec.get("all_resources_traceable") and not traceable:
        failures.append("infrastructure resource/relation without valid evidence traceability")

    return {
        "infrastructure_resource_count": len(actual_resources),
        "infrastructure_relation_count": len(actual_relations),
        "infrastructure_resource_recall": _ratio(matched_resources, len(expected_resources)),
        "infrastructure_resource_precision": _ratio(matched_resources - len(present_forbidden_resources), len(actual_resources)),
        "infrastructure_relation_recall": _ratio(matched_relations, len(expected_relations)),
        "infrastructure_relation_precision": _ratio(matched_relations - len(present_forbidden_relations), len(actual_relations)),
        "infrastructure_evidence_recall": 1.0 if traceable else 0.0,
        "false_infrastructure_relation_rate": _ratio(len(present_forbidden_relations), len(forbidden_relations)),
    }


def _resolution_observations(ir):
    observations = {}
    for edge in ir.raw_graph.edges:
        if edge.type.value != "CALLS" or "callee" not in edge.metadata:
            continue
        metadata_items = [edge.metadata, *edge.metadata.get("supporting_observations", [])]
        for metadata in metadata_items:
            if "callee" not in metadata:
                continue
            key = (
                metadata.get("call_path"),
                metadata.get("call_line"),
                metadata.get("caller", edge.source),
                metadata["callee"],
            )
            observations[key] = {
                "status": "resolved",
                "target": metadata.get("resolved_target"),
                "flow_evidence": metadata.get("flow_evidence", []),
            }
    for call in ir.raw_graph.unresolved_calls:
        key = (call.source.path, call.source.start_line, call.caller, call.callee)
        observations[key] = {"status": "unresolved", "target": None, "flow_evidence": []}
    return observations


def _edge_key(edge):
    return edge.source, edge.target, edge.type.value


def _edge_key_from_dict(item):
    return item["source"], item["target"], item["type"]


def _unknown_node_rate(ir):
    if not ir.raw_graph.nodes:
        return 0.0
    return sum(node.origin.value == "unknown" for node in ir.raw_graph.nodes) / len(ir.raw_graph.nodes)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Architecture Recovery benchmarks")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    results = run_benchmarks(args.manifest)
    payload = json.dumps(results, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
