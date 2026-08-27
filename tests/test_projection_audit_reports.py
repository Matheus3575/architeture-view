from __future__ import annotations

import json
from pathlib import Path

import pytest

from architecture_recovery import cli
from architecture_recovery.ir import (
    ArchitectureIR,
    ArchitecturalGraph,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.profiling import AnalysisProfile
from architecture_recovery.visualization import (
    ArchitecturalProjectionBuilder,
    HighLevelArchitectureProjection,
    ProjectionAudit,
    ProjectionContextLink,
    ProjectionExplanation,
    SignificanceLevel,
    audit_projection,
    build_projection_audit_report,
    render_projection_audit_json,
    render_projection_audit_markdown,
)


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "visualization_read_model"


def _stress_ir(count: int = 10_000) -> ArchitectureIR:
    refs = [f"report-stress-{index:05d}" for index in range(count)]
    evidence = [
        Evidence(
            id=ref,
            source_type=EvidenceSource.CALL_GRAPH,
            detail="report stress observation",
            source=SourceRef(path="stress.py", start_line=(index % 20) + 1),
        )
        for index, ref in enumerate(refs)
    ]
    repository = Node(
        id="repository:report-stress",
        type=NodeType.REPOSITORY,
        name="report-stress",
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=[refs[0]],
    )
    application = Node(
        id="application:report-stress",
        type=NodeType.APPLICATION,
        name="report-stress-app",
        origin=SourceOrigin.FIRST_PARTY,
        evidence_refs=refs,
    )
    edge = Edge(
        id="edge:report-stress",
        source=application.id,
        target=repository.id,
        type=EdgeType.DEPENDS_ON,
        evidence_refs=refs,
    )
    nodes = [repository, application]
    return ArchitectureIR(
        repository=RepositoryInfo(name="report-stress", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=[edge]),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=[edge]),
        evidence=evidence,
    )


