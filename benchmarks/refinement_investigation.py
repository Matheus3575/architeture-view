"""Reproducible quality, relation and visualization investigation.

This module is deliberately outside the analysis pipeline.  It observes the
existing IR, projection, read model and SVG contracts without changing them.
Timing is reported for diagnosis only; structural metrics are the stable
regression surface.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.profiling import AnalysisProfile
from architecture_recovery.rendering import render_svg
from architecture_recovery.visualization import VisualizationReadModelBuilder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = (
    ("significance_calibration", PROJECT_ROOT / "benchmarks" / "fixtures" / "significance_calibration"),
    ("visualization_read_model", PROJECT_ROOT / "benchmarks" / "fixtures" / "visualization_read_model"),
    ("infrastructure_semantics", PROJECT_ROOT / "benchmarks" / "fixtures" / "infrastructure_semantics"),
    ("projection_many_modules", PROJECT_ROOT / "benchmarks" / "fixtures" / "projection_many_modules"),
    ("workspace", PROJECT_ROOT),
)


def generate_context_fixture(root: Path) -> Path:
    """Create a neutral, bounded repository for contextual-significance checks."""

    root.mkdir(parents=True, exist_ok=True)
    (root / "entry.py").write_text(
        "from fastapi import FastAPI\n"
        "from core import load_value\n\n"
        "app = FastAPI()\n\n"
        "@app.get('/value')\n"
        "def value():\n"
        "    return load_value()\n",
        encoding="utf-8",
    )
    (root / "core.py").write_text(
        "from helper import normalize\n\n"
        "def load_value():\n"
        "    return normalize('value')\n",
        encoding="utf-8",
    )
    (root / "helper.py").write_text(
        "def normalize(value):\n"
        "    return value.strip()\n",
        encoding="utf-8",
    )
    (root / "support.py").write_text(
        "from fastapi import FastAPI\n\n"
        "support_app = FastAPI()\n\n"
        "@support_app.get('/support')\n"
        "def support():\n"
        "    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    return root


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _canonical_model_signature(model: Any) -> str:
    return model.model_dump_json()


def _svg_metrics(svg: str) -> dict[str, Any]:
    root = ElementTree.fromstring(svg)
    view_box = root.attrib.get("viewBox", "").split()
    groups = Counter(
        element.attrib.get("data-layout-group", "")
        for element in root.iter()
        if element.attrib.get("data-layout-group")
    )
    node_elements = [
        element for element in root.iter()
        if element.attrib.get("data-selection-kind") == "node"
    ]
    edge_elements = [
        element for element in root.iter()
        if element.attrib.get("data-selection-kind") == "edge"
    ]
    labels = [element.attrib.get("data-label", "") for element in node_elements]
    return {
        "valid": root.tag.endswith("svg"),
        "bytes": len(svg.encode("utf-8")),
        "width": int(float(root.attrib.get("width", 0))),
        "height": int(float(root.attrib.get("height", 0))),
        "viewbox": view_box,
        "layout_groups": dict(sorted(groups.items())),
        "node_elements": len(node_elements),
        "edge_elements": len(edge_elements),
        "max_label_length": max((len(label) for label in labels), default=0),
    }


def _relation_metrics(ir: Any, model: Any) -> dict[str, Any]:
    architectural = list(ir.architectural_graph.edges)
    infrastructure = list(ir.infrastructure_relations)
    projected = list(model.edges)
    architectural_types = Counter(edge.type.value for edge in architectural)
    infrastructure_types = Counter(str(relation.type) for relation in infrastructure)
    projected_types = Counter(edge.kind for edge in projected)
    all_relation_types = set(architectural_types) | set(infrastructure_types)
    normalized_types = Counter(item.upper() for item in all_relation_types)
    mixed_case_groups = {
        key: sorted(
            item for item in all_relation_types
            if item.upper() == key
        )
        for key in normalized_types
        if len({item for item in all_relation_types if item.upper() == key}) > 1
    }
    evidence_group_ids = {group.id for group in model.evidence_groups}
    projected_with_evidence = sum(
        bool(edge.evidence_refs or edge.evidence_group_ref in evidence_group_ids)
        for edge in projected
    )
    projected_group_bindings = sum(bool(edge.evidence_group_ref) for edge in projected)
    architectural_with_evidence = sum(bool(edge.evidence_refs) for edge in architectural)
    return {
        "architectural_edge_count": len(architectural),
        "infrastructure_relation_count": len(infrastructure),
        "projected_edge_count": len(projected),
        "architectural_type_counts": dict(sorted(architectural_types.items())),
        "infrastructure_type_counts": dict(sorted(infrastructure_types.items())),
        "projected_type_counts": dict(sorted(projected_types.items())),
        "mixed_case_relation_groups": mixed_case_groups,
        "architectural_edge_evidence_coverage": _ratio(architectural_with_evidence, len(architectural)),
        "projected_edge_evidence_coverage": _ratio(projected_with_evidence, len(projected)),
        "projected_edges_without_evidence": len(projected) - projected_with_evidence,
        "projected_edge_evidence_group_bindings": projected_group_bindings,
        "projected_edge_support_total": sum(edge.support_count for edge in projected),
        "projected_raw_edge_reference_total": sum(len(edge.raw_edge_ids) for edge in projected),
    }


def _node_metrics(ir: Any, model: Any) -> dict[str, Any]:
    significance = Counter(item.significance.value for item in model.architectural_significance)
    projected_ids = {node.id for node in model.nodes}
    external_ids = {
        node.id for node in ir.architectural_graph.nodes
        if node.type.value == "external_dependency"
    }
    selected_external = projected_ids & external_ids
    component_ids = {
        node.id for node in ir.architectural_graph.nodes
        if node.type.value == "component"
    }
    selected_components = projected_ids & component_ids
    node_degree = Counter()
    for edge in model.edges:
        node_degree[edge.source] += 1
        node_degree[edge.target] += 1
    return {
        "raw_node_count": len(ir.raw_graph.nodes),
        "raw_edge_count": len(ir.raw_graph.edges),
        "architectural_node_count": len(ir.architectural_graph.nodes),
        "architectural_edge_count": len(ir.architectural_graph.edges),
        "projected_node_count": len(model.nodes),
        "semantic_detail_count": len(model.semantic_details),
        "significance_counts": dict(sorted(significance.items())),
        "external_dependency_detailed_count": len(external_ids),
        "external_dependency_projected_count": len(selected_external),
        "component_detailed_count": len(component_ids),
        "component_projected_count": len(selected_components),
        "max_projected_degree": max(node_degree.values(), default=0),
        "top_projected_degree_nodes": [
            {"id": node_id, "degree": degree}
            for node_id, degree in sorted(node_degree.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        "projection_closure_valid": all(
            edge.source in projected_ids and edge.target in projected_ids
            for edge in model.edges
        ),
        "projection_traceability": bool(model.metadata.get("projection_traceability")),
        "low_significance_preserved": bool(model.metadata.get("low_significance_preservation")),
    }


def _quality_metrics(name: str, model: Any) -> dict[str, Any]:
    ground_truth_path = PROJECT_ROOT / "benchmarks" / "ground_truth" / f"{name}.json"
    actual_projected = set(model.metadata.get("projection_node_ids", []))
    if ground_truth_path.exists():
        specification = json.loads(ground_truth_path.read_text(encoding="utf-8"))
        projection = specification.get("read_model", {}).get("projection", {})
        expected = set(projection.get("required_significant", []))
        forbidden = set(projection.get("forbid_projected", []))
        if expected:
            true_positive = len(expected & actual_projected)
            false_positive = len((actual_projected - expected) & forbidden)
            return {
                "ground_truth_available": True,
                "significance_precision": _ratio(true_positive, len(actual_projected)),
                "significance_recall": _ratio(true_positive, len(expected)),
                "false_architectural_promotions": false_positive,
                "expected_significant_count": len(expected),
                "actual_projected_count": len(actual_projected),
            }
    auxiliary_framework_promotions = sorted(
        item.subject
        for item in model.architectural_significance
        if item.subject == "component:support.py"
        and item.significance.value in {"high", "medium"}
    )
    return {
        "ground_truth_available": False,
        "significance_precision": None,
        "significance_recall": None,
        "false_architectural_promotions": None,
        "auxiliary_framework_promotions_observed": auxiliary_framework_promotions,
    }

def analyze_scenario(name: str, repository: Path) -> dict[str, Any]:
    started = time.perf_counter()
    profile = AnalysisProfile()
    ir = analyze_repository(repository, profile=profile)
    model = VisualizationReadModelBuilder().build(ir, profile=profile)
    static_svg = render_svg(model, mode="static")
    animated_svg = render_svg(model, mode="animated")
    unprofiled_ir = analyze_repository(repository)
    repeated_model = VisualizationReadModelBuilder().build(unprofiled_ir)
    elapsed = time.perf_counter() - started
    return {
        "name": name,
        "repository": str(repository),
        "elapsed_seconds": round(elapsed, 6),
        "profile_stages": profile.as_dict().get("stages", {}),
        "nodes": _node_metrics(ir, model),
        "quality": _quality_metrics(name, model),
        "relations": _relation_metrics(ir, model),
        "svg": {
            "static": _svg_metrics(static_svg),
            "animated": _svg_metrics(animated_svg),
            "static_animated_byte_difference": static_svg != animated_svg,
        },
        "determinism": {
            "ir_repeated": _canonical_model_signature(ir) == _canonical_model_signature(unprofiled_ir),
            "read_model_repeated": _canonical_model_signature(model) == _canonical_model_signature(repeated_model),
            "static_svg_repeated": static_svg == render_svg(model, mode="static"),
            "animated_svg_repeated": animated_svg == render_svg(model, mode="animated"),
        },
    }


def run_investigation(
    scenarios: Iterable[tuple[str, Path]] = DEFAULT_SCENARIOS,
    include_generated: bool = True,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for name, repository in scenarios:
        results.append(analyze_scenario(name, Path(repository)))
    if include_generated:
        with tempfile.TemporaryDirectory(prefix="architecture-recovery-investigation-") as value:
            generated = generate_context_fixture(Path(value) / "neutral-context")
            results.append(analyze_scenario("neutral_context_generated", generated))
    return {
        "schema_version": "0.1",
        "investigation": "algorithm_refinement",
        "algorithm_changes_applied": False,
        "timing_is_diagnostic": True,
        "scenarios": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    report = run_investigation()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print("Architecture Recovery Algorithm Refinement Investigation")
    print("scenario                         projected  edges  ext detailed/projected  SVG bytes  deterministic")
    for scenario in report["scenarios"]:
        nodes = scenario["nodes"]
        svg = scenario["svg"]["static"]
        deterministic = all(scenario["determinism"].values())
        print(
            f"{scenario['name']:<32} {nodes['projected_node_count']:>9} "
            f"{scenario['relations']['projected_edge_count']:>6} "
            f"{nodes['external_dependency_detailed_count']:>4}/{nodes['external_dependency_projected_count']:<4} "
            f"{svg['bytes']:>9}  {str(deterministic):>13}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
