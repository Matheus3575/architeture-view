from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from architecture_recovery.pipeline import analyze_repository


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
    }


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
