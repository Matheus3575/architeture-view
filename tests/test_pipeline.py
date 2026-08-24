from __future__ import annotations

import json
from pathlib import Path

from architecture_recovery.ir import ArchitectureIR, Edge, EdgeType, Node, NodeType, RepositoryInfo
from architecture_recovery.architecture import ArchitectureHypothesisEngine
from architecture_recovery.pipeline import analyze_repository
import architecture_recovery.pipeline as pipeline_module
from architecture_recovery.rendering import render_graphml, render_mermaid
from architecture_recovery.validation import ArchitectureValidator


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "examples" / "simple_python_layered"


def test_pipeline_produces_valid_ir_with_evidence():
    ir = analyze_repository(str(FIXTURE))

    assert ir.schema_version == "0.2"
    assert ir.validation.valid
    assert any(item.name == "Python" for item in ir.stack.languages)
    assert any(item.name == "FastAPI" for item in ir.stack.frameworks)
    assert any(edge.type == EdgeType.IMPORTS for edge in ir.edges)
    assert any(edge.type == EdgeType.CALLS for edge in ir.edges)
    assert ir.evidence


def test_pipeline_is_deterministic():
    first = analyze_repository(str(FIXTURE)).model_dump_json()
    second = analyze_repository(str(FIXTURE)).model_dump_json()
    assert first == second


def test_validator_rejects_dangling_edge():
    ir = ArchitectureIR(
        repository=RepositoryInfo(name="test", path="."),
        nodes=[Node(id="a", type=NodeType.MODULE, name="a")],
        edges=[Edge(source="a", target="missing", type=EdgeType.DEPENDS_ON, evidence_refs=["missing-evidence"])],
    )
    report = ArchitectureValidator().validate(ir)
    assert not report.valid
    assert any("target" in error for error in report.errors)


def test_renderers_do_not_add_edges():
    ir = analyze_repository(str(FIXTURE))
    graphml = render_graphml(ir).decode("utf-8")
    mermaid = render_mermaid(ir)
    assert graphml.count("<edge ") == len(ir.architectural_graph.edges)
    assert mermaid.count("-->|") == len(ir.architectural_graph.edges)


def test_json_output_is_schema_serializable(tmp_path):
    ir = analyze_repository(str(FIXTURE))
    target = tmp_path / "architecture.json"
    target.write_text(json.dumps(ir.model_dump(mode="json")), encoding="utf-8")
    loaded = ArchitectureIR.model_validate_json(target.read_text(encoding="utf-8"))
    assert loaded.validation.valid


def test_pipeline_validates_ir_before_and_after_inference(monkeypatch):
    events: list[tuple[str, int]] = []

    class TrackingValidator(ArchitectureValidator):
        def validate(self, ir):
            events.append(("validate", len(ir.architecture.hypotheses)))
            return super().validate(ir)

    class TrackingEngine(ArchitectureHypothesisEngine):
        def infer(self, ir):
            events.append(("infer", 0))
            return super().infer(ir)

    monkeypatch.setattr(pipeline_module, "ArchitectureValidator", TrackingValidator)
    monkeypatch.setattr(pipeline_module, "ArchitectureHypothesisEngine", TrackingEngine)
    analyze_repository(str(FIXTURE))

    assert events[0] == ("validate", 0)
    assert events[1][0] == "infer"
    assert events[2][0] == "validate"
    assert events[2][1] > 0