def test_audit_cli_generates_both_reports_from_one_analysis(monkeypatch, tmp_path, capsys):
    analyzed = analyze_repository(FIXTURE)
    calls = {"count": 0}

    def fake_analyze(repository, **kwargs):
        calls["count"] += 1
        assert kwargs == {}
        return analyzed

    monkeypatch.setattr(cli, "analyze_repository", fake_analyze)
    assert cli.main(["audit", str(FIXTURE), "--output-dir", str(tmp_path)]) == 0

    assert calls["count"] == 1
    assert (tmp_path / "architecture-audit.md").exists()
    assert (tmp_path / "architecture-audit.json").exists()
    payload = json.loads((tmp_path / "architecture-audit.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1"
    assert payload["summary"]["projected_nodes"] == len(payload["nodes"])
    assert "Projection Audit complete." in capsys.readouterr().out


def test_audit_cli_supports_single_formats(tmp_path):
    assert cli.main([
        "audit", str(FIXTURE), "--output-dir", str(tmp_path / "md"), "--format", "markdown"
    ]) == 0
    assert (tmp_path / "md" / "architecture-audit.md").exists()
    assert not (tmp_path / "md" / "architecture-audit.json").exists()

    assert cli.main([
        "audit", str(FIXTURE), "--output-dir", str(tmp_path / "json"), "--format", "json"
    ]) == 0
    assert (tmp_path / "json" / "architecture-audit.json").exists()
    assert not (tmp_path / "json" / "architecture-audit.md").exists()


def test_audit_reports_are_deterministic(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    cli.main(["audit", str(FIXTURE), "--output-dir", str(first_dir)])
    cli.main(["audit", str(FIXTURE), "--output-dir", str(second_dir)])

    assert (first_dir / "architecture-audit.json").read_bytes() == (second_dir / "architecture-audit.json").read_bytes()
    assert (first_dir / "architecture-audit.md").read_bytes() == (second_dir / "architecture-audit.md").read_bytes()


def test_audit_reports_refuse_overwrite_without_force(tmp_path):
    cli.main(["audit", str(FIXTURE), "--output-dir", str(tmp_path)])
    with pytest.raises(FileExistsError, match="Use --force"):
        cli.main(["audit", str(FIXTURE), "--output-dir", str(tmp_path)])
    assert cli.main(["audit", str(FIXTURE), "--output-dir", str(tmp_path), "--force"]) == 0


def test_audit_profile_is_embedded_without_second_analysis(monkeypatch, tmp_path):
    analyzed = analyze_repository(FIXTURE)
    calls = {"count": 0}

    def fake_analyze(repository, **kwargs):
        calls["count"] += 1
        assert isinstance(kwargs.get("profile"), AnalysisProfile)
        return analyzed

    monkeypatch.setattr(cli, "analyze_repository", fake_analyze)
    cli.main(["audit", str(FIXTURE), "--output-dir", str(tmp_path), "--profile"])

    payload = json.loads((tmp_path / "architecture-audit.json").read_text(encoding="utf-8"))
    assert calls["count"] == 1
    assert "projection_audit" in payload["profile"]["stages"]
    assert "projection_audit" in payload["profile"]["stages"]


def test_large_evidence_associations_are_compact_and_counted():
    ir = _stress_ir()
    before = ir.model_dump_json()
    projection = ArchitecturalProjectionBuilder().build(ir)
    audit = audit_projection(ir, projection)
    report = build_projection_audit_report(ir, projection, audit)

    payload = render_projection_audit_json(report)
    markdown = render_projection_audit_markdown(report)
    assert ir.model_dump_json() == before
    assert len(payload) < 250_000
    assert "report-stress-00000" not in payload
    assert "report-stress-00000" not in markdown
    assert report["evidence_groups"][0]["evidence_count"] == 10_000
    assert any(node.get("evidence_group_ref") for node in report["nodes"])
    assert all("evidence_refs" not in node for node in report["nodes"])


def test_audit_parser_rejects_unknown_format():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["audit", ".", "--format", "html"])


def test_report_payload_contains_projection_relation_and_hypothesis_sections(tmp_path):
    cli.main(["audit", str(FIXTURE), "--output-dir", str(tmp_path)])
    payload = json.loads((tmp_path / "architecture-audit.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "architecture-audit.md").read_text(encoding="utf-8")

    assert {"repository", "summary", "projection", "nodes", "relations", "hypotheses", "metrics", "diagnostics"} <= payload.keys()
    assert "## Projected Relations" in markdown
    assert "## DEPENDS_ON Audit" in markdown
    assert "## Hypothesis Context Audit" in markdown
    assert "## Diagnostics" in markdown
    assert payload["metrics"]["local_only_projected_count"] == 0
    assert payload["metrics"]["projected_without_global_justification_count"] == 0
    assert "local-only significant / projected" in markdown


def test_large_context_chain_and_raw_edge_lists_are_compact():
    ir = _stress_ir()
    refs = [item.id for item in ir.evidence]
    audit = ProjectionAudit(
        projected_node_count=1,
        node_explanations=[ProjectionExplanation(
            subject_id="application:report-stress", significance=SignificanceLevel.HIGH, score=1.0, projection_eligible=True,
            evidence_refs=refs, context_root_ids=["application:report-stress"],
            context_chain=[ProjectionContextLink(root_id="application:report-stress", subject_id="application:report-stress", relation_kind="CONTEXT_ROOT", chain=["application:report-stress"], evidence_refs=refs)],
        )],
    )
    projection = HighLevelArchitectureProjection(detailed_node_count=1, high_level_node_count=1, projected_node_ids=["application:report-stress"])
    report = build_projection_audit_report(ir, projection, audit)
    node = report["nodes"][0]
    assert node["context_chain"][0]["evidence_group_ref"]
    assert "evidence_refs" not in node["context_chain"][0]
    assert report["evidence_groups"][0]["source_ref_count"] == 1
    assert len(report["evidence_groups"][0]["source_refs"]) == 1
