from __future__ import annotations

import json
from pathlib import Path

import pytest

from architecture_recovery import cli
from architecture_recovery.ir import ArchitectureIR, EdgeType, NodeType
from architecture_recovery.pipeline import analyze_repository


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "examples" / "simple_python_layered"
COMPOSE_FIXTURE = ROOT / "examples" / "compose_stack"


def test_pipeline_integrates_compose_services_and_relationships():
    ir = analyze_repository(COMPOSE_FIXTURE)

    containers = {node.name: node for node in ir.nodes if node.type in {NodeType.CONTAINER, NodeType.DATABASE, NodeType.CACHE}}
    assert set(containers) == {"api", "database", "cache"}
    assert sum(edge.type == EdgeType.DEPLOYS for edge in ir.edges) == 3
    assert {
        (edge.source, edge.target)
        for edge in ir.edges
        if edge.type == EdgeType.CONNECTS_TO
    } == {
        ("container:api", "container:database"),
        ("container:api", "container:cache"),
    }
    assert any(evidence.source_type.value == "DOCKER_COMPOSE" for evidence in ir.evidence)


def test_remote_analysis_uses_clone_context_and_preserves_origin(monkeypatch):
    captured: dict[str, str | None] = {}

    class FakeClone:
        def __enter__(self):
            return COMPOSE_FIXTURE

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    def fake_clone(url: str, ref: str | None = None):
        captured["url"] = url
        captured["ref"] = ref
        return FakeClone()

    monkeypatch.setattr("architecture_recovery.pipeline.cloned_repository", fake_clone)
    ir = analyze_repository("https://github.com/example/remote-project.git", ref="release-1")

    assert captured == {
        "url": "https://github.com/example/remote-project.git",
        "ref": "release-1",
    }
    assert ir.repository.name == "remote-project"
    assert ir.repository.source_url == "https://github.com/example/remote-project.git"


def test_local_analysis_rejects_ref():
    with pytest.raises(ValueError, match="only be used with a repository URL"):
        analyze_repository(FIXTURE, ref="main")


def test_main_cli_forwards_ref_and_writes_json(monkeypatch, tmp_path):
    captured: dict[str, str | None] = {}
    output = tmp_path / "architecture.json"
    classification_output = tmp_path / "classification.json"
    analyzed = analyze_repository(FIXTURE)

    def fake_analyze(repository: str, ref: str | None = None):
        captured["repository"] = repository
        captured["ref"] = ref
        return analyzed

    monkeypatch.setattr(cli, "analyze_repository", fake_analyze)
    result = cli.main(
        [
            "analyze",
            "https://github.com/example/project.git",
            "--branch",
            "main",
            "--output",
            str(output),
            "--classification-report",
            str(classification_output),
        ]
    )

    assert result == 0
    assert captured == {
        "repository": "https://github.com/example/project.git",
        "ref": "main",
    }
    assert ArchitectureIR.model_validate(json.loads(output.read_text(encoding="utf-8"))).validation.valid
    assert json.loads(classification_output.read_text(encoding="utf-8"))["records"]
