from pathlib import Path

import pytest

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.visualization import (
    VisualizationNode,
    VisualizationReadModelBuilder,
    validate_visualization_read_model,
)


ROOT = Path(__file__).parents[1]
FASTAPI_FIXTURE = ROOT / "benchmarks" / "fixtures" / "fastapi_semantics"
INFRA_FIXTURE = ROOT / "benchmarks" / "fixtures" / "infrastructure_semantics"
HYPOTHESIS_FIXTURE = ROOT / "benchmarks" / "fixtures" / "hypothesis_engine"


def test_read_model_preserves_framework_facts_as_details_and_closes_projection():
    ir = analyze_repository(FASTAPI_FIXTURE)
    read_model = VisualizationReadModelBuilder().build(ir)

    node_ids = {node.id for node in read_model.nodes}
    assert all(edge.source in node_ids and edge.target in node_ids for edge in read_model.edges)
    assert not any(node.kind in {"endpoint", "router", "unknown"} for node in read_model.nodes)
    assert any(detail.kind == "framework_fact" and detail.attributes.get("path") for detail in read_model.semantic_details)
    assert any(detail.kind == "framework_fact" and detail.subject == "users_router" for detail in read_model.semantic_details)
    assert read_model.unknowns == []
    assert read_model.metadata["projection_node_count"] == read_model.metadata["read_model_high_level_node_count"]
    assert read_model.metadata["boundary_exception_count"] == 0
    assert read_model.metadata["projected_edge_validity"] is True
    assert read_model.metadata["projection_traceability"] is True
    assert read_model.hypotheses
    assert all(hypothesis.evidence_refs for hypothesis in read_model.hypotheses if hypothesis.evidence_refs)
    evidence_ids = {item.id for item in read_model.evidence}
    assert all(
        ref in evidence_ids
        for item in [*read_model.nodes, *read_model.edges, *read_model.semantic_details, *read_model.hypotheses]
        for ref in item.evidence_refs
    )


def test_read_model_preserves_infrastructure_as_distinct_nodes():
    ir = analyze_repository(INFRA_FIXTURE)
    read_model = VisualizationReadModelBuilder().build(ir)

    assert any(node.layout_hints.get("semantic_kind") == "infrastructure" or node.kind == "infrastructure" for node in read_model.nodes)
    assert any(node.kind == "database" for node in read_model.nodes)
    assert any(edge.kind == "DEPENDS_ON" for edge in read_model.edges)
    assert all(node.origin_ref for node in read_model.nodes)


def test_read_model_preserves_hypotheses_as_hypotheses():
    ir = analyze_repository(HYPOTHESIS_FIXTURE)
    read_model = VisualizationReadModelBuilder().build(ir)

    layered = next(item for item in read_model.hypotheses if item.pattern == "layered")
    assert layered.status.value == "inferred"
    assert layered.evidence_refs
    assert not any(node.kind in {"layered", "mvc"} for node in read_model.nodes)


def test_read_model_is_deterministic_and_does_not_mutate_ir():
    ir = analyze_repository(FASTAPI_FIXTURE)
    before = ir.model_dump_json()

    first = VisualizationReadModelBuilder().build(ir)
    second = VisualizationReadModelBuilder().build(ir)

    assert first.model_dump_json() == second.model_dump_json()
    assert ir.model_dump_json() == before


def test_read_model_validator_rejects_orphan_edges():
    ir = analyze_repository(FASTAPI_FIXTURE)
    read_model = VisualizationReadModelBuilder().build(ir)
    read_model.edges.append(
        read_model.edges[0].model_copy(update={"id": "orphan", "target": "missing-node"})
    )

    report = validate_visualization_read_model(
        read_model,
        {item.id for item in ir.evidence},
    )
    assert not report.valid
    assert any("target does not exist" in error for error in report.errors)
