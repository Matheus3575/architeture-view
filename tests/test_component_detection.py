from __future__ import annotations

from pathlib import Path

from architecture_recovery.pipeline import analyze_repository


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "component_detection"


def test_component_candidate_groups_only_evidence_connected_first_party_modules():
    ir = analyze_repository(FIXTURE)

    assert len(ir.component_candidates) == 1
    candidate = ir.component_candidates[0]
    assert set(candidate.node_ids) == {
        "module:api",
        "module:logic",
        "module:repository",
    }
    assert candidate.status.value == "uncertain"
    assert candidate.internal_edge_ids
    assert candidate.external_edge_ids
    assert candidate.evidence_refs
    assert candidate.supporting_observations


def test_component_candidate_keeps_external_dependency_outside_first_party_members():
    ir = analyze_repository(FIXTURE)
    candidate = ir.component_candidates[0]

    assert not any(member.startswith("external:") for member in candidate.node_ids)
    assert any(
        node_id == "external_symbol:requests.get"
        for node_id in {edge.target for edge in ir.raw_graph.edges}
        if node_id.startswith("external_symbol:")
    )


def test_names_and_directory_proximity_are_not_sufficient_for_grouping():
    ir = analyze_repository(FIXTURE)

    assert "module:suggested_service" in ir.component_unassigned_node_ids
    assert "module:isolated" in ir.component_unassigned_node_ids
    assert all(
        "module:suggested_service" not in candidate.node_ids
        for candidate in ir.component_candidates
    )


def test_insufficient_schema_signal_remains_unassigned():
    ir = analyze_repository(FIXTURE)

    assert "module:schemas" in ir.component_unassigned_node_ids
    assert all("module:schemas" not in candidate.node_ids for candidate in ir.component_candidates)


def test_component_detection_does_not_add_raw_nodes_or_architecture_patterns():
    ir = analyze_repository(FIXTURE)

    assert not any(node.id.startswith("component-candidate:") for node in ir.raw_graph.nodes)
    assert not any(node.id.startswith("component-candidate:") for node in ir.architectural_graph.nodes)
    assert all(
        hypothesis.pattern not in {"MVC", "MVT", "Clean", "Hexagonal", "Microservices"}
        for hypothesis in ir.architecture.hypotheses
    )


def test_component_detection_is_deterministic_and_traceable():
    first = analyze_repository(FIXTURE)
    second = analyze_repository(FIXTURE)

    assert first.model_dump_json() == second.model_dump_json()
    evidence_ids = {evidence.id for evidence in first.evidence}
    assert all(
        set(candidate.evidence_refs) <= evidence_ids
        for candidate in first.component_candidates
    )
