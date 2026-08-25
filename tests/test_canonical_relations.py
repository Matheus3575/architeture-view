from pathlib import Path

from architecture_recovery.ir import InfrastructureRelation, canonical_relation_type
from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.rendering import render_svg
from architecture_recovery.visualization import VisualizationReadModelBuilder


ROOT = Path(__file__).resolve().parents[1]


def test_infrastructure_relation_canonicalizes_and_preserves_source_type():
    lower = InfrastructureRelation(
        id="lower",
        source="a",
        target="b",
        type="depends_on",
        evidence_refs=["e1"],
    )
    upper = InfrastructureRelation(
        id="upper",
        source="a",
        target="b",
        type="DEPENDS_ON",
        evidence_refs=["e1"],
    )

    assert lower.type == "DEPENDS_ON"
    assert upper.type == "DEPENDS_ON"
    assert lower.metadata["source_relation_type"] == "depends_on"
    assert "source_relation_type" not in upper.metadata
    assert canonical_relation_type("connects_to") == "CONNECTS_TO"


def test_canonical_relation_identity_is_shared_by_read_model_and_svg():
    ir = analyze_repository(ROOT / "benchmarks" / "fixtures" / "infrastructure_semantics")
    model = VisualizationReadModelBuilder().build(ir)
    svg = render_svg(model)

    assert {relation.type for relation in ir.infrastructure_relations} <= {
        "DEPENDS_ON", "CONNECTS_TO"
    }
    assert {edge.kind for edge in model.edges} <= {
        "DEPENDS_ON", "CONNECTS_TO", "CONTAINS", "DEPLOYS"
    }
    assert "data-kind=\"depends_on\"" not in svg
    assert "data-kind=\"DEPENDS_ON\"" in svg
    assert model.metadata["projection_traceability"] is True
    assert all(
        ref in {evidence.id for evidence in model.evidence}
        for group in model.evidence_groups
        for ref in group.evidence_refs
    )
