from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pytest

from architecture_recovery import cli
from architecture_recovery.pipeline import analyze_repository


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "visualization_read_model"


def _fake_analyzer(monkeypatch):
    analyzed = analyze_repository(FIXTURE)
    calls = {"count": 0}

    def fake_analyze(repository, **kwargs):
        calls["count"] += 1
        assert str(repository) == str(FIXTURE)
        assert kwargs == {}
        return analyzed

    monkeypatch.setattr(cli, "analyze_repository", fake_analyze)
    return calls


def test_visualize_generates_static_svg_by_default(monkeypatch, tmp_path):
    calls = _fake_analyzer(monkeypatch)
    output = tmp_path / "architecture.svg"

    result = cli.main(["visualize", str(FIXTURE), "--output", str(output)])

    assert result == 0
    assert calls["count"] == 1
    root = ElementTree.fromstring(output.read_text(encoding="utf-8"))
    assert root.attrib["data-animation-mode"] == "static"
    assert not (tmp_path / "architecture-animated.svg").exists()


def test_visualize_animated_generates_both_files_with_one_analysis(monkeypatch, tmp_path):
    calls = _fake_analyzer(monkeypatch)
    output = tmp_path / "custom.svg"

    result = cli.main([
        "visualize",
        str(FIXTURE),
        "--output",
        str(output),
        "--animated",
    ])

    animated = tmp_path / "custom-animated.svg"
    assert result == 0
    assert calls["count"] == 1
    assert output.exists()
    assert animated.exists()
    assert ElementTree.fromstring(animated.read_text(encoding="utf-8")).attrib[
        "data-animation-mode"
    ] == "animated"


def test_visualize_is_deterministic(monkeypatch, tmp_path):
    _fake_analyzer(monkeypatch)
    first = tmp_path / "first.svg"
    second = tmp_path / "second.svg"

    cli.main(["visualize", str(FIXTURE), "--output", str(first)])
    cli.main(["visualize", str(FIXTURE), "--output", str(second)])

    assert first.read_bytes() == second.read_bytes()


def test_serve_generates_artifacts_and_passes_them_to_web_once(monkeypatch, tmp_path):
    calls = _fake_analyzer(monkeypatch)
    captured = {}

    def fake_serve(static_path, animated_path, *, host, port):
        captured.update({
            "static": Path(static_path),
            "animated": Path(animated_path) if animated_path else None,
            "host": host,
            "port": port,
        })

    monkeypatch.setattr(cli, "serve_visualization", fake_serve)
    output = tmp_path / "architecture.svg"

    result = cli.main([
        "serve",
        str(FIXTURE),
        "--output",
        str(output),
        "--animated",
        "--host",
        "127.0.0.1",
        "--port",
        "8123",
    ])

    assert result == 0
    assert calls["count"] == 1
    assert captured == {
        "static": output,
        "animated": tmp_path / "architecture-animated.svg",
        "host": "127.0.0.1",
        "port": 8123,
    }


def test_visualize_rejects_missing_repository():
    with pytest.raises(ValueError, match="not a directory"):
        cli.main(["visualize", "does-not-exist"])


def test_visualize_requires_repository_argument():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["visualize"])


def test_visualize_output_is_svg_not_architecture_json(monkeypatch, tmp_path):
    _fake_analyzer(monkeypatch)
    output = tmp_path / "result.svg"

    cli.main(["visualize", str(FIXTURE), "--output", str(output)])

    text = output.read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0"')
    assert "<svg " in text

def test_visualize_profile_prints_macro_report(monkeypatch, tmp_path, capsys):
    analyzed = analyze_repository(FIXTURE)
    captured = {}

    def fake_analyze(repository, **kwargs):
        captured["profile"] = kwargs["profile"]
        assert captured["profile"] is not None
        return analyzed

    monkeypatch.setattr(cli, "analyze_repository", fake_analyze)
    output = tmp_path / "profile.svg"

    assert cli.main(["visualize", str(FIXTURE), "--output", str(output), "--profile"]) == 0
    assert "Architecture Recovery Profile" in capsys.readouterr().out
    assert set(captured["profile"].stages) >= {
        "architectural_significance_projection",
        "visualization_read_model",
        "svg_rendering",
    }
